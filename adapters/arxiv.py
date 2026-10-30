from __future__ import annotations

import xml.etree.ElementTree as ET

from .base import SearchQuery, SourceResult, Work, clean_text, normalize_doi, safe_run

URL = "https://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


async def _search(client, q: SearchQuery):
    response = await client.get(
        URL,
        params={"search_query": f"all:{q.as_text()}", "max_results": 3},
    )
    response.raise_for_status()
    root = ET.fromstring(response.text)

    works = []
    for entry in root.findall("atom:entry", NS):
        title = clean_text(entry.findtext("atom:title", default="", namespaces=NS))
        if not title:
            continue
        published = entry.findtext("atom:published", default="", namespaces=NS)
        year = int(published[:4]) if published[:4].isdigit() else None
        authors = [
            a.findtext("atom:name", default="", namespaces=NS)
            for a in entry.findall("atom:author", NS)
        ]
        works.append(Work(
            title=title,
            year=year,
            authors=[a for a in authors if a],
            venue="arXiv Preprint",
            doi=normalize_doi(entry.findtext("arxiv:doi", default="", namespaces=NS)),
            abstract=clean_text(entry.findtext("atom:summary", default="", namespaces=NS)),
            source="arXiv",
        ))
    return works


async def search(client, q: SearchQuery) -> SourceResult:
    return await safe_run("arXiv", _search, client, q)
