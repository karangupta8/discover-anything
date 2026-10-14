"""Evidence ledger, claim checker and funnel."""

import pytest
from conftest import write

from discover_anything import claims, funnel, ledger


def test_ids_are_sequential_and_entries_append_only(hunt):
    a = ledger.append(hunt, "evidence", path=write(hunt, "results/a.csv", "1"), tags=("Search",))
    b = ledger.append(hunt, "funnel", data={"stage": "s", "real": 3, "null": 1})
    assert (a.id, b.id) == ("E-001", "E-002")
    assert a.tags == ("search",)  # normalised
    lines = ledger.ledger_path(hunt).read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert ledger.read_entries(hunt) == (a, b)


def test_record_rejects_missing_or_outside_files(hunt, tmp_path):
    with pytest.raises(FileNotFoundError):
        ledger.append(hunt, "evidence", path=hunt / "nope.csv")
    outside = tmp_path / "outside.csv"
    outside.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match="outside the hunt folder"):
        ledger.append(hunt, "evidence", path=outside)
    with pytest.raises(ValueError, match="unknown kind"):
        ledger.append(hunt, "gossip")


def test_verify_detects_changed_and_missing(hunt):
    a = write(hunt, "results/a.csv", "1")
    b = write(hunt, "results/b.csv", "2")
    ledger.append(hunt, "evidence", path=a)
    ledger.append(hunt, "evidence", path=b)
    a.write_text("changed", encoding="utf-8")
    b.unlink()
    assert [c.status for c in ledger.verify(hunt)] == ["changed", "missing"]


def test_missing_ledger_has_helpful_error(tmp_path):
    with pytest.raises(FileNotFoundError, match="discover new"):
        ledger.read_entries(tmp_path)


WRITEUP = """# Result

The period is 3.18 days [E-001]. It is about 1.4 Earth radii.
No numbers in this sentence.

- Depth 450 ppm [E-001, E-002]
- Phase plot in `fig_01.png` and [link](https://x.org/2026)

| Stage | Count |
|---|---|
| signals | 500 |

```
code 123
```
"""


def test_check_claims_flags_uncited_numbers_and_unknown_ids(hunt):
    ledger.append(hunt, "evidence", path=write(hunt, "results/fit.json", "{}"))
    report = claims.check_text(WRITEUP, ledger.read_entries(hunt), hunt)
    problems = [(i.line, i.problem) for i in report.issues]
    assert (3, "number without evidence citation") in problems      # 1.4 Earth radii
    assert any("E-002" in p and "not in the ledger" in p for _, p in problems)
    assert (11, "number without evidence citation") in problems     # table row
    assert all(line != 15 for line, _ in problems)                   # code block ignored
    assert report.units_with_numbers == 4
    assert not report.ok


def test_check_claims_detects_cited_file_changed(hunt):
    path = write(hunt, "results/fit.json", "{}")
    ledger.append(hunt, "evidence", path=path)
    path.write_text('{"p": 2}', encoding="utf-8")
    report = claims.check_text("Period 3.2 d [E-001].", ledger.read_entries(hunt), hunt)
    assert report.issues and "changed" in report.issues[0].problem


def test_check_claims_clean_text_passes(hunt):
    ledger.append(hunt, "evidence", path=write(hunt, "results/fit.json", "{}"))
    report = claims.check_text("Period 3.18 d [E-001]. No other numbers here.",
                               ledger.read_entries(hunt), hunt)
    assert report.ok and report.cited == 1


def test_funnel_latest_value_per_stage_in_first_seen_order(hunt):
    for stage, real, null in (("signals", 500, 480), ("vetted", 20, 5), ("signals", 510, 470)):
        ledger.append(hunt, "funnel", data={"stage": stage, "real": real, "null": null})
    table = funnel.stages(ledger.read_entries(hunt))
    assert [(s.name, s.real) for s in table] == [("signals", 510), ("vetted", 20)]
    assert "| vetted | 20 | 5 | 0.25 |" in funnel.render(table)


def test_funnel_warnings():
    widening = (funnel.Stage("a", 10, 1, "E-1"), funnel.Stage("b", 20, 15, "E-2"))
    found = funnel.warnings(widening)
    assert any("should only narrow" in w for w in found)
    assert any("may be noise" in w for w in found)
    assert any("no null-run" in w for w in funnel.warnings((funnel.Stage("a", 5, None, "E-1"),)))
    with pytest.raises(ValueError):
        funnel.validate_counts(-1, None)
