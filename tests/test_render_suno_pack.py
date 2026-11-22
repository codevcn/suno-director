"""Tests for deterministic Suno Pack rendering and MCP-unavailable fallback."""

from __future__ import annotations

from _common import REPO_ROOT, load_yaml
from render_suno_pack import render_suno_pack


def test_render_is_deterministic() -> None:
    for example in ("instrumental", "vocal-song"):
        spec = load_yaml(REPO_ROOT / "examples" / example / "SONG-SPEC.yaml")
        out1 = render_suno_pack(spec)
        out2 = render_suno_pack(spec)
        assert out1 == out2


def test_instrumental_fallback_tags_and_fields() -> None:
    spec = load_yaml(REPO_ROOT / "examples" / "instrumental" / "SONG-SPEC.yaml")
    pack = render_suno_pack(spec)
    assert "## Title\nThree O'Clock Shade" in pack
    assert "**Instrumental**: On (Instrumental)" in pack
    assert "**Variety**: Off (0)" in pack
    assert "[Intro]" in pack
    assert "[Breakdown]" in pack
    assert "[End]" in pack
    assert "fade out ending" in pack


def test_vocal_pack_contains_required_sections() -> None:
    spec = load_yaml(REPO_ROOT / "examples" / "vocal-song" / "SONG-SPEC.yaml")
    pack = render_suno_pack(spec)
    for heading in (
        "## Title",
        "## Model recommendation",
        "## Style",
        "## Lyrics",
        "## Exclude Styles",
        "## Generation notes",
        "## Expected structure",
        "## Acceptance checklist",
    ):
        assert heading in pack
    assert "Neon Last Train" in pack
    assert "Zero-zero-fifteen" in pack
