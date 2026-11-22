"""Tests for non-blocking update check, TTL cache, SemVer checks, --json purity, and SHA256 verification."""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
from typing import Any

import pytest

from music_director.cli import main as cli_main
from music_director.updater import (
    UpdateError,
    check_for_update,
    download_installer,
    is_cache_fresh,
    maybe_notify_update,
    perform_update,
)
from music_director.version import VERSION


class _FakeResponse:
    def __init__(self, body: bytes) -> None:
        self._stream = io.BytesIO(body)

    def read(self, size: int = -1) -> bytes:
        return self._stream.read(size)

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None


def _make_release_opener(release_payload: dict[str, Any] | list[dict[str, Any]], binary_bytes: bytes = b"installer-bytes"):
    calls: list[str] = []

    def _opener(req, timeout=3.0):
        url = req.full_url
        calls.append(url)
        if url.endswith(".exe"):
            return _FakeResponse(binary_bytes)
        return _FakeResponse(json.dumps(release_payload).encode("utf-8"))

    return _opener, calls


def test_semver_update_comparison_with_mock_github_api(tmp_path: Path) -> None:
    cache_file = tmp_path / "update-check.json"
    opener_newer, _ = _make_release_opener(
        {
            "tag_name": "v0.10.0",
            "html_url": "https://github.com/codevcn/suno-director/releases/tag/v0.10.0",
            "assets": [
                {
                    "name": "SunoDirector-Setup-0.10.0.exe",
                    "browser_download_url": "https://github.com/codevcn/suno-director/releases/download/v0.10.0/SunoDirector-Setup-0.10.0.exe",
                    "digest": "sha256:" + ("a" * 64),
                }
            ],
        }
    )
    status = check_for_update(current_version="0.2.0", cache_path=cache_file, force_refresh=True, urlopen_fn=opener_newer)
    assert status["update_available"] is True
    assert status["latest_version"] == "0.10.0"

    opener_same, _ = _make_release_opener({"tag_name": "v0.2.0", "assets": []})
    status_same = check_for_update(current_version="0.2.0", cache_path=cache_file, force_refresh=True, urlopen_fn=opener_same)
    assert status_same["update_available"] is False


def test_ttl_cache_avoids_redundant_network_and_refreshes_when_expired(tmp_path: Path) -> None:
    cache_file = tmp_path / "update-check.json"
    opener, calls = _make_release_opener({"tag_name": "v0.3.0", "assets": []})

    first = check_for_update(current_version="0.2.0", cache_path=cache_file, now=1000.0, urlopen_fn=opener)
    assert first["from_cache"] is False
    assert len(calls) == 1

    # Within 24h TTL -> should read from cache with zero network requests
    second = check_for_update(current_version="0.2.0", cache_path=cache_file, now=2000.0, ttl_seconds=86400, urlopen_fn=opener)
    assert second["from_cache"] is True
    assert len(calls) == 1

    # Past TTL -> refreshes from GitHub API
    third = check_for_update(current_version="0.2.0", cache_path=cache_file, now=100000.0, ttl_seconds=86400, urlopen_fn=opener)
    assert third["from_cache"] is False
    assert len(calls) == 2

    # Corrupted cache safely degrades to stale
    cache_file.write_text("{broken json", encoding="utf-8")
    assert is_cache_fresh(None) is False


