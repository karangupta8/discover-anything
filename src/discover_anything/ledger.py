"""Append-only evidence ledger for a hunt.

Every result file, frozen setting, funnel count, waiver, attestation,
preregistration and novelty check is one JSON line in
``.discover/ledger.jsonl``. Entries are never edited or deleted; corrections are
new entries. File-backed entries store a SHA-256 so later changes are detected.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

STATE_DIR = ".discover"
LEDGER_FILE = "ledger.jsonl"
KINDS = frozenset(
    {"evidence", "frozen", "funnel", "waiver", "attestation", "prereg", "novelty", "review"}
)
ID_PREFIX = "E-"


@dataclass(frozen=True)
class Entry:
    id: str
    kind: str
    time: str
    path: str | None = None
    sha256: str | None = None
    bytes: int | None = None
    tags: tuple[str, ...] = ()
    note: str = ""
    script: str | None = None
    git_commit: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps({**asdict(self), "tags": list(self.tags)}, ensure_ascii=False)

    @staticmethod
    def from_json(line: str) -> Entry:
        raw = json.loads(line)
        return Entry(**{**raw, "tags": tuple(raw.get("tags", ()))})


@dataclass(frozen=True)
class FileCheck:
    entry_id: str
    path: str
    status: str  # ok | changed | missing


def ledger_path(root: Path) -> Path:
    return Path(root) / STATE_DIR / LEDGER_FILE


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_commit(root: Path) -> str | None:
    """Current commit of the repository containing root, or None."""
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout.strip() or None


def read_entries(root: Path) -> tuple[Entry, ...]:
    path = ledger_path(root)
    if not path.is_file():
        raise FileNotFoundError(f"no ledger at {path}; run `discover new` first")
    lines = path.read_text(encoding="utf-8").splitlines()
    return tuple(Entry.from_json(line) for line in lines if line.strip())


def _relative(root: Path, path: Path) -> str:
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(Path(root).resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"{path} is outside the hunt folder {root}") from exc


def append(root: Path, kind: str, *, path: Path | None = None, tags: tuple[str, ...] = (),
           note: str = "", script: str | None = None,
           data: dict[str, Any] | None = None) -> Entry:
    """Write one new entry and return it."""
    if kind not in KINDS:
        raise ValueError(f"unknown kind {kind!r}; expected one of {sorted(KINDS)}")
    root = Path(root)
    existing = read_entries(root)
    rel = sha = size = None
    if path is not None:
        full = Path(path) if Path(path).is_absolute() else root / path
        if not full.is_file():
            raise FileNotFoundError(f"cannot record missing file: {full}")
        rel, sha, size = _relative(root, full), file_sha256(full), full.stat().st_size
    entry = Entry(
        id=f"{ID_PREFIX}{len(existing) + 1:03d}", kind=kind, time=now_iso(), path=rel,
        sha256=sha, bytes=size, tags=tuple(t.strip().lower() for t in tags if t.strip()),
        note=note.strip(), script=script, git_commit=git_commit(root), data=dict(data or {}),
    )
    with open(ledger_path(root), "a", encoding="utf-8") as handle:
        handle.write(entry.to_json() + "\n")
    return entry


def find(entries: tuple[Entry, ...], entry_id: str) -> Entry | None:
    wanted = entry_id.strip().upper()
    return next((e for e in entries if e.id.upper() == wanted), None)


def check_file(root: Path, entry: Entry) -> FileCheck | None:
    """Compare a file-backed entry with the file on disk now."""
    if entry.path is None:
        return None
    full = Path(root) / entry.path
    if not full.is_file():
        return FileCheck(entry.id, entry.path, "missing")
    status = "ok" if file_sha256(full) == entry.sha256 else "changed"
    return FileCheck(entry.id, entry.path, status)


def verify(root: Path, entries: tuple[Entry, ...] | None = None) -> tuple[FileCheck, ...]:
    entries = read_entries(root) if entries is None else entries
    checks = (check_file(root, e) for e in entries)
    return tuple(c for c in checks if c is not None)


def with_tag(entries: tuple[Entry, ...], tag: str, kind: str = "evidence") -> tuple[Entry, ...]:
    return tuple(e for e in entries if e.kind == kind and tag in e.tags)


def latest(entries: tuple[Entry, ...], kind: str, key: str, value: str) -> Entry | None:
    """Most recent entry of a kind whose data[key] equals value."""
    matches = [e for e in entries if e.kind == kind and e.data.get(key) == value]
    return matches[-1] if matches else None
