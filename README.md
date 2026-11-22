<p align="center">
  <img src="assets/logos/v1-baton-pulse-cyan.svg" width="96" height="96" alt="Suno Director — V1 Baton Pulse (Cyan Pulse)" />
</p>

<h1 align="center">Suno Director (<code>sudirector</code>)</h1>

<p align="center">
  Spec-driven, credit-guarded AI music production CLI &amp; Global Agent Skill framework for Suno AI.
</p>

<p align="center">
  <a href="https://github.com/codevcn/suno-director/releases"><img src="https://img.shields.io/badge/version-v0.2.0%20(SemVer)-38BDF8?style=flat-square" alt="Version v0.2.0" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-0EA5E9?style=flat-square" alt="MIT License" /></a>
  <img src="https://img.shields.io/badge/python-3.11%2B-38BDF8?style=flat-square" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/skills-Codex%20%7C%20Antigravity%20%7C%20Claude%20Code-0B0D12?style=flat-square" alt="Supported Agents" />
</p>

---

**Suno Director (`sudirector`)** is an independent AI music-production framework built downstream of `bitwize-music-studio/claude-ai-music-skills` and `jtydhr88/music-composition-skills`. It separates creative musical intent (`SONG-SPEC.yaml`) from Suno execution evidence, enforces runtime capability & credit safety before calling Official Suno MCP tools, and closes the feedback loop with structured `diagnosis.yaml` root-cause routing (`SPEC_ERROR` vs `RENDER_ERROR`).

## Table of Contents

- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [CLI Reference (`sudirector`)](#cli-reference-sudirector)
- [Global AI Skill Usage](#global-ai-skill-usage)
- [Architecture Overview](#architecture-overview)
- [Configuration & Runtime Overrides](#configuration--runtime-overrides)
- [Testing & Building from Source](#testing--building-from-source)
- [Versioning (SemVer 2.0.0)](#versioning-semver-200)
- [Troubleshooting](#troubleshooting)
- [License & Third-Party Notices](#license--third-party-notices)

---

## Key Features

- **Unified `SONG-SPEC.yaml` Single Source of Truth**: Holds harmony, melody contour, section form, energy curve, instrumentation, lyrics, pronunciation overrides, and acceptance gates without mixing raw MCP payloads.
- **One Decision, One Writer**: Strict domain separation across 8 core specialist roles (`music-director`, `composition-architect`, `arrangement-architect`, `lyric-writer`, `pronunciation-specialist`, `suno-engineer`, `execution-guard`, `take-reviewer`).
- **3-Layer Truth & Credit Guard (`sudirector preflight`)**:
  - Queries live `account-usage` before any spend, enforces `per_cycle` or explicit `budget` approval, protects `download_credits`, and never silently downgrades requested models (`v6` -> `v6-mini`).
  - Applies observed `runtime_overrides` on top of declared `account-usage` features (for example omitting `exclude_styles` and `sliders` on `free`/`v6-mini` when Suno returns `403 feature_not_on_plan`).
- **Deterministic Offline Fallback (`suno-pack.md`)**: Generates clean copy-paste production packs for `suno.com` even when Official Suno MCP is unavailable.
- **Global AI Skill + Standalone Windows CLI**: Works from **any** workspace via `sudirector` and installs globally for **Codex**, **Antigravity**, and **Claude Code**.

---

## Tech Stack

- **Runtime & CLI**: Python 3.11+, `PyYAML >= 6.0`, `jsonschema >= 4.20`
- **Packaging**: PyInstaller (`--onedir`), Inno Setup 6 (`PrivilegesRequired=lowest` per-user Windows installer), Pillow (icon/BMP assets)
- **Testing**: `pytest >= 8.0`
- **Versioning**: Built-in SemVer 2.0.0 parser, comparator, and bumper (`src/music_director/version.py`)

---

## Prerequisites

- **Windows End Users (Installer)**: Windows 10/11 (x64). No Python installation required for the `SunoDirector-Setup-0.2.0.exe` bundle. Optional: Official Suno MCP configured in your AI client (falls back to `exports/suno-pack.md` if absent).
- **Developers (From Source)**:
  - Python `3.11+`
  - Git (with submodules if tracking upstream docs)
  - Optional for Windows installer builds: `pyinstaller`, `pillow`, and **Inno Setup 6** (`ISCC.exe`)

---

## Installation

### Option 1: Windows Installer (`SunoDirector-Setup-0.2.0.exe`)

1. Download `SunoDirector-Setup-0.2.0.exe` from the [GitHub Releases](https://github.com/codevcn/suno-director/releases) page.
2. Run the installer (per-user install into `%LOCALAPPDATA%\Programs\SunoDirector` — no Administrator UAC prompt required):
   - Adds `sudirector` to your user `PATH`.
   - Installs the Global AI Skill (`suno-director`) by default into all three AI agents:
     - **Codex**: `%USERPROFILE%\.codex\skills\suno-director`
     - **Antigravity**: `%USERPROFILE%\.gemini\config\skills\suno-director`
     - **Claude Code**: `%USERPROFILE%\.claude\skills\suno-director`
3. Verify in a terminal:
   ```powershell
   sudirector --version
   ```
   Expected output:
   ```text
   sudirector 0.2.0
   ```

### Option 2: Install From Source (Developer Mode)

1. Clone the repository (including read-only upstream submodules):
   ```bash
   git clone --recurse-submodules https://github.com/codevcn/suno-director.git
   cd suno-director
   ```
2. Install runtime and dev dependencies in editable mode:
   ```bash
   python -m pip install -e ".[dev]"
   ```
3. Install the Global AI Skill across Codex, Antigravity, and Claude Code:
   ```bash
   sudirector install-skill
   ```

---

## CLI Reference (`sudirector`)

Every subcommand supports `--json` for deterministic AI agent parsing.

| Command | Purpose | Example |
|---|---|---|
| `init <slug>` | Create `workspace/<slug>/SONG-SPEC.yaml`, `exports/`, `runs/` | `sudirector init midnight-neon --json` |
| `validate <file>` | Validate `song-spec`, `execution-plan`, or `diagnosis` against schema & rules | `sudirector validate examples/vocal-song/SONG-SPEC.yaml --json` |
| `render <spec>` | Compile validated `SONG-SPEC.yaml` into deterministic `exports/suno-pack.md` | `sudirector render examples/vocal-song/SONG-SPEC.yaml` |
| `preflight <spec>` | Run Execution Guard against `account-usage` YAML/JSON snapshot | `sudirector preflight examples/vocal-song/SONG-SPEC.yaml --account tests/fixtures/free-account.yaml --json` |
| `install-skill` | Install `suno-director` Global Skill to Codex, Antigravity, Claude Code | `sudirector install-skill --agents codex antigravity claude` |
| `update` | Check for updates or download, SHA256-verify, and run silent upgrade | `sudirector update --check --json` / `sudirector update --yes` |
| `version` | Print or compute SemVer 2.0.0 bumps, comparisons, and compatibility | `sudirector version --bump minor --json` |

> **Non-blocking Update Checks**: Normal commands refresh `%APPDATA%\SunoDirector\update-check.json` lazily in a detached background process (24h TTL) and write update notices strictly to `stderr` so `--json` `stdout` never breaks. Pass `--no-update-check` or set `SUDIRECTOR_NO_UPDATE_CHECK=1` to disable.

### Quick Example Workflow

```bash
# 1. Initialize a new song workspace anywhere on disk
sudirector init neon-last-train

# 2. Validate spec & anti-AI-tell heuristics
sudirector validate examples/vocal-song/SONG-SPEC.yaml

# 3. Export deterministic manual fallback pack
sudirector render examples/vocal-song/SONG-SPEC.yaml

# 4. Run Execution Guard preflight (blocked until explicitly approved under per_cycle)
sudirector preflight examples/vocal-song/SONG-SPEC.yaml --account tests/fixtures/free-account.yaml
sudirector preflight examples/vocal-song/SONG-SPEC.yaml --account tests/fixtures/free-account.yaml --approve --out execution-plan.yaml
```

---

## Global AI Skill Usage

Once installed, an agent running inside **any** directory activates `suno-director` without needing this repository open as its workspace:

1. Agent creates `./workspace/<song-slug>/SONG-SPEC.yaml` via `sudirector init`.
2. Agent populates composition, arrangement, lyrics/phonetics (skipped automatically if `vocal.enabled: false`), and Suno style fields respecting `references/ownership.md`.
3. Agent validates (`sudirector validate --json`) and compiles fallback (`sudirector render --json`).
4. Agent calls Official Suno MCP `account-usage` (0 credits) -> runs `sudirector preflight` -> asks user confirmation before calling `audio-create` / `audio-covers-create` / `audio-extensions-create` / `audio-edit`.
5. Agent audits generated takes via `audio-listen` / `audio-listen-wait` (0 credits), produces schema-validated `diagnosis.yaml`, and performs targeted revisions only on diagnosed `spec_path` entries.

If your MCP client has no Suno server connected, the skill automatically delivers `exports/suno-pack.md` for manual paste on `suno.com`.

---

## Architecture Overview

```text
User Brief
   │
   ▼
music-director (orchestrator & targeted spec revision)
   ├── composition-architect      (music.* & form[])
   ├── arrangement-architect      (arrangement.*, energy_curve, vocal section direction)
   ├── lyric-writer               (lyrics.text, rhyme, prosody QC)
   ├── pronunciation-specialist   (lyrics.pronunciation_overrides)
   └── suno-engineer              (generation.* & deterministic suno-pack.md)
   │
   ▼
SONG-SPEC.yaml ──► sudirector validate ──► sudirector render (offline fallback)
   │
   ▼
sudirector preflight (account-usage + runtime_overrides + budget/model gate)
   │
   ▼
Official Suno MCP (audio-create / cover / extend / edit / wait / retrieve / listen)
   │
   ▼
take-reviewer (diagnosis.yaml: SPEC_ERROR vs RENDER_ERROR + adherence map)
   └──► Targeted revision of diagnosed spec_path only ──► Regenerate / Accept
```

### Repository Structure

```text
├── src/music_director/        # Packaged Python core & `sudirector` CLI + SemVer logic
├── packaging/
│   ├── global-skill/          # Single self-contained `suno-director` Global Skill bundle
│   ├── sudirector.spec        # PyInstaller --onedir build definition
│   ├── installer.iss          # Inno Setup 6 per-user Windows installer script
│   ├── generate_icons.py      # Renders PNG, multi-size ICO, and Inno BMPs from SVG geometry
│   └── build_release.ps1      # End-to-end test + PyInstaller + Inno Setup release builder
├── assets/logos/              # V1-V8 SVG logo concepts, interactive showcase.html, Cyan Pulse icons
├── governance/                # OWNERSHIP.md, ROUTING.md, EXECUTION_POLICY.md, UPSTREAM_POLICY.md, ADOPTION.md
├── skills/                    # Repository-native 8 V1 specialist skills
├── schemas/                   # JSON Schemas (song-spec, execution-plan, diagnosis)
├── templates/                 # Canonical SONG-SPEC.yaml template
├── adapters/suno/             # Live capability normalization, runtime_overrides, tool routing
├── scripts/                   # Backward-compatible CLI shims & check_upstreams.py
├── examples/                  # Reference instrumental and vocal-song specs + exports
├── upstream/                  # Read-only pinned submodules (`bitwize`, `composition`)
└── tests/                     # Pytest suite (architecture, schemas, guard, SemVer, CLI)
```

---

## Configuration & Runtime Overrides

Bundled Suno adapter defaults live in `adapters/suno/capabilities.yaml`. When `account-usage` reports a capability that the live backend actually rejects (for example `Free` returning `403 feature_not_on_plan` for `exclude_styles` and `sliders`), `execution_guard` layers:

```text
Bundled capabilities.yaml ──► %APPDATA%\SunoDirector\runtime-overrides.yaml ──► Live account-usage ──► Effective mcp_payload
```

End users or agents can update runtime overrides without modifying installed binaries by writing `%APPDATA%\SunoDirector\runtime-overrides.yaml`:

```yaml
runtime_overrides:
  free:
    v6-mini:
      exclude_styles:
        effective: false
      sliders:
        effective: false
```

---

## Testing & Building from Source

Run the full automated test suite:

```bash
pytest -v
```

Build the standalone Windows `--onedir` bundle and Inno Setup installer (`dist/installer/SunoDirector-Setup-<version>.exe`):

```powershell
powershell -ExecutionPolicy Bypass -File packaging\build_release.ps1
```

---

## Versioning (SemVer 2.0.0)

`sudirector` follows **Semantic Versioning 2.0.0** (`MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]`):

- Single version source of truth: `src/music_director/version.py` (`VERSION = "0.2.0"`), verified by tests to match `pyproject.toml`.
- `0.x.y` releases allow minor feature/API iterations while maintaining strict schema validation and credit-guard invariants.
- Built-in CLI utilities:
  ```bash
  sudirector version --bump patch --json
  sudirector version --compare 0.1.0 0.2.0-rc.1 --json
  sudirector version --check 0.1.5 --json
  ```

---

## Troubleshooting

- **`sudirector` is not recognized right after running Windows Setup**: Already-open terminals or IDE windows cache their initial `PATH`. Either open a new terminal or invoke `%LOCALAPPDATA%\Programs\SunoDirector\sudirector.exe` directly.
- **Suno returns `403 feature_not_on_plan`**: Check `execution-plan.yaml` -> `omitted_controls` and verify `%APPDATA%\SunoDirector\runtime-overrides.yaml` / `adapters/suno/capabilities.yaml` marks unsupported controls for your plan/model as `effective: false`.
- **Download blocked by `sudirector preflight --operation download`**: Intentional V1 protection (`approved_download_credit_budget: 0`). Audition takes for free via `song_url` or `audio-listen` first, and only download after approving download credit spend.

---

## License & Third-Party Notices

Original framework code and documentation are released under the [MIT License](LICENSE). See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for upstream attributions (`bitwize-music-studio/claude-ai-music-skills`, `jtydhr88/music-composition-skills`) and `NOTICE` compliance boundaries.
