"""Abgleich einer Literaturangabe mit den gefundenen Treffern.

Rein deterministisch, ohne Sprachmodell. Das Urteil, ob eine Quelle eine
Aussage inhaltlich stützt, trifft Claude anhand des Abstracts, nicht dieses Modul.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import List, Optional

from adapters.base import Work, normalize_doi
from models import ReferenceInput

TITLE_MATCH = 0.90    # ab hier gilt der Titel als gefunden
TITLE_SIMILAR = 0.70  # darunter "nicht gefunden", darüber "unsicher"
YEAR_TOLERANCE = 1    # Preprint und Veröffentlichung weichen oft um ein Jahr ab


def normalize(text: str) -> str:
    """Kleinschreibung, Akzente und Satzzeichen entfernen."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^\w\s]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def title_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def surname(name: str) -> str:
    parts = normalize(name).split()
    return parts[-1] if parts else ""


def author_check(expected: List[str], work: Work) -> Optional[bool]:
    """True/False, oder None, wenn keine Vergleichsdaten vorliegen."""
    if not expected or not work.authors:
        return None
    found = {surname(a) for a in work.authors}
    return all(surname(e) in found for e in expected)


def year_check(expected: Optional[int], work: Work) -> Optional[bool]:
    if expected is None or work.year is None:
        return None
    return abs(expected - work.year) <= YEAR_TOLERANCE


@dataclass
class Verdict:
    status: str  # "gefunden" | "abweichend" | "unsicher" | "nicht gefunden"
    title_score: float = 0.0
    best: Optional[Work] = None
    issues: List[str] = field(default_factory=list)


def evaluate(ref: ReferenceInput, works: List[Work]) -> Verdict:
    if not works:
        return Verdict(status="nicht gefunden")

    ref_doi = normalize_doi(ref.doi)
    scored = [
        (bool(ref_doi and w.doi == ref_doi), title_similarity(ref.title, w.title), w)
        for w in works
    ]
    # Ein exakter DOI-Treffer schlägt jede Titel-Ähnlichkeit
    doi_hit, score, best = max(scored, key=lambda t: (t[0], t[1]))

    issues: List[str] = []
    if author_check(ref.authors, best) is False:
        issues.append(
            f"Autoren weichen ab: erwartet {', '.join(ref.authors)}, "
            f"gefunden {', '.join(best.authors)}"
        )
    if year_check(ref.year, best) is False:
        issues.append(f"Jahr weicht ab: erwartet {ref.year}, gefunden {best.year}")

    if doi_hit or score >= TITLE_MATCH:
        status = "abweichend" if issues else "gefunden"
        return Verdict(status, score, best, issues)
    if score >= TITLE_SIMILAR:
        return Verdict("unsicher", score, best, ["Ähnlicher Titel gefunden, bitte manuell prüfen"])
    return Verdict("nicht gefunden", score)
