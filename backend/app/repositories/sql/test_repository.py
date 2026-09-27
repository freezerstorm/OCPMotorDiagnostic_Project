"""Dépôt des TESTS — version PostgreSQL (Étape 4).

Interface identique à la version mémoire :
    get(test_id) -> dict | None
    add(test: dict) -> dict     # enregistre la fiche + ses mesures
    next_id() -> str            # identifiant lisible « T-0001 » …
    list(motor_id, mode, limit) -> list[dict]
"""

from sqlalchemy import select, text
from sqlalchemy.orm import Session, selectinload

from app.models.test import Measurements, Test
from app.repositories.serializers import test_to_dict


def _flatten(measurements: dict) -> dict:
    """Transforme la structure imbriquée {insulation: {...}, winding: {...},
    values: {...}} en dictionnaire plat pour les colonnes de la table."""
    flat: dict = {}
    for group in ("insulation", "winding", "values"):
        flat.update(measurements.get(group) or {})
    # La tension de test vit dans le groupe « insulation » côté API
    # (insulation.test_voltage_v) et dans une colonne dédiée en base.
    if "test_voltage_v" in flat:
        flat["insulation_test_voltage_v"] = flat.pop("test_voltage_v")
    return flat


class TestRepository:
    """Stocke et retrouve les fiches de diagnostic dans PostgreSQL."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def next_id(self) -> str:
        """Génère l'identifiant lisible du test (ex. « T-0042 ») grâce à
        la séquence SQL dédiée (créée dans la migration 0001)."""
        value = self._db.execute(text("SELECT nextval('test_id_seq')")).scalar_one()
        return f"T-{value:04d}"

    def add(self, test: dict) -> dict:
        """Enregistre une fiche de diagnostic + sa ligne de mesures.

        test doit contenir : test_id, mode, status, motor_id, et
        éventuellement decision, observation, measurements,
        source_ref et created_at (utilisés par l'import historique
        — Étape 15 ; l'API, elle, ne les définit pas).
        """
        flat = _flatten(test.get("measurements") or {})
        measurements = Measurements(
            insulation_test_voltage_v=flat.get("insulation_test_voltage_v"),
            ph1_ph2_mohm=flat.get("ph1_ph2_mohm"),
            ph2_ph3_mohm=flat.get("ph2_ph3_mohm"),
            ph3_ph1_mohm=flat.get("ph3_ph1_mohm"),
            ph1_ground_mohm=flat.get("ph1_ground_mohm"),
            ph2_ground_mohm=flat.get("ph2_ground_mohm"),
            ph3_ground_mohm=flat.get("ph3_ground_mohm"),
            r12_ohm=flat.get("r12_ohm"),
            r23_ohm=flat.get("r23_ohm"),
            r31_ohm=flat.get("r31_ohm"),
            temperature_c=flat.get("temperature_c"),
            current_a=flat.get("current_a"),
            vibration_mm_s=flat.get("vibration_mm_s"),
            continuity_ok=flat.get("continuity_ok"),
            temp_bearing_de_c=flat.get("temp_bearing_de_c"),
            temp_bearing_nde_c=flat.get("temp_bearing_nde_c"),
            ref_meter_insulation=flat.get("ref_meter_insulation"),
            ref_meter_resistance=flat.get("ref_meter_resistance"),
            ref_meter_cl=flat.get("ref_meter_cl"),
            ref_meter_temperature=flat.get("ref_meter_temperature"),
        )
        row = Test(
            test_id=test["test_id"],
            mode=test["mode"],
            status=test.get("status", "completed"),
            decision=test.get("decision"),
            observation=test.get("observation"),
            motor_id=test["motor_id"],
            measurements=measurements,
            source_ref=test.get("source_ref"),
            **(
                {
                    "requested_by_service": admin.get("requested_by_service"),
                    "notice": admin.get("notice"),
                    "work_order": admin.get("work_order"),
                    "received_at": admin.get("received_at"),
                    "repair_internal": admin.get("repair_internal"),
                    "repair_external": admin.get("repair_external"),
                }
                if (admin := test.get("admin"))
                else {}
            ),
            **({"created_at": test["created_at"]} if test.get("created_at") else {}),
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return test_to_dict(row)

    def get_by_source_ref(self, source_ref: str) -> dict | None:
        """Retrouve une fiche par sa référence d'ORIGINE (import historique,
        Étape 15) — permet de ne jamais importer deux fois la même ligne."""
        row = self._db.scalar(
            select(Test)
            .options(selectinload(Test.measurements))
            .where(Test.source_ref == source_ref)
        )
        return test_to_dict(row) if row else None

    def get(self, test_id: str) -> dict | None:
        """Renvoie une fiche de test (avec mesures), ou None."""
        row = self._db.scalar(
            select(Test)
            .options(selectinload(Test.measurements))
            .where(Test.test_id == test_id)
        )
        return test_to_dict(row) if row else None

    def list(
        self,
        motor_id: str | None = None,
        mode: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """Liste les fiches (les plus récentes d'abord), filtres facultatifs."""
        stmt = (
            select(Test)
            .options(selectinload(Test.measurements))
            .order_by(Test.created_at.desc(), Test.id.desc())
            .limit(limit)
        )
        if motor_id:
            stmt = stmt.where(Test.motor_id == motor_id)
        if mode:
            stmt = stmt.where(Test.mode == mode)

        rows = self._db.scalars(stmt).all()
        return [test_to_dict(row) for row in rows]

    def update(self, test_id: str, changes: dict) -> dict | None:
        """Met à jour les champs d'une fiche (ex. status='archived').

        Seules les clés présentes dans « changes » sont modifiées.
        Renvoie la fiche à jour, ou None si le test est inconnu.
        """
        row = self._db.scalar(
            select(Test).where(Test.test_id == test_id)
        )
        if row is None:
            return None

        for key, value in changes.items():
            if key == "admin":
                # Zone administrative : sous-dictionnaire → colonnes plates
                admin = value or {}
                for akey, avalue in admin.items():
                    if hasattr(row, akey):
                        setattr(row, akey, avalue)
                continue
            if key == "measurements":
                # É17 : mesures ajoutées/mises à jour après création
                # (test sous tension saisi en manuel). Fusion : seuls les
                # champs fournis (non nuls) sont écrits.
                flat = _flatten(value or {})
                target = row.measurements
                if target is None:
                    target = Measurements(test_id=row.id)
                    self._db.add(target)
                for mkey, mvalue in flat.items():
                    if mvalue is not None and hasattr(target, mkey):
                        setattr(target, mkey, mvalue)
                continue
            if value is not None and hasattr(row, key):
                setattr(row, key, value)

        self._db.commit()
        # Recharge avec les mesures pour renvoyer la fiche complète
        refreshed = self._db.scalar(
            select(Test)
            .options(selectinload(Test.measurements))
            .where(Test.test_id == test_id)
        )
        return test_to_dict(refreshed)
