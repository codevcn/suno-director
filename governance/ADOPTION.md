# Upstream Concept Adoption Ledger

This document records **what each local V1 skill adopted** from the two upstream repositories, **what was newly engineered**, and **what was intentionally excluded**.

---

## 1. `music-director`
- **Local role**: Workflow orchestrator, brief intake, targeted `SONG-SPEC` revision from `diagnosis.yaml`, workspace manager.
- **Adopted from `composition`**: S0–S7 stage-gate philosophy (`mc-workflow`), intent-before-form discipline, and boundary enforcement ("one owner per decision").
- **Newly engineered**: Unified `SONG-SPEC` schema replacing split `ARR-SPEC` + album track markdown; structured `diagnosis -> spec_path` revision loop.
- **Excluded**: Bitwize 7-phase documentary album directory pipeline, Postgres/state DB, and `composition`'s 20-point manual Chinese prose table verbatim.

## 2. `composition-architect`
- **Local role**: Owns `music.*` (key, mode, tempo, meter, harmony, melody) and `form[]`.
- **Adopted from `composition`**: `mc-melody`, `mc-harmony`, `mc-progressions`, `mc-modulation`, `mc-form`, `mc-development`, `mc-rhythm-groove` rules:
  - Asymmetric section lengths (never all multiples of 8 bars).
  - Dual harmonic notation (Roman numerals + ASCII chord letters).
  - Motif definition + per-section development tracking (never every section as unrelated `new` material).
  - Out-of-key / modal color requirement in bridge or contrast sections.
- **Excluded**: Symbolic ABC/MusicXML/MIDI exporter (`mc-symbolic-score`), third-party book quotations, and Chinese reference prose (`NOTICE`).

## 3. `arrangement-architect`
- **Local role**: Owns `arrangement.*` and `vocal.section_direction`.
- **Adopted from `composition`**: `mc-arrangement-arch`, `mc-orchestration`, `mc-texture-layering`, `mc-rhythm-section`, `mc-vocal-direction`, `mc-mix-intent`:
  - Non-monotonic `energy_curve` (mandatory drop/contrast before climax).
  - Explicit instrument entry/exit events (`section_layers`) and `transitions` (subtractive arranging).
  - V2 differentiation (second verse must evolve from first verse).
  - Anti-fade-out explicit ending design.
  - Per-section vocal delivery & chorus variation.
- **Excluded**: Real-audio DSP/EQ/compression parameters (Phase 2) and book excerpts.

## 4. `lyric-writer`
- **Local role**: Owns `lyrics.text`, `rhyme_strategy`, `prosody_notes`.
- **Adopted from `bitwize`**: `lyric-writer` craft principles:
  - Instrumental Guard (skip cleanly when `vocal.enabled == false`).
  - Rhyme discipline (no consecutive identical end-words or self-rhymes).
  - Prosody & syllable-count consistency per section.
  - Verse-to-chorus anti-echo check (no repeated hook lines right before chorus).
  - Word-count & section-density pacing relative to `target_duration_seconds`.
- **Excluded**: Bitwize true-crime documentary legal verification sub-agents (Phase 2).

## 5. `pronunciation-specialist`
- **Local role**: Owns `lyrics.pronunciation_overrides`.
- **Adopted from `bitwize`**: `pronunciation-specialist` and `pronunciation-guide.md`:
  - Instrumental Guard.
  - Homograph disambiguation (`live`, `read`, `lead`, `wind`, `tear`, `bass`).
  - Tech term, acronym, proper noun, and number phonetic spelling rules.
- **Excluded**: Bitwize album-wide SQL/Python scanner tools.

## 6. `suno-engineer`
- **Local role**: Owns `generation.*` and compilation to Suno surface / `suno-pack.md`.
- **Adopted from `bitwize`**: Suno v6 family prompting (`v6`, `v6-wild`, `v6-mini`), vocals-first ordering, `Variety: Off` when style is engineered, `Max Mode` guidance, strict Lyrics Box rule (no parenthetical stage directions), performance cues `<= 3` per section, artist blocklist awareness.
- **Adopted from `composition`**: `mc-render-compile` rules: ban hollow adjectives (`epic`, `beautiful`, `amazing`, `masterpiece`, `perfect`), translate quantitative timing/feel into audible prose, add `fade out ending` to `exclude_styles` when an explicit ending is desired.
- **Newly engineered**: Pure deterministic compiler `scripts/render_suno_pack.py` reading `SONG-SPEC.yaml` with zero runtime LLM invention.

## 7. `execution-guard`
- **Local role**: Mandatory preflight gate, capability normalization, model resolution, credit/download protection, and MCP tool dispatch.
- **Adopted from `bitwize`**: `mcp-api-mapping.md` cost awareness (`10` credits/call, `20` Max Mode, download credit scarcity) and preflight `account-usage` check.
- **Newly engineered**: Normalized capability snapshot decoupling specs from Suno plan tiers, hard block on unavailable requested models (no silent downgrade), `per_cycle` vs `budget` modes, and semantic routing (`adapters/suno/routing.yaml`) that defers argument schemas to live MCP tool definitions.

## 8. `take-reviewer`
- **Local role**: Post-generation evaluation, AI-tell audit, `SPEC_ERROR` vs `RENDER_ERROR` classification, structured `diagnosis.yaml`.
- **Adopted from `bitwize`**: `check-take` non-destructive inspection via `audio-retrieve`, `audio-listen`, and `audio-listen-wait` (0 credits, no download).
- **Adopted from `composition`**: `mc-ai-tell-audit` separation between `spec_adherence` and AI-tell indicators (monotonic energy, static arrangement, grid stiffness, identical choruses, default fade-out).
- **Newly engineered**: Machine-validated `diagnosis.schema.json` with exact `spec_path` pointers and `next_action.owner` routing.
