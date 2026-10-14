"""Prepare a fresh-context adversarial review for a second model or session."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .gates import claim_status
from .ledger import append
from .resources import read_template
from .review_text import RESPONSE_HEADER, REVIEW_PLACEHOLDER

EXCLUDED_DIRS = {"data", ".discover", ".git", "__pycache__", ".venv"}
_REVIEWER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


@dataclass(frozen=True)
class ReviewPack:
    prompt: Path
    file_list: Path
    review_stub: Path
    response_stub: Path


def _claim_summary(root: Path) -> str:
    folder = root / "claims"
    cards = sorted(folder.glob("*.md")) if folder.is_dir() else []
    if not cards:
        return "<no claim cards yet: describe the claim in one paragraph>"
    lines = []
    for card in cards:
        status = claim_status(card.read_text(encoding="utf-8")) or "status not set"
        lines.append(f"- {card.stem} ({status}): see claims/{card.name}")
    return "Claims in this hunt:\n" + "\n".join(lines)


def _files_for_review(root: Path) -> list[str]:
    files = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if path.is_file() and not (set(rel.parts) & EXCLUDED_DIRS) and path.name != ".gitkeep":
            files.append(rel.as_posix())
    return files


def make_pack(root: Path, reviewer: str, claim: str | None = None) -> ReviewPack:
    if not _REVIEWER_RE.match(reviewer):
        raise ValueError("reviewer must be a short name like 'codex' or 'fresh-claude'")
    root = Path(root)
    today = date.today().isoformat()
    folder = root / "reviews" / f"PACK_{reviewer}_{today}"
    folder.mkdir(parents=True, exist_ok=True)

    template = read_template("adversarial-review.md")
    claim_text = claim or _claim_summary(root)
    prompt = template.replace(
        "<one paragraph: object or event, signal or passage, what is claimed>", claim_text
    )
    prompt += (f"\n\nWrite your review to `reviews/REVIEW_{reviewer}_{today}.md`. "
               "Do not read any conversation history; work only from the files.\n")
    prompt_path = folder / "PROMPT.md"
    prompt_path.write_text(prompt, encoding="utf-8")
    list_path = folder / "FILES.txt"
    list_path.write_text("\n".join(_files_for_review(root)) + "\n", encoding="utf-8")

    review = root / "reviews" / f"REVIEW_{reviewer}_{today}.md"
    response = root / "reviews" / f"RESPONSE_{reviewer}_{today}.md"
    if not review.exists():
        review.write_text(f"# Review by {reviewer}, {today}\n\n{REVIEW_PLACEHOLDER}\n",
                          encoding="utf-8")
    if not response.exists():
        response.write_text(
            f"# Response to {reviewer} review, {today}\n\n"
            f"{RESPONSE_HEADER}\n"
            "|---|---|---|---|---|\n", encoding="utf-8")
    append(root, "review", path=prompt_path, data={"reviewer": reviewer})
    return ReviewPack(prompt_path, list_path, review, response)
