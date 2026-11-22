# Music Director — Canonical Agent Instructions

This repository is **Music Director**, an AI music-production framework built with a unified `SONG-SPEC` Single Source of Truth, strict domain ownership, a credit-guarded execution layer over the Official Suno MCP, and a structured diagnosis feedback loop (`Brief -> SONG-SPEC -> Preflight -> Approval -> Execute -> Listen -> Diagnose -> Targeted Spec Revision`).

All AI agents (Antigravity, Claude Code, Codex, or other MCP-enabled agents) MUST follow this file as the canonical source of instructions.

---

## 1. Core Architectural Boundaries

1. **Single Source of Truth (`SONG-SPEC.yaml`)**: Creative intent lives in `workspace/<song-slug>/SONG-SPEC.yaml`. Never mix run logs, raw MCP responses, or execution history into `SONG-SPEC.yaml`.
2. **Execution Evidence Separation**: Run logs, preflight snapshots, diagnosis reports, and exported prompts live alongside the spec under:
   - `workspace/<song-slug>/exports/suno-pack.md`
   - `workspace/<song-slug>/runs/<timestamp>/execution-plan.yaml`
   - `workspace/<song-slug>/runs/<timestamp>/account-before.yaml`
   - `workspace/<song-slug>/runs/<timestamp>/result.yaml`
   - `workspace/<song-slug>/runs/<timestamp>/diagnosis.yaml`
   - `workspace/<song-slug>/runs/<timestamp>/account-after.yaml`
3. **8 Core Skills Only (V1)**: All work routes strictly through the 8 skills in `skills/*/SKILL.md` per `governance/OWNERSHIP.md` and `governance/ROUTING.md`. Never invent duplicate skills or split spec-revision away from `music-director`.
4. **Read-Only Upstreams**: `upstream/bitwize` and `upstream/composition` are read-only Git submodules. Never edit files inside `upstream/` or blindly copy/overwrite from them.

---

## 2. Hard Operational Rules

1. **Mandatory Execution Guard**: No agent may call any credit-spending Suno MCP tool (`audio-create`, `audio-covers-create`, `audio-extensions-create`, `audio-edit`, `audio-stems-create`, `audio-download`, `image-create`, `video-*`, `speech-create`, `sounds-create`, etc.) without first passing through `skills/execution-guard/SKILL.md` and producing a passing `execution-plan`.
2. **Live MCP Reality > Static Docs**: Always query `account-usage` and inspect the live MCP tool parameter schemas at runtime rather than trusting static assumptions.
3. **No Silent Model Downgrade**: If `generation.model_preference` requests an unavailable model (e.g., `v6` on a `Free` account), **BLOCK** execution and present explicit choices (`auto`/`v6-mini`, manual `suno-pack.md` fallback, or upgrading externally).
4. **Download Credit Protection**: Never call `audio-download` automatically in V1. Review takes using `audio-retrieve`, `audio-listen`, and `audio-listen-wait` (0 credits). Only download when the user explicitly requests and approves download credit spend.
5. **Distinguish `SPEC_ERROR` vs `RENDER_ERROR`**: `take-reviewer` must classify root causes accurately and emit structured `diagnosis.yaml` validated against `schemas/diagnosis.schema.json`. `music-director` modifies only the `spec_path` entries indicated by diagnosis—never rewrite an entire spec blindly.
6. **Creative Layer != MCP Availability**: Even when Suno MCP is unavailable or disconnected, `scripts/validate_spec.py` and `scripts/render_suno_pack.py` must produce a deterministic `exports/suno-pack.md` for manual paste on `suno.com`.
7. **Notice Compliance**: Respect `THIRD_PARTY_NOTICES.md`. Never copy third-party book quotations or Chinese reference prose from `upstream/composition`.
