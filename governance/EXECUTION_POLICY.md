# Execution & Credit Guard Policy (V1)

## 1. Mandatory Gate Rule

> **HARD RULE:** No agent may call any Suno MCP tool that can spend credits (`audio-create`, `audio-covers-create`, `audio-extensions-create`, `audio-edit`, `audio-stems-create`, `audio-download`, `image-create`, `video-*`, `speech-create`, `sounds-create`) unless `execution-guard` has run preflight and issued an `allowed` `execution-plan.yaml`.

This is a strict behavioral governance gate enforced across `AGENTS.md` and all skill definitions.

---

## 2. Preflight Algorithm

Before every credit-spending execution:

1. **Query Live Capabilities**: Call `account-usage` (0 credits). Never assume plan tier or credits from memory.
2. **Normalize Capability Snapshot**: Convert live `account-usage` response into normalized structure:
   - `plan` (`free` | `pro` | `premier` | unknown)
   - `song_credits.remaining`
   - `download_credits.remaining`
   - `models.allowed` (exact list from live `allowed_models`)
   - `capabilities` (`create`, `cover`, `extend`, `edit`, `download`)
3. **Validate Spec**: Run `python scripts/validate_spec.py <SONG-SPEC.yaml>`. Any validation error blocks execution.
4. **Resolve Model (No Silent Downgrade)**:
   - If `generation.model_preference == "auto"`, select best allowed model from `models.allowed` (priority: `v6` > `v6-wild` > `v6-mini` > first allowed).
   - If `generation.model_preference` names an explicit model (e.g., `v6`) and it is **not** in `models.allowed`:
     - **BLOCK** execution immediately.
     - Report clearly: *"Spec requires `<requested>`, but current `<plan>` account only allows `<allowed>`."*
     - Offer 3 choices: (1) update spec to `auto` or an allowed model, (2) export `exports/suno-pack.md` manual fallback, or (3) upgrade plan externally.
5. **Estimate Cost**: Compute expected `song_credits` (default `10`, or `20` if `max_mode: true`; `0` for `audio-full-song`) and `download_credits` (`0` for generation; `1` per new song download).
6. **Check Approved Budget & Confirmation Mode**:
   - **`per_cycle` (Default)**: Present Operation, Resolved Model, Expected Cost, Output Count (2 takes), and Remaining Credits After Execution. Require explicit user approval before running.
   - **`budget` (Power-User Mode)**: Allowed only when user explicitly grants a budget (`confirmation_mode: budget`, `allow_auto_iteration: true`, `approved_song_credit_budget > 0`). Agent may iterate until `approved_song_credit_budget` would be exceeded, then must stop and ask.
7. **Log & Execute**: Write `execution-plan.yaml` and `account-before.yaml`, call the mapped Suno MCP tool, wait/retrieve, and record `result.yaml` + `account-after.yaml`.

---

## 3. Download Credit Protection

Free accounts carry only lifetime trial download credits (e.g., `7`), and paid plans have monthly caps (`20`/`60`).
- **Never auto-call `audio-download` in V1.**
- All take listening and evaluation MUST use `audio-retrieve`, `audio-listen`, and `audio-listen-wait` (0 credits) or browser playback via `song_url`.
- `audio-download` is only permitted when the user explicitly requests a download and approves spending `download_credits` (`approved_download_credit_budget >= 1`).

---

## 4. Fallback When Suno MCP Is Unavailable

If Suno MCP is disconnected, unauthenticated, or blocked:
- Run `python scripts/render_suno_pack.py <SONG-SPEC.yaml>` to produce `exports/suno-pack.md`.
- Present the copy-paste pack (`Title`, `Model recommendation`, `Style`, `Lyrics`, `Exclude Styles`, `Generation notes`, `Expected structure`, `Acceptance checklist`) so the user can generate manually on `suno.com`.
