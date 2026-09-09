"""Point d'entrée de l'API FastAPI.

Ce fichier assemble les différents modules. Il reste volontairement MINCE :
la configuration est dans app/core/, les routes dans app/api/.
"""

import sys
from pathlib import Path

# Rend le dossier 'diagnostic_rules/' (à la racine de backend/) importable
# sans avoir à le placer dans app/. Il reste ainsi clairement séparé du
# code de l'application.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Backend du kit de diagnostic de moteurs électriques (OCP). "
        "Documentation interactive des routes : /docs"
    ),
)

# Permet au frontend Vite (port 5173) d'appeler l'API en développement.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # dev uniquement
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
