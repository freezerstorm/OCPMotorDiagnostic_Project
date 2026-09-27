"""Base commune des modèles SQLAlchemy.

Toutes les tables héritent de Base pour être enregistrées dans une
même « métadonnée », utilisée par Alembic pour construire les migrations.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Classe de base déclarative (style SQLAlchemy 2.0)."""
