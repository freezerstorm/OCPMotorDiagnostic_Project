"""Routes API des TESTS de diagnostic.

Une seule fiche pour les deux modes (§3). Le POST crée le test ET le
moteur si celui-ci est inconnu (logique dans app/services/tests.py).
"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select

from app.api.deps import get_motor_repository, get_test_repository
from app.db.session import SessionLocal
from app.models.test import Test
from app.repositories.sql.motor_repository import MotorRepository
from app.repositories.sql.test_repository import TestRepository
from app.schemas.tests import (
    TEST_MODE_AUTO,
    TEST_MODE_MANUAL,
    TestCreate,
    TestRead,
    TestUpdate,
)
from app.services import registre as registre_service
from app.services.tests import (
    create_test,
    update_test,
    validate_offline,
    validate_online,
)

router = APIRouter(prefix="/tests", tags=["Tests"])


@router.get("", response_model=list[TestRead])
def list_tests(
    motor_id: str | None = Query(default=None, description="Filtre : identifiant moteur"),
    mode: Literal[TEST_MODE_MANUAL, TEST_MODE_AUTO] | None = Query(default=None, description="Filtre : mode de test"),
    limit: int = Query(default=50, ge=1, le=200, description="Nombre maximum de résultats"),
    motor_repo: MotorRepository = Depends(get_motor_repository),
    test_repo: TestRepository = Depends(get_test_repository),
) -> list[TestRead]:
    """Liste les fiches de diagnostic (plus récentes d'abord)."""
    tests = test_repo.list(motor_id=motor_id, mode=mode, limit=limit)
    return _with_motors(tests, motor_repo)


@router.post("", status_code=201, response_model=TestRead)
def create_test_route(
    payload: TestCreate,
    motor_repo: MotorRepository = Depends(get_motor_repository),
    test_repo: TestRepository = Depends(get_test_repository),
) -> TestRead:
    """Crée une fiche de diagnostic (manuel ou automatique)."""
    record = create_test(payload, motor_repo, test_repo)
    return TestRead.model_validate(record)


@router.post("/{test_id}/validate-offline", response_model=TestRead)
def validate_offline_route(
    test_id: str,
    motor_repo: MotorRepository = Depends(get_motor_repository),
    test_repo: TestRepository = Depends(get_test_repository),
) -> TestRead:
    """VALIDER LE TEST HORS TENSION (§5.4) — l'étape 4 du parcours.

    La session passe de « brouillon » à « hors tension validé ».
    """
    try:
        record = validate_offline(test_id, test_repo)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if record is None:
        raise HTTPException(status_code=404, detail=f"Test '{test_id}' introuvable.")
    return TestRead.model_validate(_with_motor(record, motor_repo))


@router.post("/{test_id}/validate-online", response_model=TestRead)
def validate_online_route(
    test_id: str,
    motor_repo: MotorRepository = Depends(get_motor_repository),
    test_repo: TestRepository = Depends(get_test_repository),
) -> TestRead:
    """VALIDER LE TEST SOUS TENSION (§6.1) — l'étape 6 du parcours.

    Refusé si le test hors tension n'a pas d'abord été validé.
    """
    try:
        record = validate_online(test_id, test_repo)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if record is None:
        raise HTTPException(status_code=404, detail=f"Test '{test_id}' introuvable.")
    return TestRead.model_validate(_with_motor(record, motor_repo))


@router.get("/{test_id}", response_model=TestRead)
def get_test(
    test_id: str,
    motor_repo: MotorRepository = Depends(get_motor_repository),
    test_repo: TestRepository = Depends(get_test_repository),
) -> TestRead:
    """Renvoie une fiche de diagnostic (404 si inconnue)."""
    test = test_repo.get(test_id)
    if test is None:
        raise HTTPException(status_code=404, detail=f"Test '{test_id}' introuvable.")
    return TestRead.model_validate(_with_motor(test, motor_repo))


def _with_motor(test: dict, motor_repo: MotorRepository) -> dict:
    """Rattache la fiche moteur au test avant sérialisation."""
    motor = motor_repo.get(test["motor_id"])
    if motor is None:
        raise HTTPException(status_code=500, detail=f"Moteur '{test['motor_id']}' manquant en mémoire.")
    return {**test, "motor": motor}


def _with_motors(tests: list[dict], motor_repo: MotorRepository) -> list[TestRead]:
    """Rattache la fiche moteur à chaque test de la liste."""
    return [TestRead.model_validate(_with_motor(t, motor_repo)) for t in tests]


@router.patch("/{test_id}", response_model=TestRead)
def update_test_route(
    test_id: str,
    payload: TestUpdate,
    motor_repo: MotorRepository = Depends(get_motor_repository),
    test_repo: TestRepository = Depends(get_test_repository),
) -> TestRead:
    """Met à jour partiellement une fiche (ex. archiver un test)."""
    changes = payload.model_dump(exclude_unset=True)
    updated = update_test(test_id, changes, test_repo)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Test '{test_id}' introuvable.")

    # REGISTRE NUMÉRIQUE : après la décision du technicien (validation
    # du diagnostic faite à l'étape précédente), l'essai rejoint
    # automatiquement le registre — une ligne indépendante, jamais
    # remplacée. Un échec de registre n'annule JAMAIS la décision
    # (l'outil de complément tools/backfill_registre.py peut réparer).
    if changes.get("decision"):
        db = SessionLocal()
        try:
            row = db.scalar(select(Test).where(Test.test_id == test_id))
            if row is not None:
                registre_service.sync_entry_for_test(
                    db, row,
                    societe_reparation=changes.get("repair_company"),
                )
        except Exception:
            import logging

            logging.getLogger("registre").exception(
                "Ligne de registre non ajoutée pour %s (compléter via backfill).", test_id
            )
        finally:
            db.close()

    return TestRead.model_validate(_with_motor(updated, motor_repo))
