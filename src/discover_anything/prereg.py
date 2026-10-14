"""Preregistration: freeze predictions before new data exists.

``freeze`` writes a manifest with SHA-256 checksums, the git commit and the
time, and records it in the ledger. ``zenodo_draft`` uploads the files to a
Zenodo *draft* deposition to obtain a reserved DOI; publishing stays a
deliberate human action on the Zenodo website.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .http import HttpClient
from .ledger import Entry, append, file_sha256, git_commit, now_iso

ZENODO_API = "https://zenodo.org/api"
ZENODO_SANDBOX_API = "https://sandbox.zenodo.org/api"


@dataclass(frozen=True)
class PreregCheck:
    manifest: str
    path: str
    status: str  # ok | changed | missing


def freeze(root: Path, files: list[Path], note: str = "") -> tuple[Path, Entry]:
    root = Path(root)
    if not files:
        raise ValueError("give at least one predictions file to freeze")
    items = []
    for name in files:
        full = Path(name) if Path(name).is_absolute() else root / name
        if not full.is_file():
            raise FileNotFoundError(f"cannot freeze missing file: {full}")
        rel = full.resolve().relative_to(root.resolve()).as_posix()
        items.append({"path": rel, "sha256": file_sha256(full), "bytes": full.stat().st_size})
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    manifest = {"frozen_at": now_iso(), "git_commit": git_commit(root), "note": note,
                "files": items}
    out = root / "prereg" / f"MANIFEST_{stamp}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    entry = append(root, "prereg", path=out, note=note, data={"files": items})
    return out, entry


def verify(root: Path) -> tuple[PreregCheck, ...]:
    root = Path(root)
    checks = []
    for manifest_path in sorted((root / "prereg").glob("MANIFEST_*.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for item in manifest["files"]:
            full = root / item["path"]
            status = ("missing" if not full.is_file()
                      else "ok" if file_sha256(full) == item["sha256"] else "changed")
            checks.append(PreregCheck(manifest_path.name, item["path"], status))
    return tuple(checks)


def zenodo_draft(root: Path, manifest_path: Path, *, title: str, creators: list[str],
                 token: str, description: str = "", sandbox: bool = False,
                 http: HttpClient | None = None) -> dict[str, Any]:
    """Create a Zenodo draft holding the manifest and frozen files. Never publishes."""
    if not token:
        raise ValueError("a Zenodo token is required (set ZENODO_TOKEN)")
    if not creators:
        raise ValueError("at least one creator name is required")
    http = http or HttpClient()
    api = ZENODO_SANDBOX_API if sandbox else ZENODO_API
    auth = {"Authorization": f"Bearer {token}"}
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    metadata = {"metadata": {
        "title": title, "upload_type": "dataset",
        "description": description or f"Preregistered predictions frozen at {manifest['frozen_at']}.",
        "creators": [{"name": name} for name in creators],
        "prereserve_doi": True,
    }}
    created = http.post_json(f"{api}/deposit/depositions", metadata, headers=auth)
    bucket = created["links"]["bucket"]
    for path in [Path(manifest_path), *[Path(root) / f["path"] for f in manifest["files"]]]:
        http.put_bytes(f"{bucket}/{path.name}", path.read_bytes(), headers=auth)
    doi = created.get("metadata", {}).get("prereserve_doi", {}).get("doi")
    return {"id": created["id"], "reserved_doi": doi, "edit_url": created["links"].get("html"),
            "published": False}
