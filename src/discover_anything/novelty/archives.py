"""Historical-event connectors: Smithsonian GVP eruptions; manual catalogue checks."""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..http import HttpClient
from .base import Match, Target, require

GVP_WFS = "https://webservices.volcano.si.edu/geoserver/GVP-VOTW/ows"
EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


@dataclass(frozen=True)
class GvpEruptions:
    name: str = "Smithsonian Global Volcanism Program (Holocene eruptions)"
    domain: str = "archives"
    method: str = "GVP WFS; year filter on server, distance filter locally"
    human_url: str = "https://volcano.si.edu/"

    def applies(self, target: Target) -> str | None:
        return None if target.has_place else "needs a volcano name (place) or lat/lon"

    def query(self, target: Target, http: HttpClient) -> tuple[tuple[Match, ...], str]:
        filters = []
        if target.place and target.lat is None:
            filters.append(f"Volcano_Name ILIKE '%{target.place.replace(chr(39), chr(39) * 2)}%'")
        if target.year_from is not None:
            filters.append(f"StartDateYear >= {int(target.year_from)}")
        if target.year_to is not None:
            filters.append(f"StartDateYear <= {int(target.year_to)}")
        if target.lat is not None and not (target.year_from or target.year_to):
            raise ValueError("a lat/lon search needs a year range to keep the query small")
        params = {"service": "WFS", "version": "2.0.0", "request": "GetFeature",
                  "typeName": "GVP-VOTW:Smithsonian_VOTW_Holocene_Eruptions",
                  "outputFormat": "application/json", "count": "5000",
                  "CQL_FILTER": " AND ".join(filters) or "INCLUDE"}
        data = http.get_json(GVP_WFS, params)
        features = require(data, "features", "Smithsonian GVP")
        total = data.get("numberMatched", data.get("totalFeatures"))
        if isinstance(total, int) and total > len(features):
            raise RuntimeError(f"GVP returned {len(features)} of {total} eruptions; narrow the years")
        matches = []
        for feature in features:
            props = feature["properties"]
            lon, lat = feature["geometry"]["coordinates"][:2]
            if target.lat is not None and haversine_km(target.lat, target.lon, lat, lon) > target.radius_km:
                continue
            date = "-".join(str(props.get(k)) for k in ("StartDateYear", "StartDateMonth",
                                                         "StartDateDay") if props.get(k))
            matches.append(Match(f"{props['Volcano_Name']} {date}",
                                 f"{props.get('Activity_Type', '')}, VEI {props.get('ExplosivityIndexMax')}",
                                 f"https://volcano.si.edu/volcano.cfm?vn={props.get('Volcano_Number')}"))
        searched = []
        if target.place and target.lat is None:
            searched.append(f"volcano name ~ {target.place}")
        if target.lat is not None:
            searched.append(f"within {target.radius_km:g} km of {target.lat:.3f}, {target.lon:.3f}")
        if target.year_from is not None or target.year_to is not None:
            searched.append(f"years {target.year_from or '…'}–{target.year_to or '…'}")
        return tuple(matches), "; ".join(searched)


@dataclass(frozen=True)
class ManualSource:
    name: str
    human_url: str
    domain: str = "archives"
    method: str = "manual"

    def applies(self, target: Target) -> str | None:
        return None

    def query(self, target: Target, http: HttpClient) -> tuple[tuple[Match, ...], str]:
        raise NotImplementedError("manual sources are checked by a person")


CONNECTORS = (
    GvpEruptions(),
    ManualSource("Meteoritical Bulletin Database", "https://www.lpi.usra.edu/meteor/"),
)
