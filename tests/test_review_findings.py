"""Regression tests for the code review: every gate bypass and silent-'none' path it found."""

import json

import pytest
from conftest import write
from test_novelty import SKY, FakeHttp

from discover_anything import claims, gates, ledger, prereg
from discover_anything.novelty import astronomy, literature
from discover_anything.novelty.base import Target, run_connector
from discover_anything.review_text import is_response_filled, is_review_filled


def gate(root, name):
    return {g.name: g for g in gates.evaluate(root).gates}[name]


# --- placeholders ------------------------------------------------------------

@pytest.mark.parametrize("value", ["TBD", "todo", "n/a", "xxx", "<one sentence>", "none"])
def test_placeholder_answers_do_not_fill_kickoff(value):
    assert not gates.is_filled(value)


def test_multiline_question_cannot_prefill_other_fields(tmp_path):
    from discover_anything.hunt import create_hunt
    root = create_hunt(tmp_path / "x", question="Where?\n- **The gap (why):** none at all").root
    assert gates.field_value((root / "KICKOFF.md").read_text(encoding="utf-8"), "The gap") == ""


@pytest.mark.parametrize("name", ["con", "AUX", "nul.txt", "trailing."])
def test_reserved_hunt_names_rejected(tmp_path, name):
    from discover_anything.hunt import create_hunt
    with pytest.raises(ValueError):
        create_hunt(tmp_path / name)


# --- evidence must be intact --------------------------------------------------

def _calibrated(root):
    for tag in ("known-answer", "null", "injection"):
        ledger.append(root, "evidence", path=write(root, f"controls/{tag}.json", '{"n": 1}'), tags=(tag,))
    ledger.append(root, "frozen", path=write(root, "settings.yml", "snr: 9"), note="n")


def test_changed_null_evidence_fails_calibrate(filled_hunt):
    _calibrated(filled_hunt)
    assert gate(filled_hunt, "Calibrate").status == "pass"
    (filled_hunt / "controls/null.json").write_text('{"n": 0}', encoding="utf-8")
    result = gate(filled_hunt, "Calibrate")
    assert result.status == "fail" and any("changed" in d for d in result.details)


def test_empty_evidence_file_does_not_count(filled_hunt):
    ledger.append(filled_hunt, "evidence", path=write(filled_hunt, "controls/null.json", ""), tags=("null",))
    assert any("is empty" in d for d in gate(filled_hunt, "Calibrate").details)


def test_integrity_blocks_all_passed(filled_hunt):
    entry = ledger.append(filled_hunt, "evidence", path=write(filled_hunt, "results/a.csv", "1"))
    (filled_hunt / entry.path).write_text("2", encoding="utf-8")
    status = gates.evaluate(filled_hunt)
    assert status.integrity and not status.all_passed


# --- funnel warnings -------------------------------------------------------------

def test_null_as_large_as_real_fails_search_unless_waived(filled_hunt):
    ledger.append(filled_hunt, "evidence", path=write(filled_hunt, "results/s.csv", "1"), tags=("search",))
    ledger.append(filled_hunt, "funnel", data={"stage": "signals", "real": 100, "null": 95})
    ledger.append(filled_hunt, "funnel", data={"stage": "vetted", "real": 10, "null": 9})
    assert gate(filled_hunt, "Search").status == "fail"
    ledger.append(filled_hunt, "waiver", note="expected at this SNR; tiering instead",
                  data={"check": "funnel-warnings"})
    assert gate(filled_hunt, "Search").status == "pass"


# --- reviews -------------------------------------------------------------------

def test_empty_response_rows_and_short_reviews_rejected():
    assert not is_response_filled("| # | Finding | Fixed / disputed |\n|---|---|---|\n| 1 | | |\n")
    assert is_response_filled("| # | Finding | Fixed / disputed |\n|---|---|---|\n| 1 | odd/even | fixed |\n")
    assert not is_review_filled("Looks fine to me, nice work. " * 3)


# --- novelty gate ------------------------------------------------------------------

def _live_claim(root):
    write(root, "claims/C1.md", "**Status:** candidate\n")


def test_novelty_log_that_checked_no_catalogue_fails(filled_hunt):
    _live_claim(filled_hunt)
    log = write(filled_hunt, "novelty/C1_x.md", "log")
    ledger.append(filled_hunt, "novelty", path=log, data={"claim": "C1", "catalogues_checked": 0, "pending": []})
    assert "checked no catalogue" in gate(filled_hunt, "Novelty").details[0]


def test_pending_sources_fail_until_waived(filled_hunt):
    _live_claim(filled_hunt)
    log = write(filled_hunt, "novelty/C1_x.md", "log")
    ledger.append(filled_hunt, "novelty", path=log,
                  data={"claim": "C1", "catalogues_checked": 5, "pending": ["NASA ADS"]})
    assert gate(filled_hunt, "Novelty").status == "fail"
    ledger.append(filled_hunt, "waiver", note="ADS checked by hand 2026-10-14, no hits",
                  data={"check": "novelty-incomplete"})
    assert gate(filled_hunt, "Novelty").status == "pass"


