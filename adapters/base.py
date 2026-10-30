"""Gemeinsame Datentypen und Hilfsfunktionen für alle Datenbank-Adapter."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import List, Optional


@dataclass
class SearchQuery:
    title: str
    author: Optional[str] = None
    year: Optional[int] = None
    use_year_in_query: bool = False

    def as_text(self) -> str:
        parts = [self.title]
        if self.author:
            parts.append(self.author)
        if self.use_year_in_query and self.year:
            parts.append(str(self.year))
        return " ".join(parts)


@dataclass
class Work:
    title: str
    year: Optional[int] = None
    authors: List[str] = field(default_factory=list)
    venue: Optional[str] = None
    doi: Optional[str] = None
    abstract: Optional[str] = None
    source: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SourceResult:
    source: str
    status: str  # "ok" | "leer" | "fehler"
    works: List[Work] = field(default_factory=list)
    error: Optional[str] = None


def clean_text(text: Optional[str]) -> Optional[str]:
    """Entfernt HTML/JATS-Tags und überflüssige Leerzeichen."""
    if not text:
        return None
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def normalize_doi(doi: Optional[str]) -> Optional[str]:
    """Vereinheitlicht DOIs, damit sie sich vergleichen lassen."""
    if not doi:
        return None
    doi = doi.strip().lower()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
    return doi or None


async def safe_run(source: str, fn, client, q: SearchQuery) -> SourceResult:
    """Führt einen Adapter aus. Fehler werden sichtbar gemeldet, nicht verschluckt."""
    try:
        works = await fn(client, q)
    except Exception as exc:
        return SourceResult(source=source, status="fehler", error=f"{type(exc).__name__}: {exc}")
    return SourceResult(source=source, status="ok" if works else "leer", works=works)
