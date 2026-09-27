"""Point d'entrée de l'API FastAPI.

Ce fichier reste volontairement MINCE : il crée l'application, gère le
cycle de vie (démarrage/arrêt du client MQTT), active le CORS (dev) et
branche les routeurs.
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.mqtt.client import mqtt_client
from app.services.acquisition import acquisition_manager
from app.ws.manager import hub
from app.ws.routes import attach_websocket_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Démarrage : branche le hub WebSocket + connecte le client MQTT.

    Arrêt : coupe proprement la connexion MQTT.
    """
    hub.attach_loop(asyncio.get_running_loop())
    mqtt_client.start()
    # Surveillance permanente : détecte la perte d'un kit en pleine acquisition
    watchdog_task = asyncio.create_task(acquisition_manager.watchdog())
    yield
    watchdog_task.cancel()
    mqtt_client.stop()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Backend du kit de diagnostic de moteurs électriques (OCP). "
        "Documentation interactive des routes : /docs"
    ),
    lifespan=lifespan,
)

# --- CORS : DEV UNIQUEMENT (toutes origines autorisées) ---
# En développement, le navigateur passe par le proxy Vite (frontend),
# donc le CORS n'intervient que si l'on appelle l'API directement
# depuis une autre origine. À restreindre avant toute mise en production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routes HTTP de l'application (regroupées sous /api/v1) ---
app.include_router(api_router)

# --- Routes WebSocket (temps réel) ---
attach_websocket_routes(app)


@app.get("/api/v1/health")
def health() -> dict:
    """Route de contrôle : vérifie que le backend est bien vivant."""
    return {
        "status": "ok",
        "application": settings.app_name,
        "version": settings.app_version,
    }
