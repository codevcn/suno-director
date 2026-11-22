"""Compatibility shim forwarding to music_director.render_suno_pack."""

from __future__ import annotations

import sys
from pathlib import Path

_SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from music_director.render_suno_pack import (  # noqa: E402,F401
    default_output_path,
    main,
    render_suno_pack,
)

if __name__ == "__main__":
    raise SystemExit(main())
