"""MCP server exposing the hunt tools to any MCP-capable agent.

Human decisions are deliberately *not* exposed: waivers, attestations (expert
review seen, follow-up done) and Zenodo uploads stay CLI-only, so an agent
can't mark its own homework.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from . import calibration, claims, funnel, gates, ledger, novelty, prereg, review
from .hunt import create_hunt, find_hunt_root

try:  # mcp >= 2
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _Server

INSTRUCTIONS = (
    "Tools for agent-driven citizen science. Follow the discover-anything skill: calibrate on "
    "known answers, record every result file in the ledger and cite its ID, freeze thresholds "
    "before searching, run the null test, check novelty before calling anything new, and leave "
    "attestations and waivers to the human (`discover attest`, `discover waive`)."
)

server = _Server("discover-anything", instructions=INSTRUCTIONS)


def _root(hunt: str) -> Path:
    return find_hunt_root(Path(hunt))


def _inside(root: Path, file: str) -> Path:
    """Resolve a file argument and refuse anything outside the hunt folder."""
    full = (Path(file) if Path(file).is_absolute() else root / file).resolve()
    if root.resolve() not in full.parents:
        raise ValueError(f"{file} is outside the hunt folder")
    return full


@server.tool()
def new_hunt(path: str, question: str = "", domain: str = "other") -> dict[str, Any]:
    """Create a hunt folder (KICKOFF, HANDOFF, RUNLOG, LESSONS, ledger and working folders).

    domain: astronomy, archives or other.
    """
    created = create_hunt(Path(path), question=question or None, domain=domain)
    return {"root": str(created.root), "files": list(created.files)}


@server.tool()
def hunt_status(hunt: str) -> dict[str, Any]:
    """Evaluate the nine gates for the hunt folder and return the next action."""
    status = gates.evaluate(_root(hunt))
    return {"gates": [asdict(g) for g in status.gates], "integrity": list(status.integrity),
            "next_action": status.current.next_action if status.current else "All gates passed.",
            "report": gates.render(status)}


@server.tool()
def record_evidence(hunt: str, file: str, tags: list[str] | None = None, note: str = "",
                    script: str = "") -> dict[str, Any]:
    """Register a result file written by a script. Returns the evidence ID to cite, e.g. [E-004].

    Useful tags: known-answer, null, injection, search, holdout, vetting.
    """
    root = _root(hunt)
    full = Path(file) if Path(file).is_absolute() else root / file
    return asdict(ledger.append(root, "evidence", path=full, tags=tuple(tags or ()), note=note,
                                script=script or None))


@server.tool()
def list_evidence(hunt: str, kind: str = "") -> list[dict[str, Any]]:
    """List ledger entries, optionally of one kind (evidence, frozen, funnel, novelty, ...)."""
    return [asdict(e) for e in ledger.read_entries(_root(hunt)) if not kind or e.kind == kind]


@server.tool()
def verify_evidence(hunt: str) -> list[dict[str, Any]]:
    """Check every recorded file is unchanged since it was recorded."""
    return [asdict(c) for c in ledger.verify(_root(hunt))]


@server.tool()
def check_claims(hunt: str, file: str) -> dict[str, Any]:
    """Find statements with numbers that cite no evidence ID, or cite changed files."""
    root = _root(hunt)
    return asdict(claims.check_file_claims(_inside(root, file), ledger.read_entries(root), root))


@server.tool()
def freeze_settings(hunt: str, file: str, note: str) -> dict[str, Any]:
    """Freeze a thresholds/settings file before searching. Note says what and why."""
    root = _root(hunt)
    full = Path(file) if Path(file).is_absolute() else root / file
    return asdict(ledger.append(root, "frozen", path=full, note=note))


@server.tool()
def funnel_add(hunt: str, stage: str, real: int, null: int | None = None, note: str = "") -> str:
    """Record how many items survive a stage in the real run and in the null run."""
    root = _root(hunt)
    funnel.validate_counts(real, null)
    ledger.append(root, "funnel", note=note, data={"stage": stage, "real": real, "null": null})
    table = funnel.stages(ledger.read_entries(root))
    return "\n".join([funnel.render(table), *funnel.warnings(table)])


@server.tool()
def funnel_show(hunt: str) -> str:
    """Return the funnel table (markdown) and any warnings."""
    table = funnel.stages(ledger.read_entries(_root(hunt)))
    return "\n".join([funnel.render(table), *funnel.warnings(table)])


@server.tool()
def novelty_sources() -> list[dict[str, str]]:
    """List the catalogues and literature sources the novelty check can query."""
    return [{"name": c.name, "domain": c.domain, "method": c.method}
            for c in novelty.all_connectors()]


@server.tool()
def novelty_check(hunt: str, claim: str, ids: list[str] | None = None, ra: float | None = None,
                  dec: float | None = None, radius_arcsec: float = 30.0, place: str = "",
                  lat: float | None = None, lon: float | None = None, radius_km: float = 100.0,
                  year_from: int | None = None, year_to: int | None = None,
                  keywords: list[str] | None = None, domain: str = "",
                  sources: list[str] | None = None) -> dict[str, Any]:
    """Query catalogues and literature for a claim and write novelty/<claim>_<date>.md.

    Reports what was found per source; 'not-checked' and 'manual' rows must be done by hand.
    """
    root = _root(hunt)
    target = novelty.Target(ids=tuple(ids or ()), ra=ra, dec=dec, radius_arcsec=radius_arcsec,
                            lat=lat, lon=lon, radius_km=radius_km, place=place or None,
                            year_from=year_from, year_to=year_to, keywords=tuple(keywords or ()))
    connectors = novelty.select(domain or None, tuple(sources or ()))
    rows = novelty.run(target, connectors)
    path, entry = novelty.write_log(root, claim, target, rows)
    return {"log": str(path), "entry": entry.id, "summary": novelty.summary(rows),
            "rows": [asdict(r) for r in rows]}


@server.tool()
def prereg_freeze(hunt: str, files: list[str], note: str = "") -> dict[str, Any]:
    """Freeze predictions files with SHA-256 checksums before the new data exists."""
    root = _root(hunt)
    out, entry = prereg.freeze(root, [root / f if not Path(f).is_absolute() else Path(f)
                                      for f in files], note)
    return {"manifest": str(out), "entry": entry.id}


@server.tool()
def prereg_verify(hunt: str) -> list[dict[str, Any]]:
    """Check preregistered files are unchanged."""
    return [asdict(c) for c in prereg.verify(_root(hunt))]


@server.tool()
def review_pack(hunt: str, reviewer: str, claim: str = "") -> dict[str, str]:
    """Prepare PROMPT.md and a file list for a fresh session or second model to review."""
    pack = review.make_pack(_root(hunt), reviewer, claim or None)
    return {k: str(v) for k, v in asdict(pack).items()}


@server.tool()
def score_known_answers(known: list[dict[str, Any]], found: list[dict[str, Any]], key: str,
                        value: str = "", rel_tol: float = 0.01) -> dict[str, Any]:
    """Recall of known answers in pipeline output, matched by key and optional numeric value."""
    return calibration.score_known_answers(known, found, key, value or None, rel_tol)


@server.tool()
def judge_agreement(expected: dict[str, str], predicted: dict[str, str]) -> dict[str, Any]:
    """Accuracy, Cohen's kappa and per-label precision/recall of a judge against labels."""
    return calibration.judge_agreement(expected, predicted)


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()
