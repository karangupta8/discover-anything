"""Locate the bundled skills and hunt templates.

In an installed wheel they live in ``discover_anything/_skills``; in a source
checkout they live in the repository's ``skills/`` folder.
"""

from pathlib import Path

MAIN_SKILL = "discover-anything"
_PACKAGE_DIR = Path(__file__).resolve().parent


def skills_root() -> Path:
    """Directory holding every bundled skill folder."""
    for candidate in (_PACKAGE_DIR / "_skills", _PACKAGE_DIR.parents[1] / "skills"):
        if (candidate / MAIN_SKILL / "SKILL.md").is_file():
            return candidate
    raise FileNotFoundError(
        "bundled skills not found; reinstall discover-anything or run from a source checkout"
    )


def skill_names() -> tuple[str, ...]:
    """Names of all bundled skills, main skill first."""
    names = sorted(p.parent.name for p in skills_root().glob("*/SKILL.md"))
    return (MAIN_SKILL, *[n for n in names if n != MAIN_SKILL])


def templates_dir() -> Path:
    return skills_root() / MAIN_SKILL / "assets" / "templates"


def read_template(name: str) -> str:
    path = templates_dir() / name
    if not path.is_file():
        raise FileNotFoundError(f"template not found: {name}")
    return path.read_text(encoding="utf-8")
