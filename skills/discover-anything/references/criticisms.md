# Criticisms and Answers

What people said about the October 2026 agent-driven planet hunts, whether it
holds up, and which rule answers it. Most of these generalise to any domain.

As of 9 October 2026 no named professional astronomer had commented publicly.
The criticism came from Hacker News, replies on X, and the hunters' own
measurements, which turned out to be the harshest critics of all.

---

### 1. "It's right at the edge of a noise threshold"

> "right at the edge of a noise threshold for existing models in use by
> academics" (field researcher, relayed on Hacker News)

**Valid.** Two candidates sat at depth-to-noise of about 7.2 and 7.7. One hunt's
own injections recovered only 57 to 62% of planted transits at nominal SNR 10.

**Answer:** measure the false-alarm rate and the recovery fraction (charter:
"Measure your false-alarm rate", "Measure what you can recover"). Report the
null-run rate at the candidate's strength. Tier candidates; don't headline the
weak ones.

### 2. "Noise fitting noise" / multiple testing

> "Call me when peer review confirms it; until then, it is noise fitting noise."
> (Hacker News)

**Partly valid.** Search 4 million stars and some noise passes any fixed set of
tests by chance. One hunt: 7.46 million signals reduced to 726 clean ones. Without
a measured false-alarm rate, nobody can say how many of those are noise.

**Answer:** run the null test at full scale. The same hunter ran inverted light
curves of 399,408 stars and concluded the SNR 7.5 to 9 band was "mostly noise"
(382 passed every check; about 270 expected false alarms). That answers the
critique with a number.

### 3. "Hide fake planets and run on shuffled data"

**Valid and already standard.** All three serious efforts did versions of it.

**Answer:** non-negotiables. `discover_anything.controls` has both.

### 4. "How are you ruling out known objects?"

> "how are you ruling out known objects before claiming discovery? verification
> against existing catalogs is usually the gate that slows this down."
> (Jatin Garg, reply on X)

**The most important criticism. Valid.** "The ExoFOP page is empty" is
necessary, not sufficient. Two of one hunter's first 12 signals were already
published. Large ML catalogues are not linked from a star's ExoFOP page.

**Answer:** the domain pack's novelty sources, searched by ID and position,
dated. One hunter automated this across 2,037 arXiv papers.

### 5. "A faint eclipsing binary nearby can fake this"

**Valid, and the dominant failure mode in full-frame images.** Pixel checks
rejected 93% of signals that had passed all automated tests.

**Answer:** core vetting section B. Be explicit about what amateurs cannot
exclude (companions within about 1 to 2″). That is why the end state is
"candidate". The archive equivalent is the dateline: the right page, the wrong
place.

### 6. "Hallucinations in data reduction are no joke"

**Valid in principle.** A comparison of agents on gravitational-wave analysis
(arXiv 2605.28916) found a coding agent finished fast "with silent deviations
from the specification".

**Answer:** evidence rule 1. Never trust a number the agent states; trust a
number a script computed and saved to a file you can re-run. Known-answer
recovery catches silent pipeline bugs. Second-model review caught two code errors
in one 2026 pipeline.

### 7. "AI reviewing AI"

**Valid.** Different models share blind spots; a fresh session of the same model
shares more.

**Answer:** keep AI review (it finds real bugs), and require a human expert
before any official submission.

### 8. "Too many candidates already"

> "There are way too many planet candidates discovered by the NASA TESS
> mission." (Franck Marchis, SETI Institute, 2022)

**Valid as a systemic concern.** Follow-up time is the bottleneck. Weakly vetted
community submissions waste it.

**Answer:** charter: "Respect the experts' time". Submit only the best tier to
official channels; publish the rest in the repository. Prefer projects whose
output doesn't need scarce follow-up.

### 9. Hype

Secondary coverage claimed NASA had "confirmed" a planet. It had not: TESS
approved a re-observation of a field it was going to observe anyway.

**Answer:** the language table. Write the precise sentence yourself so nobody
has to paraphrase you.

### 10. "Should have gone through established citizen-science projects"

**Partly valid.** Established projects have expert vetting and channels. But
solo projects are legitimate, and these filled gaps the established ones don't.

**Answer:** contact the relevant team when you have something and offer your
pipeline's output.

---

## What the hunters got right

- Preregistering predictions with a DOI before the telescope looked again
- Getting a TESS Director's Discretionary Time request approved
- Measuring their own false-alarm rate at scale, and demoting their own
  candidates when the numbers said so (one hunter moved 78 to a lower tier)
- Calibrating the centroid test on 1,000 known planets instead of trusting a default
- Publishing rejected candidates with reasons
- A plain-language guide for non-experts
- Crediting each other, and recovering each other's signals as a pipeline check
