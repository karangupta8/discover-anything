# Architecture

Two layers. Skills hold the method; tools hold the checks.

```
┌──────────────────────────────────────────────────────────────────┐
│  Skills: discover-anything · find-a-gap · vet-a-claim ·          │  tell the agent what to do,
│          novelty-check · preregister  (+ domain packs)           │  when, and why
├──────────────────────────────────────────────────────────────────┤
│  Tools: Python package → `discover` CLI + MCP server             │  make the rules checkable
│         ledger · gates · claims · funnel · novelty · prereg ·    │
│         review · controls · vetting · calibration · textmatch    │
└──────────────────────────────────────────────────────────────────┘
        used by any coding agent: Claude Code, Codex, Cursor, Gemini CLI …
```

## Why both

| | Instructions only | Tools only | Both |
|---|---|---|---|
| Agent knows the discipline | Yes | No: functions, not judgement | Yes |
| Rules are enforced | No: "numbers come from files" is a request | Partly | Yes: ledger, gates, claim checker |
| Works with zero install | Yes | No | Yes: skills work alone, tools add checks |
| Reproducible controls | Re-implemented per hunt | Yes | Yes |

## The ledger

`.discover/ledger.jsonl` in each hunt is append-only. Every entry has an ID
(`E-001`…), a kind, a UTC time, the git commit, and for file-backed entries the
path, size and SHA-256.

| Kind | Written by | Used by |
|---|---|---|
| `evidence` | `discover record` (tags: known-answer, null, injection, search, …) | gates 3–4, `check-claims` |
| `frozen` | `discover freeze` | gate 3: changes after freezing fail until re-frozen and a new null test is recorded |
| `funnel` | `discover funnel add` | gate 4, funnel table and warnings |
| `novelty` | `discover novelty run` | gate 6 |
| `prereg` | `discover prereg freeze` | gate 7: any frozen file changed fails |
| `review` | `discover review pack` | audit trail |
| `waiver` | `discover waive` (human) | lets a check not apply, with a reason |
| `attestation` | `discover attest` (human) | gates 8–9: expert review seen, follow-up done |

Corrections are new entries; nothing is edited or deleted. Each line stores the SHA-256 of the previous line, so an edited or deleted line breaks the chain and shows up in `discover status`. Changed or missing evidence files block "All gates passed".

## Gates

`discover status` evaluates the nine gates from files and the ledger:

| Gate | Passes when |
|---|---|
| 0 Curiosity | KICKOFF question filled |
| 1 Gap | gap, who else, how this differs filled |
| 2 Scope | data, sample cuts, size, known answers, null test, kill and stop criteria filled |
| 3 Calibrate | intact, non-empty known-answer, null and injection evidence (or injection waived); settings frozen and unchanged |
| 4 Search | search evidence; ≥ 2 funnel stages with null counts; no funnel warnings (e.g. null ≥ half of real) unless waived |
| 5 Kill | claim cards with real statuses; filled reviews each with a filled response |
| 6 Novelty | a ledger-recorded novelty log per live claim that checked ≥ 1 catalogue, with no unfinished sources unless waived (all rejected = pass: stopping is a result) |
| 7 Preregister | intact frozen manifest, or waived with a reason |
| 8 Report | human attestation: an expert has seen it |
| 9 Follow-up | human attestation of the preregistered test's outcome |

## Novelty connectors

Each connector returns `found`, `none`, `not-checked` (with the error) or
`manual`. It never reports "none" for a query that didn't run, and never
decides novelty: a star appearing in SIMBAD is expected; a TOI on it is not.
The person reads every `found` row.

New connectors implement `applies(target)` and `query(target, http)` (see
`src/discover_anything/novelty/base.py`) and are tested with a fake HTTP
client.

## Design rules

- Every operation returns data plus its evidence: inputs, hashes, versions,
  limitations.
- No operation hides a negative result.
- Operations never modify their inputs; they write new files.
- Anything that leaves the machine or represents a human judgement is CLI-only
  and done by the human.

## Relation to other projects

- **[REA](https://github.com/morluto/rea)** showed that an MCP server plus a
  bundled agent skill is the right shape for agent tooling.
- **[Antiquity](https://github.com/jessewaites/antiquity)** scaffolds workspaces
  for historical investigations; the archives domain pack builds on its method.
- **[Scientific Agent Skills](https://github.com/K-Dense-AI/scientific-agent-skills)**
  gives agents broad scientific tooling. Discover Anything is narrower and
  complementary: the gates between a result and a discovery claim.
