"""Novelty-check building blocks.

A connector queries one catalogue or literature source for a target and
returns a row for the novelty log. Rows report what was *found*; deciding
whether a finding means "already known" is left to the person, because the
right answer depends on what was found (a star in SIMBAD is expected; a TOI on
that star is not).

A connector that fails reports ``not-checked`` with the reason. It never
reports "none" for a query that didn't run.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Protocol

from ..http import HttpClient
from ..ledger import now_iso

FOUND, NONE, NOT_CHECKED, MANUAL, NOT_APPLICABLE = "found", "none", "not-checked", "manual", "n/a"
MAX_MATCHES_SHOWN = 15


@dataclass(frozen=True)
class Target:
    ids: tuple[str, ...] = ()
    ra: float | None = None
    dec: float | None = None
    radius_arcsec: float = 30.0
    lat: float | None = None
    lon: float | None = None
    radius_km: float = 100.0
    place: str | None = None
    year_from: int | None = None
    year_to: int | None = None
    keywords: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if (self.ra is None) != (self.dec is None):
            raise ValueError("give both ra and dec, or neither")
        if self.ra is not None and not (0 <= self.ra < 360 and -90 <= self.dec <= 90):
            raise ValueError("ra must be in [0, 360) and dec in [-90, 90] degrees")
        if (self.lat is None) != (self.lon is None):
            raise ValueError("give both lat and lon, or neither")
        if self.lat is not None and not (-90 <= self.lat <= 90 and -180 <= self.lon <= 180):
            raise ValueError("lat must be in [-90, 90] and lon in [-180, 180]")
        if not (math.isfinite(self.radius_arcsec) and math.isfinite(self.radius_km)):
            raise ValueError("search radius must be a finite number")
        if self.radius_arcsec <= 0 or self.radius_km <= 0:
            raise ValueError("search radius must be positive")

    @property
    def has_sky_position(self) -> bool:
        return self.ra is not None

    @property
    def has_place(self) -> bool:
        return self.lat is not None or bool(self.place)

    @property
    def search_terms(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys((*self.ids, *self.keywords)))

    def describe(self) -> str:
        parts = []
        if self.ids:
            parts.append("IDs: " + ", ".join(self.ids))
        if self.has_sky_position:
            parts.append(f"RA {self.ra:.5f}, Dec {self.dec:+.5f}, radius {self.radius_arcsec:g}″")
        if self.place:
            parts.append(f"place: {self.place}")
        if self.lat is not None:
            parts.append(f"lat {self.lat:.3f}, lon {self.lon:.3f}, radius {self.radius_km:g} km")
        if self.year_from is not None or self.year_to is not None:
            parts.append(f"years {self.year_from or '…'}–{self.year_to or '…'}")
        if self.keywords:
            parts.append("keywords: " + ", ".join(self.keywords))
        return "; ".join(parts) or "(empty target)"


@dataclass(frozen=True)
class Match:
    label: str
    detail: str = ""
    url: str | None = None


@dataclass(frozen=True)
class NoveltyRow:
    source: str
    domain: str
    status: str
    searched_by: str
    method: str
    url: str | None
    checked_at: str
    matches: tuple[Match, ...] = field(default_factory=tuple)
    note: str = ""


class Connector(Protocol):
    name: str
    domain: str
    method: str
    human_url: str

    def applies(self, target: Target) -> str | None:
        """None if the connector can run on this target, else the reason it can't."""

    def query(self, target: Target, http: HttpClient) -> tuple[tuple[Match, ...], str]:
        """Return matches and a description of what was searched."""


def run_connector(connector: Connector, target: Target, http: HttpClient) -> NoveltyRow:
    reason = connector.applies(target)
    base = dict(source=connector.name, domain=connector.domain, method=connector.method,
                url=connector.human_url, checked_at=now_iso())
    if reason:
        return NoveltyRow(status=NOT_APPLICABLE, searched_by="", note=reason, **base)
    if connector.method == "manual":
        return NoveltyRow(status=MANUAL, searched_by=target.describe(),
                          note="Automated access is blocked; check by hand and record the result.",
                          **base)
    try:
        matches, searched_by = connector.query(target, http)
    except Exception as exc:  # noqa: BLE001 - any failure must surface as not-checked
        return NoveltyRow(status=NOT_CHECKED, searched_by=target.describe(),
                          note=f"{type(exc).__name__}: {exc}"[:300], **base)
    return NoveltyRow(status=FOUND if matches else NONE, searched_by=searched_by,
                      matches=matches, **base)


def adql_string(value: str) -> str:
    """Quote a value for an ADQL string literal."""
    return "'" + value.replace("'", "''") + "'"


def require(data: object, key: str, source: str) -> object:
    """Fetch a required key from a JSON response; a missing key means the query failed."""
    if not isinstance(data, dict) or key not in data:
        raise RuntimeError(f"unexpected response from {source}: no '{key}' field")
    return data[key]


def phrase(term: str) -> str:
    """A quoted search phrase with embedded quotes removed."""
    return '"' + term.replace('"', " ").strip() + '"'


def tic_numbers(ids: tuple[str, ...]) -> tuple[str, ...]:
    found = (re.match(r"^\s*TIC\s*[-_ ]?\s*(\d+)\s*$", i, re.IGNORECASE) for i in ids)
    return tuple(m.group(1) for m in found if m)
