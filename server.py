from __future__ import annotations

import json

import httpx
from mcp.server.fastmcp import FastMCP

from adapters import search_all
from adapters.base import SearchQuery, SourceResult
from matching import evaluate
from models import LiteratureSearchInput, ReferenceInput

mcp = FastMCP("pubcheck_mcp")
USER_AGENT = "PubCheck/0.2"


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=15.0, headers={"User-Agent": USER_AGENT})


def _source_overview(results: list[SourceResult]) -> list[dict]:
    return [
        {"quelle": r.source, "status": r.status, "treffer": len(r.works), "fehler": r.error}
        for r in results
    ]


@mcp.tool(name="pubcheck_search_databases", annotations={"readOnlyHint": True, "destructiveHint": False})
async def pubcheck_search_databases(params: LiteratureSearchInput) -> str:
    """
    Sucht parallel in fünf Literaturdatenbanken. Jede Quelle meldet ihren Status getrennt,
    damit ein Ausfall nicht wie "nicht gefunden" aussieht.

    Args:
        params (LiteratureSearchInput): Validierte Suchparameter.
    """
    query = SearchQuery(
        title=params.query,
        author=params.author,
        year=params.year,
        use_year_in_query=True,
    )
    async with _client() as client:
        results = await search_all(client, query)

    works = [w for r in results for w in r.works]
    failed = [r.source for r in results if r.status == "fehler"]

    if len(failed) == len(results):
        overall = "nicht prüfbar"
    elif not works:
        overall = "nicht gefunden"
    else:
        overall = "ok"

    return json.dumps({
        "status": overall,
        "quellen": _source_overview(results),
        "hinweis": f"Ausgefallene Quellen: {', '.join(failed)}" if failed else None,
        "treffer_gesamt": len(works),
        "results": [w.to_dict() for w in works],
    }, ensure_ascii=False, indent=2)


@mcp.tool(name="pubcheck_verify_reference", annotations={"readOnlyHint": True, "destructiveHint": False})
async def pubcheck_verify_reference(params: ReferenceInput) -> str:
    """
    Prüft eine Literaturangabe aus der Hausarbeit (Titel, Autoren, Jahr, DOI)
    gegen die Datenbanken. Liefert ein Urteil: gefunden, abweichend, unsicher
    oder nicht gefunden, dazu die konkreten Abweichungen.

    Args:
        params (ReferenceInput): Die zu prüfende Angabe.
    """
    query = SearchQuery(
        title=params.title,
        author=params.authors[0] if params.authors else None,
    )
    async with _client() as client:
        results = await search_all(client, query)

    works = [w for r in results for w in r.works]
    failed = [r.source for r in results if r.status == "fehler"]
    verdict = evaluate(params, works)

    status = "nicht prüfbar" if len(failed) == len(results) else verdict.status
    hinweis = None
    if failed and verdict.status == "nicht gefunden":
        hinweis = "Einige Quellen waren nicht erreichbar; 'nicht gefunden' ist eingeschränkt aussagekräftig."

    return json.dumps({
        "status": status,
        "title_score": round(verdict.title_score, 2),
        "abweichungen": verdict.issues,
        "bester_treffer": verdict.best.to_dict() if verdict.best else None,
        "quellen": _source_overview(results),
        "hinweis": hinweis,
    }, ensure_ascii=False, indent=2)


# Startbefehl
if __name__ == "__main__":
    mcp.run()
