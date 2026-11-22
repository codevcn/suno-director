"""Compatibility shim forwarding to music_director.execution_guard."""

from __future__ import annotations

import sys
from pathlib import Path

_SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from music_director.execution_guard import (  # noqa: E402,F401
    DEFAULT_MODEL_PRIORITY,
    KNOWN_MCP_CONTROLS,
    build_sanitized_mcp_payload,
    evaluate_execution_plan,
    main,
    normalize_capability_snapshot,
    resolve_effective_capabilities,
)

if __name__ == "__main__":
    raise SystemExit(main())
