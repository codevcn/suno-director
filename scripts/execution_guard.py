"""Execution Guard: capability normalization, model resolution, credit & download protection."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

from _common import ADAPTERS_SUNO_DIR, REPO_ROOT, dump_yaml, load_yaml
from validate_spec import validate_execution_plan, validate_song_spec

DEFAULT_MODEL_PRIORITY = ["v6", "v6-wild", "v6-mini"]
KNOWN_MCP_CONTROLS = {"variety", "weirdness", "style_influence", "audio_influence", "max_mode"}


def _current_git_sha() -> str | None:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0:
            sha = proc.stdout.strip()
            return sha or None
    except OSError:
        pass
    return None


def _load_adapter_configs() -> tuple[dict[str, Any], dict[str, Any]]:
    caps = load_yaml(ADAPTERS_SUNO_DIR / "capabilities.yaml")
    routing = load_yaml(ADAPTERS_SUNO_DIR / "routing.yaml")
    return caps, routing


def normalize_capability_snapshot(raw_usage: dict[str, Any]) -> dict[str, Any]:
    """Normalize either a raw `account-usage` response or fixture into canonical capability snapshot."""
    if {"plan", "song_credits", "download_credits", "models", "capabilities"}.issubset(raw_usage.keys()):
        return raw_usage

    suno_acc = raw_usage.get("suno_account") or {}
    plan_obj = suno_acc.get("plan") or {}
    plan_name = str(plan_obj.get("name") or "unknown").lower()

    allowed_models = list(raw_usage.get("allowed_models") or [])
    features = set(raw_usage.get("features") or [])

    song_rem = int(suno_acc.get("credits_remaining") or 0)
    dl_rem = int(suno_acc.get("download_credits_remaining") or 0)

    has_download = "audio.download" in features or dl_rem > 0
    if plan_name == "free":
        dl_cap = "limited" if has_download else "none"
    elif has_download:
        dl_cap = "monthly"
    else:
        dl_cap = "none"

    return {
        "plan": plan_name,
        "song_credits": {"remaining": song_rem},
        "download_credits": {"remaining": dl_rem},
        "models": {"allowed": allowed_models},
        "capabilities": {
            "create": ("generate.simple" in features) or ("generate.custom" in features) or bool(allowed_models),
            "cover": "generate.cover" in features,
            "extend": "generate.extend" in features,
            "edit": bool(allowed_models),
            "download": dl_cap,
            "advanced_controls": "controls.advanced" in features,
            "max_mode": ("max_mode" in features) or ("controls.max_mode" in features),
        },
    }


def _resolve_model(requested: str, allowed_models: list[str], priority: list[str]) -> str | None:
    if requested == "auto":
        for candidate in priority:
            if candidate in allowed_models:
                return candidate
        return allowed_models[0] if allowed_models else None
    if requested in allowed_models:
        return requested
    return None


def resolve_effective_capabilities(
    snapshot: dict[str, Any],
    *,
    resolved_model: str | None,
    runtime_overrides: dict[str, Any] | None = None,
) -> dict[str, tuple[bool, str | None]]:
    """Layer declared snapshot capabilities with observed runtime_overrides (plan -> model -> feature)."""
    plan_name = snapshot.get("plan", "unknown")
    caps = snapshot.get("capabilities") or {}
    declared_adv = caps.get("advanced_controls", True)
    declared_max = caps.get("max_mode", plan_name in {"pro", "premier"})

    overrides = runtime_overrides or {}
    model_overrides = (overrides.get(plan_name) or {}).get(resolved_model or "", {}) or {}

    def _apply_override(
        feature_key: str,
        declared: bool,
        declared_name: str,
    ) -> tuple[bool, str | None]:
        ovr = model_overrides.get(feature_key)
        if isinstance(ovr, dict) and ovr.get("effective") is False:
            evidence = ovr.get("evidence") or "observed backend rejection"
            return (
                False,
                f"Omitted due to observed runtime incompatibility on '{plan_name}'/'{resolved_model}' "
                f"({evidence}; declared {declared_name}={declared}).",
            )
        if not declared:
            return (
                False,
                f"Omitted because account plan '{plan_name}' does not declare '{declared_name}'.",
            )
        return (True, None)

    return {
        "exclude_styles": _apply_override("exclude_styles", declared_adv, "controls.advanced"),
        "sliders": _apply_override("sliders", declared_adv, "controls.advanced"),
        "max_mode": _apply_override("max_mode", declared_max, "max_mode"),
    }


def build_sanitized_mcp_payload(
    spec: dict[str, Any],
    snapshot: dict[str, Any],
    *,
    operation: str,
    mcp_tool: str,
    resolved_model: str | None,
    runtime_overrides: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], list[dict[str, str]], str | None]:
    """Build live MCP payload, omitting incompatible controls or blocking unsupported paid toggles."""
    gen = spec["generation"]
    controls = gen.get("controls") or {}
    source = gen.get("source") or {}
    plan_name = snapshot.get("plan", "unknown")

    effective = resolve_effective_capabilities(
        snapshot,
        resolved_model=resolved_model,
        runtime_overrides=runtime_overrides,
    )
    can_exclude, exclude_reason = effective["exclude_styles"]
    can_sliders, sliders_reason = effective["sliders"]
    can_max_mode, max_mode_reason = effective["max_mode"]

    omitted: list[dict[str, str]] = []
    if controls.get("max_mode") is True and not can_max_mode:
        return (
            {},
            omitted,
            f"Unsupported control: generation.controls.max_mode is true ({max_mode_reason or plan_name}).",
        )

    payload: dict[str, Any] = {}
    if operation == "create":
        instrumental = not spec["vocal"]["enabled"]
        payload = {
            "title": spec["identity"]["title"],
            "instrumental": instrumental,
            "style": gen["style_prompt"],
        }
        if resolved_model:
            payload["model"] = resolved_model
        lyrics_text = (spec.get("lyrics") or {}).get("text") or ""
        if not instrumental or lyrics_text.strip():
            payload["lyrics"] = lyrics_text
        duration = spec["identity"].get("target_duration_seconds")
        if isinstance(duration, int) and 15 <= duration <= 360:
            payload["duration"] = duration
        if controls.get("max_mode") is True:
            payload["max_mode"] = True

        exclude_styles = gen.get("exclude_styles") or []
        if exclude_styles:
            if can_exclude:
                payload["negative_style"] = ", ".join(str(s) for s in exclude_styles if str(s).strip())
            else:
                omitted.append(
                    {
                        "control": "generation.exclude_styles",
                        "reason": exclude_reason or "Omitted by capability guard.",
                    }
                )

        mcp_controls: dict[str, Any] = {}
        for key, value in controls.items():
            if key == "max_mode":
                continue
            if key not in KNOWN_MCP_CONTROLS:
                if value is not None:
                    omitted.append(
                        {
                            "control": f"generation.controls.{key}",
                            "reason": f"Control '{key}' is not supported by live Suno MCP '{mcp_tool}' schema.",
                        }
                    )
                continue
            if value is None:
                continue
            if key == "audio_influence" and not source.get("voice_id"):
                omitted.append(
                    {
                        "control": "generation.controls.audio_influence",
                        "reason": "Omitted for 'create' without voice_id (live Suno MCP returns 400 without voice_id).",
                    }
                )
                continue
            if not can_sliders:
                omitted.append(
                    {
                        "control": f"generation.controls.{key}",
                        "reason": sliders_reason or "Omitted by capability guard.",
                    }
                )
                continue
            mcp_controls[key] = value
        if mcp_controls:
            payload["controls"] = mcp_controls

    return (payload, omitted, None)


def _build_plan(
    *,
    decision: str,
    reason: str,
    operation: str,
    mcp_tool: str,
    requested_model: str,
    resolved_model: str | None,
    est_song: int,
    est_dl: int,
    snapshot: dict[str, Any],
    policy: dict[str, Any],
    approved: bool,
    spec_revision_before: int,
    spec_revision_after: int | None = None,
    baseline_commit_sha: str | None = None,
    mcp_payload: dict[str, Any] | None = None,
    omitted_controls: list[dict[str, str]] | None = None,
    options: list[str] | None = None,
) -> dict[str, Any]:
    song_rem = snapshot["song_credits"]["remaining"]
    dl_rem = snapshot["download_credits"]["remaining"]
    plan: dict[str, Any] = {
        "decision": decision,
        "reason": reason,
        "operation": operation,
        "mcp_tool": mcp_tool,
        "requested_model": requested_model,
        "resolved_model": resolved_model,
        "estimated_song_credits": est_song,
        "estimated_download_credits": est_dl,
        "remaining_song_credits_after": (song_rem - est_song) if (decision == "allowed" and song_rem >= est_song) else None,
        "remaining_download_credits_after": (dl_rem - est_dl) if (decision == "allowed" and dl_rem >= est_dl) else None,
        "baseline_commit_sha": baseline_commit_sha,
        "spec_revision_before": spec_revision_before,
        "spec_revision_after": spec_revision_after,
        "mcp_payload": mcp_payload or {},
        "omitted_controls": omitted_controls or [],
        "capability_snapshot": snapshot,
        "approval": {
            "confirmation_mode": policy["confirmation_mode"],
            "approved": approved,
            "approved_song_credit_budget": int(policy["approved_song_credit_budget"]),
            "approved_download_credit_budget": int(policy["approved_download_credit_budget"]),
        },
    }
    if options:
        plan["options"] = options
    errs = validate_execution_plan(plan)
    if errs:
        raise ValueError(f"Internal execution plan schema error: {errs}")
    return plan


def evaluate_execution_plan(
    spec: dict[str, Any],
    raw_or_normalized_usage: dict[str, Any],
    *,
    operation: str | None = None,
    user_approved: bool | None = None,
    spent_in_budget: int = 0,
    baseline_commit_sha: str | None = None,
    runtime_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run full preflight gate: spec validation, model resolution, control sanitization, cost & approval check."""
    caps_cfg, routing_cfg = _load_adapter_configs()
    effective_overrides = (caps_cfg.get("runtime_overrides") or {}) if runtime_overrides is None else runtime_overrides
    snapshot = normalize_capability_snapshot(raw_or_normalized_usage)
    policy = spec["execution_policy"]
    gen = spec["generation"]

    op = operation or gen["intent"]
    op_cfg = routing_cfg["operations"].get(op)
    if not op_cfg:
        raise ValueError(f"Unsupported operation '{op}'.")
    mcp_tool = op_cfg["tool"]

    requested_model = gen["model_preference"]
    allowed_models = snapshot["models"]["allowed"]
    priority = caps_cfg.get("model_resolution_priority", DEFAULT_MODEL_PRIORITY)
    resolved_model = _resolve_model(requested_model, allowed_models, priority)

    cost_cfg = caps_cfg["credit_costs"][op]
    controls = gen.get("controls") or {}
    multiplier = cost_cfg["max_mode_multiplier"] if controls.get("max_mode") else 1
    est_song = int(cost_cfg["song_credits"]) * int(multiplier)
    est_dl = int(cost_cfg["download_credits"])

    rev_before = int(spec.get("revision") or 1)
    commit_sha = baseline_commit_sha if baseline_commit_sha is not None else _current_git_sha()
    mcp_payload: dict[str, Any] = {}
    omitted_controls: list[dict[str, str]] = []

    def _finish(
        decision: str,
        reason: str,
        *,
        approved: bool,
        model_out: str | None = resolved_model,
        options: list[str] | None = None,
    ) -> dict[str, Any]:
        return _build_plan(
            decision=decision,
            reason=reason,
            operation=op,
            mcp_tool=mcp_tool,
            requested_model=requested_model,
            resolved_model=model_out,
            est_song=est_song,
            est_dl=est_dl,
            snapshot=snapshot,
            policy=policy,
            approved=approved,
            spec_revision_before=rev_before,
            spec_revision_after=rev_before,
            baseline_commit_sha=commit_sha,
            mcp_payload=mcp_payload,
            omitted_controls=omitted_controls,
            options=options,
        )

    # 1. Spec validation gate
    spec_errors, _ = validate_song_spec(spec)
    if spec_errors:
        return _finish("blocked", f"SONG-SPEC validation failed: {spec_errors[0]}", approved=False)

    # 2. Download protection gate (V1 never auto-downloads)
    if op == "download":
        dl_budget = int(policy["approved_download_credit_budget"])
        dl_rem = snapshot["download_credits"]["remaining"]
        if dl_rem < est_dl:
            return _finish("blocked", f"Insufficient download credits ({dl_rem} remaining, {est_dl} needed).", approved=False)
        if dl_budget < est_dl or user_approved is False:
            return _finish(
                "blocked",
                "Download blocked: V1 protects download credits unless user explicitly approves download budget.",
                approved=False,
            )
        return _finish("allowed", "Download explicitly approved within download credit budget.", approved=True)

    # 3. Capability gate
    if not snapshot["capabilities"].get(op, False):
        return _finish("blocked", f"Account plan '{snapshot['plan']}' does not expose capability '{op}'.", approved=False)

    # 4. Model resolution gate (never silently downgrade)
    if resolved_model is None:
        return _finish(
            "blocked",
            f"Spec requires '{requested_model}', but account plan '{snapshot['plan']}' only allows {allowed_models}.",
            approved=False,
            model_out=None,
            options=[
                f"Update generation.model_preference to 'auto' or an allowed model ({', '.join(allowed_models)}).",
                "Use manual fallback via exports/suno-pack.md on suno.com.",
                "Upgrade Suno plan externally.",
            ],
        )

    # 5. Live MCP control compatibility gate (declared capabilities + runtime overrides)
    mcp_payload, omitted_controls, control_block_reason = build_sanitized_mcp_payload(
        spec,
        snapshot,
        operation=op,
        mcp_tool=mcp_tool,
        resolved_model=resolved_model,
        runtime_overrides=effective_overrides,
    )
    if control_block_reason:
        return _finish("blocked", control_block_reason, approved=False)

    # 6. Account credit balance check
    song_rem = snapshot["song_credits"]["remaining"]
    if song_rem < est_song:
        return _finish("blocked", f"Insufficient song credits ({song_rem} remaining, {est_song} required).", approved=False)

    # 7. Confirmation mode & approved budget gate
    mode = policy["confirmation_mode"]
    if mode == "per_cycle":
        if user_approved is not True:
            return _finish(
                "blocked",
                f"Approval required (per_cycle): {op} via {mcp_tool} on {resolved_model} costs {est_song} song credits (2 takes).",
                approved=False,
            )
        return _finish(
            "allowed",
            f"Approved per_cycle execution: {mcp_tool} using {resolved_model} ({est_song} song credits).",
            approved=True,
        )

    # mode == "budget"
    budget = int(policy["approved_song_credit_budget"])
    allow_auto = bool(policy["allow_auto_iteration"])
    if budget <= 0 or not allow_auto:
        return _finish("blocked", "Budget mode requires approved_song_credit_budget > 0 and allow_auto_iteration: true.", approved=False)

    if spent_in_budget + est_song > budget:
        return _finish(
            "blocked",
            f"Approved song credit budget exceeded ({spent_in_budget} spent + {est_song} needed > {budget} budget).",
            approved=False,
        )

    return _finish(
        "allowed",
        f"Allowed within approved budget ({spent_in_budget + est_song}/{budget} song credits): {mcp_tool} on {resolved_model}.",
        approved=True,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Execution Guard preflight against a SONG-SPEC and account snapshot.")
    parser.add_argument("spec_path", type=Path, help="Path to SONG-SPEC.yaml")
    parser.add_argument("--account", type=Path, required=True, help="Path to account usage YAML/JSON fixture")
    parser.add_argument("--operation", choices=["create", "cover", "extend", "edit", "download"], default=None)
    parser.add_argument("--approve", action="store_true", help="Mark per_cycle execution as explicitly approved by user")
    parser.add_argument("--spent", type=int, default=0, help="Song credits already spent in current budget session")
    parser.add_argument("--out", type=Path, default=None, help="Optional path to write execution-plan.yaml")
    args = parser.parse_args(argv)

    spec = load_yaml(args.spec_path)
    usage = load_yaml(args.account)
    plan = evaluate_execution_plan(
        spec,
        usage,
        operation=args.operation,
        user_approved=True if args.approve else None,
        spent_in_budget=args.spent,
    )

    if args.out:
        dump_yaml(plan, args.out)

    print(f"DECISION: {plan['decision'].upper()}")
    print(f"REASON: {plan['reason']}")
    print(f"TOOL: {plan['mcp_tool']} | MODEL: {plan['resolved_model']} | COST: {plan['estimated_song_credits']} song, {plan['estimated_download_credits']} download")
    if plan.get("options"):
        for idx, opt in enumerate(plan["options"], 1):
            print(f"  {idx}. {opt}")

    return 0 if plan["decision"] == "allowed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
