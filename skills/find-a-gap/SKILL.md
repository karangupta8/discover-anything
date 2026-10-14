---
name: find-a-gap
description: Help someone choose what to look for in public data. Propose concrete coverage gaps (data nobody has combined, searched, or read for a given question) sized for one person and a coding agent, each with known answers to calibrate on and the specialist who could confirm a find. Use when the user wants to find something new but has no target yet, or asks "what could I discover with an agent?". Hand off to discover-anything once a gap is chosen.
metadata:
  version: "1"
---

# Find a Gap

Every credible amateur find in 2026 started from a real coverage gap, not a
clever trick. Your job is to propose gaps worth the user's time and to be
honest about which are already crowded.

## Steps

1. **Ask only what changes the answer:** time available (a weekend, a month),
   compute (laptop, GPU, cloud budget), interests (sky, history, nature, other),
   and any skill they already have (a language, a domain). Offer defaults.
2. **Propose three gaps** using the patterns below and
   [references/starting-points.md](references/starting-points.md). For each give:
   - the gap in one sentence, and why professionals haven't filled it
   - the public data and its size
   - **known answers** the pipeline can be calibrated on (no known answers, no hunt)
   - the impostors that usually fake a find there
   - who confirms a find (catalogue, curator, telescope team) and how long that takes
   - effort, and your honest estimate of the chance of an accepted result
3. **Check the gap is still open today.** Search papers (arXiv, ADS), GitHub,
   Zenodo and recent social posts for anyone working on it in the last six
   months. Report who and when. Gaps closed within days in October 2026.
4. **Recommend one** and say why. Prefer gaps whose output is complete without
   someone else's telescope night (catalogue entries, measurements), and where
   the confirming specialist is reachable.
5. When the user chooses, hand off: "Use discover-anything to start a hunt on
   <gap>", carrying over the known answers and impostors you listed.

## Gap patterns that worked

| Pattern | Example |
|---|---|
| **New data not yet combined with old** | TESS sectors after the last multi-sector pipeline run |
| **Objects outside a pipeline's selection** | Stars seen only in full-frame images; too bright for ground surveys |
| **Signal types pipelines ignore** | Single transits; non-eclipsing variables; asteroid rotation |
| **Candidates nobody followed up** | Threshold-crossing events that never became TOIs |
| **Archives transcribed but never read for X** | Colonial letters read for meteorites, eruptions, animals |
| **Corpora in under-searched languages** | Non-English newspapers and colonial presses |
| **Cross-matching two catalogues nobody joined** | One mission's known binaries used to predict where to look in another's data |
| **Re-testing published predictions** | Preregistered predictions whose test data has just arrived |

## Red flags

Say so plainly when a gap has one of these:

- no known answers in the same data to calibrate on
- the obvious version was posted widely in the last weeks
- credit structurally goes to surveys (for example archival asteroid discovery)
- confirmation needs scarce resources (telescope nights) for a weak signal
- the user would need data or compute they said they don't have
