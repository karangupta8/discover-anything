# Agent Roles

How to split the work between the human and agents without fooling yourself.

## Division of labour

| Human | Agent |
|---|---|
| Picks the gap and the question | Reads papers and docs, summarises, finds tools and data |
| Decides thresholds from calibration numbers | Writes download, search, fit, vetting and plotting code |
| Decides what counts as a kill | Runs the pipeline, fills funnel tables |
| Looks at every plot or page scan of every candidate | Drafts claim cards, predictions, write-ups |
| Talks to people: experts, curators, telescope teams | Reviews other sessions' work adversarially |

## Session rules

1. **One script per step, numbered.** `01_targets.py`, `02_download.py`… Each
   reads the previous step's output from disk and can be re-run alone.
2. **Seeds and versions pinned.** Random seeds in every injection and null run;
   library versions in requirements; data product IDs logged.
3. **Ask for the funnel, not the winners.** "How many at each stage, and why was
   each rejected?" comes first; "show me the best" comes last.
4. **Make it argue against itself.** After each result: "List the five most
   likely reasons this is not real and the test that would distinguish each."
5. **Fresh context for review.** Reviews run in a new session or another model
   that sees only the repository and the review prompt, not the excitement.
6. **Long runs in resumable chunks.** Store per-target results so a crash
   doesn't cost a day.
7. **Hand off every session.** Update `HANDOFF.md`: where we are, what was
   learned, the next step.

## Roles

Run these as separate sessions or subagents, each with a narrow brief.

- **Librarian:** "Find every catalogue, paper, Zenodo record and GitHub repo
  that mentions <id> or position <ra, dec> within 30″ (or <place, date>). Return
  a dated table with how each source was searched."
- **Pipeline engineer:** builds and tests the numbered scripts.
- **Calibrator:** runs known-answer recovery, injection and null tests; reports
  rates with uncertainties.
- **Prosecutor:** runs [assets/templates/adversarial-review.md](../assets/templates/adversarial-review.md).
- **Explainer:** writes the plain-language guide for a curious 12-year-old. If
  it can't be explained simply, something in the analysis is unclear.

## Prompt starters

```
Before writing any code: list the data products available for <target class>,
their cadence or coverage, sizes and known systematics. Cite the documentation
page for each. Then propose the smallest sample that tests the pipeline end to end.
```

```
Write inject_and_recover.py: plant box transits at SNR 7, 8, 9, 10, 12, 15 into
200 random light curves from <sample>, run the identical search, and save a CSV
of injected vs recovered period, depth and SNR. Seed = 42. Do not change search.py.
```

```
Run the full pipeline on inverted light curves (flux -> 2*median - flux) for the
same stars. Report how many signals pass each stage, side by side with the real run.
```

```
Here is candidate <id>. Hide <season>. Fit using only the rest. Predict the
events in the hidden data with 1-sigma errors. Then, and only then, measure the
hidden data in those windows. Report the result even if it fails.
```

```
Before searching for anything new in <corpus>: list ten well-documented events
of the kind we are hunting that this corpus should contain. Run the pipeline and
report which it found, at which stage each missed one was lost, and why.
```

## Cost notes from 2026

- A $100/month agent plan was enough for a one-morning, 526-star planet search.
- A home GPU embedded 5.7 million archive passages overnight. A small judge
  model read 59,000 passages for about $3.
