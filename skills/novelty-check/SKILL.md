---
name: novelty-check
description: Check whether an object or event is already known before anyone calls it new. Queries astronomy catalogues (SIMBAD, VSX, Gaia DR3, TESS EB, APOGEE binaries, NASA Exoplanet Archive, ExoFOP), literature (arXiv, ADS, Zenodo, GitHub) and historical catalogues (Smithsonian GVP), and writes a dated novelty log. Use when the user asks "has anyone found this?", "is this new?", or before any post or submission.
metadata:
  version: "1"
---

# Novelty Check

"Not on the obvious list" is not "unknown". In October 2026, 2 of one hunter's
first 12 "new" planet signals were already published, and others had been posted
by hobbyists days earlier. This skill makes the check systematic and dated.

## Steps

1. **Gather every alias.** Names differ across catalogues. For a star: TIC,
   Gaia DR3, HIP, 2MASS, TOI, GJ, common names, plus RA/Dec. For a historical
   event: place names as written then and now, the date in both calendars where
   relevant, and nearby landmarks (volcano names, towns).
2. **Run the automated check** (inside a hunt folder):

   ```bash
   discover novelty run --claim TIC-4206066 --id "TIC 4206066" --id "Gaia DR3 ..." \
       --ra 123.456 --dec -12.345 --radius 30
   discover novelty run --claim gamkonora-1722 --place Gamkonora --year-from 1700 --year-to 1750 \
       --manual "Meteoritical Bulletin|https://www.lpi.usra.edu/meteor/"
   ```

   Or the MCP tool `novelty_check`. List sources with `discover novelty sources`.
   Set `ADS_API_TOKEN` for full-text ADS and `GITHUB_TOKEN` for higher GitHub limits.
3. **Read every `found` row.** A record is not automatically "already known":
   the star itself appearing in SIMBAD is expected. What matters is whether the
   *signal or event* is recorded (a TOI or CTOI, a VSX entry with a matching
   period, a paper discussing the same signal, an eruption with the same date).
4. **Finish the `not-checked` and `manual` rows by hand** and add the result
   to the log. They are listed under "Not yet checked".
5. **Check what the tool can't:** social posts and forums by every alias (last
   month), and the domain pack's list of recent catalogues.
6. **Write the conclusion** in the log in the charter's language: "no prior
   report found as of <date> in: …" or "already known: <where>". Credit anyone
   who got there first.

## Without the CLI

Search the same sources by hand and fill
`discover-anything/assets/templates/novelty-log.md`, one row per source, with the
date and how each was searched (index, full read, API).
