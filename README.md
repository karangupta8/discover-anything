<div align="center">

# Discover Anything

### Point your coding agent at public data. Find what everyone missed. Then try hard to prove yourself wrong.

**An agent skill + toolkit for citizen science that experts can trust.**

[Quick start](#quick-start) · [How it works](#how-it-works) · [Domains](#what-you-can-hunt) · [FAQ](#faq)

</div>

---

In one week in October 2026, people with coding agents and no institutional
affiliation found transiting-planet candidates in NASA TESS data, a meteorite
fall that no catalogue records in an 1812 newspaper, and three Javan rhinoceroses
missing from the historical record in Dutch East India Company letters. The data
had been public for years. The rhinos have since been confirmed by the specialist
who maintains their record.

None of this needed a supercomputer. What it did need was discipline. The
credible hunters, working independently, converged on the same practices:

- recover known answers before trusting a search
- measure the false-alarm rate on data where the answer is "nothing"
- go back to the primary record: the pixels, the page scan
- check every catalogue the specialists use before saying "new"
- preregister predictions before the telescope looks again
- let a fresh mind attack the result, then ask a human expert

Discover Anything packages that discipline so any coding agent follows it,
whatever your field.

## Quick start

### 1. Give your agent the skill

The skill uses the open [Agent Skills](https://agentskills.io) format and works
with Claude Code, Codex, Cursor, Gemini CLI and other agents that load skills.

```bash
npx skills add karangupta8/discover-anything
```

Or copy [`skills/discover-anything/`](skills/discover-anything/) into your
agent's skills folder (for Claude Code: `~/.claude/skills/`).

### 2. Ask your agent

```text
Use discover-anything. I'd like to find new variable stars in recent TESS sectors.
Start a hunt folder and walk me through it.
```

```text
Use discover-anything to check this claimed find before I post it: <link or folder>.
```

```text
Use find-a-gap. I have a laptop and a weekend. Suggest three gaps in public data I could work on.
```

The agent creates a hunt folder, proposes a gap and the known answers to
calibrate on, and works through the gates with you. You make the calls that
matter: scope, thresholds, what counts as a kill, and anything that leaves
your machine.

### 3. Use the controls directly (optional)

```bash
pip install -e ".[dev]"
pytest
```

```python
from discover_anything.controls import invert_flux, injection_recovery, holdout_prediction

null_flux = invert_flux(flux)                      # every "dip" is now a false alarm
recall = injection_recovery(time, flux, depth=300e-6, n_trials=50,
                            period_range=(1, 10), duration=0.08, seed=42)
```

## How it works

```
0 Curiosity → 1 Gap → 2 Scope → 3 Calibrate → 4 Search → 5 Kill → 6 Novelty
  → 7 Preregister → 8 Report → 9 Follow-up
```

Each phase ends in a gate the agent must pass before moving on: *Did the
pipeline recover known answers blind? Is the funnel recorded for both the real
and the null run? Is there a dated novelty log?* The full loop is in
[`workflow.md`](skills/discover-anything/references/workflow.md).

Every result follows the evidence rules: numbers come from files a script
wrote, never from chat; every statement is labelled as an observation, an
inference or an unknown; controls run on exactly the same code as the search;
thresholds freeze before any candidate is seen.

The project has three layers ([architecture](docs/architecture.md)):

| Layer | What it is | Where |
|---|---|---|
| **Skill** | The method: phases, gates, evidence rules, vetting, domain packs | [`skills/discover-anything/`](skills/discover-anything/) |
| **Tools** | Tested controls now; CLI and MCP server for scaffolding, evidence ledger, novelty checks and preregistration on the [roadmap](docs/architecture.md#planned) | [`src/discover_anything/`](src/discover_anything/) |

## What you can hunt

| Domain | Examples | Pack |
|---|---|---|
| **Astronomy** | Planet candidates, variable stars, eclipsing binaries, asteroid rotation periods | [astronomy.md](skills/discover-anything/references/domains/astronomy.md) |
| **Historical archives** | Meteorite falls, volcanic eruptions, animal records, lost ships in digitised letters, newspapers and logbooks | [archives.md](skills/discover-anything/references/domains/archives.md) |
| **Your field** | Anything with public data, known answers to calibrate on, and a specialist who can confirm | Start with the core loop; your `LESSONS.md` becomes the next pack |

## Where the method came from

The rules come from public work in October 2026: three independent TESS planet
hunts ([origins](docs/origins/tess-planet-hunts.md)) and two investigations of
the Dutch East India Company archive ([origins](docs/origins/archive-finds.md)).

## FAQ

<details>
<summary><strong>Do I need to be a scientist?</strong></summary>

No. You need curiosity and the willingness to believe a control over your own
excitement. The skill walks you through each step and tells you which decisions
are yours. The `find-a-gap` skill suggests starting points sized for one person.

</details>

<details>
<summary><strong>Isn't this going to flood experts with junk?</strong></summary>

That is the problem it is designed to prevent. Nothing reaches an official
channel until it has passed known-answer recovery, a measured false-alarm rate,
a primary-record check, a dated novelty search, adversarial review, and a human
expert's eye. Most candidates die along the way, and the rejections are
published too.

</details>

<details>
<summary><strong>Can I say "AI discovered" it?</strong></summary>

No. Say what happened: "found with an AI coding agent, reviewed by a second
model and a fresh session". Say "candidate" until an expert or catalogue
accepts it. The [language table](skills/discover-anything/SKILL.md#language)
has the exact wording.

</details>

<details>
<summary><strong>What does it cost?</strong></summary>

A 526-star planet search ran in one morning on a $100/month agent plan. A home
GPU embedded 5.7 million archive passages overnight, and a small model read
59,000 of them for about $3. Start laptop-sized; scale only after the pipeline
is proven.

</details>

<details>
<summary><strong>Which agents work with it?</strong></summary>

Any agent that loads Agent Skills (Claude Code, Codex, Cursor, Gemini CLI and
others). Without skill support, point the agent at `skills/discover-anything/SKILL.md`
and ask it to follow it.

</details>

## Contributing

Contributions that make finding faster or more rigorous:

- **Novelty connectors** for catalogues in your field
- **Controls and vetting tests** for a data type
- **A domain pack** for a field you know: its traps, impostors, catalogues and
  channels

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Credits

Built on the public work of Pavel Rabtsevich, Eumemic and Paras Chopra (TESS),
and Benjamin Breen and Jesse Waites (historical archives). The archives method
draws on Waites's [Antiquity](https://github.com/jessewaites/antiquity). The
skill-plus-tools shape follows [REA](https://github.com/morluto/rea). Full
sources are in [docs/sources.md](docs/sources.md).

## License

[MIT](LICENSE)
