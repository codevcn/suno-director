---
name: suno-director
description: >
  Spec-driven, credit-guarded AI music production workflow with Suno AI using
  the `sudirector` CLI and Official Suno MCP (or deterministic `suno-pack.md`
  fallback). Use from ANY directory whenever the user wants to compose, write
  lyrics/prompts, validate a SONG-SPEC, generate/cover/extend/edit tracks with
  Suno, or diagnose and iterate on generated takes safely.
---

# Suno Director (`sudirector`)

Orchestrate AI music production around a single `SONG-SPEC.yaml` Single Source of Truth, strict domain separation, deterministic validation/rendering, runtime capability guards, and structured post-generation diagnosis.

## Resolving the `sudirector` Binary

Run `sudirector` from any workspace:
- Primary (in `PATH`): `sudirector <command>`
- Windows fallback if current IDE terminal has not picked up the updated `PATH`: `%LOCALAPPDATA%\Programs\SunoDirector\sudirector.exe`

Always verify availability first if unsure (`sudirector --version`). Never edit bundled program files; store per-user runtime overrides under `%APPDATA%\SunoDirector\runtime-overrides.yaml`.

## Hard Safety & Credit Rules

1. **Preflight Before Any Spend**: Never call a credit-spending Suno MCP tool (`audio-create`, `audio-covers-create`, `audio-extensions-create`, `audio-edit`, `audio-download`, etc.) before running `sudirector preflight --json` against a fresh `account-usage` snapshot and getting `decision == "allowed"`.
2. **Per-Cycle Approval (Default)**: Under `confirmation_mode: per_cycle`, pause and present the operation, MCP tool, resolved model, credit cost, output count (`2 takes`), and remaining credits after execution. Wait for explicit user approval before passing `--approve`.
3. **No Silent Model Downgrade**: If `generation.model_preference` requests an unavailable model (e.g., `v6` on `Free`), `sudirector preflight` blocks execution. Never swap to `v6-mini` silently; present choices to the user.
4. **Download Credit Protection**: Never call `audio-download` automatically. Evaluate takes via `audio-retrieve`, `audio-listen`, and `audio-listen-wait` (0 credits) or browser links (`song_url`).
5. **Live MCP & Runtime Truth > Static Docs**: Trust `account-usage` and sanitized `mcp_payload` / `omitted_controls` from `sudirector preflight`.
6. **Diagnosis Before Spec Edit**: Never rewrite `SONG-SPEC.yaml` blindly after a bad take. Emit structured `diagnosis.yaml`, classify `SPEC_ERROR` vs `RENDER_ERROR` vs `EXECUTION_ERROR` vs `MIX_PHASE2`, and modify only the diagnosed `spec_path` entries.

## End-to-End Workflow (From Any Workspace)

1. **Initialize Spec**:
   - Run `sudirector init <song-slug> --json` (creates `./workspace/<song-slug>/SONG-SPEC.yaml`, `exports/`, `runs/` — or pass `--dir <path>`).
2. **Author Creative Spec (`SONG-SPEC.yaml`)**:
   - Follow `references/ownership.md` and `references/song-craft.md`.
   - Respect *One Decision, One Writer*: fill `identity`, `creative_direction`, `music.*` + `form[]`, `arrangement.*` + `vocal.*`, `lyrics.*` (skip sung lines if `vocal.enabled: false`), and `generation.*`.
3. **Validate & Render Fallback**:
   - Run `sudirector validate <spec> --json` until `errors` is empty.
   - Run `sudirector render <spec> --json` to write `exports/suno-pack.md`.
   - **No Suno MCP Fallback**: If Official Suno MCP tools (`account-usage`, `audio-create`, etc.) are unavailable or unauthenticated, stop cleanly and give the user `exports/suno-pack.md` for manual paste on `suno.com`.
4. **Preflight & Execute (Official Suno MCP)**:
   - See `references/mcp-playbook.md`.
   - Query `account-usage`, save snapshot to `runs/<timestamp>/account-before.yaml`, run `sudirector preflight <spec> --account <snapshot> --json`.
   - Obtain user approval, re-run with `--approve --out runs/<timestamp>/execution-plan.yaml`, then invoke only the mapped tool (`audio-create` / `audio-covers-create` / `audio-extensions-create` / `audio-edit`) using sanitized `mcp_payload`.
   - Poll `audio-wait`, call `audio-retrieve` and post-run `account-usage` -> save `account-after.yaml` and `result.yaml` (storing `spec_revision_before`, `spec_revision_after`, clip IDs, URLs; redact secrets).
5. **Zero-Credit Audit & Targeted Loop**:
   - Call `audio-listen` + `audio-listen-wait` on each take (0 credits) checking BPM, key, structure, chorus lift, vocals, ending, and artifacts.
   - Write `runs/<timestamp>/diagnosis.yaml`, validate with `sudirector validate <diagnosis> --kind diagnosis --json`, route per `references/routing.md`. Explicitly account for ambiguous detections (e.g., relative minor/major keys) rather than ignoring mismatches.
