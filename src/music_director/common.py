"""YAML/JSON loaders and config merging for Music Director."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import yaml

from .paths import adapters_suno_dir, bundle_root, schemas_dir, user_runtime_overrides_path

REPO_ROOT = bundle_root()
SCHEMAS_DIR = schemas_dir()
ADAPTERS_SUNO_DIR = adapters_suno_dir()


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
    schema_path = schemas_dir() / name
    with schema_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for k, v in patch.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k] = _deep_merge(merged[k], v)
        else:
            merged[k] = copy.deepcopy(v)
    return merged


def load_capabilities_config(user_override_path: Path | None = None) -> dict[str, Any]:
    """Load bundled Suno capabilities.yaml merged with optional user runtime overrides."""
    caps = load_yaml(adapters_suno_dir() / "capabilities.yaml")
    override_file = user_override_path or user_runtime_overrides_path()
    if override_file.exists():
        user_data = load_yaml(override_file)
        if isinstance(user_data, dict):
            extra_overrides = user_data.get("runtime_overrides", user_data)
            if isinstance(extra_overrides, dict):
                existing = caps.get("runtime_overrides") or {}
                caps["runtime_overrides"] = _deep_merge(existing, extra_overrides)
    return caps
