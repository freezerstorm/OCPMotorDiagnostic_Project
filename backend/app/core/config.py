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
    app_version: str = "0.18.1"

    # --- Base de données PostgreSQL (servira à partir de l'Étape 4) ---
    database_url: str = (
        "postgresql+psycopg://ocp:ocp_dev_password@localhost:5432/ocp_diagnostic"
    )

    # --- Broker MQTT (Étape 7) ---
    mqtt_broker_host: str = "localhost"
    mqtt_broker_port: int = 1883
    # Préfixe des sujets MQTT : « {prefix}/kits/{kit_id}/status » etc.
    # Permet d'isoler plusieurs ateliers/sites sur un même broker.
    mqtt_topic_prefix: str = "ocp"
    # Prototype MATÉRIEL unique : le sketch Arduino n'envoie pas de
    # kit_id dans ses messages → identifiant affiché par l'application.
    mqtt_prototype_kit_id: str = "ESP32-01"

    # Délai (s) sans message d'un kit avant de le considérer déconnecté
    kit_online_timeout_s: float = 8.0
    # --- Acquisition automatique (Étape 8) ---
    acquisition_duration_s: float = 60.0          # durée visée du test (~60 s)
    acquisition_lost_timeout_s: float = 5.0       # perte du kit si silence > 5 s


# Instance unique partagée par tout le backend.
# Exemple d'utilisation ailleurs :  from app.core.config import settings
settings = Settings()
