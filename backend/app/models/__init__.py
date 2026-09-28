"""Package « models » : les tables de la base de données (SQLAlchemy).

Règles du projet :
- chaque table vit dans son propre fichier (motor.py, test.py…) ;
- les objets Python sont convertis en dictionnaires par les dépôts
  (app/repositories/sql/) — les routes ne manipulent jamais les objets
  SQLAlchemy directement ;
- l'évolution des tables est versionnée par Alembic (dossier alembic/).
"""

from app.models.base import Base
from app.models.motor import Motor
from app.models.registre import RegistreEntry
from app.models.sample import AcquisitionSample
from app.models.service import Service
from app.models.test import Measurements, Test

__all__ = ["Base", "Motor", "Test", "Measurements", "AcquisitionSample", "RegistreEntry", "Service"]
