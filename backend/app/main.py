"""Point d'entrée de l'API FastAPI — Étape 1 (squelette).

Ce fichier reste volontairement MINCE : il assemble des modules.
Toutes les routes seront ajoutées dans app/api/ (Étape 3).
"""

from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Backend du kit de diagnostic de moteurs électriques (OCP). "
        "Documentation interactive des routes : /docs"
    ),
)


@app.get("/api/v1/health")
def health() -> dict:
    """Route de contrôle : vérifie que le backend est bien vivant."""
    return {
        "status": "ok",
        "application": settings.app_name,
        "version": settings.app_version,
    }
