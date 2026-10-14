# Core Vetting

Copy into each claim card. A candidate is reported only if every **must** item
passes. Failed **should** items go into the caveats, in plain words.

This is the domain-independent structure. Each domain pack adds concrete tests
under the same six headings.

## A. Is the signal real (not noise, artefact or misreading)?

- [ ] **must** Passes the frozen cuts with margin; strength (SNR, judge score)
      recorded
- [ ] **must** Null comparison: what fraction of null-run hits survive at this
      strength?
- [ ] **must** No single event, page or data point dominates the detection
- [ ] **must** Hold-out or independent confirmation: predicted from part of the
      data and found in the hidden part, or present in a second independent record
- [ ] **should** Present in an independent reduction or transcription of the
      same data
- [ ] **should** Not at a known artefact (instrument period, OCR confusion,
      template text, reprinted boilerplate)

## B. Does it belong to the source you say it does?

- [ ] **must** Location attribution checked: the right star (pixel-level) or the
      right place and date (dateline, not where it was printed)
- [ ] **must** Nearby sources that could produce it are excluded, or named as a
      caveat
- [ ] **should** The attribution test itself is calibrated on known cases, and
      its false-rejection rate is known

## C. Is it the thing you claim (not a known impostor)?

- [ ] **must** Every impostor class in the domain pack ruled out with a named test
- [ ] **must** Checked on the primary record (pixels, page scan), not only on
      derived data or a model's summary
- [ ] **should** Physical or historical plausibility checked (size, duration,
      geography, chronology)

## D. Has anyone tried to break it?

- [ ] **must** Fresh-session review with `assets/templates/adversarial-review.md`, logged
- [ ] **must** Second-model review, logged
- [ ] **must** Written response to every finding: fixed, or disputed with a reason
- [ ] **should** A human expert has seen it

## E. Is it new?

- [ ] **must** Novelty log complete for every source in the domain pack, dated
- [ ] **must** Searched by identifier and by position (coordinates, or place and
      date), because names differ across catalogues
- [ ] **must** Recent hobbyist postings checked (Zenodo, GitHub, social, forums)

## F. Can it be tested or checked by someone else?

- [ ] **must** Everything needed to reproduce it is in the repository or pointed to
- [ ] **must** Where a future observation can test it, predictions are
      preregistered before that observation
