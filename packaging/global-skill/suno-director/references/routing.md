# Diagnosis & Targeted Revision Taxonomy

Evaluate every acceptance metric explicitly as `confirmed_match`, `confirmed_mismatch`, `ambiguous`, or `not_evaluated`. Never silently ignore field mismatches (e.g., relative major/minor key ambiguity like `F# minor` vs `A major`).

| Observed Symptom | Error Class | First Owner | Action |
|---|---|---|---|
| Cross-domain spec conflict (e.g. `clean_stop` vs `tail` outro cue + missing `exclude_styles`) | `SPEC_ERROR` | `music-director` | Dispatch targeted `spec_path` fixes to owning roles before blaming backend |
| Weak harmony, unsingable range, all-8-bar robotic phrasing | `SPEC_ERROR` | `composition-architect` | Revise `music.harmony`, `music.melody`, or `form[].bars` |
| Flat chorus because spec delta/subtraction missing | `SPEC_ERROR` | `arrangement-architect` | Increase `energy_curve` contrast & add pre-chorus subtraction |
| Spec energy contrast & cues clear, yet rendered chorus stays flat | `RENDER_ERROR` | `suno-engineer` | Sharpen performance cues & `generation.style_prompt` |
| Mispronounced acronym/number/word | `SPEC_ERROR` | `pronunciation-specialist` | Spell phonetically in `lyrics.text` + record `pronunciation_overrides` |
| Unwanted fade-out after clean unambiguous stop cues | `RENDER_ERROR` | `suno-engineer` | Strengthen `exclude_styles` & cutoff metatags (`[Cold Stop]`, `[End]`) |
| Song great overall but ending cut off | `EXECUTION_ERROR` | `execution-guard` (`extend`) | Set `generation.intent: extend` + `source.audio_id` + `continue_at` |
| Single bad phrase/word in keeper take | `EXECUTION_ERROR` | `execution-guard` (`edit`) | Set `generation.intent: edit` + `source.audio_id` |
| EQ/loudness/stem balance polish needed beyond prompt control | `MIX_PHASE2` | `take-reviewer` (flag only) | Stop looping in V1; flag for DAW / stems phase |
