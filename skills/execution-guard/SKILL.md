---
name: execution-guard
description: Mandatory preflight gate before ANY credit-spending Official Suno MCP tool call. Queries live account-usage, normalizes capability snapshot, validates SONG-SPEC, resolves model without silent downgrade, estimates credits, enforces per_cycle or budget approval, protects download credits, and dispatches the semantic Suno MCP operation.
---

# Execution Guard

You are the **mandatory safety and cost gate** between `SONG-SPEC.yaml` and the Official Suno MCP server. **No agent may call any credit-spending Suno MCP tool without passing through this skill.**

## Core Principles

1. **Live MCP Reality > Static Docs**: Always call `account-usage` (0 credits) and inspect the live MCP tool schema at runtime. Never trust cached assumptions about allowed models, credits, or parameter names.
2. **No Silent Downgrade**: If `generation.model_preference` explicitly requests a model not in `allowed_models` (for example, `v6` on a `Free` account), **BLOCK** execution and present the 3 choices:
   - Update `generation.model_preference` to `"auto"` or an allowed model (e.g., `v6-mini`).
   - Use the manual fallback (`exports/suno-pack.md`).
   - Upgrade the Suno plan externally.
3. **Download Credit Protection**: Never call `audio-download` automatically in V1. Review takes using `audio-retrieve`, `audio-listen`, and `audio-listen-wait` (0 credits). Only allow `audio-download` when the user explicitly requests it and approves `approved_download_credit_budget >= 1`.

## Preflight Algorithm (Required Order)

1. **Live Capability Check**: Call `account-usage` via Official Suno MCP. (If Suno MCP is unavailable/unauthenticated, abort MCP execution and instruct the user to use `exports/suno-pack.md`.)
2. **Normalize Snapshot & Evaluate Plan**:
   - Save raw/redacted usage snapshot to `runs/<timestamp>/account-before.yaml`.
   - Run `scripts/execution_guard.py` (or equivalent logic) against `SONG-SPEC.yaml` and the live normalized capability snapshot.
   - Verify `scripts/validate_spec.py` passes with zero errors.
3. **Inspect Live Tool Schema & Cost**:
   - Check `adapters/suno/routing.yaml` for semantic tool mapping (`create -> audio-create`, `cover -> audio-covers-create`, `extend -> audio-extensions-create`, `edit -> audio-edit`).
   - Read the live MCP tool JSON schema so only currently supported arguments are sent.
   - Use the sanitized `mcp_payload` and `omitted_controls` from `scripts/execution_guard.py` so unsupported controls (or `audio_influence` without `voice_id`) are omitted/blocked with explanation instead of forwarded blindly.
4. **Approval Gate**:
   - **`confirmation_mode == "per_cycle"`** (default): Present:
     - Operation (`create` / `cover` / `extend` / `edit`) & MCP tool
     - Resolved Model
     - Expected Cost (`song_credits`, `download_credits`) & Outputs (`2 takes`)
     - Remaining Credits After Execution
     Wait for explicit user approval before executing.
   - **`confirmation_mode == "budget"`**: Only execute automatically if `allow_auto_iteration == true` and cumulative spend stays within `approved_song_credit_budget`. Stop immediately once budget would be exceeded.
5. **Execute & Record**:
   - Save `runs/<timestamp>/execution-plan.yaml` (including `baseline_commit_sha` and `spec_revision_before`).
   - Call the mapped Suno MCP tool (`audio-create` / `audio-covers-create` / `audio-extensions-create` / `audio-edit`) with an `idempotency_key`.
   - Poll `audio-wait` until `status == "complete"`, call `audio-retrieve`, then call `account-usage` again to save `runs/<timestamp>/account-after.yaml` and `runs/<timestamp>/result.yaml` (storing `baseline_commit_sha`, `spec_revision_before`, `spec_revision_after`, `clip_id`, `song_url`, duration, and returned metadata with secrets redacted).
