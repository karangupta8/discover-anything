# Origins: Dutch East India Company Archive Finds (October 2026)

Two investigations of the same transcribed archive, one month apart. Facts are
from the authors' public write-ups (see [docs/sources.md](../sources.md)).

---

## 1. Benjamin Breen: a new eyewitness account of the dodo

**The gap:** the GLOBALISE project had turned millions of handwritten Company
pages into searchable text, but nobody had read them for natural history.

**What he found:** a 1615 ship's journal in which sailors on Mauritius "caught
many tortoises, dodos". A new eyewitness record of the extinct bird.

**Lesson:** the transcription of a large archive is itself a coverage gap.
Whoever asks a new question of it first may find things in plain sight.

---

## 2. Jesse Waites: meteorite, rhinos, eruptions

**The gap:** the same archive (4.35 million pages, 1600s to 1790s), plus Dutch
and American digitised newspapers and ship logbooks, read for many questions
in parallel.

**Pipeline:**
- A deep-research pass ranked thirteen open historical questions by data
  completeness, how much AI could help, whether anyone had done it, and whether
  each answer could be checked against an original page
- One overnight GPU run embedded 5.7 million passages for semantic search
- A tiny decision model answered narrow yes/no questions for every hit
  (59,000 elephant mentions for about $3)
- A larger model read the survivors: translation, dates, places
- An agent opened the scan of each original page to check the transcription
- Catalogue checks before calling anything new

**Controls:** before searching for anything new, the pipeline had to re-find
Breen's dodo, the Laki (1783) and Tambora (1815) eruptions and a dozen other
known events. The author's image: test the metal detector on a wristwatch you
buried yourself.

**Results and their status (as of the write-up):**
- **Three Javan rhinoceroses** shipped as royal gifts in 1738 to 1740 that never
  reached the King of Kandy. **Confirmed** as previously unknown by the author
  of the standard reference on rhinos in captivity.
- **A meteorite fall** near Pandharpur, India, 6 August 1812, found in a
  Batavia newspaper's reprint of a Bombay letter. Not in six catalogues checked.
  **Candidate**, awaiting the curators.
- **Three volcanic eruptions** (Gamkonora 1722, Ciremai 1712, Slamet 1780) absent
  from the Smithsonian's list. **Candidates**, awaiting volcanologists.
- **Newspaper oddities** (sky apparitions, a sea serpent): published explicitly
  as unchecked stories, not findings.

**What didn't work:** the unknown 1808/09 eruption seen in ice cores. Many
sources searched, nothing found. Because the same pipeline found every other
eruption it was tested on, the negative result means something: the reports
probably aren't in those sources.

**Traps found:**
- The meteorite report never used the word "meteorite". Only search by
  meaning found it.
- Models placed eruptions on the wrong volcano (one 1,500 km away). Every
  location had to be re-derived from the letter's own geography.
- The place of printing is not the place of the event.

**Open-sourced as:** [Antiquity](https://github.com/jessewaites/antiquity), a
workspace scaffold for AI-assisted historical investigations.

**Lesson:** the same discipline as the planet hunts, in a different domain:
known-answer controls, a cheap-to-expensive funnel, verification against the
primary record, a novelty check against the specialists' own catalogues, and
honest status labels for every claim.

---

## Cross-domain observations

| Discipline | Planet hunts | Archive finds |
|---|---|---|
| Known-answer control | Recover published planets blind | Re-find the dodo, Laki, Tambora |
| Null / false-alarm measure | Inverted light curves | Sanity searches, wrong-period slices |
| Cheap → expensive funnel | BLS → automated vetting → pixel checks | Embeddings → tiny judge → larger reader |
| Primary-record check | Pixel-level difference images | Page scan vs transcription |
| Attribution trap | Light from a neighbouring star | Event from a different place than the dateline |
| Novelty check | ExoFOP, ML catalogues, arXiv, hobbyists | Meteoritical Bulletin, Smithsonian GVP, specialist compendia |
| Final authority | Telescope follow-up, TOI team | Catalogue curators, specialists |
