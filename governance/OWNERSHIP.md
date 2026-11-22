# Domain Ownership Matrix (V1)

Every musical, lyrical, prompt, execution, and diagnostic decision has **exactly one authoritative owner**. No two skills may claim authority over the same decision.

## 1. Ownership Table

| Domain | Authoritative Owner | Upstream Inspiration | Notes |
|---|---|---|---|
| Orchestration & Routing | `music-director` | New (Framework Core) | Coordinates S0–S7 flow and dispatches specialists |
| Unified `SONG-SPEC.yaml` Schema | `music-director` | Inspired by `ARR-SPEC` (`composition`) | Single Source of Truth for creative intent |
| Spec Revision (Post-Diagnosis) | `music-director` | New (Framework Core) | Modifies only `spec_path` targets named by `diagnosis.yaml` |
| Melody (range, motif, contour, peak) | `composition-architect` | `composition` (`mc-melody`, `mc-development`) | Owns `music.melody.*` |
| Harmony, Progressions & Modulation | `composition-architect` | `composition` (`mc-harmony`, `mc-progressions`, `mc-modulation`) | Owns `music.key`, `music.harmony.*` |
| Form & Section Bar Lengths | `composition-architect` | `composition` (`mc-form`, `mc-development`) | Owns `form[]`, `music.meter`, `music.tempo_bpm` |
| Rhythm & Groove Feel | `composition-architect` | `composition` (`mc-rhythm-groove`) | Owns rhythmic feel baseline |
| Arrangement Architecture & Energy Curve | `arrangement-architect` | `composition` (`mc-arrangement-arch`) | Owns `arrangement.energy_curve`, subtraction & contrast |
| Orchestration & Texture/Layering | `arrangement-architect` | `composition` (`mc-orchestration`, `mc-texture-layering`, `mc-rhythm-section`) | Owns `arrangement.instrumentation`, `section_layers`, `transitions` |
| Mix Intent (Non-DSP) | `arrangement-architect` | `composition` (`mc-mix-intent`) | Owns `arrangement.mix_intent` (Phase 1 intent only) |
| Vocal Arrangement (Per-Section Direction) | `arrangement-architect` | `composition` (`mc-vocal-direction`) | Owns `vocal.section_direction`, register/delivery dynamics |
| Lyrics, Rhyme & Prosody QC | `lyric-writer` | `bitwize` (`lyric-writer`) | Owns `lyrics.text`, `rhyme_strategy`, `prosody_notes` |
| Pronunciation & Phonetic Fixes | `pronunciation-specialist` | `bitwize` (`pronunciation-specialist`) | Owns `lyrics.pronunciation_overrides` |
| Suno Style Prompt, Tags & Settings | `suno-engineer` | `bitwize` (`suno-engineer`) + `composition` (`mc-render-compile`) | Owns `generation.*` (`style_prompt`, `exclude_styles`, `controls`) |
| Account Preflight, Capabilities & Budget | `execution-guard` | Live Official Suno MCP + `bitwize` cost notes | Owns `execution-plan.yaml`; enforces **Live MCP > static docs** |
| MCP Tool Choice & Execution Dispatch | `execution-guard` | Framework Core + `adapters/suno/` | Resolves `create` / `cover` / `extend` / `edit` |
| Take Evaluation & AI-Tell Audit | `take-reviewer` | `bitwize` (`check-take`) + `composition` (`mc-ai-tell-audit`) | Owns `diagnosis.yaml` & `SPEC_ERROR` vs `RENDER_ERROR` split |

## 2. Authority Precedence Rules

1. **Live Suno MCP > Static Docs**: If `account-usage` or live MCP tool schemas contradict any documentation (including `upstream/bitwize` or `adapters/suno/capabilities.yaml`), the live MCP response wins immediately.
2. **One Decision, One Writer**: Only the owning skill writes its fields in `SONG-SPEC.yaml`. For example, `suno-engineer` translates `music.*` and `arrangement.*` into `generation.style_prompt`; it never silently alters `music.tempo_bpm` or `form[]`.
3. **Diagnosis Before Edit**: After generation, no specialist edits `SONG-SPEC.yaml` until `take-reviewer` emits a structured `diagnosis.yaml` identifying the error class (`SPEC_ERROR` vs `RENDER_ERROR`) and owner.
