"""Stockage temporaire en mémoire.

Ce module simule une base de données avant l'Étape 4 (PostgreSQL).
Il est volontairement simple : des dictionnaires Python + un compteur d'ID.

Quand l'étape 4 arrivera, on remplacera InMemoryMotorRepository et
InMemoryTestRepository par des versions SQLAlchemy. Les couches au-dessus
(services, API) ne changeront pas car elles s'appuient sur l'interface
des repositories, pas sur l'implémentation.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from threading import Lock
from typing import Dict, List, Optional


def _now() -> datetime:
    return datetime.utcnow()


class InMemoryMotorRepository:
    """Stockage des moteurs en mémoire."""

    def __init__(self) -> None:
        self._seq: int = 0
        self._rows: Dict[int, dict] = {}
        self._by_motor_id: Dict[str, int] = {}
        self._by_serial: Dict[str, int] = {}
        self._lock = Lock()

    # --- interne ---
    def _next_id(self) -> int:
        self._seq += 1
        return self._seq

    def _index(self, row: dict, old_key_id: Optional[str], old_serial: Optional[str]) -> None:
        if old_key_id and old_key_id in self._by_motor_id:
            del self._by_motor_id[old_key_id]
        if old_serial and old_serial in self._by_serial:
            del self._by_serial[old_serial]
        if row.get("motor_id"):
            self._by_motor_id[row["motor_id"]] = row["id"]
        if row.get("serial_number"):
            self._by_serial[row["serial_number"]] = row["id"]

    # --- API publique ---
    def create_or_update_by_motor_id(self, data: dict) -> dict:
        """Crée un moteur, ou met à jour celui qui a le même motor_id / serial_number."""
        with self._lock:
            existing_id = None
            if data.get("motor_id") and data["motor_id"] in self._by_motor_id:
                existing_id = self._by_motor_id[data["motor_id"]]
            elif data.get("serial_number") and data["serial_number"] in self._by_serial:
                existing_id = self._by_serial[data["serial_number"]]

            if existing_id is not None:
                row = self._rows[existing_id]
                old_key_id, old_serial = row.get("motor_id"), row.get("serial_number")
                for k, v in data.items():
                    if v is not None:
                        row[k] = v
                row["updated_at"] = _now()
                self._index(row, old_key_id, old_serial)
                return deepcopy(row)

            mid = self._next_id()
            now = _now()
            row = {"id": mid, "created_at": now, "updated_at": now}
            # champs optionnels initialisés à None
            for field in (
                "motor_id", "serial_number", "designation", "brand", "model",
                "manufacturer_number", "rated_power_kw", "rated_voltage_v",
                "rated_current_a", "rated_speed_rpm", "cos_phi", "coupling",
                "service", "di_ot",
            ):
                row[field] = data.get(field)
            self._rows[mid] = row
            self._index(row, None, None)
            return deepcopy(row)

    def get(self, motor_pk: int) -> Optional[dict]:
        return deepcopy(self._rows.get(motor_pk))

    def list_recent(self, limit: int = 6) -> List[dict]:
        rows = sorted(self._rows.values(), key=lambda r: r["updated_at"], reverse=True)
        return [deepcopy(r) for r in rows[:limit]]

    def list_all(self) -> List[dict]:
        rows = sorted(self._rows.values(), key=lambda r: r["updated_at"], reverse=True)
        return [deepcopy(r) for r in rows]


class InMemoryTestRepository:
    """Stockage des diagnostics en mémoire."""

    def __init__(self) -> None:
        self._seq: int = 0
        self._rows: Dict[int, dict] = {}
        self._lock = Lock()

    def _next_id(self) -> int:
        self._seq += 1
        return self._seq

    def create(self, data: dict) -> dict:
        with self._lock:
            tid = self._next_id()
            now = _now()
            row = {
                "id": tid,
                "created_at": now,
                "updated_at": now,
                "started_at": None,
                "completed_at": None,
                "status": data["status"],
                "mode": data["mode"],
                "kit_id": data.get("kit_id"),
                "motor_id": data["motor_id"],
                "technician_decision": "pending",
                "technician_observation": None,
                "auto_conclusion": None,
            }
            self._rows[tid] = row
            return deepcopy(row)

    def get(self, test_id: int) -> Optional[dict]:
        return deepcopy(self._rows.get(test_id))

    def update(self, test_id: int, changes: dict) -> Optional[dict]:
        with self._lock:
            row = self._rows.get(test_id)
            if row is None:
                return None
            for k, v in changes.items():
                row[k] = v
            row["updated_at"] = _now()
            return deepcopy(row)

    def list_recent(self, limit: int = 6) -> List[dict]:
        rows = sorted(self._rows.values(), key=lambda r: r["created_at"], reverse=True)
        return [deepcopy(r) for r in rows[:limit]]

    def list_all(self) -> List[dict]:
        rows = sorted(self._rows.values(), key=lambda r: r["created_at"], reverse=True)
        return [deepcopy(r) for r in rows]


# Instances partagées dans toute l'application (remplacées par des sessions SQLAlchemy à l'étape 4)
motors = InMemoryMotorRepository()
tests = InMemoryTestRepository()
