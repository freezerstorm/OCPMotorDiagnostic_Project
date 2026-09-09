"""Service métier des diagnostics (tests).

Isole la logique de création, mise à jour et listing des tests.
Pour l'étape 3, le stockage est en mémoire (app/services/storage.py).
À l'étape 4, seul le repository changera ; ce service restera identique.
"""

from __future__ import annotations

from typing import List, Optional

from app.schemas.domain import (
    MotorCreate,
    TechnicianDecision,
    TestCreate,
    TestMode,
    TestOut,
    TestStatus,
    TestSummaryOut,
)
from app.services import motor_service, storage


def _build_summary(test_row: dict, motor_row: dict) -> TestSummaryOut:
    label_parts = []
    if motor_row.get("motor_id"):
        label_parts.append(motor_row["motor_id"])
    if motor_row.get("serial_number"):
        label_parts.append(f"({motor_row['serial_number']})")
    if motor_row.get("designation"):
        label_parts.append(motor_row["designation"])
    if not label_parts:
        label_parts.append(f"Moteur #{motor_row['id']}")
    return TestSummaryOut(
        id=test_row["id"],
        mode=TestMode(test_row["mode"]),
        status=TestStatus(test_row["status"]),
        created_at=test_row["created_at"],
        updated_at=test_row["updated_at"],
        technician_decision=TechnicianDecision(test_row["technician_decision"]),
        motor_id=motor_row["id"],
        motor_label=" ".join(label_parts),
        motor_serial=motor_row.get("serial_number"),
        motor_service=motor_row.get("service"),
    )


def _build_out(test_row: dict, motor_row: dict) -> TestOut:
    from app.schemas.domain import MotorOut
    return TestOut(
        id=test_row["id"],
        mode=TestMode(test_row["mode"]),
        status=TestStatus(test_row["status"]),
        created_at=test_row["created_at"],
        updated_at=test_row["updated_at"],
        started_at=test_row.get("started_at"),
        completed_at=test_row.get("completed_at"),
        kit_id=test_row.get("kit_id"),
        technician_decision=TechnicianDecision(test_row["technician_decision"]),
        technician_observation=test_row.get("technician_observation"),
        auto_conclusion=test_row.get("auto_conclusion"),
        motor=MotorOut(**motor_row),
    )


def create_test(payload: TestCreate) -> TestOut:
    """Crée un nouveau diagnostic et son moteur (création ou mise à jour)."""
    motor = motor_service.upsert_motor(payload.motor)
    initial_status = TestStatus.READY if payload.mode == TestMode.auto else TestStatus.IDLE
    row = storage.tests.create({
        "mode": payload.mode.value,
        "status": initial_status.value,
        "kit_id": payload.kit_id,
        "motor_id": motor.id,
    })
    motor_row = storage.motors.get(motor.id)
    return _build_out(row, motor_row)


def get_test(test_id: int) -> Optional[TestOut]:
    t = storage.tests.get(test_id)
    if t is None:
        return None
    m = storage.motors.get(t["motor_id"])
    return _build_out(t, m)


def update_status(test_id: int, status: TestStatus) -> Optional[TestOut]:
    changes = {"status": status.value}
    if status == TestStatus.ACQUIRING:
        changes["started_at"] = __import__("datetime").datetime.utcnow()
    if status in (TestStatus.COMPLETED, TestStatus.ANALYZED, TestStatus.REPORTED):
        changes["completed_at"] = __import__("datetime").datetime.utcnow()
    row = storage.tests.update(test_id, changes)
    if row is None:
        return None
    m = storage.motors.get(row["motor_id"])
    return _build_out(row, m)


def list_recent(limit: int = 6) -> List[TestSummaryOut]:
    out: List[TestSummaryOut] = []
    for t in storage.tests.list_recent(limit=limit):
        m = storage.motors.get(t["motor_id"])
        if m is None:
            continue
        out.append(_build_summary(t, m))
    return out


def list_all() -> List[TestSummaryOut]:
    out: List[TestSummaryOut] = []
    for t in storage.tests.list_all():
        m = storage.motors.get(t["motor_id"])
        if m is None:
            continue
        out.append(_build_summary(t, m))
    return out
