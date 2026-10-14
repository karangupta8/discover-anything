"""Create and locate hunt folders."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from . import __version__
from .ledger import LEDGER_FILE, STATE_DIR, now_iso
from .resources import read_template

HUNT_DIRS = ("scripts", "results", "controls", "claims", "novelty", "reviews", "prereg", "data")
TOP_FILES = {
    "KICKOFF.md": "project-kickoff.md",
    "HANDOFF.md": "handoff.md",
    "RUNLOG.md": "run-log.md",
    "LESSONS.md": "lessons.md",
}
DOMAINS = ("astronomy", "archives", "other")
HUNT_GITIGNORE = """# Raw data stays out of git; record pointers and checksums instead
data/
*.fits
.env
keys.yml
"""
_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


@dataclass(frozen=True)
class CreatedHunt:
    root: Path
    files: tuple[str, ...]


def _fill_kickoff(text: str, name: str, question: str | None, domain: str) -> str:
    filled = text.replace("<name>", name).replace(
        "- **Date:**", f"- **Date:** {date.today().isoformat()}", 1
    )
    if question:
        filled = filled.replace(
            "- **Question in one sentence:**", f"- **Question in one sentence:** {question}", 1
        )
    return filled + f"\n<!-- domain: {domain} -->\n"


def create_hunt(path: Path, *, question: str | None = None, domain: str = "other") -> CreatedHunt:
    """Scaffold a hunt folder. Refuses to touch an existing non-empty folder."""
    root = Path(path)
    if not _NAME_RE.match(root.name):
        raise ValueError("hunt name must start with a letter or digit and use only "
                         "letters, digits, '.', '_' or '-'")
    if domain not in DOMAINS:
        raise ValueError(f"domain must be one of {DOMAINS}")
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"{root} exists and is not empty")

    for sub in (*HUNT_DIRS, STATE_DIR):
        (root / sub).mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    for target, template in TOP_FILES.items():
        text = read_template(template).replace("<project>", root.name)
        if target == "KICKOFF.md":
            text = _fill_kickoff(text, root.name, question, domain)
        (root / target).write_text(text, encoding="utf-8")
        created.append(target)
    (root / ".gitignore").write_text(HUNT_GITIGNORE, encoding="utf-8")
    (root / STATE_DIR / LEDGER_FILE).write_text("", encoding="utf-8")
    meta = {"name": root.name, "domain": domain, "created": now_iso(), "tool_version": __version__}
    (root / STATE_DIR / "hunt.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    for sub in HUNT_DIRS:
        (root / sub / ".gitkeep").write_text("", encoding="utf-8")
    created += [".gitignore", f"{STATE_DIR}/{LEDGER_FILE}", f"{STATE_DIR}/hunt.json"]
    return CreatedHunt(root=root, files=tuple(created) + tuple(f"{d}/" for d in HUNT_DIRS))


def find_hunt_root(start: Path | None = None) -> Path:
    """Walk up from start (default: cwd) to the folder containing .discover/."""
    current = Path(start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / STATE_DIR / LEDGER_FILE).is_file():
            return candidate
    raise FileNotFoundError(
        "not inside a hunt folder (no .discover/ledger.jsonl found); run `discover new <name>`"
    )


def hunt_meta(root: Path) -> dict[str, str]:
    path = Path(root) / STATE_DIR / "hunt.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
