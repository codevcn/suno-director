"""Tests for the unified `sudirector` CLI, JSON output mode, skill installer, and user overrides."""

from __future__ import annotations

import json
from pathlib import Path

from music_director.cli import main as cli_main
from music_director.common import load_capabilities_config
from music_director.version import VERSION


def test_cli_version_flags(capsys) -> None:
    rc = cli_main(["--version"])
    assert rc == 0
    assert f"sudirector {VERSION}" in capsys.readouterr().out

    rc = cli_main(["version", "--bump", "minor", "--json", "--no-update-check"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["version"] == VERSION
    assert data["bumped"] == "0.3.0"


def test_cli_init_validate_render_preflight_workflow(tmp_path: Path, capsys) -> None:
    ws = tmp_path / "ws"
    rc = cli_main(["init", "rainy-metro", "--dir", str(ws), "--instrumental", "--json"])
    assert rc == 0
    init_res = json.loads(capsys.readouterr().out)
    spec_path = Path(init_res["spec_path"])
    assert spec_path.exists()

    # Validate the vocal example cleanly with JSON output
    repo_root = Path(__file__).resolve().parent.parent
    vocal_spec = repo_root / "examples" / "vocal-song" / "SONG-SPEC.yaml"
    rc = cli_main(["validate", str(vocal_spec), "--json"])
    assert rc == 0
    val_res = json.loads(capsys.readouterr().out)
    assert val_res["valid"] is True

    out_pack = tmp_path / "pack.md"
    rc = cli_main(["render", str(vocal_spec), "--out", str(out_pack), "--json"])
    assert rc == 0
    ren_res = json.loads(capsys.readouterr().out)
    assert Path(ren_res["output_path"]).exists()

    free_acc = repo_root / "tests" / "fixtures" / "free-account.yaml"
    rc = cli_main(["preflight", str(vocal_spec), "--account", str(free_acc), "--json", "--no-update-check"])
    assert rc == 1  # per_cycle blocked without --approve
    plan_res = json.loads(capsys.readouterr().out)
    assert plan_res["decision"] == "blocked"
    assert plan_res["tool_version"] == "0.2.0"


def test_cli_install_skill_targets_three_agents(tmp_path: Path, capsys) -> None:
    rc = cli_main(["install-skill", "--home", str(tmp_path), "--json"])
    assert rc == 0
    res = json.loads(capsys.readouterr().out)
    assert res["installed"] is True
    assert {t["agent"] for t in res["targets"]} == {"codex", "antigravity", "claude"}
    assert (tmp_path / ".codex" / "skills" / "suno-director" / "SKILL.md").exists()
    assert (tmp_path / ".gemini" / "config" / "skills" / "suno-director" / "SKILL.md").exists()
    assert (tmp_path / ".claude" / "skills" / "suno-director" / "SKILL.md").exists()


def test_user_runtime_override_merges_with_bundled_capabilities(tmp_path: Path) -> None:
    override_file = tmp_path / "runtime-overrides.yaml"
    override_file.write_text(
        "runtime_overrides:\n  free:\n    v6-mini:\n      exclude_styles:\n        effective: true\n",
        encoding="utf-8",
    )
    caps = load_capabilities_config(user_override_path=override_file)
    assert caps["runtime_overrides"]["free"]["v6-mini"]["exclude_styles"]["effective"] is True
    assert caps["runtime_overrides"]["free"]["v6-mini"]["sliders"]["effective"] is False
