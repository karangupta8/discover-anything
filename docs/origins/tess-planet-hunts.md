# Origins: TESS Planet Hunts (October 2026)

Three hunts in three days, all built with Claude Code, all on NASA TESS data.
Numbers are from their own write-ups and repositories (see [docs/sources.md](../sources.md)).

---

## 1. Pavel Rabtsevich: TIC 4206066

**The gap:** new TESS data (Sector 98, late 2025) not yet combined with the same
star's 2018 and 2020 sectors.

**What he found:** a late-K dwarf ~116 light-years away dimming every 3.18 d for about
2 h, depth ~0.04–0.05%. ~1.4 Earth radii, ~530 °C. A tentative second signal at
11.13 d, ~2.2 Earth radii.

**How he tried to kill it:**
- 22 individual dips timed, all on schedule
- Leave-one-year-out: hid each year, predicted it from the other two, right 3 of 3
- Nearby-star and pixel-localisation checks
- Gaia astrometry, photometry, RV vetting
- TRICERATOPS FPP ~0.03–0.04 (above the 0.015 validation bar, so "not validated")
- Searched 36 catalogs and literature sources and 340,505 automated TESS alerts
- An audit that removed at least one overstrong statistical claim
- "74 separate analyses and over 1,000 scripts" over two weeks

**Agent use:** Claude Code (Opus 5.5, Fable 5.1) for download, search, fits, plots,
checks. Codex and clean sessions as independent reviewers. His framing: "AI agents
helped run a falsification-heavy analysis loop."

**The masterstroke:** a TESS Director's Discretionary Time proposal, approved as DDT
program 100: 2-minute cadence on the star in Sector 110, **31 Oct to 26 Nov 2026**.
Predictions and outcome categories frozen on Zenodo before then.

**Also:** a 3D "fly to it" web page (tic4206066.pages.dev), which helped
a general audience follow the thread.

**Lesson:** depth over breadth. One star, two weeks, every test he could think of,
then put it in front of the telescope.

---

## 2. Eumemic: industrialised version

**The gap:** SPOC's multi-sector search stops at Sector 96; stars seen only in
full-frame images never get one. "A shallow transit that is 5–8σ per sector can stay
below every single-sector threshold while reaching 10–20σ when all sectors are
combined."

**Scale, in 3 days:**
- 9,979 nearby K/M dwarfs → 10 new + 2 independent recoveries (first release)
- 6,430 TOI hosts with known TOIs masked → extra planets in known systems
- 14,112 SPOC TCEs that never became TOIs, re-measured with later sectors
- 20–100 day periods
- 22,448 and 84,863 fainter M dwarfs
- 4.04 million FGKM dwarfs full-sky on AWS Graviton → 491 candidates in tiers A/B/N
- Running total 551 candidates

**Best single result:** a third transit-like signal in TOI-4342 at 18.908 d, same size
(2.2 Earth radii) as the two confirmed planets, transits in 8 sectors, centroid on the
star, no capable neighbour within 30″.

**What makes it credible:**
- Blind recovery of Pavel's planet: 3.18278 d vs his 3.182785 d; 11.13274 d vs his 11.13274 d
- Recovered TOI-700 b, c and L 98-59 b, c, d
- Injection-recovery for three search variants, with timing
- Inverted light curves of 399,408 stars as the false-alarm measurement
- Centroid test calibrated on 1,000 known TOIs (wrongly rejects only 2–3%)
- Discovered that TRICERATOPS "cannot recognise noise": it passed 5 of 24 inverted false alarms
- Binary catalog checks added "following an outside review"; caught two impostors
  that had passed every automated test
- Demoted 78 of his own candidates when the false-alarm numbers came in
- Funnel table at every stage; every rejected candidate explained
- Predictions committed to the repo before TESS re-observes

**Performance engineering worth stealing:**
- Download in processes, not threads (Python GIL), 3×
- Biweight trend fit on 10-minute means, 14× faster for the trend, ~30 ppm difference
- Compiled LEO-Vetter inner loop, 2–5×, identical results verified to 1e-9
- AWS Graviton4 2.6× faster than Intel for the same vCPUs
- STScI open-data S3 bucket ~20× faster than MAST inside AWS us-east-1
- ~130 GB transferred / 12 GB stored for 10k stars

**Lesson:** at scale, the funnel is the science. The interesting output is not the
candidate list but the measured false-alarm and recovery rates that tell you how much
to trust it.

---

## 3. Paras Chopra: laptop-sized

**The gap:** 526 nearby stars (≤ 60 pc) never observed at 2-minute cadence.

**What he found:** two Earth-sized candidates in one morning on a $100 subscription.
- TIC 370612437 ("Aakanksha"), Cygnus, 158 ly: 3.565 d, 210 ppm, ~1.04 Earth radii
- HIP 114417 ("Orbit"), Andromeda, 134 ly: 4.934 d, 279 ppm, ~1.10 Earth radii

**Checks:** NASA vs MIT reductions agree; hold-one-season-out matched 3 of 4;
inverted light curves as false-alarm baseline; red-flag triage calibrated on injected
planets; pixel difference imaging; MCMC fits.

**Agent use:** Claude Code wrote it; Codex and a fresh Claude tried to break it. A
second Codex review found overstated claims and two code errors; a written response
addresses each.

**Gaps he admits:** depth-to-noise only ~7.2 and ~7.7; TRICERATOPS set up but not
completed; no human review yet (he asked for one publicly).

**Nice touches:** plain-language GUIDE.md, a 50-second video, an RNAAS research note
draft, a CTOI draft, preregistered predictions for 2027–28 on Zenodo.

**Lesson:** the smallest version that is still honest is a great first project. It
fits on a laptop and the full workflow can be exercised end to end.

---

## Cross-cutting observations

1. **Everyone converged on the same controls** without coordinating: hold-out
   prediction, inverted light curves, injection, independent reductions, adversarial
   AI review, preregistration. That convergence is the rulebook.
2. **The obvious gap got crowded within 72 hours.** Eumemic's later updates kept
   finding signals other hobbyists had posted days earlier. First-mover advantage on
   a gap is days, not months. Speed matters; so does checking who else is there.
3. **The binding constraint moved from code to judgement.** Writing 1,000 scripts is
   now cheap. Knowing which test to run next, and when to stop believing, is not.
4. **Cost is trivial; telescope time isn't.** A $100 subscription and some AWS hours
   versus nights on ground-based telescopes to confirm. Be a good citizen of that budget.
