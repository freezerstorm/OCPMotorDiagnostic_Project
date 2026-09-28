"""Point d'entrée de l'API FastAPI.

Ce fichier reste volontairement MINCE : il crée l'application, gère le
cycle de vie (démarrage/arrêt du client MQTT), active le CORS (dev) et
branche les routeurs.
"""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

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


# --- Interface web « atelier » (production simple) -------------------
# Quand l'interface est construite (npm run build → frontend/dist/),
# le backend la sert LUI-MÊME : tout l'atelier tient sur UNE adresse,
# http://localhost:8000 — c'est ce que fait le lanceur Lancer-OCP.bat.
# En développement, frontend/dist/ n'existe pas (ou est ignoré) : ce
# bloc ne change alors STRICTEMENT rien, l'interface passe par Vite.
DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"

if (DIST / "index.html").is_file():

    @app.get("/{chemin:path}", include_in_schema=False)
    def interface_atelier(chemin: str) -> FileResponse:
        """Sert l'interface construite (SPA) et les fichiers publics.

        - un fichier existant dans frontend/dist/ est renvoyé tel quel
          (js, css, page de téléchargement, patch…) ;
        - toute autre adresse renvoie index.html : c'est ensuite le
          routage interne de React qui affiche la bonne page ;
        - une adresse /api/... inconnue reste une erreur 404 JSON
          (on ne renvoie pas index.html à un appel d'API).
        """
        if chemin.startswith("api/"):
            raise HTTPException(status_code=404, detail="Route API inconnue.")
        fichier = (DIST / chemin).resolve()
        if chemin and fichier.is_file() and str(fichier).startswith(str(DIST)):
            return FileResponse(fichier)
        return FileResponse(DIST / "index.html")
