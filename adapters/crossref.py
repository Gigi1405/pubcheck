from __future__ import annotations

from .base import SearchQuery, SourceResult, Work, clean_text, normalize_doi, safe_run

URL = "https://api.crossref.org/works"


async def _search(client, q: SearchQuery):
    response = await client.get(URL, params={"query.bibliographic": q.as_text(), "rows": 3})
    response.raise_for_status()
    items = response.json().get("message", {}).get("items", [])

    works = []
    for item in items:
        titles = item.get("title") or []
        title = clean_text(titles[0]) if titles else None
        if not title:  # Eintrag ohne Titel überspringen, Rest bleibt erhalten
            continue
        pub = item.get("published-print") or item.get("published-online") or item.get("published") or {}
        parts = pub.get("date-parts") or [[None]]
        year = parts[0][0] if parts and parts[0] else None
        containers = item.get("container-title") or []
        works.append(Work(
            title=title,
            year=year,
            authors=[a["family"] for a in item.get("author", []) if a.get("family")],
            venue=containers[0] if containers else None,
            doi=normalize_doi(item.get("DOI")),
            abstract=clean_text(item.get("abstract")),
            source="Crossref",
        ))
    return works


async def search(client, q: SearchQuery) -> SourceResult:
    return await safe_run("Crossref", _search, client, q)
