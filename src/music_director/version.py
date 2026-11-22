"""Semantic Versioning 2.0.0 implementation and single version source of truth."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

VERSION = "0.2.0"

_SEMVER_RE = re.compile(
    r"^(?P<major>0|[1-9]\d*)\."
    r"(?P<minor>0|[1-9]\d*)\."
    r"(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+(?P<build>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)


def _parse_prerelease(raw: str | None) -> tuple[int | str, ...]:
    if not raw:
        return ()
    parts: list[int | str] = []
    for item in raw.split("."):
        parts.append(int(item) if item.isdigit() else item)
    return tuple(parts)


@dataclass(frozen=True)
class SemVer:
    """SemVer 2.0.0 version representation with strict precedence comparison."""

    major: int
    minor: int
    patch: int
    prerelease: tuple[int | str, ...] = ()
    build: tuple[str, ...] = ()

    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            base += "-" + ".".join(str(p) for p in self.prerelease)
        if self.build:
            base += "+" + ".".join(self.build)
        return base

    @property
    def tag(self) -> str:
        return f"v{self}"

    @property
    def is_prerelease(self) -> bool:
        return bool(self.prerelease)

    def _precedence_key(self) -> tuple[int, int, int, int, tuple[tuple[int, int | str], ...]]:
        # Normal versions rank higher (1) than prerelease versions (0).
        rank = 0 if self.prerelease else 1
        # Numeric identifiers have lower precedence (0) than non-numeric (1).
        pre_key = tuple((0, p) if isinstance(p, int) else (1, p) for p in self.prerelease)
        return (self.major, self.minor, self.patch, rank, pre_key)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        return self._precedence_key() == other._precedence_key()

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        return self._precedence_key() < other._precedence_key()

    def __le__(self, other: object) -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        return self._precedence_key() <= other._precedence_key()

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        return self._precedence_key() > other._precedence_key()

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        return self._precedence_key() >= other._precedence_key()

    def bump(self, part: Literal["major", "minor", "patch"], prerelease: str | None = None) -> "SemVer":
        pre = _parse_prerelease(prerelease)
        if part == "major":
            return SemVer(self.major + 1, 0, 0, pre)
        if part == "minor":
            return SemVer(self.major, self.minor + 1, 0, pre)
        if part == "patch":
            return SemVer(self.major, self.minor, self.patch + 1, pre)
        raise ValueError(f"Unsupported bump target: '{part}'.")

    def is_compatible_with(self, target: "SemVer") -> bool:
        """SemVer compatibility check: 0.x breaks on minor bumps; >=1.0 breaks on major bumps."""
        if self.major == 0 or target.major == 0:
            return self.major == target.major and self.minor == target.minor
        return self.major == target.major


def parse_semver(raw: str) -> SemVer:
    """Parse a SemVer 2.0.0 string (accepting an optional leading 'v')."""
    cleaned = raw.strip()
    if cleaned.startswith("v") and len(cleaned) > 1 and cleaned[1].isdigit():
        cleaned = cleaned[1:]
    match = _SEMVER_RE.match(cleaned)
    if not match:
        raise ValueError(f"Invalid SemVer 2.0.0 string: '{raw}'")
    build_raw = match.group("build")
    return SemVer(
        major=int(match.group("major")),
        minor=int(match.group("minor")),
        patch=int(match.group("patch")),
        prerelease=_parse_prerelease(match.group("prerelease")),
        build=tuple(build_raw.split(".")) if build_raw else (),
    )


def compare_semver(left: str, right: str) -> int:
    """Compare two SemVer strings returning -1, 0, or 1 per SemVer 2.0.0 precedence."""
    a, b = parse_semver(left), parse_semver(right)
    return -1 if a < b else (1 if a > b else 0)


def bump_semver(raw: str, part: Literal["major", "minor", "patch"], prerelease: str | None = None) -> str:
    """Return incremented SemVer string."""
    return str(parse_semver(raw).bump(part, prerelease=prerelease))


def format_version_info() -> dict[str, object]:
    """Return structured version metadata for CLI `--json` and audit logs."""
    v = parse_semver(VERSION)
    return {
        "version": str(v),
        "tag": v.tag,
        "major": v.major,
        "minor": v.minor,
        "patch": v.patch,
        "is_prerelease": v.is_prerelease,
    }