def test_unstatused_claims_do_not_pass_novelty(filled_hunt):
    write(filled_hunt, "claims/C1.md", "no status here")
    assert gate(filled_hunt, "Novelty").status == "fail"


def test_bare_file_in_novelty_folder_is_not_enough(filled_hunt):
    _live_claim(filled_hunt)
    write(filled_hunt, "novelty/C1_handmade.md", "I checked stuff")
    assert gate(filled_hunt, "Novelty").status == "fail"
    ledger.append(filled_hunt, "evidence", path=filled_hunt / "novelty/C1_handmade.md", tags=("novelty",))
    assert gate(filled_hunt, "Novelty").status == "pass"


# --- ledger chain ------------------------------------------------------------------

def test_edited_ledger_line_breaks_chain(hunt):
    for i in range(3):
        ledger.append(hunt, "funnel", data={"stage": f"s{i}", "real": 10 - i, "null": 1})
    path = ledger.ledger_path(hunt)
    lines = path.read_text(encoding="utf-8").splitlines()
    lines[0] = lines[0].replace('"real": 10', '"real": 99')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert any("hash chain broken" in p for p in ledger.chain_problems(hunt))
    del lines[1]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert any("expected E-002" in p for p in ledger.chain_problems(hunt))


# --- claim checker false negatives ----------------------------------------------------

@pytest.mark.parametrize("text", [
    "Found `42` objects.",
    "# A 5 sigma result",
    "> 12 planets confirmed",
    "~~~\ncode\n~~~\nWe saw 7 dips.",
])
def test_numbers_previously_missed_are_flagged(hunt, text):
    report = claims.check_text(text, (), hunt)
    assert any(i.problem == "number without evidence citation" for i in report.issues)


def test_unclosed_fence_is_reported(hunt):
    report = claims.check_text("Intro.\n```\nWe found 9 planets.", (), hunt)
    assert any(i.problem == claims.UNCLOSED_FENCE for i in report.issues)


def test_citing_a_waiver_is_not_evidence(hunt):
    ledger.append(hunt, "waiver", note="x", data={"check": "prereg"})
    report = claims.check_text("Period 3.1 d [E-001].", ledger.read_entries(hunt), hunt)
    assert any("not evidence" in i.problem for i in report.issues)


def test_file_names_in_backticks_are_not_numbers(hunt):
    assert claims.check_text("See `fig_01.png` for the plot.", (), hunt).ok


# --- connectors: unexpected responses are not-checked ------------------------------------

@pytest.mark.parametrize("connector,routes", [
    (astronomy.SimbadCone(), {"simbad": {"error": "busy"}}),
    (astronomy.VizierCone("B/nope", "x"), {"vizier": "#INFO\tError=Table or Catalog not found\n"}),
    (astronomy.VizierCone("B/vsx/vsx", "VSX"), {"vizier": "<html>maintenance</html>"}),
    (astronomy.ExofopTarget(), {"exofop": {"oops": True}}),
    (literature.Zenodo(), {"zenodo": {"message": "rate limited"}}),
    (literature.GithubRepos(), {"api.github.com": {"incomplete_results": True, "items": []}}),
    (literature.Arxiv(), {"arxiv": "<feed xmlns='http://www.w3.org/2005/Atom'><entry><title>Error"
                                   "</title><summary>bad query</summary></entry></feed>"}),
])
def test_unexpected_responses_are_not_checked(connector, routes):
    target = Target(ids=("TIC 150428135",), ra=SKY.ra, dec=SKY.dec)
    assert run_connector(connector, target, FakeHttp(routes)).status == "not-checked"


def test_box_condition_includes_pole():
    assert "ra" not in astronomy.box_condition(10.0, 89.5, 1.0).replace("between", "")


def test_nan_radius_rejected():
    with pytest.raises(ValueError):
        Target(ra=1.0, dec=1.0, radius_arcsec=float("nan"))


# --- prereg and MCP confinement ----------------------------------------------------------

def test_zenodo_refuses_paths_outside_hunt(hunt, tmp_path):
    preds = write(hunt, "prereg/p.csv", "t\n1\n")
    out, _ = prereg.freeze(hunt, [preds])
    manifest = json.loads(out.read_text(encoding="utf-8"))
    secret = tmp_path / "secret.txt"
    secret.write_text("key", encoding="utf-8")
    manifest["files"].append({"path": "../secret.txt", "sha256": "x", "bytes": 3})
    out.write_text(json.dumps(manifest), encoding="utf-8")

    class NoNetwork:
        def post_json(self, *a, **k):
            raise AssertionError("must not contact Zenodo")

    with pytest.raises(ValueError, match="outside the hunt folder"):
        prereg.zenodo_draft(hunt, out, title="t", creators=["a"], token="t", http=NoNetwork())


def test_mcp_check_claims_cannot_read_outside_hunt(hunt, tmp_path):
    mcp_server = pytest.importorskip("discover_anything.mcp_server")
    outside = tmp_path / "private.md"
    outside.write_text("password 1234", encoding="utf-8")
    with pytest.raises(ValueError, match="outside the hunt folder"):
        mcp_server.check_claims(str(hunt), str(outside))
