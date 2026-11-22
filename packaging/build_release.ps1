# Reproducible release build: pytest -> icon generation -> PyInstaller onedir -> Inno Setup
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $RepoRoot

$Version = python -c "import sys; sys.path.insert(0, 'src'); from music_director.version import VERSION; print(VERSION)"
if ($LASTEXITCODE -ne 0) { throw "Failed to read SemVer VERSION." }
Write-Host "Building Suno Director (sudirector) v$Version..."

pytest -v
if ($LASTEXITCODE -ne 0) { throw "Pytest suite failed." }

python packaging/generate_icons.py
if ($LASTEXITCODE -ne 0) { throw "Icon generation failed." }

if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

pyinstaller --noconfirm packaging/sudirector.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller onedir build failed." }

# Smoke-test built standalone executable
& "dist\sudirector\sudirector.exe" --version
if ($LASTEXITCODE -ne 0) { throw "sudirector.exe smoke test failed." }

$Iscc = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $Iscc) { throw "Inno Setup 6 ISCC.exe not found." }

& $Iscc "/DMyAppVersion=$Version" "packaging\installer.iss"
if ($LASTEXITCODE -ne 0) { throw "Inno Setup compilation failed." }

$Installer = Join-Path $RepoRoot "dist\installer\SunoDirector-Setup-$Version.exe"
if (-not (Test-Path $Installer)) { throw "Expected installer not found at $Installer" }

Write-Host "SUCCESS: Built $Installer"
Get-FileHash $Installer -Algorithm SHA256 | Format-List
