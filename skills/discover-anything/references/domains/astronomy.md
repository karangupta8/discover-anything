# Domain Pack: Astronomy

For hunts in public telescope data: transiting planets, variable stars and
eclipsing binaries, asteroid light curves. Built from the October 2026 TESS
planet hunts (background: `docs/origins/tess-planet-hunts.md`). Check each channel's current rules before
submitting; the notes were gathered in October 2026.

## Data and compute

- **TESS light curves:** SPOC (NASA, 2-min and brighter FFI stars) and QLP (MIT,
  FFI stars to T ≈ 13.5), via MAST or the STScI open-data S3 bucket (about 20×
  faster than MAST from inside AWS us-east-1).
- **Laptop scale:** hundreds of stars, under 1 GB, hours.
- **10k-star scale:** about 130 GB transferred, 12 GB stored.
- **Millions of stars:** cloud. AWS Graviton was 2.6× faster than Intel per vCPU
  in one 2026 hunt.
- Download in processes, not threads (Python GIL): 3× in one hunt.
- TRICERATOPS needs its own Python 3.11 environment.

## Traps

- **Period grids explode on long baselines.** A fully coherent BLS grid scales
  with baseline × period range. Three sectors a year apart at 0.8 to 10 days asks
  for tens of millions of trial periods. Use semi-coherent (per-season sums) or
  stack-slide searches for multi-year data, or a narrow range around a known
  candidate. `discover_anything.controls.period_grid` refuses grids over 2 million
  points for this reason.
- **TESS pixels are 21″ wide.** In full-frame images, most shallow signals come
  from blended eclipsing binaries on neighbouring stars. Pixel checks rejected
  93% of signals that had passed 17 automated vetting tests in one full-sky search.
- **TRICERATOPS cannot recognise noise.** It passed 5 of 24 inverted false alarms
  in one hunt. It only answers "planet versus astrophysical impostor".
- **Red noise lowers measured SNR.** One hunt recovered only 57 to 62% of planted
  transits at nominal SNR 10.
- **Known systematic periods:** the 13.7-day spacecraft orbit, momentum dumps,
  1-day aliases, stellar rotation harmonics.
- **Novelty is a moving target.** The obvious gap was crowded within 72 hours of
  the first viral post.

## Vetting additions (transits)

Under the core headings in [../vetting.md](../vetting.md):

**A. Real**
- [ ] **must** At least 3 events; no single event dominates
- [ ] **must** Depth consistent across seasons (χ²/dof ≤ 5 was used in one hunt)
- [ ] **must** Null-run fraction at this SNR/MES (one hunt: below MES 10, about
      half of clean signals were expected false alarms)
- [ ] **should** Present in both SPOC and QLP / TESS-SPOC reductions

**B. On target**
- [ ] **must** Difference-image centroid within the limit (LEO-Vetter uses 15″)
- [ ] **must** No catalogued neighbour bright enough to produce the depth as a
      fully eclipsing binary, or that neighbour excluded by the centroid
- [ ] **should** Centroid test calibrated on known planets for similar stars
      (one hunt's wrongly rejected 2 to 3%; an uncalibrated neighbour check
      would have rejected 31%)
- Companions closer than about 1 to 2″ need high-resolution imaging, which is
  why the end state is "candidate".

**C. Planet, not binary**
- [ ] **must** Odd and even depths agree; no secondary eclipse
- [ ] **must** Not in the TESS EB catalogue (Prša et al. 2022) or VSX
- [ ] **must** Not a spectroscopic binary (APOGEE, Kounkel et al. 2021)
- [ ] **must** Gaia DR3 RUWE ≤ 1.4 and no non-single-star orbit, or flagged
- [ ] **should** Not grazing (b < 0.9); radius < 20 R⊕; duration consistent
      with stellar density
- [ ] **should** TRICERATOPS FPP and NFPP computed (averaged over 10 runs)
- Two 2026 candidates passed every automated test and were still binaries,
  caught only by catalogues. Catalogue checks are not optional.

## Vetting additions (variable stars)

- [ ] **must** Null tests: inverted light curves for eclipse searches;
      time-shuffled light curves for Lomb-Scargle (destroys periodicity, keeps
      noise)
- [ ] **must** Variable pinned to one star within a few arcseconds (VSX needs
      this): difference images, Gaia epoch photometry, or ASAS-SN / ZTF for
      fainter neighbours
- [ ] **must** Not catalogued anywhere, including Gaia DR3 vari_summary with a
      compatible period
- [ ] **should** Classified into a VSX type with the evidence for it (period,
      amplitude, shape, eclipse widths)

## Novelty sources

Search each by **ID** and by **coordinates** (≥ 30″ radius). Log the date.

**Planets**
- [ ] ExoFOP target page (TOIs, CTOIs, notes); full TOI and CTOI lists
- [ ] NASA Exoplanet Archive (confirmed planets, TOI table)
- [ ] SPOC TCE tables (all public multi-sector runs)
- [ ] ExoMiner++ classified TCEs (Valizadegan et al. 2025, 2026)
- [ ] Princeton ML survey candidates (11,554)
- [ ] RAVEN (Lafarga et al. 2026), T16 (Roth et al. 2026), LEO-Vetter M-dwarf
      candidates (Kunimoto et al. 2025), Eschen et al. 2024, Tschudi 2026
- [ ] Planet Hunters TESS CTOIs

**Binaries and variables**
- [ ] VSX; TESS EB catalogue (Prša et al. 2022); TESS Ten Thousand Catalog
      (Kostov et al. 2025, Sectors 1 to 82)
- [ ] Gaia DR3 variability and non-single-star tables; RUWE
- [ ] APOGEE spectroscopic binaries (Kounkel et al. 2021); SIMBAD

**Literature and hobbyists**
- [ ] NASA ADS and arXiv full text by ID and common names
- [ ] Zenodo and GitHub by ID (last 3 months); social posts by ID (last month)
- [ ] Web search by every alias (TIC, HIP, Gaia DR3, 2MASS, LSPM, GJ)

## Where results go

| Object | Channel | Notes |
|---|---|---|
| Transiting planet candidate | ExoFOP-TESS CTOI | Needs an account. Policy expects public submissions to be "suitably validated and verified". The TOI team may promote it. |
| Variable star or eclipsing binary | AAVSO VSX | Moderated, amateur submissions accepted. Needs period, type, amplitude, light curve. Discoverer credit for TESS-only finds is contested: ask the moderators first. |
| New asteroid or comet | Minor Planet Center | Credit goes to the earliest observation in the opposition, usually a survey's. Archival finds rarely earn credit. |
| Asteroid rotation period | Minor Planet Bulletin + Lightcurve Database | Long tradition of amateur papers. |
| Transit times of known planets | AAVSO Exoplanet Database via NASA Exoplanet Watch (EXOTIC) | Co-authorship when used. |
| Anything, short | RNAAS (Research Notes of the AAS) | Short, moderated, citable. |

Include in any submission: ephemeris with uncertainties; depth, duration,
SNR/MES and event count; pixel-level location result; FPP and what it does not
cover; funnel and false-alarm rate at the candidate's SNR; links to repository,
preregistration DOI and reviews; one paragraph of honest caveats.

## Preferred projects

Prefer targets whose output doesn't need someone else's telescope night to
finish: variable-star catalogues and asteroid rotation periods are complete
contributions on their own. Planet candidates need ground-based follow-up,
which is the scarce resource. The `find-a-gap` skill lists starting points.
