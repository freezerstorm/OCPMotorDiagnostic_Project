"""Routes API du REGISTRE NUMÉRIQUE.

- GET /api/v1/registre
    Toutes les lignes du registre (historique importé + essais de
    l'application), ordonnées par date. Consultation seulement :
    les lignes sont ajoutées automatiquement par l'application
    (décision du technicien) ou l'import d'historique — jamais
    modifiées ni supprimées ici.
"""

from fastapi import APIRouter

from app.db.session import SessionLocal
from app.services import registre as registre_service

router = APIRouter(prefix="/registre", tags=["Registre"])


@router.get("")
def get_registre() -> dict:
    """Le registre numérique complet (20 colonnes du fichier Excel)."""
    db = SessionLocal()
    try:
        return registre_service.list_entries(db)
    finally:
        db.close()
