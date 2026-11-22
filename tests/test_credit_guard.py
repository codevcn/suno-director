"""Tests for Execution Guard credit protection, download protection, and model resolution."""

from __future__ import annotations

import copy

from _common import REPO_ROOT, load_yaml
from execution_guard import evaluate_execution_plan, normalize_capability_snapshot


def _load_spec(name: str = "vocal-song") -> dict:
    return load_yaml(REPO_ROOT / "examples" / name / "SONG-SPEC.yaml")


def _load_account(name: str) -> dict:
    return load_yaml(REPO_ROOT / "tests" / "fixtures" / f"{name}.yaml")


def test_no_approval_per_cycle_blocked() -> None:
    spec = _load_spec()
    free_acc = _load_account("free-account")
    plan = evaluate_execution_plan(spec, free_acc, user_approved=None)
    assert plan["decision"] == "blocked"
    assert "Approval required" in plan["reason"]


def test_budget_zero_blocked() -> None:
    spec = copy.deepcopy(_load_spec())
    spec["execution_policy"]["confirmation_mode"] = "budget"
    spec["execution_policy"]["approved_song_credit_budget"] = 0
    spec["execution_policy"]["allow_auto_iteration"] = True
    plan = evaluate_execution_plan(spec, _load_account("free-account"))
    assert plan["decision"] == "blocked"
    assert "budget" in plan["reason"].lower()


def test_budget_exceeded_blocked() -> None:
    spec = copy.deepcopy(_load_spec())
    spec["execution_policy"]["confirmation_mode"] = "budget"
    spec["execution_policy"]["approved_song_credit_budget"] = 20
    spec["execution_policy"]["allow_auto_iteration"] = True
    plan = evaluate_execution_plan(spec, _load_account("free-account"), spent_in_budget=15)
    assert plan["decision"] == "blocked"
    assert "exceeded" in plan["reason"].lower()


def test_download_not_approved_blocked() -> None:
    spec = _load_spec()
    plan = evaluate_execution_plan(spec, _load_account("pro-account"), operation="download")
    assert plan["decision"] == "blocked"
    assert "download" in plan["reason"].lower()


def test_approved_budget_allowed() -> None:
    spec = copy.deepcopy(_load_spec())
    spec["execution_policy"]["confirmation_mode"] = "budget"
    spec["execution_policy"]["approved_song_credit_budget"] = 40
    spec["execution_policy"]["allow_auto_iteration"] = True
    plan = evaluate_execution_plan(spec, _load_account("free-account"), spent_in_budget=10)
    assert plan["decision"] == "allowed"
    assert plan["resolved_model"] == "v6-mini"
    assert plan["estimated_song_credits"] == 10
    assert plan["remaining_song_credits_after"] == 140


def test_capability_mismatch_blocks_without_silent_downgrade() -> None:
    spec = copy.deepcopy(_load_spec())
    spec["generation"]["model_preference"] = "v6"
    plan = evaluate_execution_plan(spec, _load_account("free-account"), user_approved=True)
    assert plan["decision"] == "blocked"
    assert plan["resolved_model"] is None
    assert "v6" in plan["reason"]
    assert "v6-mini" in plan["reason"]
    assert len(plan["options"]) == 3


