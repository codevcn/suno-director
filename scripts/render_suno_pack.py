"""Deterministic compiler from SONG-SPEC.yaml to exports/suno-pack.md."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from _common import load_yaml
from validate_spec import validate_song_spec


def _recommend_model(model_pref: str) -> str:
    if model_pref == "auto":
        return "auto (resolve via execution-guard: v6 on Pro/Premier, v6-mini on Free)"
    return model_pref


def _format_lyrics_box(spec: dict[str, Any]) -> str:
    raw_lyrics = (spec["lyrics"].get("text") or "").strip()
    if raw_lyrics:
        return raw_lyrics
    # Deterministic tags-only fallback for instrumental specs
    tags: list[str] = []
    for sec in spec["form"]:
        sec_name = sec.get("name") or sec["id"].replace("_", " ").title()
        tags.append(f"[{sec_name}]")
    tags.append("[End]")
    return "\n\n".join(tags)


def render_suno_pack(spec: dict[str, Any]) -> str:
    """Compile a validated SONG-SPEC dict deterministically into suno-pack markdown."""
    errors, _warnings = validate_song_spec(spec)
    if errors:
        joined = "\n".join(f"- {e}" for e in errors)
        raise ValueError(f"Cannot render invalid SONG-SPEC:\n{joined}")

    identity = spec["identity"]
    music = spec["music"]
    vocal = spec["vocal"]
    gen = spec["generation"]
    controls = gen.get("controls") or {}
    source = gen.get("source") or {}
    acceptance = spec["acceptance"]

    title = identity["title"].strip()
    model_rec = _recommend_model(gen["model_preference"])
    style = gen["style_prompt"].strip()
    lyrics_box = _format_lyrics_box(spec)
    excludes = ", ".join(gen.get("exclude_styles") or []) or "(none)"

    variety_val = controls.get("variety", 0)
    variety_label = "Off (0)" if variety_val == 0 else str(variety_val)
    max_mode_label = "On" if controls.get("max_mode") else "Off"
    instrumental_label = "Off (Vocal)" if vocal["enabled"] else "On (Instrumental)"

    lines: list[str] = [
        f"# Suno Pack — {title}",
        "",
        f"- **Spec Version**: {spec['spec_version']} (revision {spec['revision']})",
        f"- **Mode**: Advanced Mode (manual fallback or MCP payload reference)",
        "",
        "## Title",
        title,
        "",
        "## Model recommendation",
        model_rec,
        "",
        "## Style",
        style,
        "",
        "## Lyrics",
        "```text",
        lyrics_box,
        "```",
        "",
        "## Exclude Styles",
        excludes,
        "",
        "## Generation notes",
        f"- **Intent**: {gen['intent']}",
        f"- **Instrumental**: {instrumental_label}",
        f"- **Tempo / Meter**: {music['tempo_bpm']} BPM, {music['meter']}",
        f"- **Key**: {music['key']['tonic']} {music['key']['mode']}",
        f"- **Target Duration**: {identity['target_duration_seconds']}s",
        f"- **Variety**: {variety_label}",
        f"- **Max Mode**: {max_mode_label}",
    ]

    for slider_key in ("weirdness", "style_influence", "audio_influence"):
        if controls.get(slider_key) is not None:
            lines.append(f"- **{slider_key}**: {controls[slider_key]}")

    if source.get("audio_id"):
        lines.append(f"- **Source Audio ID**: {source['audio_id']}")
    if source.get("continue_at") is not None:
        lines.append(f"- **Continue At**: {source['continue_at']}s")

    lines.extend([
        "",
        "## Expected structure",
        "| Section ID | Name | Bars | Energy | Function |",
        "|---|---|---:|---:|---|",
    ])
    for sec in spec["form"]:
        sec_name = sec.get("name") or sec["id"]
        lines.append(
            f"| {sec['id']} | {sec_name} | {sec['bars']} | {sec['energy']} | {sec['function']} |"
        )

    lines.extend(["", "## Acceptance checklist"])
    for item in acceptance["must"]:
        lines.append(f"- [ ] **MUST**: {item}")
    for item in acceptance.get("should") or []:
        lines.append(f"- [ ] **SHOULD**: {item}")
    for item in acceptance.get("reject_if") or []:
        lines.append(f"- [ ] **REJECT IF**: {item}")

    lines.append("")
    return "\n".join(lines)


def default_output_path(spec_path: Path) -> Path:
    """Resolve <song-dir>/exports/suno-pack.md next to SONG-SPEC.yaml."""
    return spec_path.resolve().parent / "exports" / "suno-pack.md"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deterministically render SONG-SPEC.yaml into suno-pack.md.")
    parser.add_argument("spec_path", type=Path, help="Path to SONG-SPEC.yaml")
    parser.add_argument("--out", type=Path, default=None, help="Output markdown path (default: <song-dir>/exports/suno-pack.md)")
    args = parser.parse_args(argv)

    if not args.spec_path.exists():
        print(f"ERROR: File not found: {args.spec_path}", file=sys.stderr)
        return 2

    spec = load_yaml(args.spec_path)
    try:
        rendered = render_suno_pack(spec)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    out_path = args.out or default_output_path(args.spec_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(rendered, encoding="utf-8")
    print(f"RENDERED: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
