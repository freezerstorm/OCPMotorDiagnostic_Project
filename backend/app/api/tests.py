"""Routes : diagnostics (tests) — création, liste, mise à jour de statut.

Pour l'étape 3, le stockage est en mémoire.
L'étape 4 branchera PostgreSQL sans modifier ce fichier.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

from app.schemas.domain import (
    TestCreate,
    TestOut,
    TestStatus,
    TestSummaryOut,
)
from app.services import test_service

router = APIRouter()


@router.get("/recent", response_model=list[TestSummaryOut], summary="Derniers diagnostics")
def recent(limit: int = 6) -> list[TestSummaryOut]:
    """Affiche les 6 derniers tests sur la page d'accueil."""
    return test_service.list_recent(limit=limit)


@router.get("", response_model=list[TestSummaryOut], summary="Liste de tous les diagnostics (historique)")
def list_all() -> list[TestSummaryOut]:
    return test_service.list_all()


@router.get("/{test_id}", response_model=TestOut, summary="Détail d'un diagnostic")
def get_test(test_id: int) -> TestOut:
    t = test_service.get_test(test_id)
    if t is None:
        raise HTTPException(status_code=404, detail="Diagnostic introuvable")
    return t


@router.post("", response_model=TestOut, status_code=201, summary="Créer un nouveau diagnostic")
def create_test(payload: TestCreate) -> TestOut:
    """Crée un nouveau diagnostic (manuel ou automatique).

    Le moteur est automatiquement créé ou mis à jour si motor_id / serial_number
    existe déjà (auto-remplissage du formulaire).
    """
    return test_service.create_test(payload)


@router.patch("/{test_id}/status", response_model=TestOut, summary="Mettre à jour le statut")
def update_status(test_id: int, status: TestStatus) -> TestOut:
    """Utilisé pour faire avancer le cycle de vie : START → ACQUIRING → COMPLETED..."""
    t = test_service.update_status(test_id, status)
    if t is None:
        raise HTTPException(status_code=404, detail="Diagnostic introuvable")
    return t
