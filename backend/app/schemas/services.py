"""Schéma des données SERVICE (catalogue du champ « Service »).

- GET  /api/v1/services : liste des désignations (ordre du catalogue) ;
- POST /api/v1/services : ajout d'une nouvelle désignation (formule
  « ➕ Ajouter à la liste » du formulaire) — 409 si elle existe déjà.

Conventions du projet : codes machine en anglais, libellés français.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ServiceCreate(BaseModel):
    """Données attendues pour ajouter une désignation de service."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=100, description="Désignation du service (ex. KLB)")

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value):
        """Nettoie les espaces en début/fin (ex. « KLB  » → « KLB »)."""
        return value.strip() if isinstance(value, str) else value


class ServiceRead(BaseModel):
    """Désignation renvoyée par l'API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
