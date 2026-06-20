"""
Load Hermes SKILL.md files as LangChain-compatible tools.
Parses YAML frontmatter and extracts trigger keywords, description, and content.
"""
import os
import re
import yaml
from pathlib import Path
from typing import List, Dict, Any


def parse_skill_md(filepath: str) -> Dict[str, Any]:
    """
    Parse a SKILL.md file: extract YAML frontmatter and markdown body.
    Returns a dict with 'meta' (parsed frontmatter) and 'content' (markdown body).
    """
    with open(filepath, 'r') as f:
        content = f.read()

    # Extract YAML frontmatter
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter = yaml.safe_load(parts[1])
            body = parts[2].strip()
        else:
            frontmatter = {}
            body = content
    else:
        frontmatter = {}
        body = content

    return {
        "meta": frontmatter or {},
        "content": body,
        "path": filepath,
    }


def load_skills(skills_dir: str = "~/.hermes/skills") -> List[Dict[str, Any]]:
    """
    Scan skills_dir for all SKILL.md files and return parsed skill objects.
    Each skill has: name, description, triggers, content, category.
    """
    skills = []
    skills_path = Path(skills_dir).expanduser()

    if not skills_path.exists():
        print(f"WARNING: Skills directory not found: {skills_path}")
        return skills

    for root, dirs, files in os.walk(skills_path):
        if "SKILL.md" in files:
            skill_dir = Path(root)
            skill_name = skill_dir.name
            category = str(skill_dir.relative_to(skills_path).parent)
            filepath = str(skill_dir / "SKILL.md")

            try:
                parsed = parse_skill_md(filepath)
                meta = parsed["meta"]
                skills.append({
                    "name": meta.get("name", skill_name),
                    "description": meta.get("description", f"Skill: {skill_name}"),
                    "triggers": meta.get("triggers", []),
                    "version": meta.get("version", "1.0.0"),
                    "content": parsed["content"],
                    "category": category,
                    "path": filepath,
                })
            except Exception as e:
                print(f"WARNING: Failed to parse {filepath}: {e}")

    return skills


def find_skills_by_trigger(trigger_keyword: str, skills: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Find skills that match a trigger keyword."""
    matches = []
    keyword = trigger_keyword.lower()
    for skill in skills:
        triggers = [t.lower() for t in skill.get("triggers", [])]
        if keyword in triggers or keyword in skill["name"].lower() or keyword in skill["description"].lower():
            matches.append(skill)
    return matches


def build_skill_registry(skills_dir: str = "~/.hermes/skills") -> Dict[str, Dict[str, Any]]:
    """Build a name→skill registry for fast lookup."""
    skills = load_skills(skills_dir)
    return {skill["name"]: skill for skill in skills}
