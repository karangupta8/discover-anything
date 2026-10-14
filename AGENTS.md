# AGENTS.md

Instructions for AI agents working **on** this repository. If you are here to
run an investigation, load [`skills/discover-anything/SKILL.md`](skills/discover-anything/SKILL.md)
instead.

## Layout

```
skills/                            agent skills: discover-anything (main) + focused skills
src/discover_anything/             controls, vetting, ledger, gates, novelty, CLI, MCP server
skills/discover-anything/assets/templates/   hunt-folder templates (bundled into the package)
tests/                             pytest, synthetic data only, no network
docs/                              architecture, origins, lessons, sources
```

## Rules

1. **The skill is the single source of truth for the method.** Don't restate
   rules in README or docs; link to the reference file.
2. **Keep SKILL.md short.** Detail goes in `references/`, read on demand. Domain
   specifics go in `references/domains/`, never in the core loop.
3. **Facts need sources.** Any number about a real hunt must match its public
   write-up and appear in `docs/sources.md`. Don't invent examples that read as
   real.
4. **Follow the project's own language rules** in every file: "candidate", not
   "discovery"; no "AI discovered".
5. **Code:** functions return new values and never modify their inputs; type
   hints on public functions; explicit errors for invalid input; tests for every
   function on synthetic data. Long-running searches need size guards.
6. **Tests must pass:** `pytest`. Lint: `ruff check src tests`.
7. **Don't commit** data, FITS files, keys, or anything in `references/` or
   `local/` (private notes and third-party texts).
8. **This repository holds tools and method only.** Hunts and their results
   live in their own repositories.
