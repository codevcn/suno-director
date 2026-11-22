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


def main(argv: list[str] | None = None) -> int:
    args_list = list(sys.argv[1:] if argv is None else argv)
    if args_list in (["--version"], ["-V"]):
        print(f"sudirector {VERSION}")
        return 0

    parser = argparse.ArgumentParser(
        prog="sudirector",
        description="Suno Director CLI — Spec-driven, credit-guarded AI music production framework.",
    )
    parser.add_argument("-V", "--version", action="store_true", help="Print SemVer version and exit")
    parser.add_argument(
        "command",
        nargs="?",
        choices=["init", "validate", "render", "preflight", "install-skill", "version"],
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

    parser.print_help()
    return 2
