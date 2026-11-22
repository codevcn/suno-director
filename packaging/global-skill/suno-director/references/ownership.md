# Domain Ownership & Precedence

Apply **One Decision, One Writer** when editing `SONG-SPEC.yaml`:

| Domain | Specialist Role | Owned `SONG-SPEC` Paths |
|---|---|---|
| Orchestration & Spec Revision | `music-director` | Overall routing, `identity.*`, `creative_direction.*`, `acceptance.*`, targeted post-diagnosis edits |
| Musical Skeleton | `composition-architect` | `music.key`, `music.tempo_bpm`, `music.meter`, `music.harmony.*`, `music.melody.*`, `form[]` |
| Arrangement & Energy | `arrangement-architect` | `arrangement.instrumentation`, `section_layers`, `transitions`, `energy_curve`, `mix_intent`, `vocal.section_direction` |
| Lyrics & Prosody | `lyric-writer` | `lyrics.text`, `lyrics.rhyme_strategy`, `lyrics.prosody_notes` |
| Phonetics & Pronunciation | `pronunciation-specialist` | `lyrics.pronunciation_overrides` + phonetic spellings in `lyrics.text` |
| Suno Compilation | `suno-engineer` | `generation.style_prompt`, `generation.exclude_styles`, `generation.controls` |
| Preflight & Dispatch | `execution-guard` | `execution-plan.yaml`, capability/model resolution, sanitized `mcp_payload` |
| Take Audit | `take-reviewer` | `diagnosis.yaml`, `adherence` checklist, `SPEC_ERROR` vs `RENDER_ERROR` |

Never allow `suno-engineer` to silently alter `music.*` or `form[]`, and never run `lyric-writer` / `pronunciation-specialist` when `vocal.enabled == false`.
