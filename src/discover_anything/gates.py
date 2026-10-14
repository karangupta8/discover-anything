"""Evaluate a hunt folder against the nine gates of the workflow.

Gates the tool can verify are checked from files and the ledger. Gates only a
person can judge (expert review, follow-up) pass on a human attestation made
with ``discover attest``; checks that don't apply to a domain can be waived
with a reason using ``discover waive``. Both are recorded in the ledger.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from . import funnel
from .ledger import Entry, chain_problems, check_file, file_sha256, read_entries, verify, with_tag
from .review_text import is_response_filled, is_review_filled

PASS, FAIL, WAIVED, ATTESTED = "pass", "fail", "waived", "attested"
CLAIM_STATUSES = ("candidate", "rejected", "already known", "confirmed", "submitted")
LIVE_STATUSES = ("candidate", "confirmed", "submitted")
WAIVABLE = ("injection", "null-funnel", "funnel-warnings", "novelty-incomplete", "prereg", "followup")
PLACEHOLDERS = frozenset({"tbd", "todo", "none", "n/a", "na", "xxx", "lorem", "ipsum", "tba",
                          "placeholder", "fill", "later", "unknown", "?"})
MIN_FIELD_WORDS = 2
EVIDENCE_KINDS = ("evidence", "novelty", "prereg", "funnel")
ATTESTABLE = ("expert-review", "followup")


@dataclass(frozen=True)
class GateResult:
    phase: int
    name: str
    status: str
    details: tuple[str, ...]
    next_action: str = ""

    @property
    def done(self) -> bool:
        return self.status in (PASS, WAIVED, ATTESTED)


@dataclass(frozen=True)
class HuntStatus:
    gates: tuple[GateResult, ...]
    integrity: tuple[str, ...]

    @property
    def current(self) -> GateResult | None:
        return next((g for g in self.gates if not g.done), None)

    @property
    def all_passed(self) -> bool:
        return self.current is None and not self.integrity


# --- helpers -----------------------------------------------------------------

def field_value(markdown: str, label: str) -> str:
    """Text after a '- **Label...:**' line, including indented continuation lines."""
    lines = markdown.splitlines()
    for i, line in enumerate(lines):
        if line.lstrip().startswith(f"- **{label}"):
            after = line.split(":**", 1)[1] if ":**" in line else ""
            extra = []
            for nxt in lines[i + 1:]:
                if nxt.startswith(("  ", "\t")) and nxt.strip():
                    extra.append(nxt.strip())
                else:
                    break
            return " ".join([after.strip(), *extra]).strip()
    return ""


def is_filled(value: str) -> bool:
    """At least two real words, not a placeholder like TBD or <one sentence>."""
    cleaned = re.sub(r"<[^>]*>", " ", value)
    words = [w for w in re.findall(r"[A-Za-z0-9][A-Za-z0-9'./%-]*", cleaned)
             if w.lower().strip(".") not in PLACEHOLDERS]
    return len(words) >= MIN_FIELD_WORDS and len(re.findall(r"[A-Za-z0-9]", " ".join(words))) >= 3


def _missing_fields(kickoff: str, labels: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(label for label in labels if not is_filled(field_value(kickoff, label)))


def _intact(root: Path, entries: tuple[Entry, ...]) -> tuple[tuple[Entry, ...], list[str]]:
    """Entries whose files exist, are non-empty and unchanged; plus problems for the rest."""
    good, problems = [], []
    for entry in entries:
        check = check_file(root, entry)
        if check is not None and check.status != "ok":
            problems.append(f"{entry.id} {entry.path} is {check.status} since it was recorded")
        elif entry.path is not None and not entry.bytes:
            problems.append(f"{entry.id} {entry.path} is empty")
        else:
            good.append(entry)
    return tuple(good), problems


def _flag(entries: tuple[Entry, ...], kind: str, check: str) -> Entry | None:
    found = [e for e in entries if e.kind == kind and e.data.get("check") == check]
    return found[-1] if found else None


def claim_status(card: str) -> str | None:
    match = re.search(r"\*\*Status:\*\*\s*(.+)", card)
    if not match:
        return None
    value = match.group(1).strip().lower()
    if value.count("/") >= 2:  # still the template's list of options
        return None
    return next((s for s in CLAIM_STATUSES if value.startswith(s)), None)


def _claims(root: Path) -> dict[str, str | None]:
    folder = root / "claims"
    cards = sorted(folder.glob("*.md")) if folder.is_dir() else []
    return {card.stem: claim_status(card.read_text(encoding="utf-8")) for card in cards}


# --- gates ---------------------------------------------------------------------

def _kickoff_gate(phase: int, name: str, kickoff: str, labels: tuple[str, ...]) -> GateResult:
    missing = _missing_fields(kickoff, labels)
    if missing:
        return GateResult(phase, name, FAIL, tuple(f"KICKOFF.md: '{m}' is empty" for m in missing),
                          f"Fill in KICKOFF.md: {', '.join(missing)}")
    return GateResult(phase, name, PASS, (f"{len(labels)} KICKOFF.md fields filled",))


def _calibrate(root: Path, entries: tuple[Entry, ...]) -> GateResult:
    details: list[str] = []
    problems: list[str] = []
    how = {
        "known-answer": "recover known answers blind, then `discover record <file> --tag known-answer`",
        "null": "run the pipeline on inverted or shuffled data, then `discover record <file> --tag null`",
    }
    for tag in ("known-answer", "null"):
        found, bad = _intact(root, with_tag(entries, tag))
        problems.extend(bad)
        if found:
            details.append(f"{len(found)} evidence entries tagged '{tag}'")
        else:
            problems.append(f"no '{tag}' evidence: {how[tag]}")
    injection, bad = _intact(root, with_tag(entries, "injection"))
    problems.extend(bad)
    injection_waiver = _flag(entries, "waiver", "injection")
    if injection:
        details.append(f"{len(injection)} evidence entries tagged 'injection'")
    elif injection_waiver:
        details.append("injection waived: " + injection_waiver.note)
    else:
        problems.append("no 'injection' evidence: plant synthetic signals and record the recovery "
                        "with `--tag injection` (or the human waives it with a reason)")

    frozen = [e for e in entries if e.kind == "frozen"]
    if not frozen:
        problems.append("no frozen settings; run `discover freeze <thresholds file>`")
    by_path: dict[str, list[int]] = {}
    for idx, entry in enumerate(entries):
        if entry.kind == "frozen" and entry.path:
            by_path.setdefault(entry.path, []).append(idx)
    null_idx = [i for i, e in enumerate(entries) if e.kind == "evidence" and "null" in e.tags]
    for path, indices in by_path.items():
        check = check_file(root, entries[indices[-1]])
        if check and check.status != "ok":
            problems.append(f"frozen settings {path} {check.status} since freezing; "
                            "re-freeze with a reason and re-run the null test")
        elif len(indices) > 1 and not any(i > indices[-1] for i in null_idx):
            problems.append(f"{path} was re-frozen; record a new null-test result after it")
        else:
            details.append(f"settings frozen: {path}")
    if problems:
        return GateResult(3, "Calibrate", FAIL, tuple(problems + details), problems[0])
    return GateResult(3, "Calibrate", PASS, tuple(details))


def _search(root: Path, entries: tuple[Entry, ...]) -> GateResult:
    table = funnel.stages(entries)
    problems: list[str] = []
    search, bad = _intact(root, with_tag(entries, "search"))
    problems.extend(bad)
    if not search:
        problems.append("no 'search' evidence: `discover record <results file> --tag search`")
    if len(table) < 2:
        problems.append(f"{len(table)} funnel stage(s) recorded; need at least 2")
    if table and all(s.null is None for s in table) and not _flag(entries, "waiver", "null-funnel"):
        problems.append("funnel has no null-run counts")
    warnings = list(funnel.warnings(table))
    waiver = _flag(entries, "waiver", "funnel-warnings")
    if warnings and not waiver:
        problems.extend(f"funnel: {w}" for w in warnings)
    details = [f"{len(table)} funnel stages"]
    if warnings and waiver:
        details.append(f"funnel warnings waived: {waiver.note}")
    if problems:
        return GateResult(4, "Search", FAIL, tuple(problems + details), problems[0])
    return GateResult(4, "Search", PASS, tuple(details))


def _kill(root: Path) -> GateResult:
    claims = _claims(root)
    problems: list[str] = []
    if not claims:
        problems.append("no claim cards in claims/ (rejected candidates need cards too)")
    unset = [cid for cid, status in claims.items() if status is None]
    if unset:
        problems.append(f"claim cards without a status: {', '.join(unset)}")
    reviews = root / "reviews"
    review_files = sorted(reviews.glob("REVIEW_*.md")) if reviews.is_dir() else []
    if not review_files:
        problems.append("no reviews/REVIEW_*.md from a fresh session or second model")
    empty = [r.name for r in review_files if not is_review_filled(r.read_text(encoding="utf-8"))]
    if empty:
        problems.append(f"review files still empty: {', '.join(empty)}")
    unanswered = []
    for review in review_files:
        response = reviews / review.name.replace("REVIEW_", "RESPONSE_", 1)
        if not response.is_file() or not is_response_filled(response.read_text(encoding="utf-8")):
            unanswered.append(review.name)
    if unanswered:
        problems.append(f"reviews without a filled RESPONSE_ file: {', '.join(unanswered)}")
    details = (f"{len(claims)} claim cards", f"{len(review_files)} reviews")
    if problems:
        return GateResult(5, "Kill", FAIL, tuple(problems) + details, problems[0])
    return GateResult(5, "Kill", PASS, details)


def _novelty_ok(root: Path, entries: tuple[Entry, ...], cid: str) -> str | None:
    """None if the claim has an adequate, intact novelty log; else the problem."""
    logs = [e for e in entries if e.kind == "novelty" and e.data.get("claim") == cid]
    manual = [e for e in with_tag(entries, "novelty")
              if e.path and Path(e.path).name.startswith(f"{cid}_")]
    if not logs and not manual:
        return f"no novelty log for {cid}"
    if manual and not logs:
        intact, bad = _intact(root, tuple(manual[-1:]))
        return bad[0] if bad else None
    latest = logs[-1]
    intact, bad = _intact(root, (latest,))
    if bad:
        return bad[0]
    if latest.data.get("catalogues_checked", 0) < 1:
        return f"{cid}: the novelty log checked no catalogue (only literature, n/a or failed sources)"
    pending = latest.data.get("pending", [])
    if pending and not _flag(entries, "waiver", "novelty-incomplete"):
        return (f"{cid}: not checked yet: {', '.join(pending)} (rerun, or check by hand and record "
                "the log with `--tag novelty`)")
    return None


def _novelty(root: Path, entries: tuple[Entry, ...]) -> GateResult:
    claims = _claims(root)
    if not claims:
        return GateResult(6, "Novelty", FAIL, ("no claims",), "Write claim cards first")
    if any(status is None for status in claims.values()):
        return GateResult(6, "Novelty", FAIL, ("some claim cards have no status",),
                          "Set a status on every claim card")
    live = [cid for cid, status in claims.items() if status in LIVE_STATUSES]
    if not live:
        return GateResult(6, "Novelty", PASS, ("no live candidates: every claim was rejected or "
                                              "already known (stopping is a result)",))
    problems = [p for p in (_novelty_ok(root, entries, cid) for cid in live) if p]
    if problems:
        return GateResult(6, "Novelty", FAIL, tuple(problems),
                          f"Run `discover novelty run --claim <id> ...`: {problems[0]}")
    return GateResult(6, "Novelty", PASS, (f"novelty logs for {len(live)} live claim(s)",))


def _prereg(root: Path, entries: tuple[Entry, ...]) -> GateResult:
    manifests = [e for e in entries if e.kind == "prereg"]
    if not manifests:
        waiver = _flag(entries, "waiver", "prereg")
        if waiver:
            return GateResult(7, "Preregister", WAIVED, (waiver.note,))
        return GateResult(7, "Preregister", FAIL, ("no preregistration",),
                          "Run `discover prereg freeze <predictions files>`, or "
                          "`discover waive prereg --note <why no future test exists>`")
    bad = []
    for manifest in manifests:
        for item in manifest.data.get("files", []):
            full = root / item["path"]
            if not full.is_file():
                bad.append(f"{item['path']} missing")
            elif file_sha256(full) != item["sha256"]:
                bad.append(f"{item['path']} changed after preregistration")
    if bad:
        return GateResult(7, "Preregister", FAIL, tuple(bad),
                          "Preregistered files must not change; publish outcomes as new files")
    return GateResult(7, "Preregister", PASS, (f"{len(manifests)} frozen manifest(s) intact",))


def _attested(phase: int, name: str, entries: tuple[Entry, ...], check: str,
              action: str) -> GateResult:
    attestation = _flag(entries, "attestation", check)
    if attestation:
        return GateResult(phase, name, ATTESTED, (attestation.note,))
    waiver = _flag(entries, "waiver", check)
    if waiver:
        return GateResult(phase, name, WAIVED, (waiver.note,))
    return GateResult(phase, name, FAIL, (f"no '{check}' attestation from the human",), action)


def evaluate(root: Path) -> HuntStatus:
    root = Path(root)
    entries = read_entries(root)
    kickoff_path = root / "KICKOFF.md"
    kickoff = kickoff_path.read_text(encoding="utf-8") if kickoff_path.is_file() else ""
    gates = (
        _kickoff_gate(0, "Curiosity", kickoff, ("Question in one sentence",)),
        _kickoff_gate(1, "Gap", kickoff, ("The gap", "Who else is working on it",
                                          "How this angle differs")),
        _kickoff_gate(2, "Scope", kickoff, (
            "Source and products", "Sample cuts", "Expected size",
            "Known answers the pipeline must recover blind", "Null test",
            "What counts as a candidate", "What kills a candidate", "What result stops the project",
        )),
        _calibrate(root, entries),
        _search(root, entries),
        _kill(root),
        _novelty(root, entries),
        _prereg(root, entries),
        _attested(8, "Report", entries, "expert-review",
                  "After a human expert has seen it: `discover attest expert-review --note ...`"),
        _attested(9, "Follow-up", entries, "followup",
                  "After the preregistered test: `discover attest followup --note <outcome>`"),
    )
    integrity = tuple(f"{c.entry_id} {c.path}: {c.status}" for c in verify(root, entries)
                      if c.status != "ok") + tuple(chain_problems(root))
    return HuntStatus(gates, integrity)


def render(status: HuntStatus) -> str:
    marks = {PASS: "PASS", FAIL: "FAIL", WAIVED: "WAIVED", ATTESTED: "ATTESTED"}
    lines = []
    for gate in status.gates:
        lines.append(f"[{marks[gate.status]:>8}] {gate.phase} {gate.name}")
        lines.extend(f"             {d}" for d in gate.details)
    if status.integrity:
        lines.append("\nEvidence files changed or missing since recorded:")
        lines.extend(f"  {item}" for item in status.integrity)
    current = status.current
    lines.append("")
    if current:
        lines.append(f"Next: {current.next_action}")
    elif status.integrity:
        lines.append("Next: every gate passes, but recorded evidence changed; fix it before reporting.")
    else:
        lines.append("All gates passed.")
    return "\n".join(lines)
