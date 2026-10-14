"""CLI end to end, MCP tool registration, and agent setup."""

import asyncio
import json
from pathlib import Path

import pytest
from conftest import FILLED_KICKOFF, write

from discover_anything import cli, setup_agents
from discover_anything.resources import read_template, skill_names


def run(capsys, *argv):
    code = cli.main(list(argv))
    out = capsys.readouterr()
    return code, out.out, out.err


def test_cli_walkthrough(tmp_path, capsys):
    root = tmp_path / "h1"
    code, out, _ = run(capsys, "new", str(root), "--domain", "astronomy", "--question", "Which stars vary?")
    assert code == 0 and "KICKOFF.md" in out
    (root / "KICKOFF.md").write_text(FILLED_KICKOFF, encoding="utf-8")
    h = ("--hunt", str(root))

    code, out, _ = run(capsys, *h, "status")
    assert "[    FAIL] 3 Calibrate" in out and "Next:" in out

    write(root, "controls/ka.csv", "id\nA\n")
    code, out, _ = run(capsys, *h, "record", str(root / "controls/ka.csv"), "--tag", "known-answer")
    assert code == 0 and "E-001" in out and "[E-001]" in out

    write(root, "settings.yml", "snr: 9\n")
    code, out, _ = run(capsys, *h, "freeze", str(root / "settings.yml"), "--note", "from calibration")
    assert "froze settings.yml" in out

    code, _, _ = run(capsys, *h, "waive", "injection", "--note", "not applicable")
    assert code == 0
    code, out, _ = run(capsys, *h, "funnel", "add", "signals", "--real", "100", "--null", "90")
    assert code == 0
    code, out, _ = run(capsys, *h, "funnel", "show")
    assert "| signals | 100 | 90 |" in out

    write(root, "WRITEUP.md", "We found 12 variables.\n")
    code, out, _ = run(capsys, *h, "check-claims", str(root / "WRITEUP.md"))
    assert code == 1 and "number without evidence citation" in out

    code, out, _ = run(capsys, *h, "evidence", "--json")
    assert [e["kind"] for e in json.loads(out)] == ["evidence", "frozen", "waiver", "funnel"]

    code, out, _ = run(capsys, *h, "status", "--json")
    data = json.loads(out)
    assert data["current"]["name"] == "Calibrate"  # null-test evidence still missing

    code, out, _ = run(capsys, *h, "verify")
    assert code == 0


def test_cli_errors_are_reported_not_raised(tmp_path, capsys):
    code, _, err = run(capsys, "--hunt", str(tmp_path), "status")
    assert code == 1 and "not inside a hunt folder" in err
    root = tmp_path / "h2"
    run(capsys, "new", str(root))
    code, _, err = run(capsys, "new", str(root))
    assert code == 1 and "not empty" in err
    code, _, err = run(capsys, "--hunt", str(root), "funnel", "add")
    assert code == 2


def test_cli_score_known_records_evidence(tmp_path, capsys):
    root = tmp_path / "h3"
    run(capsys, "new", str(root))
    write(root, "known.csv", "id,period\nA,3.0\nB,5.0\n")
    write(root, "found.csv", "id,period\nA,3.001\n")
    code, out, _ = run(capsys, "--hunt", str(root), "score-known", "--known", str(root / "known.csv"),
                       "--found", str(root / "found.csv"), "--key", "id", "--value", "period",
                       "--out", str(root / "controls/known.json"))
    assert code == 0 and "Recall 50.0%" in out and "tagged known-answer" in out


def test_cli_dedupe_and_judge(tmp_path, capsys):
    passages = tmp_path / "p.jsonl"
    text = "the stone fell from a thunder cloud near the village and was very heavy for its size"
    passages.write_text("\n".join(json.dumps({"id": i, "text": t}) for i, t in
                                  enumerate([text, text + " indeed", "an unrelated storm report"])),
                        encoding="utf-8")
    code, out, _ = run(capsys, "dedupe", str(passages), "--id-col", "id")
    assert "3 passages → 2 distinct events" in out
    write(tmp_path, "e.csv", "id,label\n1,yes\n2,no\n")
    write(tmp_path, "p.csv", "id,label\n1,yes\n2,yes\n")
    code, out, _ = run(capsys, "judge-agreement", "--expected", str(tmp_path / "e.csv"),
                       "--predicted", str(tmp_path / "p.csv"))
    assert "accuracy=50.0%" in out


def test_mcp_server_exposes_tools_but_not_human_decisions(tmp_path):
    pytest.importorskip("mcp")
    from discover_anything import mcp_server
    names = {t.name for t in asyncio.run(mcp_server.server.list_tools())}
    assert {"new_hunt", "hunt_status", "record_evidence", "check_claims", "novelty_check",
            "prereg_freeze", "review_pack", "funnel_add"} <= names
    assert not any("attest" in n or "waive" in n or "zenodo" in n for n in names)
    root = tmp_path / "m1"
    mcp_server.new_hunt(str(root), question="Where did the 1809 eruption happen?", domain="archives")
    status = mcp_server.hunt_status(str(root))
    assert status["gates"][0]["status"] == "pass"


def test_bundled_skills_and_templates_resolve():
    names = skill_names()
    assert names[0] == "discover-anything" and "find-a-gap" in names
    assert "Kickoff" in read_template("project-kickoff.md")


def test_setup_dry_run_changes_nothing(tmp_path, capsys):
    target = tmp_path / "skills"
    assert setup_agents.run_setup("other", apply=False, skills_dir=str(target)) == 0
    assert not target.exists()
    assert "Dry run" in capsys.readouterr().out


def test_setup_copies_skills_and_backs_up_existing(tmp_path, capsys):
    target = tmp_path / "skills"
    (target / "discover-anything").mkdir(parents=True)
    (target / "discover-anything" / "mine.txt").write_text("keep", encoding="utf-8")
    assert setup_agents.run_setup("other", apply=True, skills_dir=str(target)) == 0
    assert (target / "discover-anything" / "SKILL.md").is_file()
    backups = list(target.glob("discover-anything.bak-*"))
    assert backups and (backups[0] / "mine.txt").read_text(encoding="utf-8") == "keep"


def test_setup_plan_for_claude_code_registers_mcp():
    steps = setup_agents.plan("claude-code", None)
    assert any("claude mcp add --scope user discover-anything" in s for s in steps)
    assert any(str(Path(".claude") / "skills") in s for s in steps)
