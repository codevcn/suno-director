"""Validate SONG-SPEC, diagnosis, and execution-plan YAML files."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from _common import load_schema, load_yaml

HOLLOW_ADJECTIVES = {"epic", "beautiful", "amazing", "masterpiece", "perfect"}
TAG_ONLY_LINE_RE = re.compile(r"^\s*\[[^\]]+\]\s*$")


def validate_against_schema(data: Any, schema_name: str) -> list[str]:
    """Return a list of schema validation error messages."""
    schema = load_schema(schema_name)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    messages: list[str] = []
    for err in errors:
        loc = ".".join(str(p) for p in err.path) or "<root>"
        messages.append(f"Schema error at '{loc}': {err.message}")
    return messages


def _has_sung_lyrics(text: str) -> bool:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if TAG_ONLY_LINE_RE.match(stripped):
            continue
        return True
    return False


def validate_song_spec(spec: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Validate SONG-SPEC against schema and semantic rules.

    Returns (errors, warnings).
    """
    if not isinstance(spec, dict):
        return (["SONG-SPEC root must be a YAML mapping."], [])

    errors = validate_against_schema(spec, "song-spec.schema.json")
    warnings: list[str] = []
    if errors:
        return (errors, warnings)

    # 1. Source requirements by generation intent
    gen = spec["generation"]
    intent = gen["intent"]
    source = gen["source"]
    audio_id = source.get("audio_id")
    continue_at = source.get("continue_at")

    if intent in {"cover", "extend", "edit"} and (not isinstance(audio_id, str) or not audio_id.strip()):
        errors.append(f"generation.intent '{intent}' requires a non-empty generation.source.audio_id.")

    if intent == "extend" and continue_at is None:
        errors.append("generation.intent 'extend' requires generation.source.continue_at (seconds).")

    # 2. Vocal vs Lyrics consistency
    vocal_enabled = spec["vocal"]["enabled"]
    lyrics_text = spec["lyrics"]["text"]
    has_sung = _has_sung_lyrics(lyrics_text)

    if vocal_enabled and intent != "edit" and not has_sung:
        errors.append("vocal.enabled is true, so lyrics.text must contain sung lyric lines (not empty or tags-only).")

    if not vocal_enabled and has_sung:
        errors.append("vocal.enabled is false (instrumental), so lyrics.text must not contain sung lines (use section tags only or empty string).")

    # 3. Form & Energy Curve consistency
    form_items = spec["form"]
    form_ids = [item["id"] for item in form_items]
    if len(set(form_ids)) != len(form_ids):
        errors.append("form[].id values must be unique.")

    curve = spec["arrangement"]["energy_curve"]
    curve_ids = [item["section"] for item in curve]
    if curve_ids != form_ids:
        errors.append(
            f"arrangement.energy_curve section order/IDs {curve_ids} must match form[].id {form_ids}."
        )

    # 4. Advisory / Anti-AI-Tell checks
    if len(form_items) >= 3 and all(item["bars"] % 8 == 0 for item in form_items):
        warnings.append("All form sections are multiples of 8 bars; consider asymmetric phrasing to avoid robotic structure.")

    if len(curve) >= 3:
        energies = [item["energy"] for item in curve]
        if all(b >= a for a, b in zip(energies, energies[1:])):
            warnings.append("arrangement.energy_curve is monotonically non-decreasing; consider adding a drop or subtraction before the peak.")

    style_words = {w.strip(".,;:!?\"'").lower() for w in gen["style_prompt"].split()}
    hollow_found = sorted(style_words & HOLLOW_ADJECTIVES)
    if hollow_found:
        warnings.append(
            f"generation.style_prompt contains hollow adjectives {hollow_found}; replace with concrete sonic/instrumental terms."
        )

    return (errors, warnings)


def validate_diagnosis(data: dict[str, Any]) -> list[str]:
    """Validate a diagnosis.yaml payload against schemas/diagnosis.schema.json."""
    return validate_against_schema(data, "diagnosis.schema.json")


def validate_execution_plan(data: dict[str, Any]) -> list[str]:
    """Validate an execution-plan.yaml payload against schemas/execution-plan.schema.json."""
    return validate_against_schema(data, "execution-plan.schema.json")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a SONG-SPEC.yaml (or diagnosis/execution-plan) file.")
    parser.add_argument("spec_path", type=Path, help="Path to YAML file to validate.")
    parser.add_argument(
        "--kind",
        choices=["song-spec", "diagnosis", "execution-plan"],
        default="song-spec",
        help="Schema kind to validate against (default: song-spec).",
    )
    parser.add_argument("--strict", action="store_true", help="Treat advisory warnings as errors.")
    args = parser.parse_args(argv)

    if not args.spec_path.exists():
        print(f"ERROR: File not found: {args.spec_path}", file=sys.stderr)
        return 2

    data = load_yaml(args.spec_path)
    if args.kind == "diagnosis":
        errs = validate_diagnosis(data)
        warns: list[str] = []
    elif args.kind == "execution-plan":
        errs = validate_execution_plan(data)
        warns = []
    else:
        errs, warns = validate_song_spec(data)

    for w in warns:
        print(f"WARN: {w}")
    for e in errs:
        print(f"ERROR: {e}", file=sys.stderr)

    if errs or (args.strict and warns):
        print(f"INVALID ({len(errs)} error(s), {len(warns)} warning(s)): {args.spec_path}")
        return 1

    print(f"VALID ({len(warns)} warning(s)): {args.spec_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
