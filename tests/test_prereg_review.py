"""Preregistration (including the Zenodo draft, offline) and review packs."""

import json

import pytest
from conftest import write

from discover_anything import ledger, prereg, review


def test_freeze_writes_manifest_and_ledger_entry(hunt):
    preds = write(hunt, "prereg/predictions.csv", "t\n1\n")
    out, entry = prereg.freeze(hunt, [preds], "before Sector 110")
    manifest = json.loads(out.read_text(encoding="utf-8"))
    assert manifest["files"][0]["path"] == "prereg/predictions.csv"
    assert entry.kind == "prereg" and entry.data["files"] == manifest["files"]
    assert [c.status for c in prereg.verify(hunt)] == ["ok"]
    preds.write_text("t\n2\n", encoding="utf-8")
    assert [c.status for c in prereg.verify(hunt)] == ["changed"]


def test_freeze_requires_files(hunt):
    with pytest.raises(ValueError):
        prereg.freeze(hunt, [])
    with pytest.raises(FileNotFoundError):
        prereg.freeze(hunt, [hunt / "missing.csv"])


class FakeZenodo:
    def __init__(self):
        self.calls = []

    def post_json(self, url, payload, headers=None):
        self.calls.append(("POST", url, payload))
        return {"id": 42, "links": {"bucket": "https://zenodo.test/b/1", "html": "https://zenodo.test/d/42"},
                "metadata": {"prereserve_doi": {"doi": "10.5281/zenodo.42"}}}

    def put_bytes(self, url, body, headers=None):
        self.calls.append(("PUT", url, len(body)))


def test_zenodo_draft_uploads_but_never_publishes(hunt):
    preds = write(hunt, "prereg/predictions.csv", "t\n1\n")
    out, _ = prereg.freeze(hunt, [preds])
    fake = FakeZenodo()
    result = prereg.zenodo_draft(hunt, out, title="Predictions", creators=["A. Person"],
                                 token="t", http=fake)
    assert result == {"id": 42, "reserved_doi": "10.5281/zenodo.42",
                      "edit_url": "https://zenodo.test/d/42", "published": False}
    assert [c[0] for c in fake.calls] == ["POST", "PUT", "PUT"]
    assert not any("publish" in c[1] for c in fake.calls)
    with pytest.raises(ValueError, match="token"):
        prereg.zenodo_draft(hunt, out, title="x", creators=["a"], token="", http=fake)


def test_review_pack_builds_prompt_from_claims_and_excludes_data(hunt):
    write(hunt, "claims/TIC-1.md", "**Status:** candidate\n")
    write(hunt, "data/raw.fits", "binary")
    pack = review.make_pack(hunt, "codex")
    prompt = pack.prompt.read_text(encoding="utf-8")
    assert "TIC-1 (candidate)" in prompt
    assert "Do not read any conversation history" in prompt
    files = pack.file_list.read_text(encoding="utf-8").splitlines()
    assert "claims/TIC-1.md" in files and not any(f.startswith("data/") for f in files)
    assert pack.review_stub.exists() and pack.response_stub.exists()
    assert ledger.read_entries(hunt)[-1].kind == "review"


def test_review_pack_rejects_bad_reviewer_name(hunt):
    with pytest.raises(ValueError):
        review.make_pack(hunt, "../escape")


def test_review_pack_keeps_existing_review(hunt):
    first = review.make_pack(hunt, "codex")
    first.review_stub.write_text("real review " * 20, encoding="utf-8")
    second = review.make_pack(hunt, "codex")
    assert second.review_stub.read_text(encoding="utf-8").startswith("real review")
