"""Connexion PostgreSQL — SQLAlchemy 2.

- engine          : connexion bas-niveau à la base
- SessionLocal    : fabrique de sessions (une session par requête)
- Base            : classe mère pour tous les modèles ORM

La base de données est OPTIONNELLE pour l'étape 3 : si DATABASE_URL pointe
vers une base indisponible, on lève une erreur claire qui invitera à lancer
Docker Compose (PostgreSQL) au moment de l'étape 4.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """Classe mère pour tous les modèles SQLAlchemy."""
    pass


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db():
    """Dépendance FastAPI : fournit une session de base de données.

    Utilisation dans une route :
        def ma_route(db: Session = Depends(get_db)): ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
