<div align="center">

# Discover Anything

### Point your coding agent at public data. Find what everyone missed. Then try hard to prove yourself wrong.

**Agent skills + a CLI + an MCP server that turn "AI found something" into a claim experts can check.**

[Quick start](#quick-start) · [What the tools enforce](#what-the-tools-enforce) · [Skills](#skills) · [Domains](#what-you-can-hunt) · [FAQ](#faq)

</div>

---

In one week in October 2026, people with coding agents and no institutional
affiliation found transiting-planet candidates in NASA TESS data, a meteorite
fall that no catalogue records in an 1812 newspaper, and three Javan
rhinoceroses missing from the historical record in Dutch East India Company
letters. The data had been public for years.

Finding a candidate is now cheap. The first question every expert asked was
the same: **"How are you ruling out known objects, noise and impostors?"** The
credible hunters answered with the same practices, worked out independently:
recover known answers first, measure the false-alarm rate, check the primary
record, search every catalogue, preregister, and let a fresh mind attack the
result.

Discover Anything packages that discipline so any coding agent follows it, and
**checks** that it did, instead of taking the agent's word for it.

## Quick start

```bash
pip install "discover-anything[mcp] @ git+https://github.com/karangupta8/discover-anything"
discover setup --yes          # installs the skills and registers the MCP server (Claude Code)
```

Skills only, for any agent that supports the open [Agent Skills](https://agentskills.io) format:

```bash
npx skills add karangupta8/discover-anything
```

Then ask your agent:

```text
Use find-a-gap. I have a laptop and a weekend. Suggest three gaps in public data I could work on.
```

```text
Use discover-anything to start a hunt for new variable stars in recent TESS sectors.
```

```text
Use vet-a-claim on this before I post it: <link or folder>
```

## What the tools enforce

Every hunt gets a folder and an append-only **evidence ledger**. The agent works;
the tools keep score.

```console
$ discover new tess-variables --domain astronomy
$ discover status
[    PASS] 0 Curiosity
[    PASS] 1 Gap
[    PASS] 2 Scope
[    FAIL] 3 Calibrate
             no 'null' evidence: run the pipeline on inverted or shuffled data, then `discover record <file> --tag null`
             no 'injection' evidence: plant synthetic signals and record the recovery with `--tag injection` (or the human waives it with a reason)
             frozen settings settings.yml changed since freezing; re-freeze with a reason and re-run the null test
             1 evidence entries tagged 'known-answer'
[    FAIL] 4 Search
...
Next: no 'null' evidence: run the pipeline on inverted or shuffled data, then `discover record <file> --tag null`
```

And the novelty check, run on the October 2026 planet candidate TIC 4206066:

```console
$ discover novelty run --claim TIC-4206066 --id "TIC 4206066" --ra 80.859827 --dec -1.326974
E-001  wrote novelty/TIC-4206066_2026-10-14T143012Z.md
  found: 4, none: 9, not-checked: 1, manual: 0, n/a: 0
  [found] SIMBAD (identifier): 1 record(s)            ← listed as StKM 1-561
  [found] SIMBAD (cone): 1 record(s)
  [not-checked] NASA ADS: ADS_API_TOKEN is not set
  [found] Zenodo (preprints, data, predictions): 5 record(s)
  [found] GitHub repositories (hobbyist postings): 1 record(s)   ← someone else's verification repo
```

| Rule | How it's checked |
|---|---|
| **Numbers come from files** | `discover record` hashes each result file and returns an ID; `discover check-claims WRITEUP.md` flags every number with no `[E-012]` citation, and every citation whose file changed |
| **Calibrate before searching** | Gate 3 needs evidence tagged `known-answer`, `null` and `injection` (or a human waiver with a reason) |
| **No moving the goalposts** | `discover freeze settings.yml`; editing it later fails the gate until it is re-frozen *and* a new null test is recorded |
| **Show the funnel** | `discover funnel add` records real vs null counts per stage, and warns when the null run yields as much as the real run |
| **Is it new?** | `discover novelty run` queries 15 sources and writes a dated log. A source that can't be reached is reported as *not checked*, never as "no match" |
| **Fresh-eyes review** | `discover review pack --reviewer codex` builds a prompt and file list for a second model; empty review stubs don't pass the gate |
| **Preregister** | `discover prereg freeze` checksums predictions; a changed file fails the gate. `discover prereg zenodo` creates a draft with a reserved DOI and never publishes it for you |
| **Humans make the human calls** | Waivers and attestations ("an expert has seen it") are CLI-only and are not exposed to agents over MCP |

### Novelty sources

| Astronomy | Literature and hobbyists | Historical |
|---|---|---|
| SIMBAD (identifier and cone) · AAVSO VSX · TESS eclipsing binaries (Prša+ 2022) · Gaia DR3 variability · Gaia DR3 non-single stars · APOGEE binaries · NASA Exoplanet Archive (planets, TOIs) · ExoFOP-TESS | arXiv · NASA ADS (token) · Zenodo · GitHub | Smithsonian Global Volcanism Program · Meteoritical Bulletin (manual) · any source you add with `--manual` |

### Also included

- **Controls:** inverted and time-shuffled nulls, block shuffle for red noise, box-transit injection-recovery, hold-out prediction, known-answer scoring with period aliases
- **Vetting:** odd/even depths, secondary eclipse, per-season depth consistency, single-event dominance, known systematic periods, Lomb-Scargle with false-alarm probability
- **Archives:** reprint grouping (so one story printed in ten papers counts once), judge-model agreement (accuracy, kappa, confusions) before a cheap model filters a corpus

## Skills

| Skill | Use it to |
|---|---|
| [`discover-anything`](skills/discover-anything/SKILL.md) | Run a hunt end to end: nine phases with gates, evidence rules, domain packs |
| [`find-a-gap`](skills/find-a-gap/SKILL.md) | Choose what to look for: gaps sized for one person, with known answers to calibrate on |
| [`vet-a-claim`](skills/vet-a-claim/SKILL.md) | Stress-test your own or someone else's find before it is posted or believed |
| [`novelty-check`](skills/novelty-check/SKILL.md) | Answer "has anyone found this already?" systematically, with a dated log |
| [`preregister`](skills/preregister/SKILL.md) | Make a candidate falsifiable before the telescope looks again |

## What you can hunt

| Domain | Examples | Pack |
|---|---|---|
| **Astronomy** | Planet candidates, variable stars, eclipsing binaries, asteroid rotation periods | [astronomy.md](skills/discover-anything/references/domains/astronomy.md) |
| **Historical archives** | Meteorite falls, volcanic eruptions, animal records, lost ships in digitised letters, newspapers and logbooks | [archives.md](skills/discover-anything/references/domains/archives.md) |
| **Your field** | Anything with public data, known answers to calibrate on, and a specialist who can confirm | Core loop; your `LESSONS.md` becomes the next pack |

## How it fits with other tools

[Scientific Agent Skills](https://github.com/K-Dense-AI/scientific-agent-skills)
gives agents broad scientific capability: libraries, databases, analysis and
writing, mostly for professional life-science work. Discover Anything is
narrower: the discipline for turning public data into a **discovery claim**,
with checks the agent can't skip. Use both: their skills for the analysis,
these gates for the claim.

## FAQ

<details>
<summary><strong>Do I need to be a scientist?</strong></summary>

No. You need curiosity and the willingness to believe a control over your own
excitement. `discover status` always tells you the next step, and the skills
say which decisions are yours.

</details>

<details>
<summary><strong>Isn't this going to flood experts with junk?</strong></summary>

It is designed to do the opposite. Nothing reaches an official channel until it
has passed known-answer recovery, a measured false-alarm rate, a primary-record
check, a dated novelty search, adversarial review and a human expert's eye. Most
candidates die on the way, and the rejections are kept.

</details>

<details>
<summary><strong>Can I say "AI discovered" it?</strong></summary>

No. Say "found with an AI coding agent, reviewed by a second model and a fresh
session". Say "candidate" until an expert or catalogue accepts it.

</details>

<details>
<summary><strong>Can't the agent just fake the checks?</strong></summary>

It can write a file called `null.json`. It can't make that file match a hash
recorded before the threshold changed, pass `check-claims` with uncited
numbers, or attest that an expert reviewed it. The tools make shortcuts
visible; the human still reads every plot.

</details>

<details>
<summary><strong>What does it cost?</strong></summary>

The tools are free and run locally. In 2026, a 526-star planet search ran in one
morning on a $100/month agent plan, and a small model read 59,000 archive
passages for about $3.

</details>

## Where the method came from

Public work from October 2026: three independent TESS planet hunts
([origins](docs/origins/tess-planet-hunts.md)) and two investigations of the
Dutch East India Company archive ([origins](docs/origins/archive-finds.md)).
Credit to Pavel Rabtsevich, Eumemic and Paras Chopra (TESS), and Benjamin Breen
and Jesse Waites (archives; see Waites's [Antiquity](https://github.com/jessewaites/antiquity)).
The skills-plus-tools shape follows [REA](https://github.com/morluto/rea).
Sources: [docs/sources.md](docs/sources.md).

## Contributing

Most wanted: novelty connectors for catalogues in your field, controls and
vetting tests for a data type, and domain packs. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
