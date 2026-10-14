---
name: vet-a-claim
description: Stress-test a claimed find in public data before it is posted, submitted or believed. Works on your own result or someone else's (a repository, write-up, thread or preprint). Produces a verdict with the specific tests that are missing. Use when the user says "is this real?", "check this before I post", "review this discovery", or shares a claimed planet, variable star, historical find or similar.
metadata:
  version: "1"
---

# Vet a Claim

Act as the skeptical referee the claim will eventually meet. Be specific and
fair: say what holds up as clearly as what doesn't.

## Steps

1. **State the claim exactly** in one paragraph: what object or event, what
   signal or passage, what is claimed, at what strength. If the claim is vague,
   that is the first finding.
2. **Collect the evidence trail.** For every number in the claim, find the file
   or table that produced it. If the claim is a `discover` hunt, run
   `discover status` and `discover check-claims <write-up>` and report both.
3. **Score the seven questions.** For each: done / partly / missing, with the
   file or line that shows it.
   1. Known answers recovered blind with the same pipeline?
   2. False-alarm rate measured with a null run (inverted, shuffled, wrong-period data)?
   3. Recovery measured with injections at the claimed strength (where possible)?
   4. Hold-out or independent confirmation (hidden season, second source)?
   5. Attribution: right star (pixel level) or right place and date (dateline)?
   6. Impostors ruled out by named tests (see the domain pack in
      `discover-anything/references/domains/`)?
   7. Novelty checked across catalogues, literature and recent hobbyist posts, dated?
4. **Run what you can now.** A novelty check is usually the fastest and most
   decisive: `discover novelty run --claim <id> ...` (or the `novelty-check`
   skill). Many "new" finds die here.
5. **Rank alternative explanations** from most to least likely, and name the
   test that would separate each from the claim.
6. **Quote overclaiming** sentences and give the honest rewrite (see the
   language table in `discover-anything/SKILL.md`).
7. **Verdict:** one of *reject*, *weak candidate*, *reasonable candidate*,
   *ready for an expert*. One sentence of reasoning, then the single most
   valuable next test.

## Output

A short report: claim, evidence trail table, the seven questions, alternative
explanations, overclaiming fixes, verdict. Save as
`reviews/REVIEW_<reviewer>_<date>.md` when working inside a hunt folder.

## Tone

The person may be excited. Keep it kind and concrete: "the null run is missing,
and here is the command to run it" helps more than "this is probably noise".
