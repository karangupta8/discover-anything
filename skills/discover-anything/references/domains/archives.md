# Domain Pack: Historical Archives

For hunts in digitised historical records: colonial archives, old newspapers,
ship logbooks, letters. Built from the October 2026 Dutch East India Company
investigations (Benjamin Breen's dodo; Jesse Waites's meteorite, rhinos and
eruptions). Background: `docs/origins/archive-finds.md`. For a ready-made workspace
dedicated to this domain, see [Antiquity](https://github.com/jessewaites/antiquity).

## What "the signal" is here

A passage describing an event, animal or object that the specialists'
catalogues don't record. The record is the page scan; transcriptions and model
readings are derived data.

## The pipeline shape that worked

1. **Retrieve wide.** Spelling was not standardised and OCR / handwriting
   recognition adds errors (17th-century Dutch spells "rhinoceros" about fifteen
   ways). Keyword search misses most hits. Combine keyword variants with
   semantic search over embeddings, so a passage is found by what it is about.
   A 1812 meteorite report never used the word "meteorite", which barely existed
   in English then.
2. **Sort cheap.** A small, fast model answers one narrow question per passage
   ("Is this a real animal? Is it wild? Could this describe a meteorite fall?").
   Reading 59,000 elephant mentions this way cost about $3.
3. **Read carefully.** A larger model reads only the survivors: translation,
   date, place, exact quote.
4. **Verify on the page scan.** Compare the transcription with the original
   image. Nothing is a find before this step.

## Controls

- **Known-answer recovery (the buried wristwatch):** before searching for
  anything new, the pipeline must re-find known events in the same corpus. The
  2026 run had to find Breen's dodo, the Laki eruption of 1783, Tambora in 1815
  and about a dozen others.
- **Same-search sanity checks:** the eruption search also re-found the 1711
  eruption of Awu, which the Smithsonian lists to the day.
- **Null slice:** run the judges on a slice that cannot contain the target (the
  wrong decades, the wrong region) and count what they flag.
- **Judge calibration:** keep a small labelled set per judge question with
  expected answers. Re-run it whenever the prompt or model changes.

## Traps

- **The dateline.** A report printed in one place may describe events
  elsewhere: Batavia's paper reprinted a Bombay letter about a stone that fell
  near Pandharpur. Place the event from the text's own geography, not from the
  place of printing or the archive's filing.
- **Model geography is unreliable.** One model blamed a Java ash fall on a
  volcano 1,500 km away. Every location must be justified from the document.
- **Word traps.** Period vocabulary differs from modern meaning: names of ships
  read as creatures, local names for animals, storms reported as earthquakes.
  Add each one to `LESSONS.md` the moment it is found.
- **Reprints and duplicates.** The same story travels across many papers.
  Collapse reprints to one event before counting.
- **Models fill gaps with confidence.** Names, dates and numbers in a model's
  summary must be re-read on the scan.
- **Stories are not findings.** Unverified oddities (sky apparitions, sea
  serpents) can be shared as leads only, clearly labelled.

## Vetting additions

Under the core headings in [../vetting.md](../vetting.md):

- [ ] **must** Verbatim transcription made from the page image, with archive
      reference (archive, inventory, scan or page) anyone can open
- [ ] **must** Dateline read: where and when the event happened, separately from
      where and when it was written and printed
- [ ] **must** Word traps for this source ruled out, listed by name
- [ ] **must** Event placed from the document's own geography
- [ ] **should** Corroborated in a second independent record (another letter,
      paper, logbook), or the search for one described with its boundaries
- [ ] **should** Full page image and a crop saved in `evidence/`

## Novelty sources

Depends on the class of event. Record *how* each catalogue was checked (full
read, index search, search inside a digitised copy) and the date.

- **Meteorites:** the Meteoritical Bulletin database; historical catalogues
  back to Chladni (1819); national lists; museum collection databases
- **Volcanic eruptions:** Smithsonian Global Volcanism Program
- **Animals in captivity and range records:** specialist compendia (for rhinos,
  Rookmaaker's *The Rhinoceros in Captivity* and the Rhino Resource Center)
- **Earthquakes:** historical earthquake catalogues for the region
- **Always:** the secondary literature on the corpus itself, and recent
  blog posts or repositories by others searching the same archive

## Where results go

The confirming authority is the specialist who maintains the catalogue. Write
to curators, catalogue maintainers or the relevant researcher with the archive
references, the transcription, the translation, and the list of catalogues
checked. In 2026, the rhino records were confirmed by the author of the
standard reference within days. Publish the write-up with every claim linked to
a page scan, and keep "candidate" until the specialist replies.
