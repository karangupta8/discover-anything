"""Astronomy novelty connectors: SIMBAD, VizieR catalogues, NASA Exoplanet Archive, ExoFOP."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass

from ..http import HttpClient
from .base import Match, Target, adql_string, require, tic_numbers

SIMBAD_TAP = "https://simbad.cds.unistra.fr/simbad/sim-tap/sync"
VIZIER_ASU = "https://vizier.cds.unistra.fr/viz-bin/asu-tsv"
EXOARCHIVE_TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
EXOFOP_TARGET = "https://exofop.ipac.caltech.edu/tess/target.php"


def _needs_position(target: Target) -> str | None:
    return None if target.has_sky_position else "needs RA/Dec"


def _cone_deg(target: Target) -> float:
    return target.radius_arcsec / 3600.0


def _simbad(http: HttpClient, adql: str) -> list[list]:
    data = http.get_json(SIMBAD_TAP, {"REQUEST": "doQuery", "LANG": "ADQL",
                                      "FORMAT": "json", "QUERY": adql})
    return require(data, "data", "SIMBAD")


@dataclass(frozen=True)
class SimbadCone:
    name: str = "SIMBAD (cone)"
    domain: str = "astronomy"
    method: str = "TAP cone search"
    human_url: str = "https://simbad.cds.unistra.fr/simbad/sim-fcoo"

    def applies(self, target: Target) -> str | None:
        return _needs_position(target)

    def query(self, target: Target, http: HttpClient) -> tuple[tuple[Match, ...], str]:
        adql = ("SELECT TOP 50 main_id, otype, ra, dec FROM basic WHERE CONTAINS("
                f"POINT('ICRS', ra, dec), CIRCLE('ICRS', {target.ra}, {target.dec}, "
                f"{_cone_deg(target)})) = 1")
        rows = _simbad(http, adql)
        return (tuple(Match(str(r[0]), f"type {r[1]}") for r in rows),
                f"cone {target.radius_arcsec:g}″")


@dataclass(frozen=True)
class SimbadIdentifier:
    name: str = "SIMBAD (identifier)"
    domain: str = "astronomy"
    method: str = "TAP identifier lookup"
    human_url: str = "https://simbad.cds.unistra.fr/simbad/sim-fid"

    def applies(self, target: Target) -> str | None:
        return None if target.ids else "needs an identifier"

    def query(self, target: Target, http: HttpClient) -> tuple[tuple[Match, ...], str]:
        matches = []
        for ident in target.ids:
            adql = ("SELECT b.main_id, b.otype FROM ident AS i JOIN basic AS b ON i.oidref = b.oid "
                    f"WHERE i.id = {adql_string(ident)}")
            matches += [Match(str(r[0]), f"{ident} → type {r[1]}") for r in _simbad(http, adql)]
        return tuple(matches), "identifiers: " + ", ".join(target.ids)


def parse_vizier_tsv(text: str) -> tuple[list[str], list[list[str]]]:
    """Header and data rows from a VizieR asu-tsv response.

    Layout after the '#' comments: header, units, a line of dashes, then data.
    """
    lines = [ln for ln in text.splitlines() if not ln.startswith("#") and ln.strip()]
    if not lines:
        return [], []
    header = [h.strip() for h in lines[0].split("	")]
    dashes = next((i for i, ln in enumerate(lines)
                   if set(ln.replace("	", "").strip()) <= set("-")), None)
    data = lines[dashes + 1:] if dashes is not None else lines[1:]
    return header, [[c.strip() for c in ln.split("	")] for ln in data]


@dataclass(frozen=True)
class VizierCone:
    catalog: str
    name: str
    domain: str = "astronomy"
    method: str = "VizieR cone search"
    human_url: str = "https://vizier.cds.unistra.fr/viz-bin/VizieR"

    def applies(self, target: Target) -> str | None:
        return _needs_position(target)

    def query(self, target: Target, http: HttpClient) -> tuple[tuple[Match, ...], str]:
        text = http.get_text(VIZIER_ASU, {
            "-source": self.catalog, "-c": f"{target.ra} {target.dec}",
            "-c.rs": f"{target.radius_arcsec:g}", "-out.max": "50",
        })
        error = next((ln for ln in text.splitlines() if ln.startswith("#INFO\tError=")), None)
        if error or not text.lstrip().startswith("#") or "#Title" not in text:
            raise RuntimeError(f"VizieR could not query {self.catalog}: "
                               f"{error.split('=', 1)[1].strip() if error else 'unexpected response'}")
        header, rows = parse_vizier_tsv(text)
        matches = tuple(
            Match(" ".join(r[:2]).strip() or "row", "; ".join(
                f"{h}={v}" for h, v in zip(header[2:6], r[2:6], strict=False) if v))
            for r in rows
        )
        return matches, f"{self.catalog}, cone {target.radius_arcsec:g}″"


def _exoarchive(http: HttpClient, adql: str) -> list[dict]:
    # POST: the archive's firewall rejects some ADQL in GET query strings
    return json.loads(http.post_form(EXOARCHIVE_TAP, {"query": adql, "format": "json"}))


@dataclass(frozen=True)
class ExoplanetArchiveConfirmed:
    name: str = "NASA Exoplanet Archive (confirmed planets)"
    domain: str = "astronomy"
    method: str = "TAP cone search, pscomppars"
    human_url: str = "https://exoplanetarchive.ipac.caltech.edu/"

    def applies(self, target: Target) -> str | None:
        return _needs_position(target)

    def query(self, target: Target, http: HttpClient) -> tuple[tuple[Match, ...], str]:
        adql = ("select pl_name, pl_orbper, disc_year from pscomppars where contains("
                f"point('icrs',ra,dec),circle('icrs',{target.ra},{target.dec},{_cone_deg(target)}))=1")
        rows = _exoarchive(http, adql)
        return (tuple(Match(r["pl_name"], f"P={r.get('pl_orbper')} d, discovered {r.get('disc_year')}")
                      for r in rows), f"cone {target.radius_arcsec:g}″")


def angular_sep_deg(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    r1, d1, r2, d2 = map(math.radians, (ra1, dec1, ra2, dec2))
    cos_sep = (math.sin(d1) * math.sin(d2) + math.cos(d1) * math.cos(d2) * math.cos(r1 - r2))
    return math.degrees(math.acos(min(1.0, max(-1.0, cos_sep))))


def box_condition(ra: float, dec: float, radius_deg: float) -> str:
    """ADQL box enclosing a cone, for tables without a spatial index (handles RA wrap)."""
    dec_cond = f"dec between {dec - radius_deg} and {dec + radius_deg}"
    if abs(dec) + radius_deg >= 90:
        return dec_cond  # the cone contains a pole: every RA is in range
    ratio = math.sin(math.radians(radius_deg)) / math.cos(math.radians(dec))
    half_ra = math.degrees(math.asin(min(1.0, ratio)))
    lo, hi = ra - half_ra, ra + half_ra
    if lo < 0:
        ra_cond = f"(ra >= {lo + 360} or ra <= {hi})"
    elif hi >= 360:
        ra_cond = f"(ra >= {lo} or ra <= {hi - 360})"
    else:
        ra_cond = f"ra between {lo} and {hi}"
    return f"{ra_cond} and {dec_cond}"


@dataclass(frozen=True)
class ExoplanetArchiveToi:
    name: str = "NASA Exoplanet Archive (TOI table)"
    domain: str = "astronomy"
    method: str = "TAP box search on toi, distance filtered locally"
    human_url: str = "https://exoplanetarchive.ipac.caltech.edu/cgi-bin/TblView/nph-tblView?app=ExoTbls&config=TOI"

    def applies(self, target: Target) -> str | None:
        return _needs_position(target)

    def query(self, target: Target, http: HttpClient) -> tuple[tuple[Match, ...], str]:
        radius = _cone_deg(target)
        adql = ("select toi, tid, tfopwg_disp, pl_orbper, ra, dec from toi where "
                + box_condition(target.ra, target.dec, radius))
        rows = [r for r in _exoarchive(http, adql)
                if angular_sep_deg(target.ra, target.dec, float(r["ra"]), float(r["dec"])) <= radius]
        return (tuple(Match(f"TOI {r['toi']}", f"TIC {r.get('tid')}, disposition "
                                               f"{r.get('tfopwg_disp')}, P={r.get('pl_orbper')} d")
                      for r in rows), f"cone {target.radius_arcsec:g}″")


@dataclass(frozen=True)
class ExofopTarget:
    name: str = "ExoFOP-TESS target page"
    domain: str = "astronomy"
    method: str = "ExoFOP JSON by TIC ID"
    human_url: str = "https://exofop.ipac.caltech.edu/tess/"

    def applies(self, target: Target) -> str | None:
        return None if tic_numbers(target.ids) else "needs a TIC identifier"

    def query(self, target: Target, http: HttpClient) -> tuple[tuple[Match, ...], str]:
        matches = []
        for tic in tic_numbers(target.ids):
            data = http.get_json(f"{EXOFOP_TARGET}?id={tic}&json")
            require(data, "basic_info", "ExoFOP")
            url = f"{EXOFOP_TARGET}?id={tic}"
            for toi in data.get("tois") or []:
                matches.append(Match(str(toi.get("toi")), f"TFOPWG {toi.get('disp_tfop', '')}".strip(), url))
            for ctoi in data.get("ctois") or []:
                matches.append(Match(f"CTOI {ctoi.get('ctoi', '')}", ctoi.get("user", ""), url))
            planets = (data.get("basic_info") or {}).get("confirmed_planets") or ""
            for planet in filter(None, (p.strip() for p in planets.split(","))):
                matches.append(Match(planet, "confirmed planet", url))
        return tuple(matches), "TIC " + ", ".join(tic_numbers(target.ids))


CONNECTORS = (
    SimbadIdentifier(),
    SimbadCone(),
    VizierCone("B/vsx/vsx", "AAVSO VSX (variable stars)"),
    VizierCone("J/ApJS/258/16", "TESS eclipsing binaries (Prša+ 2022)"),
    VizierCone("I/358/vclassre", "Gaia DR3 variability classifications"),
    VizierCone("I/357/tbooc", "Gaia DR3 non-single-star orbits"),
    VizierCone("J/AJ/162/184", "APOGEE spectroscopic binaries (Kounkel+ 2021)"),
    ExoplanetArchiveConfirmed(),
    ExoplanetArchiveToi(),
    ExofopTarget(),
)
