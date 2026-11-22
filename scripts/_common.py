"""Shared helpers for Music Director scripts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = REPO_ROOT / "schemas"
ADAPTERS_SUNO_DIR = REPO_ROOT / "adapters" / "suno"


def load_yaml(path: Path) -> Any:
    """Load a YAML file using safe_load."""
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def dump_yaml(data: Any, path: Path) -> None:
    """Write data cleanly as UTF-8 YAML."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)


def load_schema(name: str) -> dict[str, Any]:
    """Load a JSON schema from schemas/<name>."""
    schema_path = SCHEMAS_DIR / name
    with schema_path.open("r", encoding="utf-8") as f:
        return json.load(f)
