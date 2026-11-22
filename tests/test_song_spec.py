"""Tests for SONG-SPEC schema and semantic validation."""

from __future__ import annotations

import copy
from pathlib import Path

from _common import REPO_ROOT, load_yaml
from validate_spec import validate_song_spec


def test_examples_validate_cleanly() -> None:
    for example in ("instrumental", "vocal-song"):
        spec_path = REPO_ROOT / "examples" / example / "SONG-SPEC.yaml"
        spec = load_yaml(spec_path)
        errors, warnings = validate_song_spec(spec)
        assert errors == [], f"{example} failed validation: {errors}"
        assert warnings == [], f"{example} produced unexpected warnings: {warnings}"


def test_invalid_tempo_fails() -> None:
    spec = load_yaml(REPO_ROOT / "examples" / "instrumental" / "SONG-SPEC.yaml")
    bad = copy.deepcopy(spec)
    bad["music"]["tempo_bpm"] = 500
    errors, _ = validate_song_spec(bad)
    assert any("tempo_bpm" in e for e in errors)


def test_missing_required_field_fails() -> None:
    spec = load_yaml(REPO_ROOT / "examples" / "vocal-song" / "SONG-SPEC.yaml")
    bad = copy.deepcopy(spec)
    del bad["identity"]["intent"]
    errors, _ = validate_song_spec(bad)
    assert any("intent" in e for e in errors)


def test_extend_without_source_id_or_continue_at_fails() -> None:
    spec = load_yaml(REPO_ROOT / "examples" / "vocal-song" / "SONG-SPEC.yaml")
    bad = copy.deepcopy(spec)
    bad["generation"]["intent"] = "extend"
    errors, _ = validate_song_spec(bad)
    assert any("audio_id" in e for e in errors)
    assert any("continue_at" in e for e in errors)


def test_vocal_mismatch_fails() -> None:
    vocal_spec = load_yaml(REPO_ROOT / "examples" / "vocal-song" / "SONG-SPEC.yaml")
    bad_vocal = copy.deepcopy(vocal_spec)
    bad_vocal["lyrics"]["text"] = "[Intro]\n\n[Verse 1]\n"
    errors, _ = validate_song_spec(bad_vocal)
    assert any("sung lyric lines" in e for e in errors)

    inst_spec = load_yaml(REPO_ROOT / "examples" / "instrumental" / "SONG-SPEC.yaml")
    bad_inst = copy.deepcopy(inst_spec)
    bad_inst["lyrics"]["text"] = "[Verse 1]\nUnexpected sung words"
    errors2, _ = validate_song_spec(bad_inst)
    assert any("instrumental" in e for e in errors2)
