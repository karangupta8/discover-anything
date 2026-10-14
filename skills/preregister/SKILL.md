---
name: preregister
description: Freeze testable predictions before new data exists, so a candidate can pass or fail in public. Builds the predictions file (event times or values with uncertainties, tolerance, pass/fail/ambiguous rules), checksums it, and optionally prepares a Zenodo draft for a DOI. Use when a candidate will be re-observed (for example a TESS sector), or when the user asks how to make a claim falsifiable.
metadata:
  version: "1"
---

# Preregister

A DOI dated before the data turns "trust me" into "watch this". It needs no
credentials and is the strongest thing an amateur can do.

## Steps

1. **Find the next test.** When will new data cover the candidate? (For TESS:
   the observing schedule by sector; for a variable star: the next season; for
   a historical claim there is usually none: waive with a reason instead.)
2. **Compute predictions from frozen code.** Use only data available now. For
   periodic signals: predicted event times with 1σ uncertainties propagated
   from the ephemeris, and which fall inside the observing window. Save as
   `prereg/predictions.csv` from a script, and record the script's output with
   `discover record`.
3. **Write the rules before the data.** Fill
   `discover-anything/assets/templates/preregistration.md` as
   `prereg/PREREGISTRATION.md`: data product and detrending to be used, how each
   event is measured, the statistic and threshold, and the exact *pass*, *fail*
   and *ambiguous* outcomes, plus what will be said publicly in each case.
4. **Freeze:** `discover prereg freeze prereg/predictions.csv prereg/PREREGISTRATION.md --note "before Sector N"`.
   This writes a manifest with SHA-256 checksums and the git commit. Never edit
   these files again; outcomes go in new files.
5. **Get a DOI (the human publishes).** With `ZENODO_TOKEN` set:
   `discover prereg zenodo --manifest prereg/MANIFEST_....json --title "..." --creator "Name"`
   creates a draft with a reserved DOI. Publishing is the human's action on
   Zenodo; remind them it must happen before the observation starts.
6. **When the data arrives:** run the test exactly as written. Check
   `discover prereg verify` first. Publish the outcome either way, then the human
   runs `discover attest followup --note "<outcome, link>"`.

## If there is no future test

Historical and catalogue claims often can't be preregistered. Instead, write
down before contacting the specialist which catalogues were checked and what
would show the find is already known. Then ask the human to run
`discover waive prereg --note "<reason>"`.
