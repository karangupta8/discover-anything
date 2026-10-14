# Contributing

Discover Anything is a toolkit for **finding** things in public data and making
the claim hold up. Contributions should make finding faster or more rigorous.
Run your own hunts in your own repositories; this one holds the tools and the
method.

## What helps most

### Novelty connectors
The most common reason a "new" find fails is that it was already known. A
connector queries one catalogue or literature source and returns dated rows for
the novelty log. See `src/discover_anything/novelty/` for the interface. Good
candidates: domain catalogues (eclipsing binaries, asteroid light curves,
historical earthquakes, meteorite falls), literature indexes, data archives.

### Controls and vetting tests
Null tests, injection methods, attribution checks and impostor tests for a
data type. They must be domain-tested on synthetic data and must report failures
as clearly as passes.

### Domain packs
`skills/discover-anything/references/domains/<field>.md`: data sources and
compute, traps, vetting additions under the six core headings, novelty sources,
and where results go. A pack should come from at least one hunt run end to end
in that field. Link the hunt's repository in the pull request so reviewers can
check the traps are real.

### Skills
Focused skills live in `skills/<name>/SKILL.md`. Keep them short and route the
detail to references. A new skill should cover a task agents get wrong without it.

### Bug reports
Especially: a control that passed when it should have failed, a connector that
returned "no match" for a known object, or a gate that `discover status` passed
too easily. Include the command, the input, and the output.

## Standards

- **Accuracy.** Facts about real work must match their public source, linked in
  [docs/sources.md](docs/sources.md).
- **Language.** "Candidate" until an expert or catalogue accepts it. No "AI
  discovered".
- **No silent failures.** A connector that can't reach its source reports
  "not checked", never "no match".
- **Code.** Functions return new values and never modify inputs; type hints on
  public functions; tests on synthetic data with no network access. `pytest` and
  `ruff check src tests` pass.

## Development

```bash
python -m venv .venv
.venv/bin/pip install -e ".[dev,mcp]"     # Windows: .venv\Scripts\pip
.venv/bin/pytest
```
