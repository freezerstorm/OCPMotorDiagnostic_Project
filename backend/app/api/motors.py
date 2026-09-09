"""Routes : moteurs (recherche, création, consultation)."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.schemas.domain import MotorCreate, MotorOut
from app.services import motor_service

router = APIRouter()


@router.get("", response_model=list[MotorOut], summary="Liste des moteurs récents")
def list_motors(limit: int = Query(50, ge=1, le=500)) -> list[MotorOut]:
    return motor_service.list_recent(limit=limit)


@router.get("/find", response_model=Optional[MotorOut], summary="Recherche par ID ou matricule")
def find_motor(
    motor_id: Optional[str] = Query(None, description="Identifiant interne"),
    serial_number: Optional[str] = Query(None, description="Matricule"),
) -> Optional[MotorOut]:
    """Utilisé pour l'auto-remplissage du formulaire quand le technicien saisit un ID connu."""
    if not motor_id and not serial_number:
        raise HTTPException(status_code=400, detail="Préciser motor_id ou serial_number")
    return motor_service.find_motor(motor_id=motor_id, serial_number=serial_number)


@router.get("/{motor_pk}", response_model=MotorOut, summary="Détail d'un moteur")
def get_motor(motor_pk: int) -> MotorOut:
    m = motor_service.get_motor(motor_pk)
    if m is None:
        raise HTTPException(status_code=404, detail="Moteur introuvable")
    return m


@router.post("", response_model=MotorOut, status_code=201, summary="Créer ou mettre à jour un moteur")
def upsert_motor(payload: MotorCreate) -> MotorOut:
    return motor_service.upsert_motor(payload)
