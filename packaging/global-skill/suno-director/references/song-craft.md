# Song Craft & Anti-AI-Tell Checklist

1. **Composition**: Avoid locking every section to exact 8/16-bar multiples (`sudirector validate` warns on all-8-bar forms); reserve peak vocal pitch for the final chorus; specify concrete harmonic movement per section.
2. **Arrangement & Contrast**: `arrangement.energy_curve` must match `form[].id` and avoid monotonic climbs — plan deliberate pre-chorus subtraction/drops and distinct `section_layers` entries/exits.
3. **Lyrics & Pronunciation**: Keep syllable density matched to BPM; replace hollow buzzwords (`epic`, `beautiful`, `amazing`, `masterpiece`, `perfect`) with concrete instruments, mic feel, and groove cues; spell numbers/acronyms phonetically (`00:15` -> `Zero-zero-fifteen`).
4. **Clean Endings**: If `acceptance.must` requires a clean stop without fade-out, avoid cues like `tail`/`fades` in `lyrics.text`; use explicit stop cues (`[Outro - crisp final cadence]`, `[Cold Stop]`, `[End]`).
5. **Instrumental Guard**: When `vocal.enabled: false`, keep `lyrics.text` empty or `[Section]` tags only.
