# Charter

Rules for finding new things in public data with an AI agent. Short on purpose.
Each rule is here because someone got burned without it, or because the people
who got it right all did it.

## The one-sentence version

**Try harder to kill the signal than to find it, and write down what would kill
it before you look.**

## Principles

1. **Find a gap, not a trick.** Every credible result in October 2026 came from a
   real coverage gap: new telescope sectors not yet combined with old ones, stars
   seen only in full-frame images, an archive transcribed but never read for
   meteorites. Name the gap in one sentence and say why professionals have not
   filled it. If you cannot, assume they have.

2. **The search is cheap; the vetting is the work.** One planet hunter spent two
   weeks and 74 analyses trying to prove himself wrong. Another's pixel checks
   threw away 93% of what passed the automated tests. Budget at least three
   times as long for vetting as for searching.

3. **Bury a wristwatch first.** Before trusting a search, prove it finds things
   already known to be there: published planets, catalogued variables, a famous
   eruption in the archive. If the detector can't find the watch you buried,
   its silence means nothing.

4. **Measure your false-alarm rate.** Run the same pipeline on data where the
   answer is "nothing": inverted light curves, shuffled times, passages that
   cannot mention the target. If the null run finds as many hits as the real
   run, you found noise.

5. **Measure what you can recover.** Inject fake signals at the strength you
   claim to be sensitive to. If you recover half of them at your threshold,
   your real detections at that threshold are fragile. Say so.

6. **Novelty is a claim that needs evidence.** "Not on the obvious list" is not
   "unknown". Check official catalogues, machine-learning catalogues, the
   literature, and recent hobbyist postings. In October 2026, 2 of one hunter's
   first 12 "new" planet signals were already published, and several later ones
   had been posted by other amateurs days earlier.

7. **Go back to the original.** A model's reading of a page, a pipeline's light
   curve, an OCR transcription: all are derived. Check the claim against the
   primary record (the pixels, the scan) before calling it a find.

8. **Preregister.** Before new data exists, publish predicted times or outcomes,
   the tolerance, and what counts as failure. Get a DOI. Nobody can then accuse
   you of fitting the answer afterwards. It is the strongest thing an amateur
   can do, and it needs no credentials.

9. **Use a different mind to attack the result.** A fresh session and a second
   model caught real code errors and overstated claims in 2026 hunts. Then ask a
   human expert. AI review is necessary, not sufficient.

10. **Say exactly what it is.** Candidate, not discovery. "No prior report found
    as of <date>", not "nobody knew". Give the bar it does not yet clear.

11. **Publish everything.** Code, data pointers, rejected candidates, reviews,
    funnel counts. Reproducibility turns a post into a contribution.

12. **Respect the experts' time.** Telescope nights and curators' attention are
    the scarce resources, not candidates. Only send what you would defend to the
    person who has to act on it.

13. **Enjoy it.** Name things informally, build the fly-through, show your kids.

## Non-negotiables

- [ ] Known answers recovered blind with the same pipeline
- [ ] Null test run through the full pipeline, counts reported
- [ ] Injection-recovery at the claimed sensitivity, recovery fraction reported
      (where the domain allows synthetic injection)
- [ ] Hold-out or independent-source test: hide part of the data and predict it,
      or confirm in a second, independent record
- [ ] Source attribution checked (right star, right page, right place and date)
- [ ] Primary record checked (pixels, scan) for every reported claim
- [ ] Novelty search across every source in the domain pack, logged with date
- [ ] Adversarial review by a fresh session and a second model, every point answered
- [ ] Predictions preregistered before any public "discovery" language, where a
      future observation can test them
- [ ] The word "candidate" in every headline until an expert or catalogue accepts it
- [ ] A human expert asked before submitting to any official channel

## When to stop

Stop and do not publish if any of these holds:

- The null run produces hits at a rate comparable to the real run
- The signal sits in one season, one sector or one source, and the hold-out fails
- Source attribution puts the signal on a neighbour, a reprint, another place
- A catalogue already lists it
- You cannot explain the result to a skeptic in two minutes without hand-waving

Stopping is a result. Write it down; it calibrates the next hunt.
