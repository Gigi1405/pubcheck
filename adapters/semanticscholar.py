from __future__ import annotations

import os

from .base import SearchQuery, SourceResult, Work, clean_text, normalize_doi, safe_run

URL = "https://api.semanticscholar.org/graph/v1/paper/search"
FIELDS = "title,year,authors,venue,externalIds,abstract"


async def _search(client, q: SearchQuery):
    headers = {}
    api_key = os.environ.get("S2_API_KEY")  # optional, ohne Schlüssel stark limitiert
    if api_key:
        headers["x-api-key"] = api_key

    response = await client.get(
        URL,
        params={"query": q.as_text(), "limit": 3, "fields": FIELDS},
        headers=headers,
    )
    response.raise_for_status()

    works = []
    for item in response.json().get("data", []):
        if not item.get("title"):
            continue
        ext_ids = item.get("externalIds") or {}
        works.append(Work(
            title=item["title"],
            year=item.get("year"),
            authors=[a["name"] for a in item.get("authors", []) if a.get("name")],
            venue=item.get("venue") or None,
            doi=normalize_doi(ext_ids.get("DOI")),
            abstract=clean_text(item.get("abstract")),
            source="Semantic Scholar",
        ))
    return works


async def search(client, q: SearchQuery) -> SourceResult:
    return await safe_run("Semantic Scholar", _search, client, q)
