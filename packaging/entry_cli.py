"""PyInstaller clean entry shim for sudirector."""

from music_director.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
