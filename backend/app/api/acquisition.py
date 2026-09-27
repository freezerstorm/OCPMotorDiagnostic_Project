"""Routes API de l'ACQUISITION automatique (~60 s).

- POST /api/v1/tests/{test_id}/acquisition/start  → START (kit requis)
- POST /api/v1/tests/{test_id}/acquisition/stop   → QUIT
- GET  /api/v1/tests/{test_id}/samples            → série temporelle

Le déroulé temps réel (échantillons, états) est poussé par WebSocket
(/ws/kits) : cette API ne fait que déclencher et interroger.
"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.test import Test
from app.repositories.sql.sample_repository import SampleRepository
from app.services.acquisition import acquisition_manager
from app.services.kits import kit_registry

router = APIRouter(prefix="/tests", tags=["Acquisition"])


class StartAcquisitionRequest(BaseModel):
    """Corps de la demande de démarrage : le kit à utiliser."""

    model_config = ConfigDict(extra="forbid")
    kit_id: str


@router.post("/{test_id}/acquisition/start", status_code=201)
async def start_acquisition(test_id: str, payload: StartAcquisitionRequest) -> dict:
    """Démarre l'acquisition (START) — le kit doit être réellement connecté."""
    if not kit_registry.is_online(payload.kit_id):
        raise HTTPException(
            status_code=400,
            detail=f"Kit '{payload.kit_id}' hors ligne : impossible de démarrer (§8).",
        )
    try:
        return await acquisition_manager.start(test_id, payload.kit_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{test_id}/acquisition/stop")
async def stop_acquisition(test_id: str) -> dict:
    """Arrête l'acquisition (QUIT)."""
    await acquisition_manager.stop(test_id, reason="user_quit")
    return {"test_id": test_id, "status": "stopped"}


@router.get("/{test_id}/samples")
def list_samples(test_id: str) -> dict:
    """Série temporelle complète d'un test (pour la page View Graph)."""
    db = SessionLocal()
    try:
        row = db.scalar(select(Test).where(Test.test_id == test_id))
        if row is None:
            raise HTTPException(status_code=404, detail=f"Test '{test_id}' introuvable.")
        samples = SampleRepository(db).list_for_test(row.id)
        return {"test_id": test_id, "count": len(samples), "samples": samples}
    finally:
        db.close()
