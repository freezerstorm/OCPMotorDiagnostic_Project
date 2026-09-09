"""Point d'entrée des routes API versionnées.

Les routes sont réparties dans des fichiers par thème (health, motors, tests)
et assemblées ici. Chaque fichier de route ne contient QUE la logique HTTP :
lecture de la requête, appel du service, renvoi de la réponse.
"""

from fastapi import APIRouter

from app.api import health, motors, tests

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router, tags=["Système"])
api_router.include_router(motors.router, prefix="/motors", tags=["Moteurs"])
api_router.include_router(tests.router, prefix="/tests", tags=["Diagnostics"])
