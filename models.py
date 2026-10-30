from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class LiteratureSearchInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    query: str = Field(..., min_length=3, description="Titel oder Suchbegriffe")
    author: Optional[str] = Field(default=None, description="Nachname des Autors")
    year: Optional[int] = Field(default=None, ge=1900, le=2100, description="Erscheinungsjahr")


class ReferenceInput(BaseModel):
    """Eine Literaturangabe aus der Hausarbeit, die geprüft werden soll."""
    model_config = ConfigDict(str_strip_whitespace=True)
    title: str = Field(..., min_length=3, description="Titel der Publikation")
    authors: List[str] = Field(default_factory=list, description="Nachnamen der Autoren")
    year: Optional[int] = Field(default=None, ge=1900, le=2100)
    doi: Optional[str] = Field(default=None, description="DOI, falls vorhanden")
