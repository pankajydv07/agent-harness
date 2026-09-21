from pathlib import Path
import yaml

SKILL_DIRS = [
    Path.cwd() / ".agents" / "skills",
    Path.home() / ".agents" / "skills",
]

def find_skills() -> dict:
    """Map each skill name to its description and SKILL.md path."""
    skills = {}
    for directory in SKILL_DIRS:
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*/SKILL.md")):
            try:
                content = path.read_text(encoding="utf-8")
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    meta = yaml.safe_load(parts[1])
                    description = " ".join(meta.get("description", "").split())
                    skills[meta["name"]] = {"description": description, "path": path}
            except Exception:
                continue
    return skills

SKILLS = find_skills()

def skills_prompt() -> str:
    if not SKILLS:
        return ""
    return "\n".join(f"- {name}: {s['description']}" for name, s in SKILLS.items())

def read_skill(name: str) -> str:
    """Open a skill and return its full instructions."""
    if name not in SKILLS:
        return f"No skill named '{name}'."
    return SKILLS[name]["path"].read_text(encoding="utf-8")
