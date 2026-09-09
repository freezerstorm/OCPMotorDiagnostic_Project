"""Routes : vérification de l'état du backend."""

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/health", summary="État du backend")
def health() -> dict:
    """Route de contrôle utilisée par le frontend pour savoir si le backend répond."""
    return {
        "status": "ok",
        "application": settings.app_name,
        "version": settings.app_version,
    }
