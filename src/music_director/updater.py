"""Non-blocking update checker and self-updater for Suno Director (`sudirector`)."""

from __future__ import annotations

import hashlib
import json
import os
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .paths import detect_install_mode, is_frozen, update_cache_path, update_lock_path
from .version import VERSION, compare_semver, parse_semver

GITHUB_REPO = "codevcn/suno-director"
DEFAULT_TTL_SECONDS = 24 * 60 * 60
LOCK_EXPIRY_SECONDS = 60


class UpdateError(RuntimeError):
    """Raised when an explicit update check, download, or verification fails."""


@dataclass(frozen=True)
class ReleaseInfo:
    version: str
    tag_name: str
    release_url: str
    asset_name: str | None
    asset_url: str | None
    sha256: str | None
    prerelease: bool = False


def _ssl_context() -> ssl.SSLContext:
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def _default_urlopen(req: urllib.request.Request, timeout: float):
    return urllib.request.urlopen(req, timeout=timeout, context=_ssl_context())


def _fetch_json(url: str, *, timeout: float, urlopen_fn: Callable[..., Any]) -> Any:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"sudirector/{VERSION}",
        },
    )
    with urlopen_fn(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw)


def _extract_release_info(payload: dict[str, Any]) -> ReleaseInfo | None:
    tag = str(payload.get("tag_name") or "").strip()
    if not tag:
        return None
    try:
        parsed = parse_semver(tag)
    except ValueError:
        return None

    ver_str = str(parsed)
    expected_name = f"SunoDirector-Setup-{ver_str}.exe".lower()
    assets = payload.get("assets") or []

    chosen_asset: dict[str, Any] | None = None
    for asset in assets:
        name = str(asset.get("name") or "")
        if name.lower() == expected_name:
            chosen_asset = asset
            break
    if chosen_asset is None:
        for asset in assets:
            name = str(asset.get("name") or "")
            if name.lower().endswith(".exe"):
                chosen_asset = asset
                break

    sha256: str | None = None
    asset_name: str | None = None
    asset_url: str | None = None
    if chosen_asset:
        asset_name = str(chosen_asset.get("name") or "") or None
        asset_url = str(chosen_asset.get("browser_download_url") or "") or None
        digest = str(chosen_asset.get("digest") or "").strip()
        if digest.lower().startswith("sha256:"):
            sha256 = digest.split(":", 1)[1].strip().lower()

    return ReleaseInfo(
        version=ver_str,
        tag_name=tag,
        release_url=str(payload.get("html_url") or f"https://github.com/{GITHUB_REPO}/releases/tag/{tag}"),
        asset_name=asset_name,
        asset_url=asset_url,
        sha256=sha256,
        prerelease=bool(payload.get("prerelease") or parsed.is_prerelease),
    )


def fetch_latest_release(
    *,
    repo: str = GITHUB_REPO,
    include_prereleases: bool = False,
    timeout: float = 3.0,
    urlopen_fn: Callable[..., Any] | None = None,
) -> ReleaseInfo | None:
    """Query GitHub Releases for the latest SemVer release."""
    opener = urlopen_fn or _default_urlopen
    if not include_prereleases:
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        data = _fetch_json(url, timeout=timeout, urlopen_fn=opener)
        if not isinstance(data, dict):
            return None
        return _extract_release_info(data)

    url = f"https://api.github.com/repos/{repo}/releases?per_page=10"
    items = _fetch_json(url, timeout=timeout, urlopen_fn=opener)
    if not isinstance(items, list):
        return None

    candidates: list[ReleaseInfo] = []
    for item in items:
        if not isinstance(item, dict) or item.get("draft"):
            continue
        info = _extract_release_info(item)
        if info is not None:
            candidates.append(info)
    if not candidates:
        return None
    candidates.sort(key=lambda r: parse_semver(r.version), reverse=True)
    return candidates[0]


