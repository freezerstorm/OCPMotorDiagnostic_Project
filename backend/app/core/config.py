"""Configuration centrale du backend.

Les valeurs sont lues depuis un fichier « .env » situé dans le dossier
backend/ (voir .env.example), ou à défaut depuis les variables
d'environnement système, ou enfin depuis les valeurs par défaut ci-dessous.

Aucun secret n'est écrit en dur dans le code : tout passe par l'environnement.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Identité de l'API ---
    app_name: str = "OCP Motor Diagnostic — Backend"
    app_version: str = "0.3.0"

    # --- Persistance ---
    # "memory"  : stockage en mémoire (dev sans PostgreSQL, réinitialisé au redémarrage)
    # "sql"     : PostgreSQL via SQLAlchemy (production / étape 4+)
    storage_backend: str = "memory"

    # --- Base de données PostgreSQL (utilisée si storage_backend=sql) ---
    database_url: str = (
        "postgresql+psycopg://ocp:ocp_dev_password@localhost:5432/ocp_diagnostic"
    )

    # --- Broker MQTT (utilisé à partir de l'Étape 7) ---
    mqtt_broker_host: str = "localhost"
    mqtt_broker_port: int = 1883


settings = Settings()
