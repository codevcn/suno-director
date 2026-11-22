# Third-Party Notices and Upstream Attribution

This repository (**Music Director**) is an independent AI music-production framework
synthesizing architectural concepts and operational practices from two upstream repositories.
Neither upstream is copied verbatim as a bundle; both are tracked as read-only Git submodules
under `upstream/`.

## Upstream Knowledge Sources

1. **bitwize-music-studio/claude-ai-music-skills**
   - Repository: https://github.com/bitwize-music-studio/claude-ai-music-skills
   - Submodule path: `upstream/bitwize`
   - Upstream License: `CC0-1.0` (Public Domain Dedication)
   - Adopted concepts: Suno v6-family operational guidance (`v6`, `v6-wild`, `v6-mini`),
     prompt surface constraints, Creative Sliders behavior (`Variety Off`, `Max Mode`),
     phonetic/pronunciation risk checks, lyric QC practices, and `audio-listen` take checking.

2. **jtydhr88/music-composition-skills**
   - Repository: https://github.com/jtydhr88/music-composition-skills
   - Submodule path: `upstream/composition`
   - Upstream License: `MIT` (applies to the original skill architecture, schema structure,
     checklists, boundary tables, and style-fusion ownership rules)
   - Important `NOTICE` exclusion respected:
     Per upstream `NOTICE`, quotations, translated passages, and figure references from
     third-party music theory/orchestration books inside `upstream/composition/**/reference*.md`
     are NOT covered by the MIT license. Those copyrighted quotations and Chinese reference
     prose are **not** copied or redistributed in this repository's `skills/` or `governance/`.

## External Services and Trademarks

- **Suno** and the Official Suno MCP server (`https://api.suno.com/mcp`) are trademarks and
  services of Suno, Inc. Mention of Suno models (`v6`, `v6-wild`, `v6-mini`) and MCP tool
  names is strictly for technical interoperability.
- Users are responsible for complying with Suno's Terms of Service and plan-specific
  commercial licensing rules for any audio they generate.
