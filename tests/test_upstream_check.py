"""Tests for non-mutating upstream tracking script."""

from __future__ import annotations

from pathlib import Path

from _common import REPO_ROOT
from check_upstreams import check_upstreams, format_upstream_report


def test_check_upstreams_offline_reads_lock_and_pinned_submodules() -> None:
    lock_path = REPO_ROOT / "upstream-lock.yaml"
    before_bytes = lock_path.read_bytes()

    results = check_upstreams(lock_path, repo_root=REPO_ROOT, offline=True)
    assert set(results.keys()) == {"bitwize", "composition"}
    for name, info in results.items():
        assert info["local_head"] == info["locked"], f"{name} submodule drifted from lock"
        assert info["status"] == "up_to_date"
        assert info["review_required"] is False

    report = format_upstream_report(results)
    assert "UPSTREAM STATUS" in report
    assert "up to date" in report
    assert lock_path.read_bytes() == before_bytes


def test_check_upstreams_detects_remote_update_without_mutating_lock() -> None:
    lock_path = REPO_ROOT / "upstream-lock.yaml"
    before_bytes = lock_path.read_bytes()

    def fake_remote(repo_url: str, branch: str, sub_dir: Path | None) -> str | None:
        if "claude-ai-music-skills" in repo_url:
            return "deadbeef00000000000000000000000000000001"
        return None

    def fake_diff(sub_dir: Path, locked: str, target: str, watched: list[str]) -> list[str]:
        if sub_dir.name == "bitwize":
            return ["reference/suno/models.md", "skills/suno-engineer/SKILL.md"]
        return []

    results = check_upstreams(
        lock_path,
        repo_root=REPO_ROOT,
        offline=False,
        remote_head_resolver=fake_remote,
        changed_files_resolver=fake_diff,
    )
    assert results["bitwize"]["status"] == "update_available"
    assert results["bitwize"]["review_required"] is True
    assert "reference/suno/models.md" in results["bitwize"]["changed_relevant_paths"]

    report = format_upstream_report(results)
    assert "review required" in report
    assert "reference/suno/models.md" in report
    assert lock_path.read_bytes() == before_bytes
