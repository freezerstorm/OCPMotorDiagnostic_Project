"""Configuration d'Alembic (migrations).

Ce fichier relie Alembic à :
1. l'adresse de la base (lue dans la configuration du projet, jamais
   en dur ici) ;
2. les modèles SQLAlchemy (app/models) : Alembic compare l'état de la
   base avec ces modèles pour générer les migrations.

Usage (depuis backend/) :
    .venv/bin/alembic upgrade head          # applique les migrations
    .venv/bin/alembic revision --autogenerate -m "description"
    .venv/bin/alembic downgrade -1          # annule la dernière
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Permet d'importer « app.* » quel que soit le répertoire de lancement
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings  # noqa: E402
from app.models import Base  # noqa: E402  (importe aussi les modèles)

config = context.config

# L'adresse de connexion vient TOUJOURS de la configuration du projet
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Mode « hors ligne » : génère le SQL sans se connecter."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Mode « en ligne » : applique les migrations à la base."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
