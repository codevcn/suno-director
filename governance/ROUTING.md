# Routing Rules & Taxonomy (V1)

`music-director` acts strictly as an **orchestrator and router**, never as a monolith that solves musical, lyrical, or prompt problems itself.

---

## 1. Forward Production Pipeline

```text
1. Brief Intake           -> music-director (initializes identity, creative_direction, acceptance)
2. Musical Skeleton       -> composition-architect (music.*, form[])
3. Arrangement & Arc      -> arrangement-architect (arrangement.*, vocal.*)
4. Lyrics (if vocal)      -> lyric-writer -> pronunciation-specialist
5. Backend Compilation    -> suno-engineer (generation.* + deterministic render_suno_pack.py)
6. Preflight & Guard      -> execution-guard (validate_spec -> account-usage -> budget/model check -> approval)
7. Execution              -> Official Suno MCP (or manual exports/suno-pack.md fallback)
8. Post-Generation Audit  -> take-reviewer (audio-retrieve + audio-listen -> diagnosis.yaml)
9. Targeted Loop          -> music-director routes ONLY diagnosed spec_path items back to owning specialist
```

*Note: If `vocal.enabled == false`, Step 4 (`lyric-writer` and `pronunciation-specialist`) is skipped cleanly by the Instrumental Guard.*

---

## 2. Post-Generation Diagnosis Routing Taxonomy

When `take-reviewer` evaluates takes, it maps observed symptoms to the **first owner** and `class` (`SPEC_ERROR` vs `RENDER_ERROR` vs `EXECUTION_ERROR` vs `MIX_PHASE2`):

| Symptom | Error Class (Typical) | First Owner | Action / Escalation |
|---|---|---|---|
| Wrong chord progression or flat harmony | `SPEC_ERROR` | `composition-architect` | Update `music.harmony` |
| Weak / unsingable melody or awkward phrasing | `SPEC_ERROR` | `composition-architect` | Adjust `music.melody` / register |
| Form feels too long, short, or monotonous (all 8-bar multiples) | `SPEC_ERROR` | `composition-architect` | Adjust `form[].bars` / asymmetry |
| Chorus fails to lift | `SPEC_ERROR` if delta small; `RENDER_ERROR` if spec delta clear | `arrangement-architect` (first) or `suno-engineer` | Increase contrast/subtraction before chorus, or sharpen cue/style |
| Instrumentation too dense/thin or enters/exits awkwardly | `SPEC_ERROR` | `arrangement-architect` | Revise `arrangement.section_layers` / `transitions` |
| Lyrics cliché, poor rhyme, or rhythmic mismatch | `SPEC_ERROR` | `lyric-writer` | Revise `lyrics.text` / prosody |
| Suno mispronounces a word, name, or acronym | `SPEC_ERROR` | `pronunciation-specialist` | Add phonetic spelling to `lyrics.pronunciation_overrides` and `lyrics.text` |
| Vocal style wrong despite clear `vocal.*` spec | `RENDER_ERROR` | `suno-engineer` | Refine vocal descriptors / performance cues / model choice |
| Genre or timbre drifted despite clear `arrangement.*` | `RENDER_ERROR` | `suno-engineer` | Check `Variety: Off`, tighten `generation.style_prompt` & `exclude_styles` |
| Tempo drifted significantly from `music.tempo_bpm` | `RENDER_ERROR` | `suno-engineer` -> escalate `composition-architect` | Make BPM explicit in `style_prompt`; adjust phrasing if repeated |
| Section skipped or compressed | `SPEC_ERROR` or `RENDER_ERROR` | `arrangement-architect` + `suno-engineer` | Check lyric density/section tags and `max_mode` / duration |
| Audible AI artifacts, muddy ending, or unwanted fade-out | `RENDER_ERROR` | `suno-engineer` | Add `fade out ending` to `exclude_styles`, refine tags or `model` |
| Bad or abrupt ending on an otherwise strong take | `SPEC_ERROR` or `EXECUTION_ERROR` | `arrangement-architect` or `execution-guard` (`extend`) | Revise outro spec or run `generation.intent: extend` |
| Song great overall but cut short before ending | `EXECUTION_ERROR` | `execution-guard` (`extend`) | Switch intent to `extend` with `source.audio_id` + `continue_at` |
| Single line/word error in an otherwise keeper take | `EXECUTION_ERROR` | `execution-guard` (`edit`) | Switch intent to `edit` targeting localized section/line |
| Want to reinterpret production while keeping melody/structure | `EXECUTION_ERROR` | `execution-guard` (`cover`) | Switch intent to `cover` with `source.audio_id` |
| Subtle mix/EQ/loudness imbalance (stems/mastering needed) | `MIX_PHASE2` | `take-reviewer` (flag only in V1) | Flag for manual DAW / Phase 2 pipeline; do not loop endlessly in V1 |

---

## 3. Phase 2 Extension Hooks (Architectural Placeholders Only)

Phase 2 modules are **not** implemented as skills in V1. When Phase 2 is unlocked after V1 acceptance:
- `stem-qc` & `mix-engineer` & `mastering-engineer` will hook after `take-reviewer` (`verdict: accept`) via `selected_take_id` + explicit download approval.
- `album-director`, `artwork-director`, `video-director`, `release-manager` will wrap multiple `workspace/<song-slug>/` folders.
- `research-orchestrator` and persistent state/DB hooks will sit upstream of `music-director` brief intake.
