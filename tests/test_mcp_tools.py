"""MCP tool wrappers, called directly (the server decorators return the functions)."""

import pytest
from conftest import write

mcp_server = pytest.importorskip("discover_anything.mcp_server")


def test_mcp_tool_wrappers_round_trip(hunt):
    h = str(hunt)
    write(hunt, "results/fit.json", "{}")
    entry = mcp_server.record_evidence(h, "results/fit.json", tags=["search"], note="fit")
    assert entry["id"] == "E-001" and entry["tags"] == ("search",)
    write(hunt, "settings.yml", "snr: 9")
    assert mcp_server.freeze_settings(h, "settings.yml", "from calibration")["kind"] == "frozen"
    table = mcp_server.funnel_add(h, "signals", 100, 90)
    assert "| signals | 100 | 90 |" in table and "may be noise" in table
    assert "signals" in mcp_server.funnel_show(h)
    write(hunt, "WRITEUP.md", "Period 3.2 d [E-001]. Depth 400 ppm.")
    report = mcp_server.check_claims(h, "WRITEUP.md")
    assert report["units_with_numbers"] == 2 and len(report["issues"]) == 1
    assert [c["status"] for c in mcp_server.verify_evidence(h)] == ["ok", "ok"]
    assert len(mcp_server.list_evidence(h, kind="funnel")) == 1
    assert any(s["domain"] == "archives" for s in mcp_server.novelty_sources())
    write(hunt, "prereg/p.csv", "t\n1\n")
    assert mcp_server.prereg_freeze(h, ["prereg/p.csv"])["entry"].startswith("E-")
    assert mcp_server.prereg_verify(h)[0]["status"] == "ok"
    assert mcp_server.review_pack(h, "codex")["prompt"].endswith("PROMPT.md")
    known = mcp_server.score_known_answers([{"id": "a"}], [{"id": "a"}], "id")
    assert known["recall"] == 1.0
    assert mcp_server.judge_agreement({"1": "y"}, {"1": "y"})["accuracy"] == 1.0
    assert "next_action" in mcp_server.hunt_status(h)
