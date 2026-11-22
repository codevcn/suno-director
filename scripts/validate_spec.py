"""Compatibility shim forwarding to music_director.validate_spec."""

from __future__ import annotations

import sys
from pathlib import Path

_SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from music_director.validate_spec import (  # noqa: E402,F401
    HOLLOW_ADJECTIVES,
    TAG_ONLY_LINE_RE,
    main,
    validate_against_schema,
    validate_diagnosis,
    validate_execution_plan,
    validate_file,
    validate_song_spec,
)

if __name__ == "__main__":
    raise SystemExit(main())
