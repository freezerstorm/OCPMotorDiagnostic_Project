"""Connexion PostgreSQL (SQLAlchemy).

L'adresse de la base vient de la configuration (backend/.env ou
variable DATABASE_URL). Aucun accès direct depuis les routes : elles
passent par les dépôts (app/repositories/sql/), qui reçoivent une
« session » grâce à get_db().
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# engine : le « connecteur » vers PostgreSQL (créé une seule fois).
engine = create_engine(settings.database_url, pool_pre_ping=True)

# SessionLocal : usine à « sessions » (une session = une conversation
# avec la base, utilisée pendant la durée d'une requête API).
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Dépendance FastAPI : fournit une session puis la referme.

    Chaque requête HTTP ouvre SA propre session : deux requêtes
    simultanées ne se marchent pas dessus.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
