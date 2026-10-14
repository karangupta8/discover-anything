"""Novelty checks: query catalogues and literature, write a dated novelty log."""

from __future__ import annotations

import json
import re
from dataclasses import asdict
from datetime import UTC, date, datetime
from pathlib import Path

from ..http import HttpClient
from ..ledger import Entry, append
from . import archives, astronomy, literature
from .base import (
    FOUND,
    MANUAL,
    MAX_MATCHES_SHOWN,
    NONE,
    NOT_APPLICABLE,
    NOT_CHECKED,
    Connector,
    Match,
    NoveltyRow,
    Target,
    run_connector,
)

__all__ = ["Target", "Match", "NoveltyRow", "all_connectors", "select", "run", "render_log",
           "write_log", "manual_source"]

_CLAIM_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def all_connectors() -> tuple[Connector, ...]:
    return (*astronomy.CONNECTORS, *literature.CONNECTORS, *archives.CONNECTORS)


def manual_source(name: str, url: str) -> Connector:
    return archives.ManualSource(name=name, human_url=url, domain="manual")


def select(domain: str | None = None, names: tuple[str, ...] = ()) -> tuple[Connector, ...]:
    """Connectors for a domain (plus literature, always), or those whose names contain any of names."""
    pool = all_connectors()
    if names:
        wanted = tuple(n.lower() for n in names)
        chosen = tuple(c for c in pool if any(w in c.name.lower() for w in wanted))
        if not chosen:
            raise ValueError(f"no connector matches {names}; see `discover novelty sources`")
        return chosen
    if domain in (None, "other"):
        return pool
    return tuple(c for c in pool if c.domain in (domain, "literature"))


def run(target: Target, connectors: tuple[Connector, ...],
        http: HttpClient | None = None) -> tuple[NoveltyRow, ...]:
    http = http or HttpClient()
    return tuple(run_connector(c, target, http) for c in connectors)


def summary(rows: tuple[NoveltyRow, ...]) -> dict[str, int]:
    keys = (FOUND, NONE, NOT_CHECKED, MANUAL, NOT_APPLICABLE)
    return {k: sum(r.status == k for r in rows) for k in keys}


def catalogues_checked(rows: tuple[NoveltyRow, ...]) -> int:
    """Non-literature sources that actually answered (found or none)."""
    return sum(r.status in (FOUND, NONE) and r.domain != "literature" for r in rows)


def _conclusion(rows: tuple[NoveltyRow, ...], day: str) -> str:
    counts = summary(rows)
    lines = []
    if counts[FOUND]:
        lines.append(f"Records found in {counts[FOUND]} source(s). Inspect each one below "
                     "before calling anything new; a record may be the same object or event.")
    elif counts[NONE]:
        lines.append(f"No records found as of {day} in the {counts[NONE]} source(s) that were checked.")
    else:
        lines.append("Nothing was checked: every source failed, was manual or didn't apply. "
                     "This log is not evidence of novelty.")
    pending = [r.source for r in rows if r.status in (NOT_CHECKED, MANUAL)]
    if pending:
        lines.append("Not yet checked (do these by hand and add the result): "
                     + "; ".join(pending) + ".")
    return " ".join(lines)


def render_log(claim: str, target: Target, rows: tuple[NoveltyRow, ...]) -> str:
    day = date.today().isoformat()
    out = [f"# Novelty Log: {claim}", "", f"**Target:** {target.describe()}",
           f"**Checked:** {day} with `discover novelty run`", "",
           "| Source | Status | Searched by | Method | Results | Link |", "|---|---|---|---|---|---|"]
    for row in rows:
        note = row.note.replace("|", "/") if row.note else ""
        results = f"{len(row.matches)}" if row.status == FOUND else note or "–"
        link = f"[open]({row.url})" if row.url else ""
        out.append(f"| {row.source} | {row.status} | {row.searched_by or '–'} | {row.method} | "
                   f"{results} | {link} |")
    for row in rows:
        if row.status != FOUND:
            continue
        out += ["", f"## {row.source}", ""]
        for match in row.matches[:MAX_MATCHES_SHOWN]:
            label = f"[{match.label}]({match.url})" if match.url else match.label
            out.append(f"- {label}" + (f": {match.detail}" if match.detail else ""))
        if len(row.matches) > MAX_MATCHES_SHOWN:
            out.append(f"- … and {len(row.matches) - MAX_MATCHES_SHOWN} more (see the JSON file)")
    out += ["", "## Hobbyist postings checked", "",
            "GitHub and Zenodo rows above. Also search social posts and forums by every alias, "
            "and record what you found here.", "",
            "## Conclusion", "", _conclusion(rows, day), ""]
    return "\n".join(out)


def write_log(root: Path, claim: str, target: Target,
              rows: tuple[NoveltyRow, ...]) -> tuple[Path, Entry]:
    if not _CLAIM_RE.match(claim):
        raise ValueError("claim id must use only letters, digits, '.', '_' or '-'")
    root = Path(root)
    stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H%M%SZ")
    folder = root / "novelty"
    folder.mkdir(parents=True, exist_ok=True)
    md_path = folder / f"{claim}_{stamp}.md"
    if md_path.exists():
        raise FileExistsError(f"{md_path} already exists; wait a second and rerun")
    md_path.write_text(render_log(claim, target, rows), encoding="utf-8")
    json_path = folder / f"{claim}_{stamp}.json"
    json_path.write_text(json.dumps({"claim": claim, "target": asdict(target),
                                     "rows": [asdict(r) for r in rows]}, indent=2),
                         encoding="utf-8")
    entry = append(root, "novelty", path=md_path, tags=("novelty",),
                   data={"claim": claim, "summary": summary(rows), "json": json_path.name,
                         "catalogues_checked": catalogues_checked(rows),
                         "pending": [r.source for r in rows if r.status in (NOT_CHECKED, MANUAL)]})
    return md_path, entry
