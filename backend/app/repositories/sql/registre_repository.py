"""Dépôt du REGISTRE NUMÉRIQUE — lecture et ajout de lignes.

Le registre n'offre AUCUNE modification ni suppression : chaque essai
(ou ligne importée) ajoute une ligne, jamais remplacée (demande client).
"""

from sqlalchemy import func, nullslast, select
from sqlalchemy.orm import Session

from app.models.registre import RegistreEntry

# Ordre d'affichage (demande client) : dates RÉCENTES en premier ;
# l'ordre d'import départage les lignes de même date ; les lignes
# sans date (non renseignée dans le fichier) restent en dernier.
_ORDER = (
    nullslast(RegistreEntry.entry_date.desc()),
    RegistreEntry.id.desc(),
)


def entry_to_dict(row: RegistreEntry) -> dict:
    """Ligne ORM → dictionnaire plat (clés = colonnes du registre réel)."""
    return {
        "entry_date": row.entry_date.isoformat() if row.entry_date else None,
        "matricule": row.matricule,
        "di_ot": row.di_ot,
        "couplage": row.couplage,
        "service": row.service,
        "un_v": row.un_v,
        "in_a": row.in_a,
        "uo_v": row.uo_v,
        "io_a": row.io_a,
        "isolement": row.isolement,
        "isolement_ph_m": row.isolement_ph_m,
        "r": row.r,
        "nature": row.nature,
        "puissance": row.puissance,
        "societe": row.societe,
        "bt_mt": row.bt_mt,
        "observation": row.observation,
        "source": row.source,
    }


class RegistreRepository:
    """Ajoute et relit les lignes du registre (jamais modifier/supprimer)."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def exists_for_test(self, test_row_id: int) -> bool:
        """Vrai si cet essai a déjà sa ligne (idempotence)."""
        return self._db.scalar(
            select(RegistreEntry.id).where(RegistreEntry.test_row_id == test_row_id)
        ) is not None

    def exists_source_ref(self, source_ref: str) -> bool:
        """Vrai si cette référence d'import existe déjà (idempotence)."""
        return self._db.scalar(
            select(RegistreEntry.id).where(RegistreEntry.source_ref == source_ref)
        ) is not None

    def add(self, values: dict, test_row_id: int | None, source: str,
            source_ref: str | None = None) -> RegistreEntry:
        """Ajoute UNE ligne (les champs absents restent vides)."""
        row = RegistreEntry(
            test_row_id=test_row_id, source=source,
            source_ref=source_ref, **values,
        )
        self._db.add(row)
        self._db.commit()
        return row

    def list(self) -> list[dict]:
        """Toutes les lignes, ordonnées par date d'essai."""
        rows = self._db.scalars(select(RegistreEntry).order_by(*_ORDER)).all()
        return [entry_to_dict(row) for row in rows]

    def count(self) -> int:
        return self._db.scalar(select(func.count(RegistreEntry.id))) or 0
