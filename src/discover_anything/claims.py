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
    re.compile(r"`[^`]*[A-Za-z_/\\][^`]*`"),     # inline code naming files or identifiers
    re.compile(r"\]\([^)]*\)"),                # link targets
    re.compile(r"https?://\S+"),               # bare URLs
    re.compile(r"<!--.*?-->"),                 # html comments
    CITATION_RE,
)
_LIST_MARKER = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
_TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{3,}")
_FENCE = re.compile(r"^\s*(```|~~~)")
_HEADING_OR_QUOTE = re.compile(r"^\s*(?:#{1,6}|>+)\s*")
CITABLE_KINDS = ("evidence", "novelty", "prereg", "funnel")
UNCLOSED_FENCE = "unclosed code fence: everything after it was skipped"
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
    fence: str | None = None
    fence_line = 0

    def flush() -> None:
        nonlocal buffer
        if buffer:
            text = " ".join(buffer)
            units.extend(Unit(start, s) for s in _SENTENCE_SPLIT.split(text) if s.strip())
            buffer = []

    for number, raw in enumerate(lines, start=1):
        line = raw.rstrip()
        marker = _FENCE.match(line)
        if marker and (fence is None or marker.group(1) == fence):
            flush()
            fence, fence_line = (None, 0) if fence else (marker.group(1), number)
            continue
        if fence:
            continue
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        if _HEADING_OR_QUOTE.match(stripped):
            flush()
            text = _HEADING_OR_QUOTE.sub("", stripped)
            if text:
                units.append(Unit(number, text))
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
    if fence:
        units.append(Unit(fence_line, UNCLOSED_FENCE))
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
        if unit.text == UNCLOSED_FENCE:
            issues.append(ClaimIssue(unit.line, unit.text, UNCLOSED_FENCE))
            continue
        citations = [c.strip() for m in CITATION_RE.finditer(unit.text) for c in m.group(1).split(",")]
        for cid in citations:
            entry = find(entries, cid)
            if entry is None:
                issues.append(ClaimIssue(unit.line, unit.text, f"cites {cid}, which is not in the ledger"))
                continue
            if entry.kind not in CITABLE_KINDS:
                issues.append(ClaimIssue(unit.line, unit.text,
                                         f"cites {cid}, a {entry.kind} entry, not evidence"))
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
