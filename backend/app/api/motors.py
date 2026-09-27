"""Routes API des MOTEURS.

Rappel (§19 du cahier des charges) : il n'existe volontairement PAS de
page « Gestion des moteurs » dans l'interface. Ces routes servent
uniquement le formulaire de diagnostic :
- GET  /api/v1/motors/{motor_id} : auto-remplissage si le moteur est connu ;
- POST /api/v1/motors            : création (au besoin, lors d'un test).
"""

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_motor_repository
from app.repositories.sql.motor_repository import MotorRepository
from app.schemas.motors import MotorCreate, MotorRead

router = APIRouter(prefix="/motors", tags=["Moteurs"])


@router.get("/{motor_id:path}", response_model=MotorRead)
def get_motor(motor_id: str, repo: MotorRepository = Depends(get_motor_repository)) -> MotorRead:
    """Renvoie la fiche d'un moteur (404 si inconnu)."""
    motor = repo.get(motor_id)
    if motor is None:
        raise HTTPException(status_code=404, detail=f"Moteur '{motor_id}' introuvable.")
    return MotorRead.model_validate(motor)


@router.post("", status_code=201, response_model=MotorRead)
def create_motor(payload: MotorCreate, repo: MotorRepository = Depends(get_motor_repository)) -> MotorRead:
    """Enregistre un nouveau moteur (409 s'il existe déjà)."""
    try:
        motor = repo.create(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return MotorRead.model_validate(motor)
