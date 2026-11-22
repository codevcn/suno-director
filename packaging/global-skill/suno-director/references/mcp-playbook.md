# Suno MCP Execution Playbook

1. **Inspect Live Capabilities (0 credits)**:
   - Call `account-usage` via Official Suno MCP. Save output to `runs/<timestamp>/account-before.yaml`.
2. **Run Preflight (`sudirector preflight`)**:
   - Dry-run: `sudirector preflight SONG-SPEC.yaml --account runs/<ts>/account-before.yaml --json`
   - Check `decision`, `resolved_model`, `estimated_song_credits`, `omitted_controls` (e.g., runtime incompatibility overrides on Free/`v6-mini`), and `mcp_payload`.
   - If `decision == "blocked"` for model mismatch or credit policy, surface options to the user — never bypass or downgrade silently.
3. **Execute Approved Cycle**:
   - After explicit user confirmation (`per_cycle`), run with `--approve --out runs/<ts>/execution-plan.yaml`.
   - Tool mapping: `create -> audio-create`, `cover -> audio-covers-create`, `extend -> audio-extensions-create`, `edit -> audio-edit`.
   - Pass only the fields inside `execution-plan.yaml`'s `mcp_payload` plus a unique `idempotency_key`.
   - If the backend rejects an optional field (e.g. `403 feature_not_on_plan`), record `attempt-00-rejected.yaml` and add a local override under `%APPDATA%\SunoDirector\runtime-overrides.yaml` before retrying.
4. **Settle & Listen (0 credits)**:
   - Call `audio-wait` (`until: "complete"`), `audio-retrieve` for all returned clip IDs, and `account-usage` again (`account-after.yaml`).
   - Run `audio-listen` + `audio-listen-wait` on every take and save structured findings in `runs/<ts>/result.yaml` (`spec_revision_before`, `spec_revision_after`, clip URLs, metrics) and `runs/<ts>/diagnosis.yaml`.
