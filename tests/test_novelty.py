"""Novelty connectors with a fake HTTP client (no network)."""

import json

import pytest

from discover_anything import ledger, novelty
from discover_anything.novelty import archives, astronomy, literature
from discover_anything.novelty.base import Target, run_connector, tic_numbers

VIZIER_TSV = """#
# VizieR Astronomical Server
#Title: AAVSO VSX
OID\tName\tV\tRAJ2000\tDEJ2000\tType
 \t \t \tdeg\tdeg\t
--------\t------\t-\t-------\t-------\t----
1547452\tTOI-700\t0\t97.09679\t-65.57931\tEP
"""

ARXIV_XML = """<?xml version='1.0' encoding='UTF-8'?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry><id>http://arxiv.org/abs/2001.00001</id><title>The First Habitable
  Zone Earth-sized Planet</title><published>2020-01-06T00:00:00Z</published></entry>
</feed>"""


class FakeHttp:
    """Routes by URL substring; raises for anything unexpected."""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def _match(self, url):
        self.calls.append(url)
        for key, value in self.routes.items():
            if key in url:
                if isinstance(value, Exception):
                    raise value
                return value
        raise AssertionError(f"unexpected URL {url}")

    def get_text(self, url, params=None, headers=None):
        return self._match(url)

    def get_json(self, url, params=None, headers=None):
        return self._match(url)

    def post_form(self, url, form, headers=None):
        self.calls.append(form["query"])
        return self._match(url)


SKY = Target(ids=("TIC 150428135", "TOI-700"), ra=97.0967, dec=-65.5786)


def test_target_validation():
    with pytest.raises(ValueError):
        Target(ra=10.0)
    with pytest.raises(ValueError):
        Target(ra=400.0, dec=0.0)
    with pytest.raises(ValueError):
        Target(lat=1.0)
    assert "RA 97.09670" in SKY.describe()
    assert tic_numbers(("TIC 123", "tic-456", "TOI-700")) == ("123", "456")


def test_vizier_cone_parses_rows():
    http = FakeHttp({"vizier": VIZIER_TSV})
    row = run_connector(astronomy.VizierCone("B/vsx/vsx", "VSX"), SKY, http)
    assert row.status == "found"
    assert row.matches[0].label == "1547452 TOI-700"
    assert "RAJ2000=97.09679" in row.matches[0].detail


def test_parse_vizier_tsv_without_units_line():
    header, rows = astronomy.parse_vizier_tsv("a\tb\n---\t---\n1\t2\n3\t4\n")
    assert header == ["a", "b"] and rows == [["1", "2"], ["3", "4"]]
    assert astronomy.parse_vizier_tsv("#only comments\n") == ([], [])


def test_simbad_identifier_escapes_quotes():
    http = FakeHttp({"simbad": {"data": [["TOI-700", "PM*"]]}})
    target = Target(ids=("O'Brien's star",))
    row = run_connector(astronomy.SimbadIdentifier(), target, http)
    assert row.status == "found"
    assert astronomy.adql_string("O'Brien") == "'O''Brien'"


def test_exoarchive_toi_filters_box_corners_by_true_distance():
    rows = json.dumps([
        {"toi": "700.01", "tid": 1, "tfopwg_disp": "CP", "pl_orbper": 16.05, "ra": 97.0967, "dec": -65.5786},
        {"toi": "999.01", "tid": 2, "tfopwg_disp": "PC", "pl_orbper": 1.0,
         "ra": 97.0967 + 0.0083 * 2.3, "dec": -65.5786 + 0.0080},  # inside box, outside cone
    ])
    http = FakeHttp({"exoplanetarchive": rows})
    row = run_connector(astronomy.ExoplanetArchiveToi(), SKY, http)
    assert [m.label for m in row.matches] == ["TOI 700.01"]
    assert "between" in http.calls[0]


def test_box_condition_wraps_ra():
    assert "or" in astronomy.box_condition(0.001, 10.0, 0.01)
    assert "or" in astronomy.box_condition(359.999, 10.0, 0.01)
    assert "between" in astronomy.box_condition(180.0, 10.0, 0.01)


def test_exofop_lists_tois_ctois_and_planets():
    payload = {"tois": [{"toi": "TOI 700.01", "disp_tfop": "CP"}], "ctois": [{"ctoi": "150428135.05"}],
               "basic_info": {"confirmed_planets": "TOI-700 b, TOI-700 c"}}
    row = run_connector(astronomy.ExofopTarget(), SKY, FakeHttp({"exofop": payload}))
    assert [m.label for m in row.matches] == ["TOI 700.01", "CTOI 150428135.05", "TOI-700 b", "TOI-700 c"]


