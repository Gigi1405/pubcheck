"""Registry aller Datenbank-Adapter. Neue Quelle = neues Modul + Eintrag hier."""
from __future__ import annotations

import asyncio
from typing import List

from . import arxiv, crossref, dblp, openalex, semanticscholar
from .base import SearchQuery, SourceResult

ADAPTERS = [
    crossref.search,
    openalex.search,
    semanticscholar.search,
    dblp.search,
    arxiv.search,
]


async def search_all(client, q: SearchQuery) -> List[SourceResult]:
    """Fragt alle Quellen parallel ab. Jede Quelle liefert ihren eigenen Status."""
    return list(await asyncio.gather(*(fn(client, q) for fn in ADAPTERS)))
