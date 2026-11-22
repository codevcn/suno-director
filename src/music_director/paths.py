"""Resource and user-state path resolution for both source repo and frozen Windows builds."""

from __future__ import annotations

import os
import sys
from pathlib import Path

SKILL_DIR_NAME = "suno-director"


def is_frozen() -> bool:
    """Return True when running inside a PyInstaller bundle."""
    return bool(getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"))


def bundle_root() -> Path:
    """Return root directory holding bundled read-only assets (schemas, templates, adapters)."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS"))
    candidate = Path(__file__).resolve().parent.parent.parent
    if (candidate / "schemas").is_dir() and (candidate / "templates").is_dir():
        return candidate
    return Path(__file__).resolve().parent


def schemas_dir() -> Path:
    return bundle_root() / "schemas"


def templates_dir() -> Path:
    return bundle_root() / "templates"


def adapters_suno_dir() -> Path:
    return bundle_root() / "adapters" / "suno"


def global_skill_source_dir() -> Path:
    return bundle_root() / "packaging" / "global-skill" / SKILL_DIR_NAME


def user_config_dir() -> Path:
    """Return writable user configuration directory outside installation root."""
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA") or (Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config"))
    return base / "SunoDirector"


def user_runtime_overrides_path() -> Path:
    return user_config_dir() / "runtime-overrides.yaml"


def default_skill_targets(home: Path | None = None) -> dict[str, Path]:
    """Return supported global AI agent skill directories (Codex, Antigravity, Claude Code)."""
    root = home or Path.home()
    return {
        "codex": root / ".codex" / "skills" / SKILL_DIR_NAME,
        "antigravity": root / ".gemini" / "config" / "skills" / SKILL_DIR_NAME,
        "claude": root / ".claude" / "skills" / SKILL_DIR_NAME,
    }
