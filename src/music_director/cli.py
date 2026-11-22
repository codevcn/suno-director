"""Unified CLI entry point for Suno Director (`sudirector`)."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

from .common import dump_yaml, load_yaml
from .execution_guard import main as preflight_main
from .paths import default_skill_targets, global_skill_source_dir, templates_dir
from .render_suno_pack import main as render_main
from .updater import UpdateError, check_for_update, maybe_notify_update, perform_update, refresh_cache_silently
from .validate_spec import main as validate_main
from .version import VERSION, bump_semver, compare_semver, format_version_info, parse_semver

_SLUG_RE = re.compile(r"[^a-z0-9-]+")


def _normalize_slug(raw: str) -> str:
    slug = _SLUG_RE.sub("-", raw.strip().lower()).strip("-")
    if not slug:
        raise ValueError(f"Invalid song slug '{raw}'.")
    return slug


def _cmd_init(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="sudirector init", description="Initialize a song workspace from SONG-SPEC template.")
    parser.add_argument("slug", help="Song workspace slug (e.g. midnight-neon)")
    parser.add_argument("--dir", type=Path, default=Path.cwd() / "workspace", help="Base workspace directory (default: ./workspace)")
    parser.add_argument("--title", default=None, help="Optional song title")
    parser.add_argument("--language", default="en", help="Primary lyric language code (default: en)")
    parser.add_argument("--instrumental", action="store_true", help="Set vocal.enabled: false")
    parser.add_argument("--force", action="store_true", help="Overwrite existing SONG-SPEC.yaml if present")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit JSON output")
    args = parser.parse_args(argv)

    slug = _normalize_slug(args.slug)
    song_dir = args.dir / slug
    spec_path = song_dir / "SONG-SPEC.yaml"
    if spec_path.exists() and not args.force:
        msg = f"SONG-SPEC already exists: {spec_path} (use --force to overwrite)"
        if args.as_json:
            print(json.dumps({"initialized": False, "error": msg}))
        else:
            print(f"ERROR: {msg}", file=sys.stderr)
        return 1

    template = load_yaml(templates_dir() / "SONG-SPEC.yaml")
    template["identity"]["title"] = args.title or slug.replace("-", " ").title()
    template["identity"]["language"] = args.language
    template["lyrics"]["language"] = args.language
    if args.instrumental:
        template["vocal"]["enabled"] = False
        template["vocal"]["singer_count"] = 0

    (song_dir / "exports").mkdir(parents=True, exist_ok=True)
    (song_dir / "runs").mkdir(parents=True, exist_ok=True)
    dump_yaml(template, spec_path)

    if args.as_json:
        print(json.dumps({"initialized": True, "slug": slug, "song_dir": str(song_dir), "spec_path": str(spec_path)}))
    else:
        print(f"INITIALIZED: {spec_path}")
    return 0


def _cmd_install_skill(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="sudirector install-skill",
        description="Install the Global AI Skill (suno-director) for Codex, Antigravity, and Claude Code.",
    )
    parser.add_argument(
        "--agents",
        nargs="+",
        choices=["codex", "antigravity", "claude"],
        default=["codex", "antigravity", "claude"],
        help="Target AI agents (default: codex antigravity claude)",
    )
    parser.add_argument("--home", type=Path, default=None, help="Override user home directory")
    parser.add_argument("--dry-run", action="store_true", help="Preview installation paths without writing files")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit JSON output")
    args = parser.parse_args(argv)

    source = global_skill_source_dir()
    if not (source / "SKILL.md").exists():
        msg = f"Bundled Global Skill not found at {source}"
        if args.as_json:
            print(json.dumps({"installed": False, "error": msg}))
        else:
            print(f"ERROR: {msg}", file=sys.stderr)
        return 2

    targets = default_skill_targets(args.home)
    installed: list[dict[str, str]] = []
    for agent in args.agents:
        dest = targets[agent]
        if not args.dry_run:
            if dest.exists():
                shutil.rmtree(dest)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source, dest)
        installed.append({"agent": agent, "path": str(dest)})

    if args.as_json:
        print(json.dumps({"installed": True, "dry_run": args.dry_run, "targets": installed}))
    else:
        verb = "WOULD INSTALL" if args.dry_run else "INSTALLED"
        for item in installed:
            print(f"{verb} [{item['agent']}]: {item['path']}")
    return 0


def _cmd_version(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="sudirector version", description="Show or evaluate SemVer 2.0.0 version metadata.")
    parser.add_argument("--bump", choices=["major", "minor", "patch"], default=None, help="Compute bumped SemVer from current version")
    parser.add_argument("--pre", default=None, help="Optional prerelease identifier when using --bump")
    parser.add_argument("--compare", nargs=2, metavar=("LEFT", "RIGHT"), default=None, help="Compare two SemVer strings (-1, 0, 1)")
    parser.add_argument("--check", default=None, help="Validate a SemVer string and report compatibility with current CLI")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit JSON output")
    args = parser.parse_args(argv)

    payload: dict[str, Any] = format_version_info()
    if args.bump:
        payload["bumped"] = bump_semver(VERSION, args.bump, prerelease=args.pre)
    if args.compare:
        payload["comparison"] = {
            "left": args.compare[0],
            "right": args.compare[1],
            "result": compare_semver(args.compare[0], args.compare[1]),
        }
    if args.check:
        cur = parse_semver(VERSION)
        target = parse_semver(args.check)
        payload["check"] = {
            "input": args.check,
            "parsed": str(target),
            "compatible": cur.is_compatible_with(target),
        }

    if args.as_json:
        print(json.dumps(payload))
    elif args.bump:
        print(payload["bumped"])
    elif args.compare:
        print(payload["comparison"]["result"])
    elif args.check:
        chk = payload["check"]
        print(f"{chk['parsed']} (compatible={chk['compatible']})")
    else:
        print(f"sudirector {VERSION}")
    return 0


def _cmd_update(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="sudirector update",
        description="Check for newer Suno Director releases or upgrade installed CLI & Global Skills.",
    )
    parser.add_argument("--check", action="store_true", help="Check GitHub Releases directly and report status without installing")
    parser.add_argument("--refresh-cache", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt when installing update")
    parser.add_argument("--force", action="store_true", help="Reinstall even if already at latest SemVer version")
    parser.add_argument("--pre", action="store_true", help="Include prerelease versions (e.g. -rc.1)")
    parser.add_argument("--no-launch", action="store_true", help="Download and verify installer without launching it")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit JSON output")
    args = parser.parse_args(argv)

    if args.refresh_cache:
        ok = refresh_cache_silently()
        return 0 if ok else 0

    if args.check:
        try:
            status = check_for_update(force_refresh=True, include_prereleases=args.pre, timeout=6.0)
        except Exception as exc:
            if args.as_json:
                print(json.dumps({"error": str(exc), "current_version": VERSION}))
            else:
                print(f"ERROR: Failed to check updates: {exc}", file=sys.stderr)
            return 1
        if args.as_json:
            print(json.dumps(status))
        elif status["update_available"]:
            print(f"Update available: v{status['current_version']} -> v{status['latest_version']} ({status['release_url']})")
        else:
            print(f"Up to date: v{status['current_version']} (latest: v{status['latest_version']})")
        return 0

    try:
        preview = check_for_update(force_refresh=True, include_prereleases=args.pre, timeout=6.0)
    except Exception as exc:
        if args.as_json:
            print(json.dumps({"status": "error", "error": str(exc)}))
        else:
            print(f"ERROR: Failed to query latest release: {exc}", file=sys.stderr)
        return 1

    if preview["update_available"] and not args.yes and not args.as_json and preview["install_mode"] != "source":
        if sys.stdin.isatty():
            reply = input(f"Upgrade sudirector v{preview['current_version']} -> v{preview['latest_version']}? [y/N]: ").strip().lower()
            if reply not in {"y", "yes"}:
                print("Cancelled.")
                return 1
        else:
            print("ERROR: Non-interactive update requires --yes.", file=sys.stderr)
            return 1

    try:
        res = perform_update(
            force=args.force,
            include_prereleases=args.pre,
            no_launch=args.no_launch,
        )
    except UpdateError as exc:
        if args.as_json:
            print(json.dumps({"status": "error", "error": str(exc)}))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.as_json:
        print(json.dumps(res))
    elif res["status"] == "up_to_date":
        print(f"Already up to date: v{res['current_version']}.")
    elif res["status"] == "source_checkout":
        print(f"v{res['current_version']} -> v{res['latest_version']} available. {res['hint']}")
    elif res["status"] == "updated_pip":
        print(f"Updated via pip to v{res['latest_version']}. Run `sudirector install-skill` to refresh Global Skills.")
    else:
        print(f"Verified v{res['latest_version']} installer ({res['installer_path']}). Launching silent updater...")
    return 0


def _dispatch_command(cmd: str, rest: list[str]) -> int:
    if cmd == "init":
        return _cmd_init(rest)
    if cmd == "validate":
        return validate_main(rest)
    if cmd == "render":
        return render_main(rest)
    if cmd == "preflight":
        return preflight_main(rest)
    if cmd == "install-skill":
        return _cmd_install_skill(rest)
    if cmd == "version":
        return _cmd_version(rest)
    if cmd == "update":
        return _cmd_update(rest)
    if cmd == "check-update":
        return _cmd_update(["--check", *rest])
    return 2


def main(argv: list[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    no_update_check = "--no-update-check" in raw_args
    args_list = [arg for arg in raw_args if arg != "--no-update-check"]

    if args_list in (["--version"], ["-V"]):
        print(f"sudirector {VERSION}")
        return 0

    parser = argparse.ArgumentParser(
        prog="sudirector",
        description="Suno Director CLI — Spec-driven, credit-guarded AI music production framework.",
    )
    parser.add_argument("-V", "--version", action="store_true", help="Print SemVer version and exit")
    parser.add_argument("--no-update-check", action="store_true", help="Skip background update check")
    parser.add_argument(
        "command",
        nargs="?",
        choices=["init", "validate", "render", "preflight", "install-skill", "version", "update", "check-update"],
        help="Subcommand to execute",
    )
    parser.add_argument("rest", nargs=argparse.REMAINDER, help="Subcommand arguments")

    if not args_list:
        parser.print_help()
        return 0

    known = parser.parse_args(args_list[:1])
    if known.version:
        print(f"sudirector {VERSION}")
        return 0

    cmd = args_list[0]
    rest = args_list[1:]
    if cmd not in {"init", "validate", "render", "preflight", "install-skill", "version", "update", "check-update"}:
        parser.print_help()
        return 2

    rc = _dispatch_command(cmd, rest)
    if not no_update_check and cmd not in {"update", "check-update"}:
        maybe_notify_update()
    return rc
