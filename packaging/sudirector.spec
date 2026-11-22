# PyInstaller --onedir spec for Suno Director (`sudirector`)

from pathlib import Path

ROOT = Path(SPECPATH).resolve().parent

datas = [
    (str(ROOT / "schemas"), "schemas"),
    (str(ROOT / "templates"), "templates"),
    (str(ROOT / "adapters"), "adapters"),
    (str(ROOT / "governance"), "governance"),
    (str(ROOT / "packaging" / "global-skill"), "packaging/global-skill"),
]

a = Analysis(
    [str(ROOT / "packaging" / "entry_cli.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=["yaml", "jsonschema"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "PIL", "tkinter"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="sudirector",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    icon=str(ROOT / "assets" / "logos" / "music-director.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="sudirector",
)
