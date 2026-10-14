from pathlib import Path

import pytest

from discover_anything.hunt import create_hunt

FILLED_KICKOFF = """# Kickoff: demo

- **Date:** 2026-10-14
- **Question in one sentence:** Which bright stars in Sector 90 vary but are uncatalogued?
- **The gap (why professionals haven't done this):** No variable sweep after Sector 82.
- **Who else is working on it (searched papers / GitHub / Zenodo / social on 2026-10-14):** Kostov 2025 (Sectors 1-82 only).
- **How this angle differs:** Recent sectors and all variable classes.

## Data
- **Source and products:** QLP light curves
- **Sample cuts (exact, reproducible):** T <= 11, camera 1 CCD 1
- **Expected size:** about 2,000 stars, under 1 GB
- **Compute plan and estimated hours:** laptop, 2 hours

## Known answers for calibration
- **Known answers the pipeline must recover blind:** VSX variables in the field
- **Injection grid (or why injection doesn't apply):** sinusoids 0.1-3 percent
- **Null test:** time-shuffled light curves

## Success and failure criteria
- **What counts as a candidate:** periodic, above threshold, on target
- **What kills a candidate:** neighbour, systematic period, catalogued
- **What result stops the project:** recall below 70 percent
"""


@pytest.fixture
def hunt(tmp_path: Path) -> Path:
    return create_hunt(tmp_path / "demo", question=None, domain="astronomy").root


@pytest.fixture
def filled_hunt(hunt: Path) -> Path:
    (hunt / "KICKOFF.md").write_text(FILLED_KICKOFF, encoding="utf-8")
    return hunt


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path
