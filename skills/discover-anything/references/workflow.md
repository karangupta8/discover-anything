# Workflow

Nine phases. Each ends in a gate: a question you must be able to answer "yes" to
before moving on. Write the answer in `RUNLOG.md` ([assets/templates/run-log.md](../assets/templates/run-log.md)).

```
0 Curiosity → 1 Gap → 2 Scope → 3 Calibrate → 4 Search → 5 Kill → 6 Novelty
  → 7 Preregister → 8 Report → 9 Follow-up
```

---

## Phase 0: Curiosity

Read around the topic for an hour. What do professionals currently do, what do
they say is missing, what is the data, how big is it.

**Agent:** summarise recent papers on the topic and list their "open problems"
and "limitations" sections. Check what you say against the papers themselves.

**Gate:** can I explain the basic physics or history, and the main
false-positive mechanism, in plain words?

## Phase 1: Find the gap

Name the coverage gap in one sentence. Gaps that worked in 2026:

- "The multi-sector planet search stops at Sector 96; later sectors are not yet
  combined with older data." (TESS)
- "Stars observed only in full-frame images never get a multi-sector search." (TESS)
- "Threshold-crossing events that never became TOIs are never followed up." (TESS)
- "Pipelines ignore single transits." (long-period planets)
- "The archive has been transcribed, but nobody has read it for meteorite falls."
  (Dutch East India Company papers)

**Gate:** have I searched for anyone already filling this gap in the last six
months (papers, GitHub, Zenodo, social posts)? Write down who, and how this angle
differs.

## Phase 2: Scope

Fill in `KICKOFF.md` ([assets/templates/project-kickoff.md](../assets/templates/project-kickoff.md)).
Pick a sample small enough to run on one machine first (one 2026 hunt: 526
stars, 440 MB, 1.5 to 3 hours on 12 cores). Scale only after the pipeline is
proven.

**Gate:** sample defined by explicit, reproducible cuts; data size and compute
estimated; success and failure criteria written.

## Phase 3: Calibrate (before hunting)

1. **Known-answer recovery.** Run on targets with known answers (published
   planets, catalogued variables, famous recorded events). Recover them blind.
2. **Injection-recovery.** Plant synthetic signals across the strength grid.
   Record the recovery fraction at each level
   (`discover_anything.controls.injection_recovery`).
3. **Null run.** The same pipeline on data that cannot contain the target:
   inverted or shuffled light curves (`discover_anything.controls.invert_flux`),
   or a corpus slice from the wrong period or place. Count every hit that
   passes your cuts.
4. Set thresholds from 1 to 3, not from intuition. One 2026 hunt found that half
   of the clean signals below MES 10 were expected false alarms, and raised the
   bar.

**Gate:** known answers recovered; null false-alarm rate small compared with
expected real yield; thresholds justified by numbers and frozen in `RUNLOG.md`.

## Phase 4: Search

Run the calibrated pipeline. Keep everything, not only the winners. Record the
funnel counts at every stage. That table is the heart of every credible write-up.

**Gate:** funnel table filled; nothing hand-picked before the cuts.

## Phase 5: Kill every survivor

Run [vetting.md](vetting.md) and the domain pack's checks per candidate. Then
adversarial review: a fresh session and a second model with
[assets/templates/adversarial-review.md](../assets/templates/adversarial-review.md).

**Gate:** every survivor has a claim card; every rejection has a reason.

## Phase 6: Novelty

Search every novelty source in the domain pack, by identifier and by position
(coordinates, or place and date). Log the date checked. Include recent hobbyist
postings. In October 2026 several people found the same planet signals within
days of each other.

**Gate:** novelty log written; credit given to anyone who got there first.

## Phase 7: Preregister

Where a future observation can test the claim, fill in
[assets/templates/preregistration.md](../assets/templates/preregistration.md) and publish to
Zenodo for a DOI **before** that observation. Include predicted values with
uncertainties, the tolerance, and explicit pass, fail and ambiguous outcomes.

For historical claims there is no future observation. The equivalent is to
write down, before contacting the specialist, exactly which catalogues were
checked and what result would show the find is already known.

**Gate:** DOI or frozen file with checksum exists, dated before the data.

## Phase 8: Report

- Write-up with funnel, controls, caveats, and the charter's language
- Public repository: code, claim cards, reviews and responses
- Ask a human expert (forums, direct email, the relevant citizen-science team)
- Then, if warranted, the official channel in the domain pack

**Gate:** a human expert has seen it, or we tried in good faith and say so.

## Phase 9: Follow-up

When new data arrives, run the preregistered test exactly as written. Publish
the outcome whether it passes or fails. Add what you learned to `LESSONS.md`.

**Gate:** outcome posted under the same DOI or repository, including failures.

---

## Time budget (rule of thumb)

| Phase | Share |
|---|---|
| 0 to 2: curiosity, gap, scope | 15% |
| 3: calibrate | 20% |
| 4: search | 10% |
| 5 and 6: kill, novelty | 40% |
| 7 to 9: preregister, report, follow up | 15% |
