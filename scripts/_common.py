"""Compatibility shim re-exporting helpers from music_director.common."""

from __future__ import annotations

import sys
from pathlib import Path

_SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from music_director.common import (  # noqa: E402,F401
    ADAPTERS_SUNO_DIR,
    REPO_ROOT,
    SCHEMAS_DIR,
    dump_yaml,
    load_capabilities_config,
    load_schema,
    load_yaml,
)