def test_raw_account_usage_normalization() -> None:
    raw = {
        "allowed_models": ["v6-mini"],
        "features": ["generate.simple", "generate.cover", "generate.extend", "audio.download", "controls.advanced"],
        "suno_account": {
            "credits_remaining": 150,
            "download_credits_remaining": 7,
            "plan": {"name": "Free", "period": None},
        },
    }
    snap = normalize_capability_snapshot(raw)
    assert snap["plan"] == "free"
    assert snap["models"]["allowed"] == ["v6-mini"]
    assert snap["song_credits"]["remaining"] == 150
    assert snap["download_credits"]["remaining"] == 7
    assert snap["capabilities"]["download"] == "limited"
    # Snapshot reports declared capability faithfully from account-usage
    assert snap["capabilities"]["advanced_controls"] is True
    assert snap["capabilities"]["max_mode"] is False

    # Layer 1 (default): runtime_overrides from adapters/suno/capabilities.yaml disables free/v6-mini
    # exclude_styles & sliders despite declared controls.advanced=True
    spec = _load_spec()
    plan = evaluate_execution_plan(spec, raw, user_approved=True)
    assert plan["decision"] == "allowed"
    assert plan["resolved_model"] == "v6-mini"
    assert plan["spec_revision_before"] == spec["revision"]
    assert plan["spec_revision_after"] == spec["revision"]
    assert "negative_style" not in plan["mcp_payload"]
    assert "controls" not in plan["mcp_payload"]
    omitted_by_name = {item["control"]: item["reason"] for item in plan["omitted_controls"]}
    assert {"generation.exclude_styles", "generation.controls.variety"}.issubset(omitted_by_name.keys())
    assert "observed runtime incompatibility" in omitted_by_name["generation.exclude_styles"]

    # Layer 2: when runtime_overrides is removed ({}), guard uses live declared capability again
    plan_no_override = evaluate_execution_plan(spec, raw, user_approved=True, runtime_overrides={})
    assert plan_no_override["decision"] == "allowed"
    assert "negative_style" in plan_no_override["mcp_payload"]
    assert plan_no_override["mcp_payload"]["controls"] == {"variety": 0}
    assert plan_no_override["omitted_controls"] == []


def test_unsupported_controls_omitted_with_explanation() -> None:
    raw_without_adv = {
        "allowed_models": ["v6-mini"],
        "features": ["generate.simple", "generate.custom"],
        "suno_account": {
            "credits_remaining": 50,
            "download_credits_remaining": 0,
            "plan": {"name": "Free", "period": None},
        },
    }
    spec = copy.deepcopy(_load_spec())
    spec["generation"]["controls"]["weirdness"] = 0.45
    spec["generation"]["controls"]["style_influence"] = 0.8
    spec["generation"]["controls"]["audio_influence"] = 0.7
    spec["generation"]["controls"]["custom_unknown_knob"] = 0.9

    plan = evaluate_execution_plan(spec, raw_without_adv, user_approved=True)
    assert plan["decision"] == "allowed"
    payload = plan["mcp_payload"]
    assert "negative_style" not in payload
    assert "controls" not in payload
    omitted_names = {item["control"] for item in plan["omitted_controls"]}
    assert {
        "generation.exclude_styles",
        "generation.controls.variety",
        "generation.controls.weirdness",
        "generation.controls.style_influence",
        "generation.controls.audio_influence",
        "generation.controls.custom_unknown_knob",
    }.issubset(omitted_names)


def test_unsupported_max_mode_blocked_with_explanation() -> None:
    raw_free = {
        "allowed_models": ["v6-mini"],
        "features": ["generate.simple", "generate.custom", "controls.advanced"],
        "suno_account": {
            "credits_remaining": 150,
            "download_credits_remaining": 7,
            "plan": {"name": "Free", "period": None},
        },
    }
    spec = copy.deepcopy(_load_spec())
    spec["generation"]["controls"]["max_mode"] = True
    plan = evaluate_execution_plan(spec, raw_free, user_approved=True)
    assert plan["decision"] == "blocked"
    assert "max_mode" in plan["reason"]


def test_audio_influence_omitted_on_create_without_voice_id() -> None:
    raw_pro = {
        "allowed_models": ["v6", "v6-wild", "v6-mini"],
        "features": ["generate.simple", "generate.custom", "controls.advanced"],
        "suno_account": {
            "credits_remaining": 2500,
            "download_credits_remaining": 20,
            "plan": {"name": "Pro", "period": "month"},
        },
    }
    spec = copy.deepcopy(_load_spec())
    spec["generation"]["controls"]["audio_influence"] = 0.6
    plan = evaluate_execution_plan(spec, raw_pro, user_approved=True)
    assert plan["decision"] == "allowed"
    assert "audio_influence" not in plan["mcp_payload"].get("controls", {})
    assert any(item["control"] == "generation.controls.audio_influence" for item in plan["omitted_controls"])