def read_update_cache(cache_path: Path | None = None) -> dict[str, Any] | None:
    path = cache_path or update_cache_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def write_update_cache(
    info: ReleaseInfo,
    *,
    cache_path: Path | None = None,
    now: float | None = None,
) -> dict[str, Any]:
    path = cache_path or update_cache_path()
    payload = {
        "checked_at": time.time() if now is None else float(now),
        "latest_version": info.version,
        "tag_name": info.tag_name,
        "release_url": info.release_url,
        "asset_name": info.asset_name,
        "asset_url": info.asset_url,
        "sha256": info.sha256,
        "prerelease": info.prerelease,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def is_cache_fresh(
    cache: dict[str, Any] | None,
    *,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
    now: float | None = None,
) -> bool:
    if not cache:
        return False
    checked_at = cache.get("checked_at")
    if not isinstance(checked_at, (int, float)):
        return False
    cur = time.time() if now is None else float(now)
    return (cur - float(checked_at)) < ttl_seconds


def _build_status_from_cache(current_version: str, cache: dict[str, Any], *, from_cache: bool) -> dict[str, Any]:
    latest = str(cache.get("latest_version") or current_version)
    try:
        available = compare_semver(latest, current_version) > 0
    except ValueError:
        available = False
    return {
        "current_version": current_version,
        "latest_version": latest,
        "tag_name": cache.get("tag_name") or f"v{latest}",
        "update_available": available,
        "from_cache": from_cache,
        "release_url": cache.get("release_url"),
        "asset_name": cache.get("asset_name"),
        "asset_url": cache.get("asset_url"),
        "sha256": cache.get("sha256"),
        "install_mode": detect_install_mode(),
    }


def check_for_update(
    *,
    current_version: str = VERSION,
    cache_path: Path | None = None,
    force_refresh: bool = False,
    include_prereleases: bool = False,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
    now: float | None = None,
    urlopen_fn: Callable[..., Any] | None = None,
    timeout: float = 3.0,
) -> dict[str, Any]:
    """Check cached or live GitHub release status with strict SemVer comparison."""
    path = cache_path or update_cache_path()
    cache = read_update_cache(path)
    if not force_refresh and is_cache_fresh(cache, ttl_seconds=ttl_seconds, now=now):
        assert cache is not None
        return _build_status_from_cache(current_version, cache, from_cache=True)

    info = fetch_latest_release(
        include_prereleases=include_prereleases,
        timeout=timeout,
        urlopen_fn=urlopen_fn,
    )
    if info is None:
        if cache is not None:
            return _build_status_from_cache(current_version, cache, from_cache=True)
        return {
            "current_version": current_version,
            "latest_version": current_version,
            "tag_name": f"v{current_version}",
            "update_available": False,
            "from_cache": False,
            "release_url": None,
            "asset_name": None,
            "asset_url": None,
            "sha256": None,
            "install_mode": detect_install_mode(),
        }

    saved = write_update_cache(info, cache_path=path, now=now)
    return _build_status_from_cache(current_version, saved, from_cache=False)


def _detached_popen_kwargs() -> dict[str, Any]:
    if os.name != "nt":
        return {"start_new_session": True}
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return {"creationflags": flags, "close_fds": True}


def spawn_background_cache_refresh(
    *,
    lock_path: Path | None = None,
    now: float | None = None,
) -> bool:
    """Spawn detached background child process to refresh update cache without delaying CLI."""
    lock = lock_path or update_lock_path()
    cur = time.time() if now is None else float(now)
    try:
        if lock.exists() and (cur - lock.stat().st_mtime) < LOCK_EXPIRY_SECONDS:
            return False
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text(str(os.getpid()), encoding="utf-8")
    except OSError:
        return False

    cmd = (
        [sys.executable, "update", "--refresh-cache"]
        if is_frozen()
        else [sys.executable, "-m", "music_director", "update", "--refresh-cache"]
    )
    env = os.environ.copy()
    env["SUDIRECTOR_NO_UPDATE_CHECK"] = "1"
    try:
        subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
            **_detached_popen_kwargs(),
        )
        return True
    except OSError:
        return False


def refresh_cache_silently(
    *,
    cache_path: Path | None = None,
    lock_path: Path | None = None,
    urlopen_fn: Callable[..., Any] | None = None,
) -> bool:
    """Worker routine executed by detached `--refresh-cache` process; never raises."""
    lock = lock_path or update_lock_path()
    try:
        info = fetch_latest_release(timeout=3.0, urlopen_fn=urlopen_fn)
        if info is not None:
            write_update_cache(info, cache_path=cache_path)
            return True
        return False
    except Exception:
        return False
    finally:
        try:
            if lock.exists():
                lock.unlink()
        except OSError:
            pass


def maybe_notify_update(
    *,
    current_version: str = VERSION,
    cache_path: Path | None = None,
    lock_path: Path | None = None,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
    now: float | None = None,
    spawner: Callable[[], bool] | None = None,
    err_stream: Any = None,
) -> bool:
    """Passive non-blocking update check run after a main CLI command completes.

    Prints notice strictly to `stderr` so `--json` `stdout` stays valid JSON.
    """
    stream = sys.stderr if err_stream is None else err_stream
    if os.environ.get("SUDIRECTOR_NO_UPDATE_CHECK") == "1":
        return False

    cache = read_update_cache(cache_path)
    if not is_cache_fresh(cache, ttl_seconds=ttl_seconds, now=now):
        refresh_fn = spawner or (lambda: spawn_background_cache_refresh(lock_path=lock_path, now=now))
        try:
            refresh_fn()
        except Exception:
            pass

    if not cache:
        return False

    latest = str(cache.get("latest_version") or "")
    if not latest:
        return False
    try:
        if compare_semver(latest, current_version) > 0:
            print(
                f"[sudirector] Update available: v{current_version} -> v{latest} (run `sudirector update` to upgrade)",
                file=stream,
            )
            return True
    except ValueError:
        return False
    return False


def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().lower()


def verify_file_sha256(file_path: Path, expected_sha256: str) -> bool:
    actual = compute_sha256(file_path)
    return actual == expected_sha256.strip().lower()


