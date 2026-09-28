"""Dépendances partagées par les routes.

FastAPI injecte ces dépôts dans les fonctions des routes. Chaque dépôt
travaille sur une session PostgreSQL dédiée à la requête en cours
(ouverte puis refermée automatiquement par get_db).
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.sql.motor_repository import MotorRepository
from app.repositories.sql.service_repository import ServiceRepository
from app.repositories.sql.test_repository import TestRepository


def get_motor_repository(db: Session = Depends(get_db)) -> MotorRepository:
    """Fournit le dépôt des moteurs pour la requête en cours."""
    return MotorRepository(db)


def get_service_repository(db: Session = Depends(get_db)) -> ServiceRepository:
    """Fournit le dépôt des services (catalogue du formulaire)."""
    return ServiceRepository(db)


def get_test_repository(db: Session = Depends(get_db)) -> TestRepository:
    """Fournit le dépôt des tests pour la requête en cours."""
    return TestRepository(db)
