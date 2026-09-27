"""Dépôt des MOTEURS — version PostgreSQL (Étape 4).

Même interface que la version mémoire (Étape 3) :
    get(motor_id) -> dict | None
    create(motor: dict) -> dict      # lève ValueError si déjà présent
    update(motor: dict) -> dict      # lève KeyError si inconnu
Les dictionnaires renvoyés sont « prêts pour l'API » (dates en ISO).
"""

from sqlalchemy.orm import Session

from app.models.motor import Motor
from app.repositories.serializers import motor_to_dict


class MotorRepository:
    """Stocke et retrouve les fiches moteur dans PostgreSQL."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, motor_id: str) -> dict | None:
        """Renvoie la fiche moteur, ou None si inconnue."""
        motor = self._db.get(Motor, motor_id)
        return motor_to_dict(motor) if motor else None

    def create(self, motor: dict) -> dict:
        """Enregistre un nouveau moteur (created_at posé par la base)."""
        if self._db.get(Motor, motor["motor_id"]) is not None:
            raise ValueError(f"Moteur {motor['motor_id']} déjà enregistré.")

        row = Motor(**motor)
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return motor_to_dict(row)

    def update(self, motor: dict) -> dict:
        """Met à jour un moteur existant (les champs à None ne sont pas
        modifiés ; motor_id et created_at ne sont jamais écrasés)."""
        row = self._db.get(Motor, motor["motor_id"])
        if row is None:
            raise KeyError(f"Moteur {motor['motor_id']} inconnu.")

        for key, value in motor.items():
            if value is not None and key not in ("motor_id", "created_at"):
                setattr(row, key, value)
        self._db.commit()
        self._db.refresh(row)
        return motor_to_dict(row)