def download_installer(
    url: str,
    dest_path: Path,
    *,
    expected_sha256: str | None = None,
    allow_unverified: bool = False,
    timeout: float = 60.0,
    urlopen_fn: Callable[..., Any] | None = None,
) -> Path:
    """Download installer atomically over HTTPS and enforce SHA256 verification."""
    if not url.startswith("https://"):
        raise UpdateError(f"Refusing non-HTTPS installer URL: {url}")
    if not expected_sha256 and not allow_unverified:
        raise UpdateError("Release asset has no SHA256 digest; refusing unverified binary download.")

    opener = urlopen_fn or _default_urlopen
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    part_path = dest_path.with_suffix(dest_path.suffix + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": f"sudirector/{VERSION}"})

    try:
        with opener(req, timeout=timeout) as resp, part_path.open("wb") as out:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                out.write(chunk)
    except (urllib.error.URLError, OSError) as exc:
        if part_path.exists():
            part_path.unlink(missing_ok=True)
        raise UpdateError(f"Failed to download installer: {exc}") from exc

    if expected_sha256 and not verify_file_sha256(part_path, expected_sha256):
        actual = compute_sha256(part_path)
        part_path.unlink(missing_ok=True)
        raise UpdateError(f"SHA256 mismatch for downloaded installer (expected {expected_sha256}, got {actual}).")

    if dest_path.exists():
        dest_path.unlink()
    part_path.replace(dest_path)
    return dest_path


def launch_windows_installer(installer_path: Path, *, wait_pid: int | None = None) -> None:
    """Spawn silent Inno Setup updater after waiting for current executable PID to exit."""
    pid = os.getpid() if wait_pid is None else int(wait_pid)
    helper_dir = installer_path.parent
    ps_script = helper_dir / "run-updater.ps1"
    ps_script.write_text(
        f"$ErrorActionPreference = 'SilentlyContinue'\n"
        f"Wait-Process -Id {pid} -Timeout 10\n"
        f"Start-Process -FilePath '{str(installer_path).replace(chr(39), chr(39)*2)}' "
        f"-ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/CLOSEAPPLICATIONS'\n",
        encoding="utf-8",
    )
    subprocess.Popen(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps_script)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **_detached_popen_kwargs(),
    )


def perform_update(
    *,
    current_version: str = VERSION,
    force: bool = False,
    include_prereleases: bool = False,
    no_launch: bool = False,
    cache_path: Path | None = None,
    urlopen_fn: Callable[..., Any] | None = None,
    install_mode_override: str | None = None,
) -> dict[str, Any]:
    """Execute explicit `sudirector update` workflow according to runtime install mode."""
    try:
        status = check_for_update(
            current_version=current_version,
            cache_path=cache_path,
            force_refresh=True,
            include_prereleases=include_prereleases,
            urlopen_fn=urlopen_fn,
            timeout=8.0,
        )
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        raise UpdateError(f"Failed to check GitHub Releases: {exc}") from exc

    mode = install_mode_override or status["install_mode"]
    latest = status["latest_version"]

    if not status["update_available"] and not force:
        return {
            "status": "up_to_date",
            "install_mode": mode,
            "current_version": current_version,
            "latest_version": latest,
        }

    if mode == "source":
        return {
            "status": "source_checkout",
            "install_mode": mode,
            "current_version": current_version,
            "latest_version": latest,
            "release_url": status["release_url"],
            "hint": "Running from git source checkout. Run `git pull && python -m pip install -e .[dev]` to update.",
        }

    if mode == "pip":
        if no_launch:
            return {
                "status": "ready_pip",
                "install_mode": mode,
                "current_version": current_version,
                "latest_version": latest,
                "command": f"python -m pip install --upgrade git+https://github.com/{GITHUB_REPO}.git@{status['tag_name']}",
            }
        proc = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", f"git+https://github.com/{GITHUB_REPO}.git@{status['tag_name']}"],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise UpdateError(f"pip upgrade failed: {proc.stderr.strip() or proc.stdout.strip()}")
        return {
            "status": "updated_pip",
            "install_mode": mode,
            "current_version": current_version,
            "latest_version": latest,
        }

    # mode == "installer" (Windows frozen --onedir installed via Inno Setup)
    asset_url = status.get("asset_url")
    asset_name = status.get("asset_name") or f"SunoDirector-Setup-{latest}.exe"
    if not asset_url:
        raise UpdateError(f"Release {status['tag_name']} does not contain a Windows installer asset.")

    dest_dir = Path(tempfile.gettempdir()) / "SunoDirectorUpdate"
    dest_path = download_installer(
        asset_url,
        dest_dir / asset_name,
        expected_sha256=status.get("sha256"),
        urlopen_fn=urlopen_fn,
    )

    if not no_launch:
        launch_windows_installer(dest_path)

    return {
        "status": "ready_installer" if no_launch else "launching_installer",
        "install_mode": mode,
        "current_version": current_version,
        "latest_version": latest,
        "installer_path": str(dest_path),
        "sha256": status.get("sha256"),
    }
