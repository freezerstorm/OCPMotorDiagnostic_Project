"""Services métier relatifs aux moteurs.

La couche « service » isole la logique métier de la couche API.
Les routes API appellent ces fonctions ; elles-mêmes appellent les repositories.
Quand on passera à PostgreSQL (Étape 4), seul le fichier storage.py changera.
"""

from __future__ import annotations

from typing import List, Optional

from app.schemas.domain import MotorCreate, MotorOut
from app.services import storage


def _row_to_out(row: dict) -> MotorOut:
    return MotorOut(**row)


def get_motor(motor_pk: int) -> Optional[MotorOut]:
    row = storage.motors.get(motor_pk)
    return _row_to_out(row) if row else None


def find_motor(motor_id: Optional[str] = None, serial_number: Optional[str] = None) -> Optional[MotorOut]:
    """Recherche un moteur par son identifiant interne OU son matricule.

    Utilisé pour l'auto-remplissage du formulaire quand le technicien saisit
    un ID déjà connu.
    """
    if motor_id:
        for row in storage.motors.list_all():
            if row.get("motor_id") == motor_id:
                return _row_to_out(row)
    if serial_number:
        for row in storage.motors.list_all():
            if row.get("serial_number") == serial_number:
                return _row_to_out(row)
    return None


def upsert_motor(payload: MotorCreate) -> MotorOut:
    """Crée ou met à jour un moteur (recherche par motor_id puis serial_number)."""
    row = storage.motors.create_or_update_by_motor_id(payload.model_dump(exclude_none=False))
    return _row_to_out(row)


def list_recent(limit: int = 6) -> List[MotorOut]:
    return [_row_to_out(r) for r in storage.motors.list_recent(limit=limit)]
