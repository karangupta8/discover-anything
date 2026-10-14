"""`discover` command line."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from . import __version__, calibration, claims, funnel, gates, ledger, novelty, prereg, review
from .hunt import DOMAINS, create_hunt, find_hunt_root, hunt_meta


def _root(args: argparse.Namespace) -> Path:
    return find_hunt_root(Path(args.hunt) if args.hunt else None)


def _print(data: Any, as_json: bool, text: str) -> None:
    print(json.dumps(data, indent=2, default=str) if as_json else text)


def _read_table(path: str) -> list[dict[str, str]]:
    text = Path(path).read_text(encoding="utf-8")
    if path.endswith((".jsonl", ".ndjson")):
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    if path.endswith(".json"):
        return list(json.loads(text))
    return list(csv.DictReader(text.splitlines()))


# --- hunt lifecycle ------------------------------------------------------------

def cmd_new(args: argparse.Namespace) -> int:
    created = create_hunt(Path(args.path), question=args.question, domain=args.domain)
    print(f"Created hunt at {created.root}")
    for name in created.files:
        print(f"  {name}")
    print("\nNext: fill in KICKOFF.md, then run `discover status` inside the folder.")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    root = _root(args)
    status = gates.evaluate(root)
    data = {"hunt": str(root), "gates": [asdict(g) for g in status.gates],
            "integrity": list(status.integrity),
            "current": asdict(status.current) if status.current else None}
    _print(data, args.json, f"Hunt: {hunt_meta(root).get('name', root.name)}\n\n" + gates.render(status))
    return 0


def cmd_record(args: argparse.Namespace) -> int:
    root = _root(args)
    entry = ledger.append(root, "evidence", path=Path(args.file).resolve(), tags=tuple(args.tag),
                          note=args.note or "", script=args.script)
    _print(asdict(entry), args.json, f"{entry.id}  {entry.path}  sha256 {entry.sha256[:12]}…  "
                                     f"tags: {', '.join(entry.tags) or '–'}\n"
                                     f"Cite it as [{entry.id}].")
    return 0


def cmd_evidence(args: argparse.Namespace) -> int:
    entries = ledger.read_entries(_root(args))
    if args.id:
        entry = ledger.find(entries, args.id)
        if entry is None:
            print(f"{args.id} not found", file=sys.stderr)
            return 1
        print(json.dumps(asdict(entry), indent=2))
        return 0
    shown = [e for e in entries if not args.kind or e.kind == args.kind]
    lines = [f"{e.id}  {e.kind:<11} {e.time}  {e.path or e.data.get('stage') or e.data.get('check') or ''}"
             f"  {','.join(e.tags)}  {e.note[:60]}" for e in shown]
    _print([asdict(e) for e in shown], args.json, "\n".join(lines) or "Ledger is empty.")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    checks = ledger.verify(_root(args))
    bad = [c for c in checks if c.status != "ok"]
    text = "\n".join(f"{c.entry_id}  {c.status:<8} {c.path}" for c in checks) or "Nothing recorded."
    _print([asdict(c) for c in checks], args.json, text)
    return 1 if bad else 0


def cmd_check_claims(args: argparse.Namespace) -> int:
    root = _root(args)
    report = claims.check_file_claims(Path(args.file), ledger.read_entries(root), root)
    lines = [f"{report.units_with_numbers} statements with numbers, {report.cited} cited."]
    lines += [f"  line {i.line}: {i.problem}\n    {i.text[:140]}" for i in report.issues]
    lines.append("OK: every number cites evidence." if report.ok else
                 f"{len(report.issues)} problem(s). Record the source file with "
                 "`discover record` and cite its ID like [E-004].")
    _print(asdict(report), args.json, "\n".join(lines))
    return 0 if report.ok else 1


def cmd_freeze(args: argparse.Namespace) -> int:
    root = _root(args)
    entry = ledger.append(root, "frozen", path=Path(args.file).resolve(), note=args.note)
    print(f"{entry.id}  froze {entry.path} (sha256 {entry.sha256[:12]}…). "
          "Changing it later fails the Calibrate gate until re-frozen with a reason "
          "and a new null test is recorded.")
    return 0


def cmd_flag(kind: str, allowed: tuple[str, ...]):
    def run(args: argparse.Namespace) -> int:
        if args.check not in allowed:
            print(f"{kind} applies to: {', '.join(allowed)}", file=sys.stderr)
            return 2
        entry = ledger.append(_root(args), kind, note=args.note, data={"check": args.check})
        print(f"{entry.id}  {kind} '{args.check}': {args.note}")
        return 0
    return run


def cmd_funnel(args: argparse.Namespace) -> int:
    root = _root(args)
    if args.action == "add":
        funnel.validate_counts(args.real, args.null)
        entry = ledger.append(root, "funnel", note=args.note or "",
                              data={"stage": args.stage, "real": args.real, "null": args.null})
        print(f"{entry.id}  stage '{args.stage}': real {args.real}, null {args.null}")
    table = funnel.stages(ledger.read_entries(root))
    if args.action == "show" or args.json:
        _print([asdict(s) for s in table], args.json, funnel.render(table))
    for warning in funnel.warnings(table):
        print(f"warning: {warning}", file=sys.stderr)
    return 0


# --- novelty, prereg, review ---------------------------------------------------------

def _target(args: argparse.Namespace) -> novelty.Target:
    return novelty.Target(
        ids=tuple(args.id), ra=args.ra, dec=args.dec, radius_arcsec=args.radius,
        lat=args.lat, lon=args.lon, radius_km=args.radius_km, place=args.place,
        year_from=args.year_from, year_to=args.year_to, keywords=tuple(args.keyword))


def cmd_novelty(args: argparse.Namespace) -> int:
    if args.action == "sources":
        for c in novelty.all_connectors():
            print(f"{c.domain:<11} {c.name}  ({c.method})")
        return 0
    root = _root(args)
    domain = args.domain or hunt_meta(root).get("domain")
    connectors = novelty.select(domain, tuple(args.source))
    connectors += tuple(novelty.manual_source(*m.split("|", 1)) for m in args.manual)
    target = _target(args)
    rows = novelty.run(target, connectors)
    path, entry = novelty.write_log(root, args.claim, target, rows)
    counts = novelty.summary(rows)
    print(f"{entry.id}  wrote {path.relative_to(root)}")
    print("  " + ", ".join(f"{k}: {v}" for k, v in counts.items()))
    for row in rows:
        if row.status == "found":
            print(f"  [found] {row.source}: {len(row.matches)} record(s)")
        elif row.status in ("not-checked", "manual"):
            print(f"  [{row.status}] {row.source}: {row.note}")
    return 0


def cmd_prereg(args: argparse.Namespace) -> int:
    root = _root(args)
    if args.action == "freeze":
        out, entry = prereg.freeze(root, [Path(f).resolve() for f in args.files], args.note or "")
        print(f"{entry.id}  wrote {out.relative_to(root)}. Publish it (e.g. `discover prereg "
              "zenodo`) before the new data exists; never edit the frozen files.")
        return 0
    if args.action == "verify":
        checks = prereg.verify(root)
        for c in checks:
            print(f"{c.status:<8} {c.manifest}  {c.path}")
        return 0 if all(c.status == "ok" for c in checks) else 1
    import os
    result = prereg.zenodo_draft(root, Path(args.manifest), title=args.title,
                                 creators=args.creator, token=os.environ.get("ZENODO_TOKEN", ""),
                                 description=args.description or "", sandbox=args.sandbox)
    print(json.dumps(result, indent=2))
    print("Draft created, NOT published. Review it on Zenodo and publish it yourself.")
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    pack = review.make_pack(_root(args), args.reviewer, args.claim)
    print(f"Prompt:   {pack.prompt}\nFiles:    {pack.file_list}\n"
          f"Review →  {pack.review_stub}\nResponse → {pack.response_stub}\n"
          "Open a fresh session (or another model) in the hunt folder and give it only PROMPT.md.")
    return 0


# --- calibration and archive helpers ----------------------------------------------------

def cmd_score_known(args: argparse.Namespace) -> int:
    aliases = tuple(float(a) for a in args.aliases.split(","))
    result = calibration.score_known_answers(_read_table(args.known), _read_table(args.found),
                                             args.key, args.value, args.rel_tol, aliases)
    text = (f"Recall {result['recall']:.1%} ({len(result['recovered'])}/{result['n_known']}). "
            f"Missed: {', '.join(result['missed']) or 'none'}. "
            f"Wrong value: {', '.join(w['key'] for w in result['wrong_value']) or 'none'}.")
    if args.out:
        out = Path(args.out)
        out.write_text(json.dumps(result, indent=2), encoding="utf-8")
        entry = ledger.append(_root(args), "evidence", path=out.resolve(),
                              tags=("known-answer",), note=text)
        text += f"\n{entry.id}  recorded {entry.path} tagged known-answer."
    _print(result, args.json, text)
    return 0


def cmd_judge(args: argparse.Namespace) -> int:
    exp = {r[args.id_col]: r[args.label_col] for r in _read_table(args.expected)}
    pred = {r[args.id_col]: r[args.label_col] for r in _read_table(args.predicted)}
    result = calibration.judge_agreement(exp, pred)
    _print(result, args.json, f"n={result['n']} accuracy={result['accuracy']:.1%} "
                              f"kappa={result['kappa']:.2f}\nconfusions: {result['confusions']}")
    return 0


def cmd_dedupe(args: argparse.Namespace) -> int:
    from .textmatch import group_duplicates, near_duplicates
    rows = _read_table(args.file)
    texts = [r[args.text_col] for r in rows]
    groups = group_duplicates(len(texts), near_duplicates(texts, args.threshold))
    multi = [g for g in groups if len(g) > 1]
    data = [[rows[i].get(args.id_col, i) if args.id_col else i for i in g] for g in groups]
    _print(data, args.json, f"{len(texts)} passages → {len(groups)} distinct events; "
                            f"{len(multi)} groups of reprints/duplicates.")
    return 0


def cmd_setup(args: argparse.Namespace) -> int:
    from .setup_agents import run_setup
    return run_setup(args.client, apply=args.yes, skills_dir=args.skills_dir)


def cmd_mcp(args: argparse.Namespace) -> int:
    from .mcp_server import main as serve
    serve()
    return 0


# --- parser -----------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="discover", description="Find what's hiding in public data, "
                                "then try hard to prove yourself wrong.")
    p.add_argument("--version", action="version", version=f"discover-anything {__version__}")
    p.add_argument("--hunt", help="hunt folder (default: search upward from the current folder)")
    sub = p.add_subparsers(dest="command", required=True)

    def add(name: str, func, help_: str) -> argparse.ArgumentParser:
        sp = sub.add_parser(name, help=help_, description=help_)
        sp.set_defaults(func=func)
        sp.add_argument("--json", action="store_true", help="machine-readable output")
        return sp

    sp = add("new", cmd_new, "create a hunt folder with the workflow's files and folders")
    sp.add_argument("path")
    sp.add_argument("--question")
    sp.add_argument("--domain", choices=DOMAINS, default="other")

    add("status", cmd_status, "check which of the nine gates pass and what to do next")

    sp = add("record", cmd_record, "register a result file in the evidence ledger")
    sp.add_argument("file")
    sp.add_argument("--tag", action="append", default=[],
                    help="e.g. known-answer, null, injection, search, holdout, vetting")
    sp.add_argument("--script", help="script that produced the file")
    sp.add_argument("--note")

    sp = add("evidence", cmd_evidence, "list ledger entries, or show one")
    sp.add_argument("id", nargs="?")
    sp.add_argument("--kind", choices=sorted(ledger.KINDS))

    add("verify", cmd_verify, "check recorded files are unchanged since recording")

    sp = add("check-claims", cmd_check_claims, "flag numbers in a write-up that cite no evidence")
    sp.add_argument("file")

    sp = add("freeze", cmd_freeze, "freeze a thresholds/settings file before searching")
    sp.add_argument("file")
    sp.add_argument("--note", required=True, help="what is frozen and why (or why re-frozen)")

    sp = add("waive", cmd_flag("waiver", gates.WAIVABLE),
             "waive a check that doesn't apply, with the reason (human decision)")
    sp.add_argument("check", choices=gates.WAIVABLE)
    sp.add_argument("--note", required=True)

    sp = add("attest", cmd_flag("attestation", gates.ATTESTABLE),
             "record a human-judged gate: expert review seen, follow-up done")
    sp.add_argument("check", choices=gates.ATTESTABLE)
    sp.add_argument("--note", required=True, help="who, when, outcome, link")

    sp = add("funnel", cmd_funnel, "record or show funnel counts (real vs null run)")
    sp.add_argument("action", choices=("add", "show"))
    sp.add_argument("stage", nargs="?")
    sp.add_argument("--real", type=int)
    sp.add_argument("--null", type=int)
    sp.add_argument("--note")

    sp = add("novelty", cmd_novelty, "check catalogues and literature; write a dated novelty log")
    sp.add_argument("action", choices=("run", "sources"))
    sp.add_argument("--claim", help="claim id (file name in claims/ without .md)")
    sp.add_argument("--id", action="append", default=[], help="identifier, repeatable")
    sp.add_argument("--ra", type=float)
    sp.add_argument("--dec", type=float)
    sp.add_argument("--radius", type=float, default=30.0, help="arcsec (default 30)")
    sp.add_argument("--lat", type=float)
    sp.add_argument("--lon", type=float)
    sp.add_argument("--radius-km", type=float, default=100.0)
    sp.add_argument("--place", help="place or volcano name")
    sp.add_argument("--year-from", type=int)
    sp.add_argument("--year-to", type=int)
    sp.add_argument("--keyword", action="append", default=[])
    sp.add_argument("--domain", choices=DOMAINS)
    sp.add_argument("--source", action="append", default=[], help="only connectors matching this")
    sp.add_argument("--manual", action="append", default=[],
                    help="'Name|URL' of a source to check by hand, repeatable")

    sp = add("prereg", cmd_prereg, "freeze predictions with checksums; optional Zenodo draft")
    sp.add_argument("action", choices=("freeze", "verify", "zenodo"))
    sp.add_argument("files", nargs="*")
    sp.add_argument("--note")
    sp.add_argument("--manifest")
    sp.add_argument("--title")
    sp.add_argument("--creator", action="append", default=[])
    sp.add_argument("--description")
    sp.add_argument("--sandbox", action="store_true")

    sp = add("review", cmd_review, "prepare a fresh-context adversarial review pack")
    sp.add_argument("action", choices=("pack",))
    sp.add_argument("--reviewer", required=True, help="e.g. codex, fresh-claude, gemini")
    sp.add_argument("--claim", help="one-paragraph claim (default: built from claim cards)")

    sp = add("score-known", cmd_score_known, "recall of known answers in pipeline output")
    sp.add_argument("--known", required=True, help="CSV/JSON/JSONL of known answers")
    sp.add_argument("--found", required=True, help="CSV/JSON/JSONL of pipeline output")
    sp.add_argument("--key", required=True, help="column identifying an object or event")
    sp.add_argument("--value", help="numeric column to compare, e.g. period")
    sp.add_argument("--rel-tol", type=float, default=0.01)
    sp.add_argument("--aliases", default="1,0.5,2", help="accepted value multiples")
    sp.add_argument("--out", help="write result JSON here and record it as known-answer evidence")

    sp = add("judge-agreement", cmd_judge, "accuracy and kappa of a judge model against labels")
    sp.add_argument("--expected", required=True)
    sp.add_argument("--predicted", required=True)
    sp.add_argument("--id-col", default="id")
    sp.add_argument("--label-col", default="label")

    sp = add("dedupe", cmd_dedupe, "group reprints and near-duplicate passages")
    sp.add_argument("file", help="CSV/JSON/JSONL of passages")
    sp.add_argument("--text-col", default="text")
    sp.add_argument("--id-col")
    sp.add_argument("--threshold", type=float, default=0.5)

    sp = add("setup", cmd_setup, "install the skills and register the MCP server with an agent")
    sp.add_argument("--client", default="claude-code",
                    choices=("claude-code", "codex", "cursor", "gemini-cli", "other"))
    sp.add_argument("--skills-dir", help="copy skills here instead of the client's default")
    sp.add_argument("--yes", action="store_true", help="apply the plan (default: dry run)")

    add("mcp", cmd_mcp, "run the MCP server over stdio")
    return p


def _utf8_console() -> None:
    """Windows consoles default to cp1252; never crash on a non-ASCII catalogue name."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def main(argv: list[str] | None = None) -> int:
    _utf8_console()
    args = build_parser().parse_args(argv)
    if args.command == "funnel" and args.action == "add" and (args.stage is None or args.real is None):
        print("funnel add needs a stage name and --real", file=sys.stderr)
        return 2
    if args.command == "novelty" and args.action == "run" and not args.claim:
        print("novelty run needs --claim", file=sys.stderr)
        return 2
    try:
        return int(args.func(args) or 0)
    except (FileNotFoundError, FileExistsError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
