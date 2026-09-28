"""Dépôt des SERVICES — catalogue du champ « Service » du formulaire.

Interface :
    list() -> list[dict]             # ordre du catalogue (id croissant)
    get_by_name(name) -> dict | None # recherche exacte (insensible à la casse)
    create(service: dict) -> dict    # lève ValueError si déjà présent

Les dictionnaires renvoyés sont « prêts pour l'API » (dates en ISO).
"""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.service import Service
from app.repositories.serializers import service_to_dict


class ServiceRepository:
    """Stocke et retrouve les désignations de services dans PostgreSQL."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def list(self) -> list[dict]:
        """Toutes les désignations, dans l'ordre du catalogue."""
        rows = self._db.scalars(select(Service).order_by(Service.id)).all()
        return [service_to_dict(row) for row in rows]

    def get_by_name(self, name: str) -> dict | None:
        """Recherche exacte SANS tenir compte de la casse (évite les doublons
        « KLB » / « klb »)."""
        row = self._db.scalar(
            select(Service).where(Service.name.ilike(name))
        )
        return service_to_dict(row) if row else None

    def create(self, service: dict) -> dict:
        """Ajoute une désignation (ValueError si déjà présente)."""
        if self.get_by_name(service["name"]) is not None:
            raise ValueError(f"Service « {service['name']} » déjà présent dans la liste.")

        row = Service(name=service["name"])
        self._db.add(row)
        try:
            self._db.commit()
        except IntegrityError as exc:
            self._db.rollback()
            raise ValueError(f"Service « {service['name']} » déjà présent dans la liste.") from exc
        self._db.refresh(row)
        return service_to_dict(row)
