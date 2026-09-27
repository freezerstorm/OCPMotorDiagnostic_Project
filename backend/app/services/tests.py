"""Service des TESTS de diagnostic : création d'une fiche de test.

Logique métier appliquée (§9 du cahier des charges) :
- si le moteur existe déjà dans l'historique, ses informations sont
  reprises ; les champs fournis permettent de les corriger ;
- si le moteur est inconnu, il est créé à partir de la fiche saisie ;
- le statut initial dépend du mode : un test manuel est enregistré
  complet, un test automatique reste un brouillon (l'acquisition du kit
  le fera passer à « completed » à l'Étape 8).
"""

from app.repositories.sql.motor_repository import MotorRepository
from app.repositories.sql.test_repository import TestRepository
from app.schemas.tests import (
    TEST_MODE_MANUAL,
    TEST_STATUS_COMPLETED,
    TEST_STATUS_DRAFT,
    TEST_STATUS_OFFLINE_VALIDATED,
    TestCreate,
)


def _build_motor_payload(payload_motor: dict, existing_motor: dict | None) -> dict:
    """Construit la fiche moteur à enregistrer.

    - Aucun moteur connu → la fiche saisie est utilisée telle quelle.
    - Moteur connu → on part de la fiche existante et on écrase
      uniquement les champs renseignés dans le formulaire (correction
      possible par le technicien).
    """
    if existing_motor is None:
        return dict(payload_motor)

    merged = dict(existing_motor)
    for key, value in payload_motor.items():
        if value is not None:
            merged[key] = value
    return merged


def create_test(payload: TestCreate, motor_repo: MotorRepository, test_repo: TestRepository) -> dict:
    """Crée un test (et son moteur si besoin) puis renvoie la fiche complète."""
    motor_data = payload.motor.model_dump()
    motor_id = motor_data["motor_id"]

    # 1. Récupérer ou créer le moteur
    existing = motor_repo.get(motor_id)
    motor_record = (
        motor_repo.create(motor_data)
        if existing is None
        else motor_repo.update(_build_motor_payload(motor_data, existing))
    )

    # 2. Construire la fiche de test (created_at est posé par la base).
    # É17 : la session naît TOUJOURS en brouillon — le statut évolue
    # par les validations du technicien (validate-offline puis
    # validate-online) et l'acquisition du kit. L'ancienne règle
    # « manuel → completed » appartient au flux tout-en-un.
    record = {
        "test_id": test_repo.next_id(),
        "mode": payload.mode,
        "status": TEST_STATUS_DRAFT,
        "decision": None,
        "observation": None,
        "motor_id": motor_id,
        "measurements": payload.measurements.model_dump(),
        "admin": payload.admin.model_dump() if payload.admin else {},
    }

    # 3. Enregistrer et renvoyer la fiche (avec les infos moteur rattachées)
    stored = test_repo.add(record)
    return {**stored, "motor": motor_record}


def update_test(
    test_id: str,
    changes: dict,
    test_repo: TestRepository,
) -> dict | None:
    """Applique les changements demandés à une fiche de diagnostic.

    Utilisé à l'Étape 6 pour archiver un test (status → 'archived') ;
    servira aussi à l'Étape 11 pour enregistrer la décision du
    technicien et son observation.
    """
    return test_repo.update(test_id, changes)


def validate_offline(test_id: str, test_repo: TestRepository) -> dict | None:
    """VALIDER LE TEST HORS TENSION (É16, §5.4).

    La session passe de « draft » à « offline_validated ». Refusé
    (ValueError) si la session n'est plus en brouillon.
    """
    row = test_repo.get(test_id)
    if row is None:
        return None
    if row["status"] != TEST_STATUS_DRAFT:
        raise ValueError(
            f"Le test hors tension a déjà été validé "
            f"(statut actuel : {row['status']})."
        )
    return test_repo.update(test_id, {"status": TEST_STATUS_OFFLINE_VALIDATED})


def validate_online(test_id: str, test_repo: TestRepository) -> dict | None:
    """VALIDER LE TEST SOUS TENSION (É16, §6.1).

    La session passe de « offline_validated » à « completed ».
    Refusé (ValueError) si le test hors tension n'a pas été validé.
    """
    row = test_repo.get(test_id)
    if row is None:
        return None
    if row["status"] != TEST_STATUS_OFFLINE_VALIDATED:
        raise ValueError(
            "Le test hors tension doit être validé avant de valider "
            f"le test sous tension (statut actuel : {row['status']})."
        )
    # Décision client (26/09/2026) : la tension d'alimentation est
    # OBLIGATOIRE pour valider le test sous tension.
    tension = ((row.get("measurements") or {}).get("values") or {}).get("supply_voltage_v")
    if tension is None:
        raise ValueError(
            "Tension d'alimentation manquante : saisissez la tension "
            "d'alimentation (V) mesurée pendant le test avant de valider."
        )
    return test_repo.update(test_id, {"status": TEST_STATUS_COMPLETED})
