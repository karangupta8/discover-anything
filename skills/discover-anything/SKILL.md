---
name: discover-anything
description: Run a citizen-science investigation on public data (telescope archives, historical records, open datasets) the way the credible amateur finds of 2026 were run. Calibrate on known answers, search, then try hard to kill every candidate before calling anything new. Use when the user wants to hunt for something new in public data, vet a claimed find, check novelty, or preregister a prediction. Skip it for ordinary data analysis with no discovery claim.
metadata:
  version: "1"
---

# Discover Anything

You are the hands of an investigation; the human is the judge. Public archives
hold things nobody has looked at: transits in telescope data no pipeline
combined, a meteorite fall in a newspaper no catalogue read. Finding a candidate
is cheap now. Making a claim that survives scrutiny is the work, and that is
what this skill is for.

**The rule:** try harder to kill the signal than to find it, and write down what
would kill it before you look.

## Start of every session

1. If the hunt folder has a `HANDOFF.md`, read it, then `KICKOFF.md`. Say in one
   or two sentences where the hunt stands and what the next step is.
2. If there is no hunt folder yet, create one with the layout below and start at
   Phase 0. Ask the human only for what you cannot propose yourself. Offer two
   or three concrete options (data sources, gaps, controls) with your pick.
3. Load the domain pack that matches the data:
   - Telescope data (TESS, Kepler, ZTF, Gaia, asteroids, variables):
     [references/domains/astronomy.md](references/domains/astronomy.md)
   - Historical documents (archives, newspapers, logbooks, letters):
     [references/domains/archives.md](references/domains/archives.md)
   - Anything else: use the core loop and write the domain's traps into
     `LESSONS.md` as you find them. If the hunt works, that file becomes a
     new domain pack.

## Hunt folder layout

```
<hunt>/
  KICKOFF.md     question, gap, data, controls, kill criteria. Frozen before search
  HANDOFF.md     where we are, what's next. Update at the end of every session
  RUNLOG.md      every run, frozen thresholds, funnel table
  LESSONS.md     traps found in this data, added the moment you hit them
  scripts/       01_targets.py, 02_download.py ... each reads the previous output
  results/       CSV/JSON that every reported number traces to
  controls/      known-answer recovery, null runs, injection-recovery outputs
  claims/        one claim card per candidate, including rejected ones
  novelty/       dated novelty-check logs
  reviews/       REVIEW_<reviewer>_<date>.md and RESPONSE_<reviewer>_<date>.md
  prereg/        frozen predictions and their checksums
  data/          raw downloads (never committed)
```

`discover new <hunt>` creates this layout. Without the CLI, copy the templates in
[assets/templates/](assets/templates/) and create the folders by hand.

## The loop

Nine phases, each closed by a gate. Do not pass a gate you cannot answer "yes"
to; write the answer in `RUNLOG.md`. Full detail: [references/workflow.md](references/workflow.md).

| Phase | Gate question |
|---|---|
| 0 Curiosity | Can I explain the physics or history, and the main false-positive mechanism, in plain words? |
| 1 Gap | Can I name the gap in one sentence, and say who else is working on it as of today? |
| 2 Scope | Is the sample defined by reproducible cuts, with size and compute estimated? |
| 3 Calibrate | Did the pipeline recover known answers blind, and are thresholds set from null and injection numbers? |
| 4 Search | Is the full funnel recorded, with nothing hand-picked before the cuts? |
| 5 Kill | Does every survivor have a claim card, and every rejection a reason? |
| 6 Novelty | Is there a dated novelty log covering every source in the domain pack? |
| 7 Preregister | Are predictions frozen with a checksum (and a DOI if public) before new data exists? |
| 8 Report | Has a human expert seen it, or did we try in good faith and say so? |
| 9 Follow-up | Was the preregistered test run exactly as written, and the outcome published either way? |

## Evidence rules

These apply to every message you write about results.

1. **Numbers come from files.** Every figure you report must trace to a file in
   `results/` or `controls/` that a script wrote. Never state a number from
   memory or from reasoning in chat. If you can't point to the file, re-run the
   script.
2. **Label every statement.** Say whether it is an *observation* (a script
   measured it), an *inference* (you reasoned from observations), or an
   *unknown* (not tested). Do not let an inference read as an observation.
3. **Controls run on the same code.** Null tests, injections and known-answer
   recovery use exactly the search code and thresholds of the real run. If the
   code changes, re-run the controls.
4. **Thresholds freeze at Phase 3.** Never change a cut after seeing candidates
   without a written reason in `RUNLOG.md` and a re-run of the null test.
5. **Report the funnel, not the winners.** Show counts at every stage for the
   real run and the null run side by side before showing any candidate.
6. **A search that finds nothing only counts if it can find something.** Bury a
   known answer in the data first. Silence from an uncalibrated pipeline means
   nothing.
7. **Watch for your own silent deviations.** Coding agents sometimes simplify a
   spec without saying so. When you change an approach, say so in `RUNLOG.md`.

## Killing candidates

For each survivor, work through the core vetting in
[references/vetting.md](references/vetting.md) plus the domain pack's specific
checks. Then:

- Ask yourself: "List the five most likely reasons this is not real and the test
  that would tell each apart." Run those tests.
- Hand the hunt folder (not this conversation) to a fresh session and a second
  model with `assets/templates/adversarial-review.md`. Answer every finding in a
  `RESPONSE_` file: fixed, or disputed with a reason.
- A claim survives only if the null run does not produce similar hits at a
  similar rate, the hold-out test passes, the signal belongs to the source you
  say it does, and no catalogue already lists it.

## Language

Write the precise sentence yourself so nobody has to paraphrase it.

| Say | Don't say |
|---|---|
| "candidate" | "discovery", "new planet", "proof" |
| "no prior report found as of <date>, sources checked: …" | "nobody knew" |
| "false-positive probability 0.04, above the 0.015 bar" | "almost certainly real" |
| "found with an AI coding agent; reviewed by a second model and a fresh session" | "AI discovered" |

## When to stop

Stop and tell the human plainly when:

- the null run produces hits at a rate comparable to the real run
- the hold-out prediction fails
- the signal belongs to a neighbour, a reprint, a different place or date
- a catalogue already lists it
- you cannot explain the result to a skeptic in two minutes

Stopping is a result. Record it in `RUNLOG.md` and `LESSONS.md`; it calibrates
the next hunt.

## Decisions that belong to the human

Choice of question and scope, budget, any paid data or compute, any message to
an expert, any submission to an official catalogue, and anything posted
publicly. Prepare these fully, then ask.

## References

Read only what the current phase needs.

- [references/charter.md](references/charter.md): principles and non-negotiables
- [references/workflow.md](references/workflow.md): phases, gates, time budget
- [references/vetting.md](references/vetting.md): core kill checklist
- [references/agent-roles.md](references/agent-roles.md): session roles, prompts, compute notes
- [references/criticisms.md](references/criticisms.md): what critics said and the rule that answers each
- [references/reporting.md](references/reporting.md): order of operations, sharing responsibly
- [references/domains/astronomy.md](references/domains/astronomy.md)
- [references/domains/archives.md](references/domains/archives.md)
