"""Assembleur des routes API.

Chaque module de app/api/ déclare son propre sous-routeur ; ce fichier
les regroupe tous sous le préfixe commun /api/v1. Ajouter un domaine =
créer un module + l'inclure ici.
"""

from fastapi import APIRouter

from app.api import acquisition, analysis, kits, motors, registre, report, services, tests

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(motors.router)
api_router.include_router(tests.router)
api_router.include_router(kits.router)
api_router.include_router(acquisition.router)
api_router.include_router(analysis.router)
api_router.include_router(report.router)
api_router.include_router(registre.router)
api_router.include_router(services.router)
