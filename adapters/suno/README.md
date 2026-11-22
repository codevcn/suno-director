# Official Suno MCP Adapter

This adapter translates backend-agnostic `SONG-SPEC.yaml` creative & generation intents into **Official Suno MCP** operations, while guaranteeing graceful fallback to `exports/suno-pack.md` when Suno MCP is unavailable.

## Authority Rule

> **Live MCP Tool Definitions > Static Adapter Docs.**

- `routing.yaml` defines **semantic mapping** between `SONG-SPEC.generation.intent` and Official Suno MCP tool names.
- Exact request parameter names, optional fields, and enums MUST be read from the live MCP tool schema at runtime.
- `capabilities.yaml` documents how `account-usage` outputs normalize into a capability snapshot and provides baseline credit cost estimates used by `execution-guard`.

## Supported V1 Operations

| `generation.intent` | Primary MCP Tool | Follow-up MCP Tools | Purpose |
|---|---|---|---|
| `create` | `audio-create` | `audio-wait`, `audio-retrieve`, `audio-listen`, `audio-listen-wait` | Generate 2 new song takes |
| `cover` | `audio-covers-create` | `audio-wait`, `audio-retrieve`, `audio-listen`, `audio-listen-wait` | Reinterpret production/style while keeping source identity |
| `extend` | `audio-extensions-create` | `audio-wait`, `audio-full-song`, `audio-retrieve`, `audio-listen` | Continue a cut-off or incomplete take from `source.continue_at` |
| `edit` | `audio-edit` | `audio-wait`, `audio-retrieve`, `audio-listen` | Fix localized word/line/section defects on a strong take |

## Manual Fallback

When Suno MCP is disconnected, unauthenticated, or blocked by plan/model constraints, run:
```bash
python scripts/render_suno_pack.py <workspace>/<song-slug>/SONG-SPEC.yaml
```
and paste the generated sections from `exports/suno-pack.md` directly into `suno.com` (Advanced Mode).
