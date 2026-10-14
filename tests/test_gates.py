"""The gate checker: a hunt walks from Phase 0 to Phase 9."""

from pathlib import Path

import pytest
from conftest import write

from discover_anything import gates, ledger, prereg
from discover_anything.gates import field_value, is_filled


def status_of(root: Path) -> dict[str, str]:
    return {g.name: g.status for g in gates.evaluate(root).gates}


def test_fresh_hunt_fails_at_curiosity(hunt):
    result = gates.evaluate(hunt)
    assert result.current.phase == 0
    assert "Question in one sentence" in result.current.next_action


def test_question_flag_fills_phase_zero(tmp_path):
    from discover_anything.hunt import create_hunt
    root = create_hunt(tmp_path / "q", question="Where did the 1809 eruption happen?").root
    assert status_of(root)["Curiosity"] == "pass"
    assert gates.evaluate(root).current.phase == 1


def test_placeholders_do_not_count_as_filled():
    assert not is_filled("<one sentence>")
    assert not is_filled("  ")
    assert is_filled("QLP light curves")


def test_field_value_reads_continuation_lines():
    text = "- **Sample cuts:** T <= 11\n  and camera 1\n- **Next:** x"
    assert field_value(text, "Sample cuts") == "T <= 11 and camera 1"


def test_filled_kickoff_passes_first_three_gates(filled_hunt):
    s = status_of(filled_hunt)
    assert (s["Curiosity"], s["Gap"], s["Scope"]) == ("pass", "pass", "pass")
    assert gates.evaluate(filled_hunt).current.phase == 3


def _calibrate(root: Path) -> None:
    for tag in ("known-answer", "null", "injection"):
        ledger.append(root, "evidence", path=write(root, f"controls/{tag}.json", "{}"), tags=(tag,))
    ledger.append(root, "frozen", path=write(root, "settings.yml", "snr: 9\n"), note="from calibration")


def test_calibrate_needs_controls_and_freeze(filled_hunt):
    assert status_of(filled_hunt)["Calibrate"] == "fail"
    _calibrate(filled_hunt)
    assert status_of(filled_hunt)["Calibrate"] == "pass"


def test_injection_can_be_waived_with_reason(filled_hunt):
    for tag in ("known-answer", "null"):
        ledger.append(filled_hunt, "evidence", path=write(filled_hunt, f"controls/{tag}.json", "{}"),
                      tags=(tag,))
    ledger.append(filled_hunt, "frozen", path=write(filled_hunt, "settings.yml", "x"), note="n")
    assert status_of(filled_hunt)["Calibrate"] == "fail"
    ledger.append(filled_hunt, "waiver", note="archive search: no synthetic injection",
                  data={"check": "injection"})
    assert status_of(filled_hunt)["Calibrate"] == "pass"


def test_editing_frozen_settings_fails_calibrate(filled_hunt):
    _calibrate(filled_hunt)
    write(filled_hunt, "settings.yml", "snr: 7\n")  # loosened after seeing candidates
    result = {g.name: g for g in gates.evaluate(filled_hunt).gates}["Calibrate"]
    assert result.status == "fail"
    assert "changed since freezing" in result.next_action


def test_refreeze_requires_new_null_run(filled_hunt):
    _calibrate(filled_hunt)
    write(filled_hunt, "settings.yml", "snr: 8\n")
    ledger.append(filled_hunt, "frozen", path=filled_hunt / "settings.yml", note="raised after review")
    assert status_of(filled_hunt)["Calibrate"] == "fail"
    ledger.append(filled_hunt, "evidence", path=write(filled_hunt, "controls/null2.json", "{}"),
                  tags=("null",))
    assert status_of(filled_hunt)["Calibrate"] == "pass"


def _search(root: Path) -> None:
    ledger.append(root, "evidence", path=write(root, "results/search.csv", "id\n1\n"), tags=("search",))
    ledger.append(root, "funnel", data={"stage": "signals", "real": 500, "null": 480})
    ledger.append(root, "funnel", data={"stage": "vetted", "real": 12, "null": 1})


