# Music Director

An AI music-production framework built around a unified **SONG-SPEC** Single Source of Truth, strict domain ownership, a credit-guarded **Official Suno MCP** execution layer (with deterministic manual `suno-pack.md` fallback), and a closed-loop **Diagnosis → Targeted Revision** workflow.

> **Concept:** An independent AI music-production framework downstream of `bitwize-music-studio/claude-ai-music-skills` (Suno production craft) and `jtydhr88/music-composition-skills` (composition & arrangement intelligence), rather than a raw merge of the two repositories.

## Architecture Overview (V1)

```text
User Brief
   │
   ▼
music-director (orchestrator & spec revision)
   ├── composition-architect      (music.* & form[])
   ├── arrangement-architect      (arrangement.*, energy_curve, vocal section direction)
   ├── lyric-writer               (lyrics.text, rhyme, prosody QC)
   ├── pronunciation-specialist   (lyrics.pronunciation_overrides)
   └── suno-engineer              (generation.* & deterministic suno-pack)
   │
   ▼
SONG-SPEC.yaml ──► scripts/validate_spec.py ──► scripts/render_suno_pack.py (fallback)
   │
   ▼
execution-guard (account-usage preflight, model resolution, credit approval)
   │
   ▼
Official Suno MCP (audio-create / cover / extend / edit / wait / retrieve / listen)
   │
   ▼
take-reviewer (structured diagnosis.yaml: SPEC_ERROR vs RENDER_ERROR)
   └──► Targeted revision via music-director ──► Regenerate / Accept
```

## Quick Start

### 1. Install lightweight Python dependencies
```bash
python -m pip install -r requirements.txt
```

### 2. Validate a `SONG-SPEC.yaml`
```bash
python scripts/validate_spec.py examples/instrumental/SONG-SPEC.yaml
python scripts/validate_spec.py examples/vocal-song/SONG-SPEC.yaml
```

### 3. Render a deterministic Suno Pack (works with or without Suno MCP)
```bash
python scripts/render_suno_pack.py examples/vocal-song/SONG-SPEC.yaml
```

### 4. Run Execution Guard preflight check
```bash
python scripts/execution_guard.py examples/vocal-song/SONG-SPEC.yaml --account tests/fixtures/free-account.yaml
```

### 5. Check upstream repositories (read-only diff detection, never auto-overwrites)
```bash
python scripts/check_upstreams.py
```

### 6. Run tests
```bash
pytest
```

## Repository Structure

- `AGENTS.md` / `CLAUDE.md` — Canonical agent instructions and thin Claude pointer.
- `governance/` — `OWNERSHIP.md`, `ROUTING.md`, `EXECUTION_POLICY.md`, `UPSTREAM_POLICY.md`, `ADOPTION.md`.
- `skills/` — The 8 core V1 agent skills (`SKILL.md`).
- `schemas/` — JSON Schemas (`song-spec.schema.json`, `diagnosis.schema.json`, `execution-plan.schema.json`).
- `templates/` — Blank canonical `SONG-SPEC.yaml`.
- `adapters/suno/` — Capability normalization rules, credit cost defaults, semantic tool routing, and runtime authority guidance.
- `scripts/` — Lightweight Python tools (`validate_spec.py`, `render_suno_pack.py`, `execution_guard.py`, `check_upstreams.py`).
- `examples/` — Reference `instrumental` and `vocal-song` specs with rendered packs.
- `upstream/` — Read-only Git submodules (`bitwize`, `composition`) pinned via `upstream-lock.yaml`.
- `tests/` — Pytest suite covering spec validation, credit/model guards, deterministic rendering, diagnosis routing, and upstream checking.

## Phase 2 Extension Hooks (Not Implemented in V1)

Phase 2 capabilities—stem separation QC, mixing/mastering automation, multi-track album workflows, artwork/video generation, release preparation, external research agents, and persistent DB state—are intentionally excluded from V1 skills to keep the core production loop fast and reliable. See `governance/ROUTING.md` for planned Phase 2 extension points.

## License & Notices

Code and original framework materials are licensed under the [MIT License](LICENSE). See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for upstream attributions and `NOTICE` boundaries.
