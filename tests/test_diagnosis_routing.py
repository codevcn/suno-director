"""Tests for structured diagnosis validation and targeted feedback routing."""

from __future__ import annotations

import copy

from _common import REPO_ROOT, load_yaml
from validate_spec import main as validate_cli, validate_diagnosis


def test_chorus_no_lift_spec_error_routes_to_arrangement_architect() -> None:
    diagnosis = {
        "take_id": "take-mock-001",
        "song_url": "https://suno.com/song/take-mock-001",
        "verdict": "revise",
        "scores": {
            "spec_adherence": 0.85,
            "musical_quality": 0.62,
            "vocal_quality": 0.78,
            "artifact_risk": 0.12,
        },
        "ai_tells": ["flat_chorus_contrast"],
        "issues": [
            {
                "id": "chorus_no_lift",
                "severity": "high",
                "class": "SPEC_ERROR",
                "domain": "arrangement",
                "evidence": "Verse energy=65 and Chorus energy=70 in SONG-SPEC; delta (5) is too small to create lift.",
                "spec_path": [
                    "form[3].energy",
                    "arrangement.energy_curve",
                    "arrangement.transitions",
                ],
                "recommended_change": "Drop pre-chorus tail layers and raise chorus energy contrast >= 25 points.",
            }
        ],
        "next_action": {
            "type": "revise_spec",
            "owner": "arrangement-architect",
        },
    }
    assert validate_diagnosis(diagnosis) == []


def test_diagnosis_yaml_file_validates_against_schema() -> None:
    sample_path = REPO_ROOT / "tests" / "fixtures" / "diagnosis-sample.yaml"
    data = load_yaml(sample_path)
    assert validate_diagnosis(data) == []
    assert validate_cli([str(sample_path), "--kind", "diagnosis"]) == 0


def test_invalid_diagnosis_rejected_by_schema() -> None:
    sample_path = REPO_ROOT / "tests" / "fixtures" / "diagnosis-sample.yaml"
    bad = copy.deepcopy(load_yaml(sample_path))
    bad["next_action"]["owner"] = "non-existent-skill"
    bad["issues"][0]["spec_path"] = []
    bad["unexpected_extra_key"] = True
    errs = validate_diagnosis(bad)
    assert len(errs) >= 3

    # Simulate targeted revision touching only diagnosed paths
    spec = load_yaml(REPO_ROOT / "examples" / "vocal-song" / "SONG-SPEC.yaml")
    original_lyrics = copy.deepcopy(spec["lyrics"])
    original_harmony = copy.deepcopy(spec["music"]["harmony"])

    spec["revision"] += 1
    spec["form"][3]["energy"] = 90
    spec["arrangement"]["energy_curve"][3]["energy"] = 90
    spec["status"]["phase"] = "revising"

    assert spec["lyrics"] == original_lyrics
    assert spec["music"]["harmony"] == original_harmony
    assert spec["form"][3]["energy"] == 90


def test_chorus_no_lift_render_error_routes_to_suno_engineer() -> None:
    diagnosis = {
        "take_id": "take-mock-002",
        "song_url": "https://suno.com/song/take-mock-002",
        "verdict": "revise",
        "scores": {
            "spec_adherence": 0.58,
            "musical_quality": 0.65,
            "vocal_quality": 0.74,
            "artifact_risk": 0.15,
        },
        "ai_tells": ["flat_chorus_contrast"],
        "issues": [
            {
                "id": "chorus_no_lift",
                "severity": "high",
                "class": "RENDER_ERROR",
                "domain": "suno",
                "evidence": "Spec already defines pre_chorus=58 -> chorus=86 with drum drop, but Suno rendered flat chorus dynamics.",
                "spec_path": [
                    "generation.style_prompt",
                    "lyrics.text",
                ],
                "recommended_change": "Sharpen chorus performance cue and add dynamic contrast phrasing in style_prompt.",
            }
        ],
        "next_action": {
            "type": "retry_render",
            "owner": "suno-engineer",
        },
    }
    assert validate_diagnosis(diagnosis) == []


def test_diagnosis_yaml_file_validates_against_schema() -> None:
    sample_path = REPO_ROOT / "tests" / "fixtures" / "diagnosis-sample.yaml"
    data = load_yaml(sample_path)
    assert validate_diagnosis(data) == []
    assert validate_cli([str(sample_path), "--kind", "diagnosis"]) == 0


def test_invalid_diagnosis_rejected_by_schema() -> None:
    sample_path = REPO_ROOT / "tests" / "fixtures" / "diagnosis-sample.yaml"
    bad = copy.deepcopy(load_yaml(sample_path))
    bad["next_action"]["owner"] = "non-existent-skill"
    bad["issues"][0]["spec_path"] = []
    bad["unexpected_extra_key"] = True
    errs = validate_diagnosis(bad)
    assert len(errs) >= 3
