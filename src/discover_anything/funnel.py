"""Funnel table: counts at each stage for the real run and the null run."""

from __future__ import annotations

from dataclasses import dataclass

from .ledger import Entry


@dataclass(frozen=True)
class Stage:
    name: str
    real: int
    null: int | None
    entry_id: str


def stages(entries: tuple[Entry, ...]) -> tuple[Stage, ...]:
    """Latest count per stage, in the order stages were first recorded."""
    order: list[str] = []
    latest: dict[str, Stage] = {}
    for entry in entries:
        if entry.kind != "funnel":
            continue
        name = str(entry.data["stage"])
        if name not in latest:
            order.append(name)
        latest[name] = Stage(name, int(entry.data["real"]),
                             None if entry.data.get("null") is None else int(entry.data["null"]),
                             entry.id)
    return tuple(latest[name] for name in order)


def validate_counts(real: int, null: int | None) -> None:
    if real < 0 or (null is not None and null < 0):
        raise ValueError("funnel counts must be non-negative")


def render(table: tuple[Stage, ...]) -> str:
    if not table:
        return "_No funnel stages recorded yet._"
    rows = ["| Stage | Real | Null | Null / real | Entry |", "|---|---|---|---|---|"]
    for stage in table:
        null = "–" if stage.null is None else str(stage.null)
        ratio = "–" if stage.null is None or stage.real == 0 else f"{stage.null / stage.real:.2f}"
        rows.append(f"| {stage.name} | {stage.real} | {null} | {ratio} | {stage.entry_id} |")
    return "\n".join(rows)


def warnings(table: tuple[Stage, ...]) -> tuple[str, ...]:
    """Plain-language problems with the funnel."""
    found: list[str] = []
    for prev, cur in zip(table, table[1:], strict=False):
        if cur.real > prev.real:
            found.append(f"stage '{cur.name}' has more real items ({cur.real}) than "
                         f"'{prev.name}' ({prev.real}); stages should only narrow")
    last = table[-1] if table else None
    if last and last.null is not None and last.real > 0 and last.null / last.real >= 0.5:
        found.append(f"final stage: null run yields {last.null} vs {last.real} real; "
                     "at least half the survivors may be noise")
    if table and all(s.null is None for s in table):
        found.append("no null-run counts recorded; the funnel can't show a false-alarm rate")
    return tuple(found)
