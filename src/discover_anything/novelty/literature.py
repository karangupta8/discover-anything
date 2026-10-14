"""Literature and hobbyist-posting connectors: arXiv, NASA ADS, Zenodo, GitHub."""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from ..http import HttpClient
from .base import Match, Target, phrase, require

ATOM = "{http://www.w3.org/2005/Atom}"


def _terms(target: Target) -> str | None:
    return None if target.search_terms else "needs an identifier or keywords"


@dataclass(frozen=True)
class Arxiv:
    name: str = "arXiv (full text metadata)"
    domain: str = "literature"
    method: str = "arXiv API, quoted phrase"
    human_url: str = "https://arxiv.org/search/"

    def applies(self, target: Target) -> str | None:
        return _terms(target)

    def query(self, target: Target, http: HttpClient) -> tuple[tuple[Match, ...], str]:
        matches = []
        for term in target.search_terms:
            xml = http.get_text("https://export.arxiv.org/api/query",
                                {"search_query": f"all:{phrase(term)}", "max_results": "25"})
            for entry in ET.fromstring(xml).findall(f"{ATOM}entry"):
                title = " ".join((entry.findtext(f"{ATOM}title") or "").split())
                if title.lower() == "error":
                    raise RuntimeError("arXiv API returned an error entry: "
                                       + " ".join((entry.findtext(f"{ATOM}summary") or "").split()))
                matches.append(Match(title, f"term: {term}; {entry.findtext(f'{ATOM}published', '')[:10]}",
                                     entry.findtext(f"{ATOM}id")))
        return tuple(matches), "phrases: " + ", ".join(target.search_terms)


@dataclass(frozen=True)
class Ads:
    name: str = "NASA ADS"
    domain: str = "literature"
    method: str = "ADS API, quoted phrase (needs ADS_API_TOKEN)"
    human_url: str = "https://ui.adsabs.harvard.edu/"

    def applies(self, target: Target) -> str | None:
        return _terms(target)

    def query(self, target: Target, http: HttpClient) -> tuple[tuple[Match, ...], str]:
        token = os.environ.get("ADS_API_TOKEN")
        if not token:
            raise RuntimeError("ADS_API_TOKEN is not set; get a free token at "
                               "ui.adsabs.harvard.edu → Settings → API Token")
        matches = []
        for term in target.search_terms:
            data = http.get_json("https://api.adsabs.harvard.edu/v1/search/query",
                                 {"q": f"full:{phrase(term)}", "fl": "bibcode,title,year", "rows": "25"},
                                 headers={"Authorization": f"Bearer {token}"})
            for doc in require(require(data, "response", "ADS"), "docs", "ADS"):
                title = (doc.get("title") or [""])[0]
                matches.append(Match(title, f"term: {term}; {doc.get('year')} {doc.get('bibcode')}",
                                     f"https://ui.adsabs.harvard.edu/abs/{doc.get('bibcode')}"))
        return tuple(matches), "full-text phrases: " + ", ".join(target.search_terms)


@dataclass(frozen=True)
class Zenodo:
    name: str = "Zenodo (preprints, data, predictions)"
    domain: str = "literature"
    method: str = "Zenodo records API, quoted phrase"
    human_url: str = "https://zenodo.org/search"

    def applies(self, target: Target) -> str | None:
        return _terms(target)

    def query(self, target: Target, http: HttpClient) -> tuple[tuple[Match, ...], str]:
        matches = []
        for term in target.search_terms:
            data = http.get_json("https://zenodo.org/api/records", {"q": phrase(term), "size": "25"})
            for hit in require(require(data, "hits", "Zenodo"), "hits", "Zenodo"):
                meta = hit.get("metadata", {})
                matches.append(Match(meta.get("title", ""), f"term: {term}; "
                                     f"{meta.get('publication_date', '')}", hit.get("doi_url")))
        return tuple(matches), "phrases: " + ", ".join(target.search_terms)


@dataclass(frozen=True)
class GithubRepos:
    name: str = "GitHub repositories (hobbyist postings)"
    domain: str = "literature"
    method: str = "GitHub search API (GITHUB_TOKEN optional)"
    human_url: str = "https://github.com/search"

    def applies(self, target: Target) -> str | None:
        return _terms(target)

    def query(self, target: Target, http: HttpClient) -> tuple[tuple[Match, ...], str]:
        token = os.environ.get("GITHUB_TOKEN")
        headers = {"Accept": "application/vnd.github+json",
                   **({"Authorization": f"Bearer {token}"} if token else {})}
        matches = []
        for term in target.search_terms:
            data = http.get_json("https://api.github.com/search/repositories",
                                 {"q": phrase(term), "per_page": "25"}, headers=headers)
            if data.get("incomplete_results"):
                raise RuntimeError("GitHub search timed out (incomplete_results); retry later")
            for repo in require(data, "items", "GitHub"):
                matches.append(Match(repo["full_name"], f"term: {term}; updated "
                                     f"{repo.get('pushed_at', '')[:10]}", repo.get("html_url")))
        return tuple(matches), "phrases: " + ", ".join(target.search_terms)


CONNECTORS = (Arxiv(), Ads(), Zenodo(), GithubRepos())
