"""Configuration centrale du backend.

Les valeurs sont lues depuis un fichier « .env » situé dans le dossier
backend/ (voir .env.example), ou à défaut depuis les variables
d'environnement du système, ou enfin depuis les valeurs par défaut ci-dessous.

Aucun secret n'est écrit en dur dans le code : tout passe par l'environnement.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Regroupe toutes les valeurs de configuration du projet."""

    model_config = SettingsConfigDict(
        env_file=".env",      # fichier lu si présent (lancé depuis backend/)
        env_file_encoding="utf-8",
        extra="ignore",       # on ignore les variables inconnues
    )

    # --- Identité de l'API ---
    app_name: str = "OCP Motor Diagnostic — Backend"
    app_version: str = "0.1.0"

    # --- Base de données PostgreSQL (servira à partir de l'Étape 4) ---
    database_url: str = (
        "postgresql+psycopg://ocp:ocp_dev_password@localhost:5432/ocp_diagnostic"
    )

    # --- Broker MQTT (servira à partir de l'Étape 7) ---
    mqtt_broker_host: str = "localhost"
    mqtt_broker_port: int = 1883


# Instance unique partagée par tout le backend.
# Exemple d'utilisation ailleurs :  from app.core.config import settings
settings = Settings()