def test_failure_is_not_checked_never_none():
    http = FakeHttp({"vizier": TimeoutError("timed out")})
    row = run_connector(astronomy.VizierCone("B/vsx/vsx", "VSX"), SKY, http)
    assert row.status == "not-checked"
    assert "TimeoutError" in row.note


def test_connector_without_needed_input_is_not_applicable():
    row = run_connector(astronomy.SimbadCone(), Target(ids=("X",)), FakeHttp({}))
    assert row.status == "n/a" and "RA/Dec" in row.note


def test_arxiv_zenodo_github(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    http = FakeHttp({
        "arxiv": ARXIV_XML,
        "zenodo": {"hits": {"hits": [{"metadata": {"title": "Predictions", "publication_date": "2026-10-06"},
                                      "doi_url": "https://doi.org/10.5281/zenodo.1"}]}},
        "api.github.com": {"items": [{"full_name": "someone/tic-check", "html_url": "https://github.com/x",
                                      "pushed_at": "2026-10-10T00:00:00Z"}]},
    })
    target = Target(ids=("TOI-700",))
    rows = [run_connector(c, target, http) for c in
            (literature.Arxiv(), literature.Zenodo(), literature.GithubRepos())]
    assert [r.status for r in rows] == ["found", "found", "found"]
    assert rows[0].matches[0].label == "The First Habitable Zone Earth-sized Planet"


def test_ads_without_token_is_not_checked(monkeypatch):
    monkeypatch.delenv("ADS_API_TOKEN", raising=False)
    row = run_connector(literature.Ads(), Target(ids=("TOI-700",)), FakeHttp({}))
    assert row.status == "not-checked" and "ADS_API_TOKEN" in row.note


def test_gvp_filters_by_distance_and_requires_years_for_position():
    features = {"features": [
        {"properties": {"Volcano_Name": "Gamkonora", "StartDateYear": 1673, "StartDateMonth": 5,
                        "Volcano_Number": 268040, "Activity_Type": "Confirmed Eruption",
                        "ExplosivityIndexMax": 5}, "geometry": {"coordinates": [127.53, 1.38]}},
        {"properties": {"Volcano_Name": "Far Away", "StartDateYear": 1700},
         "geometry": {"coordinates": [10.0, 50.0]}},
    ]}
    http = FakeHttp({"volcano.si.edu": features})
    target = Target(lat=1.4, lon=127.5, radius_km=50, year_from=1600, year_to=1800)
    row = run_connector(archives.GvpEruptions(), target, http)
    assert [m.label for m in row.matches] == ["Gamkonora 1673-5"]
    no_years = run_connector(archives.GvpEruptions(), Target(lat=1.4, lon=127.5), http)
    assert no_years.status == "not-checked"
    assert archives.haversine_km(0, 0, 0, 1) == pytest.approx(111.19, rel=1e-3)


def test_manual_sources_are_reported_as_manual():
    row = run_connector(novelty.manual_source("Rhino Resource Center", "https://rhinoresourcecenter.com"),
                        Target(place="Batavia"), FakeHttp({}))
    assert row.status == "manual"


def test_select_by_domain_and_name():
    astro = novelty.select("astronomy")
    assert all(c.domain in ("astronomy", "literature") for c in astro)
    assert [c.name for c in novelty.select(names=("smithsonian",))] == [
        "Smithsonian Global Volcanism Program (Holocene eruptions)"]
    with pytest.raises(ValueError):
        novelty.select(names=("nothing-like-this",))


def test_write_log_records_ledger_entry(hunt):
    http = FakeHttp({"vizier": VIZIER_TSV, "simbad": TimeoutError("down")})
    rows = novelty.run(SKY, (astronomy.VizierCone("B/vsx/vsx", "VSX"), astronomy.SimbadCone()), http)
    path, entry = novelty.write_log(hunt, "TOI-700", SKY, rows)
    text = path.read_text(encoding="utf-8")
    assert "| VSX | found |" in text and "| SIMBAD (cone) | not-checked |" in text
    assert "Not yet checked" in text and "Inspect each one" in text
    assert entry.kind == "novelty" and entry.data["claim"] == "TOI-700"
    assert entry.data["summary"]["found"] == 1
    assert (hunt / "novelty" / entry.data["json"]).is_file()
    assert ledger.read_entries(hunt)[-1] == entry
    with pytest.raises(ValueError):
        novelty.write_log(hunt, "../bad", SKY, rows)
