from __future__ import annotations

from .base import SearchQuery, SourceResult, Work, normalize_doi, safe_run

URL = "https://api.openalex.org/works"


def _rebuild_abstract(inverted: dict | None) -> str | None:
    """OpenAlex liefert Abstracts als invertierten Index: {wort: [positionen]}."""
    if not inverted:
        return None
    positions = {}
    for word, idxs in inverted.items():
        for idx in idxs:
            positions[idx] = word
    text = " ".join(positions[i] for i in sorted(positions))
    return text or None


async def _search(client, q: SearchQuery):
    response = await client.get(URL, params={"search": q.as_text(), "per-page": 3})
    response.raise_for_status()

    works = []
    for item in response.json().get("results", []):
        title = item.get("title") or item.get("display_name")
        if not title:
            continue
        source = (item.get("primary_location") or {}).get("source") or {}
        authors = [
            (a.get("author") or {}).get("display_name", "")
            for a in item.get("authorships", [])
        ]
        works.append(Work(
            title=title,
            year=item.get("publication_year"),
            authors=[a for a in authors if a],
            venue=source.get("display_name"),
            doi=normalize_doi(item.get("doi")),
            abstract=_rebuild_abstract(item.get("abstract_inverted_index")),
            source="OpenAlex",
        ))
    return works


async def search(client, q: SearchQuery) -> SourceResult:
    return await safe_run("OpenAlex", _search, client, q)
