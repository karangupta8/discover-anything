# Architecture

Discover Anything has two layers, skills and tools. Each covers what the other can't.

```
┌───────────────────────────────────────────────────────────────┐
│  Skill: SKILL.md + references (method, gates, evidence rules) │  tells the agent when and why
├───────────────────────────────────────────────────────────────┤
│  Tools: Python package → CLI + MCP server                     │  makes the rules checkable
└───────────────────────────────────────────────────────────────┘
          used by any coding agent: Claude Code, Codex, Cursor, Gemini CLI …
```

## Why a skill *and* tools

| | Instructions only (AGENTS.md / skill) | Tools only | Both |
|---|---|---|---|
| Agent knows the discipline | Yes | No: it gets functions, not judgement | Yes |
| Rules are enforced | No: "numbers come from files" is a request | Partly | Yes: the ledger and gate checker verify it |
| Works with zero install | Yes | No | Yes: the skill works alone, tools add rigour |
| Reproducible controls | Each hunt re-implements them | Yes | Yes |
| Easy to copy | Very | Moderately | Hardest: method and tools improve together |

Instructions alone can't check anything. An agent can say it ran a null test.
Tools alone don't teach the agent why the null test matters, or when to stop.
The skills hold the method; the tools hold the checks.

## Layer 1: the skill

`skills/discover-anything/` follows the open Agent Skills format: a `SKILL.md`
the agent loads on demand, plus references it reads only when a phase needs
them. Domain packs (`references/domains/*.md`) carry what changes between fields:
data sources, traps, impostor classes, novelty sources, official channels. The
core loop and evidence rules don't change.

A new domain starts as one hunt's `LESSONS.md` and becomes a pack once a hunt
in that domain has run end to end.

## Layer 2: the tools

A Python package (`discover-anything`), because the scientific ecosystem
(astropy, lightkurve, astroquery, numpy) lives there. It exposes the same
operations as a CLI (`discover …`) and as an MCP server, so any agent can call
them and a human can run them by hand.

### Available now

| Module | Operation | Control |
|---|---|---|
| `controls` | `invert_flux` | Null test: dips become bumps |
| `controls` | `inject_box_transit`, `injection_recovery` | Plant synthetic signals; measure recall at a strength |
| `controls` | `holdout_prediction` | Fit on visible data; predict and measure the hidden part |
| `controls` | `bls_search`, `period_grid` | Minimal search used by the controls, with a grid-size guard |

### Planned

| Operation | What it does | Why it matters |
|---|---|---|
| `discover new <hunt>` | Scaffold a hunt folder from `templates/` | Every hunt starts with the gates in place |
| `discover status` | Read the hunt folder; report which gates pass and what is missing | Turns the workflow into a checklist the agent can't skip |
| Evidence ledger: `record`, `cite` | Each result file registered with hash, script, commit, time → evidence ID | Makes "numbers come from files" checkable |
| `discover check-claims <file>` | Flag numbers in a write-up with no evidence ID | Catches stated-but-not-computed numbers before review |
| `funnel` | Record stage counts for real and null runs; render the side-by-side table | The table every credible write-up needs |
| `known_answer_recovery` | Score recall on a list of known answers for any pipeline output | Domain-neutral "buried wristwatch" |
| `shuffle_time` | Time-shuffled null for periodicity searches | Null test for Lomb–Scargle style searches |
| Novelty connectors | SIMBAD, VSX, ExoFOP, NASA Exoplanet Archive, Gaia, ADS, arXiv, Zenodo, GitHub; Meteoritical Bulletin, Smithsonian GVP | One call → a dated novelty-log row per source |
| `prereg freeze` | Hash predictions and code, record commit, prepare a Zenodo draft | Preregistration in one step; the human publishes |
| `review pack` | Bundle the hunt folder and the adversarial prompt for a second model | Fresh-context review without the conversation |
| `judge calibrate` (archives) | Run a judge prompt on its labelled set; report agreement | Detects drift when a prompt or model changes |
| `setup` | Register the MCP server and install the skill into supported agents | One-command start |

### Tool design rules

- Every operation returns data plus the evidence behind it: inputs, file
  hashes, versions, and stated limitations.
- No operation hides a negative result. Controls report failures as prominently
  as successes.
- Operations never modify their inputs; they write new files.
- Anything that leaves the machine (submissions, posts, emails) is prepared by
  tools and sent only by the human.

## Relation to other projects

- **[REA](https://github.com/morluto/rea)** showed that an MCP server plus a
  bundled agent skill is the right shape for agent tooling. Discover Anything
  applies that shape to citizen science.
- **[Antiquity](https://github.com/jessewaites/antiquity)** scaffolds workspaces
  for historical investigations. The archives domain pack builds on its method.
  Use it directly for archive work if you prefer a dedicated workspace.
- **[Scientific Agent Skills](https://github.com/K-Dense-AI/scientific-agent-skills)**
  gives agents broad scientific tooling (databases, analysis libraries) for
  professional research. Discover Anything is narrower and complementary: the
  discipline for turning public data into a claim experts can trust. The two
  can be installed together.