def test_non_blocking_notify_triggers_background_refresh_and_writes_stderr_only(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.delenv("SUDIRECTOR_NO_UPDATE_CHECK", raising=False)
    cache_file = tmp_path / "update-check.json"
    cache_file.write_text(
        json.dumps({"checked_at": 100.0, "latest_version": "9.9.9"}),
        encoding="utf-8",
    )
    spawned: list[bool] = []
    # Stale timestamp -> spawns background refresh while emitting cached notification to stderr
    notified = maybe_notify_update(
        current_version="0.2.0",
        cache_path=cache_file,
        ttl_seconds=3600,
        now=99999.0,
        spawner=lambda: spawned.append(True) or True,
    )
    assert notified is True
    assert spawned == [True]
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Update available: v0.2.0 -> v9.9.9" in captured.err


def test_json_stdout_never_corrupted_by_update_notice(tmp_path: Path, monkeypatch, capsys) -> None:
    cache_file = tmp_path / "update-check.json"
    cache_file.write_text(
        json.dumps({"checked_at": 9999999999.0, "latest_version": "9.9.9"}),
        encoding="utf-8",
    )
    monkeypatch.delenv("SUDIRECTOR_NO_UPDATE_CHECK", raising=False)
    monkeypatch.setattr("music_director.updater.update_cache_path", lambda: cache_file)

    repo_root = Path(__file__).resolve().parent.parent
    vocal_spec = repo_root / "examples" / "vocal-song" / "SONG-SPEC.yaml"
    rc = cli_main(["validate", str(vocal_spec), "--json"])
    assert rc == 0
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)  # Must parse cleanly as strict JSON
    assert parsed["valid"] is True
    assert f"Update available: v{VERSION} -> v9.9.9" in captured.err

    # --no-update-check suppresses stderr notice completely
    rc2 = cli_main(["validate", str(vocal_spec), "--json", "--no-update-check"])
    assert rc2 == 0
    captured2 = capsys.readouterr()
    assert json.loads(captured2.out)["valid"] is True
    assert captured2.err == ""


def test_sha256_verification_accepts_valid_and_rejects_corrupt_installer(tmp_path: Path) -> None:
    payload = b"MZ-simulated-inno-setup-binary"
    good_sha = hashlib.sha256(payload).hexdigest()
    opener, _ = _make_release_opener({}, binary_bytes=payload)

    dest = tmp_path / "SunoDirector-Setup-0.3.0.exe"
    downloaded = download_installer(
        "https://github.com/codevcn/suno-director/releases/download/v0.3.0/SunoDirector-Setup-0.3.0.exe",
        dest,
        expected_sha256=good_sha,
        urlopen_fn=opener,
    )
    assert downloaded.exists()
    assert downloaded.read_bytes() == payload

    bad_dest = tmp_path / "bad.exe"
    with pytest.raises(UpdateError, match="SHA256 mismatch"):
        download_installer(
            "https://github.com/codevcn/suno-director/releases/download/v0.3.0/SunoDirector-Setup-0.3.0.exe",
            bad_dest,
            expected_sha256="0" * 64,
            urlopen_fn=opener,
        )
    assert not bad_dest.exists()
    assert not bad_dest.with_suffix(".exe.part").exists()

    with pytest.raises(UpdateError, match="no SHA256 digest"):
        download_installer(
            "https://github.com/codevcn/suno-director/releases/download/v0.3.0/SunoDirector-Setup-0.3.0.exe",
            bad_dest,
            expected_sha256=None,
            urlopen_fn=opener,
        )


def test_perform_update_handles_source_and_installer_modes(tmp_path: Path, monkeypatch) -> None:
    binary = b"setup-payload-0.3.0"
    sha = hashlib.sha256(binary).hexdigest()
    opener, _ = _make_release_opener(
        {
            "tag_name": "v0.3.0",
            "html_url": "https://github.com/codevcn/suno-director/releases/tag/v0.3.0",
            "assets": [
                {
                    "name": "SunoDirector-Setup-0.3.0.exe",
                    "browser_download_url": "https://github.com/codevcn/suno-director/releases/download/v0.3.0/SunoDirector-Setup-0.3.0.exe",
                    "digest": f"sha256:{sha}",
                }
            ],
        },
        binary_bytes=binary,
    )
    cache_file = tmp_path / "cache.json"

    src_res = perform_update(
        current_version="0.2.0",
        cache_path=cache_file,
        urlopen_fn=opener,
        install_mode_override="source",
    )
    assert src_res["status"] == "source_checkout"

    monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))
    inst_res = perform_update(
        current_version="0.2.0",
        no_launch=True,
        cache_path=cache_file,
        urlopen_fn=opener,
        install_mode_override="installer",
    )
    assert inst_res["status"] == "ready_installer"
    assert Path(inst_res["installer_path"]).read_bytes() == binary
