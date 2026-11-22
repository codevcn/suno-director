"""Read-only upstream drift detector against upstream-lock.yaml and Git submodules."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

from _common import REPO_ROOT, load_yaml


def _run_git(cwd: Path, args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def _get_local_head(submodule_dir: Path) -> str | None:
    if not submodule_dir.exists():
        return None
    rc, out, _ = _run_git(submodule_dir, ["rev-parse", "HEAD"])
    return out if rc == 0 and out else None


def _get_remote_head(repo_url: str, branch: str, submodule_dir: Path | None = None) -> str | None:
    target = str(submodule_dir) if (submodule_dir and submodule_dir.exists()) else repo_url
    rc, out, _ = _run_git(REPO_ROOT, ["ls-remote", repo_url, f"refs/heads/{branch}"])
    if rc == 0 and out:
        return out.split()[0]
    if target != repo_url:
        rc2, out2, _ = _run_git(submodule_dir, ["ls-remote", "origin", f"refs/heads/{branch}"])
        if rc2 == 0 and out2:
            return out2.split()[0]
    return None


def _get_changed_watched_paths(
    submodule_dir: Path,
    locked_commit: str,
    target_commit: str,
    watched_paths: list[str],
) -> list[str]:
    if not submodule_dir.exists() or locked_commit == target_commit:
        return []
    rc, out, _ = _run_git(submodule_dir, ["diff", "--name-only", locked_commit, target_commit])
    if rc != 0 or not out:
        return []
    changed_files = [line.strip() for line in out.splitlines() if line.strip()]
    matched: list[str] = []
    for fpath in changed_files:
        for wp in watched_paths:
            wp_norm = wp.rstrip("/")
            if fpath == wp_norm or fpath.startswith(wp_norm + "/"):
                matched.append(fpath)
                break
    return sorted(set(matched))


def check_upstreams(
    lock_path: Path,
    *,
    repo_root: Path = REPO_ROOT,
    offline: bool = False,
    remote_head_resolver: Callable[[str, str, Path | None], str | None] | None = None,
    changed_files_resolver: Callable[[Path, str, str, list[str]], list[str]] | None = None,
) -> dict[str, dict[str, Any]]:
    """Inspect all upstreams listed in upstream-lock.yaml without mutating files."""
    lock_data = load_yaml(lock_path) or {}
    resolve_remote = remote_head_resolver or _get_remote_head
    resolve_diff = changed_files_resolver or _get_changed_watched_paths

    results: dict[str, dict[str, Any]] = {}
    for name, cfg in lock_data.items():
        sub_path = repo_root / cfg["submodule_path"]
        locked = str(cfg["commit"])
        branch = str(cfg.get("branch", "main"))
        repo_url = str(cfg["repo"])
        watched = list(cfg.get("watched_paths") or [])

        local_head = _get_local_head(sub_path)
        remote_head = None if offline else resolve_remote(repo_url, branch, sub_path)
        latest = remote_head or local_head or locked

        status = "up_to_date"
        if local_head and local_head != locked:
            status = "local_submodule_drift"
        if remote_head and remote_head != locked:
            status = "update_available"

        compare_target = remote_head if (remote_head and remote_head != locked) else (local_head or locked)
        changed_relevant = resolve_diff(sub_path, locked, compare_target, watched)

        results[name] = {
            "repo": repo_url,
            "locked": locked,
            "local_head": local_head,
            "latest": latest,
            "status": status,
            "changed_relevant_paths": changed_relevant,
            "review_required": status != "up_to_date",
        }
    return results


def format_upstream_report(results: dict[str, dict[str, Any]]) -> str:
    """Format human-readable UPSTREAM STATUS report."""
    lines = ["UPSTREAM STATUS", ""]
    any_review = False
    for name, info in results.items():
        if info["review_required"]:
            any_review = True
        lines.append(name)
        lines.append(f"  locked: {info['locked'][:12]}")
        lines.append(f"  local:  {(info['local_head'] or 'missing')[:12]}")
        lines.append(f"  latest: {info['latest'][:12]}")
        lines.append(f"  status: {info['status']}")
        if info["changed_relevant_paths"]:
            lines.append("  changed relevant paths:")
            for p in info["changed_relevant_paths"]:
                lines.append(f"    - {p}")
        lines.append("")
    lines.append("Action:")
    lines.append("  review required (read-only check; run manual diff/adapt pipeline)" if any_review else "  up to date")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only check of upstream submodules vs upstream-lock.yaml.")
    parser.add_argument("--lock", type=Path, default=REPO_ROOT / "upstream-lock.yaml")
    parser.add_argument("--offline", action="store_true", help="Skip remote git ls-remote lookup.")
    args = parser.parse_args(argv)

    if not args.lock.exists():
        print(f"ERROR: Lockfile not found: {args.lock}", file=sys.stderr)
        return 2

    results = check_upstreams(args.lock, offline=args.offline)
    print(format_upstream_report(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
