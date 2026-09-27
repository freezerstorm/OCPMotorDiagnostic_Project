"""Routes API des KITS (présence temps réel sur le broker MQTT).

Ces routes servent la page « Connexion au kit » (§8) :
- GET /api/v1/kits : liste les kits connus avec leur état.
La « connexion » d'un kit est détectée passivement (messages MQTT),
il n'y a pas de POST : on ne peut pas inventer un kit absent.
"""

from fastapi import APIRouter, HTTPException

from app.schemas.kits import KitStatus
from app.services.kits import kit_registry

router = APIRouter(prefix="/kits", tags=["Kits"])


@router.get("", response_model=list[KitStatus])
def list_kits() -> list[KitStatus]:
    """Liste les kits connus du broker et leur état actuel."""
    return [KitStatus.model_validate(item) for item in kit_registry.list()]


@router.get("/{kit_id}", response_model=KitStatus)
def get_kit(kit_id: str) -> KitStatus:
    """État d'un kit précis (404 si jamais vu)."""
    for item in kit_registry.list():
        if item["kit_id"] == kit_id:
            return KitStatus.model_validate(item)
    raise HTTPException(status_code=404, detail=f"Kit '{kit_id}' inconnu.")
