from __future__ import annotations

import re

from .base import SearchQuery, SourceResult, Work, normalize_doi, safe_run

URL = "https://dblp.org/search/publ/api"


def _clean_author(name: str) -> str:
    # DBLP hängt bei Namensgleichheit Nummern an, z. B. "Anna Müller 0001"
    return re.sub(r"\s\d{4}$", "", name).strip()


async def _search(client, q: SearchQuery):
    response = await client.get(URL, params={"q": q.as_text(), "format": "json", "h": 3})
    response.raise_for_status()
    hits = response.json().get("result", {}).get("hits", {}).get("hit", [])

    works = []
    for hit in hits:
        info = hit.get("info", {})
        title = info.get("title")
        if not title:
            continue
        # DBLP liefert Autoren mal als Dict, mal als Liste
        authors = info.get("authors", {}).get("author", [])
        if isinstance(authors, dict):
            authors = [authors]
        names = [(a.get("text") if isinstance(a, dict) else a) or "" for a in authors]

        year = str(info.get("year", ""))
        works.append(Work(
            title=title.rstrip("."),
            year=int(year) if year.isdigit() else None,
            authors=[_clean_author(n) for n in names if n],
            venue=info.get("venue") or None,
            doi=normalize_doi(info.get("doi")),
            source="DBLP",
        ))
    return works


async def search(client, q: SearchQuery) -> SourceResult:
    return await safe_run("DBLP", _search, client, q)
