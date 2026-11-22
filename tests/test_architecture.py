"""Tests for V1 repository architecture, skill count, and governance consistency."""

from __future__ import annotations

import yaml

from _common import REPO_ROOT

EXPECTED_SKILLS = {
    "music-director",
    "composition-architect",
    "arrangement-architect",
    "lyric-writer",
    "pronunciation-specialist",
    "suno-engineer",
    "execution-guard",
    "take-reviewer",
}


def test_exactly_eight_core_skills_exist() -> None:
    skills_dir = REPO_ROOT / "skills"
    found = {p.name for p in skills_dir.iterdir() if p.is_dir()}
    assert found == EXPECTED_SKILLS
    for name in EXPECTED_SKILLS:
        skill_md = skills_dir / name / "SKILL.md"
        assert skill_md.exists(), f"Missing {skill_md}"
        content = skill_md.read_text(encoding="utf-8")
        assert content.startswith("---\n")
        frontmatter = yaml.safe_load(content.split("---\n", 2)[1])
        assert frontmatter["name"] == name
        assert isinstance(frontmatter["description"], str) and len(frontmatter["description"]) > 20


def test_ownership_and_routing_reference_all_core_skills() -> None:
    ownership = (REPO_ROOT / "governance" / "OWNERSHIP.md").read_text(encoding="utf-8")
    routing = (REPO_ROOT / "governance" / "ROUTING.md").read_text(encoding="utf-8")
    for name in EXPECTED_SKILLS:
        assert name in ownership, f"{name} missing from governance/OWNERSHIP.md"
        assert name in routing, f"{name} missing from governance/ROUTING.md"