def test_search_needs_evidence_and_funnel_with_null(filled_hunt):
    _calibrate(filled_hunt)
    assert status_of(filled_hunt)["Search"] == "fail"
    _search(filled_hunt)
    assert status_of(filled_hunt)["Search"] == "pass"


def _kill(root: Path, status: str = "candidate") -> None:
    write(root, "claims/TIC-1.md", f"# Claim: TIC-1\n\n**Status:** {status}\n")
    write(root, "reviews/REVIEW_codex_2026-10-14.md",
          "# Review\n\n" + "The odd and even depths differ by more than two sigma in sector 90. " * 4)
    write(root, "reviews/RESPONSE_codex_2026-10-14.md",
          "| # | Finding | Fixed / disputed |\n|---|---|---|\n| 1 | odd/even depth | fixed in fit v2 |\n")


def test_kill_rejects_template_status_and_stub_reviews(filled_hunt):
    write(filled_hunt, "claims/TIC-1.md", "**Status:** candidate / rejected / already known\n")
    from discover_anything.review import make_pack
    make_pack(filled_hunt, "codex")  # creates stub REVIEW_/RESPONSE_ files
    gate = {g.name: g for g in gates.evaluate(filled_hunt).gates}["Kill"]
    assert gate.status == "fail"
    joined = " ".join(gate.details)
    assert "without a status" in joined and "still empty" in joined


def test_full_walk_to_all_gates_passed(filled_hunt):
    _calibrate(filled_hunt)
    _search(filled_hunt)
    _kill(filled_hunt)
    assert status_of(filled_hunt)["Kill"] == "pass"
    assert status_of(filled_hunt)["Novelty"] == "fail"
    log = write(filled_hunt, "novelty/TIC-1_2026-10-14.md", "# Novelty Log")
    ledger.append(filled_hunt, "novelty", path=log, data={"claim": "TIC-1", "catalogues_checked": 6,
                                                          "pending": []})
    assert status_of(filled_hunt)["Novelty"] == "pass"
    predictions = write(filled_hunt, "prereg/predictions.csv", "t,err\n3100.5,0.01\n")
    prereg.freeze(filled_hunt, [predictions], "before Sector 110")
    assert status_of(filled_hunt)["Preregister"] == "pass"
    ledger.append(filled_hunt, "attestation", note="AAVSO moderator replied 2026-10-20",
                  data={"check": "expert-review"})
    ledger.append(filled_hunt, "attestation", note="12/12 events predicted", data={"check": "followup"})
    result = gates.evaluate(filled_hunt)
    assert all(g.done for g in result.gates)
    assert result.current is None
    assert "All gates passed." in gates.render(result)


def test_all_rejected_claims_pass_novelty_as_a_result(filled_hunt):
    _kill(filled_hunt, status="rejected: neighbour")
    gate = {g.name: g for g in gates.evaluate(filled_hunt).gates}["Novelty"]
    assert gate.status == "pass" and "stopping is a result" in gate.details[0]


def test_changed_prereg_file_fails(filled_hunt):
    predictions = write(filled_hunt, "prereg/predictions.csv", "t\n1\n")
    prereg.freeze(filled_hunt, [predictions])
    predictions.write_text("t\n2\n", encoding="utf-8")
    assert status_of(filled_hunt)["Preregister"] == "fail"


def test_prereg_waiver(filled_hunt):
    ledger.append(filled_hunt, "waiver", note="historical claim, no future observation",
                  data={"check": "prereg"})
    assert status_of(filled_hunt)["Preregister"] == "waived"


def test_integrity_reports_changed_evidence(filled_hunt):
    path = write(filled_hunt, "results/a.csv", "1\n")
    entry = ledger.append(filled_hunt, "evidence", path=path)
    path.write_text("2\n", encoding="utf-8")
    assert any(entry.id in item and "changed" in item for item in gates.evaluate(filled_hunt).integrity)


@pytest.mark.parametrize("status,expected", [
    ("**Status:** candidate", "candidate"),
    ("**Status:** rejected (centroid offset)", "rejected"),
    ("**Status:** candidate / rejected / already known / confirmed", None),
    ("no status line", None),
])
def test_claim_status_parsing(status, expected):
    assert gates.claim_status(status) == expected
