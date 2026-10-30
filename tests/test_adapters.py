"""Parser-Tests mit gefälschten HTTP-Antworten, ohne Netzwerkzugriff."""
import asyncio

import httpx

from adapters import crossref, openalex
from adapters.base import SearchQuery


def run_with(handler, adapter):
    async def go():
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            return await adapter.search(client, SearchQuery(title="Test"))
    return asyncio.run(go())


def test_crossref_skips_empty_title_and_keeps_rest():
    payload = {"message": {"items": [
        {"title": [], "DOI": "10.1/x"},
        {
            "title": ["Real Paper"],
            "DOI": "https://doi.org/10.1/Y",
            "author": [{"family": "Müller"}],
            "published-print": {"date-parts": [[2021]]},
            "container-title": ["Journal"],
        },
    ]}}
    result = run_with(lambda req: httpx.Response(200, json=payload), crossref)

    assert result.status == "ok"
    assert len(result.works) == 1
    assert result.works[0].doi == "10.1/y"
    assert result.works[0].year == 2021


def test_http_error_is_reported_not_swallowed():
    result = run_with(lambda req: httpx.Response(500), crossref)
    assert result.status == "fehler"
    assert result.error is not None


def test_openalex_rebuilds_abstract_from_inverted_index():
    payload = {"results": [{
        "title": "T",
        "publication_year": 2020,
        "authorships": [],
        "abstract_inverted_index": {"world": [1], "Hello": [0]},
    }]}
    result = run_with(lambda req: httpx.Response(200, json=payload), openalex)
    assert result.works[0].abstract == "Hello world"
