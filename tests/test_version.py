"""Tests for SemVer 2.0.0 parsing, precedence, bumps, compatibility, and manifest sync."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from music_director.version import (
    VERSION,
    bump_semver,
    compare_semver,
    format_version_info,
    parse_semver,
)


def test_pyproject_version_matches_package_version() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["version"] == VERSION
    assert VERSION == "0.1.0"


def test_semver_parsing_and_validation() -> None:
    v = parse_semver("v1.2.3-alpha.1+build.45")
    assert (v.major, v.minor, v.patch) == (1, 2, 3)
    assert v.prerelease == ("alpha", 1)
    assert v.build == ("build", "45")
    assert v.is_prerelease is True

    for bad in ("01.0.0", "1.2", "1.2.3.4", "1.2.x", ""):
        with pytest.raises(ValueError):
            parse_semver(bad)


def test_semver_precedence_rules() -> None:
    ordered = [
        "1.0.0-alpha",
        "1.0.0-alpha.1",
        "1.0.0-alpha.beta",
        "1.0.0-beta",
        "1.0.0-beta.2",
        "1.0.0-beta.11",
        "1.0.0-rc.1",
        "1.0.0",
        "1.0.1",
        "1.1.0",
        "2.0.0",
    ]
    for low, high in zip(ordered, ordered[1:]):
        assert compare_semver(low, high) == -1
        assert compare_semver(high, low) == 1
    assert compare_semver("0.1.0+build.1", "0.1.0+build.2") == 0


def test_semver_bump_and_compatibility() -> None:
    assert bump_semver("0.1.0", "patch") == "0.1.1"
    assert bump_semver("0.1.0", "minor") == "0.2.0"
    assert bump_semver("0.1.0", "major") == "1.0.0"
    assert bump_semver("0.1.0", "minor", prerelease="rc.1") == "0.2.0-rc.1"

    assert parse_semver("0.1.0").is_compatible_with(parse_semver("0.1.9")) is True
    assert parse_semver("0.1.0").is_compatible_with(parse_semver("0.2.0")) is False
    assert parse_semver("1.0.0").is_compatible_with(parse_semver("1.5.2")) is True
    assert parse_semver("1.0.0").is_compatible_with(parse_semver("2.0.0")) is False

    info = format_version_info()
    assert info["version"] == "0.1.0"
    assert info["tag"] == "v0.1.0"
