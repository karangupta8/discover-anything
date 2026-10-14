"""Check that every number in a write-up cites ledger evidence.

Enforces the rule "numbers come from files": a sentence, list item or table
row containing a number must carry a citation like ``[E-004]`` or
``[E-004, E-007]``, and every cited entry must exist and its file must be
unchanged since it was recorded.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .ledger import Entry, check_file, find

CITATION_RE = re.compile(r"\[(E-\d+(?:\s*,\s*E-\d+)*)\]", re.IGNORECASE)
_STRIP_PATTERNS = (
    re.compile(r"`[^`]*`"),                    # inline code
    re.compile(r"\]\([^)]*\)"),                # link targets
    re.compile(r"https?://\S+"),               # bare URLs
    re.compile(r"<!--.*?-->"),                 # html comments
    CITATION_RE,
)
_LIST_MARKER = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
_TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{3,}")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\"'])")


@dataclass(frozen=True)
class Unit:
    line: int
    text: str


@dataclass(frozen=True)
class ClaimIssue:
    line: int
    text: str
    problem: str


@dataclass(frozen=True)
class ClaimReport:
    units_with_numbers: int
    cited: int
    issues: tuple[ClaimIssue, ...]

    @property
    def ok(self) -> bool:
        return not self.issues


def _units(markdown: str) -> list[Unit]:
    """Split markdown into checkable units: sentences, list items, table rows."""
    lines = markdown.splitlines()
    units: list[Unit] = []
    buffer: list[str] = []
    start = 0
    in_code = False

    def flush() -> None:
        nonlocal buffer
        if buffer:
            text = " ".join(buffer)
            units.extend(Unit(start, s) for s in _SENTENCE_SPLIT.split(text) if s.strip())
            buffer = []

    for number, raw in enumerate(lines, start=1):
        line = raw.rstrip()
        if line.lstrip().startswith("```"):
            flush()
            in_code = not in_code
            continue
        if in_code:
            continue
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith(">"):
            flush()
            continue
        if stripped.startswith("|"):
            flush()
            next_line = lines[number].strip() if number < len(lines) else ""
            is_header = bool(_TABLE_SEP.match(next_line))
            if not (_TABLE_SEP.match(stripped) or is_header):
                units.append(Unit(number, stripped))
            continue
        if _LIST_MARKER.match(line):
            flush()
            start, buffer = number, [_LIST_MARKER.sub("", line).strip()]
            continue
        if not buffer:
            start = number
        buffer.append(stripped)
    flush()
    return units


def _has_number(text: str) -> bool:
    cleaned = text
    for pattern in _STRIP_PATTERNS:
        cleaned = pattern.sub(" ", cleaned)
    return bool(re.search(r"\d", cleaned))


def check_text(markdown: str, entries: tuple[Entry, ...], root: Path | None = None) -> ClaimReport:
    issues: list[ClaimIssue] = []
    with_numbers = cited = 0
    for unit in _units(markdown):
        citations = [c.strip() for m in CITATION_RE.finditer(unit.text) for c in m.group(1).split(",")]
        for cid in citations:
            entry = find(entries, cid)
            if entry is None:
                issues.append(ClaimIssue(unit.line, unit.text, f"cites {cid}, which is not in the ledger"))
                continue
            check = check_file(root, entry) if root is not None else None
            if check is not None and check.status != "ok":
                issues.append(ClaimIssue(
                    unit.line, unit.text, f"cites {cid}, whose file {check.path} is {check.status}"
                ))
        if not _has_number(unit.text):
            continue
        with_numbers += 1
        if citations:
            cited += 1
        else:
            issues.append(ClaimIssue(unit.line, unit.text, "number without evidence citation"))
    return ClaimReport(with_numbers, cited, tuple(issues))


def check_file_claims(path: Path, entries: tuple[Entry, ...], root: Path) -> ClaimReport:
    return check_text(Path(path).read_text(encoding="utf-8"), entries, root)
