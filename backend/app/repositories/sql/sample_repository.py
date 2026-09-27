"""Dépôt des échantillons d'acquisition (série temporelle d'un test)."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.sample import AcquisitionSample


class SampleRepository:
    """Stocke et relit les échantillons mesurés par le kit."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def add(self, test_row_id: int, t_s: float, values: dict) -> None:
        """Ajoute un échantillon (valeurs partielles autorisées)."""
        self._db.add(AcquisitionSample(
            test_id=test_row_id,
            t_s=t_s,
            temperature_c=values.get("temperature_c"),
            current_a=values.get("current_a"),
            vib_x_mm_s=values.get("vib_x_mm_s"),
            vib_y_mm_s=values.get("vib_y_mm_s"),
            vib_z_mm_s=values.get("vib_z_mm_s"),
            vib_global_mm_s=values.get("vib_global_mm_s"),
        ))

    def commit(self) -> None:
        self._db.commit()

    def count_for_test(self, test_row_id: int) -> int:
        return self._db.scalar(
            select(func.count(AcquisitionSample.id)).where(AcquisitionSample.test_id == test_row_id)
        ) or 0

    def list_for_test(self, test_row_id: int) -> list[dict]:
        """Tous les échantillons d'un test, triés par instant."""
        rows = self._db.scalars(
            select(AcquisitionSample)
            .where(AcquisitionSample.test_id == test_row_id)
            .order_by(AcquisitionSample.t_s)
        ).all()
        return [{
            "t_s": row.t_s,
            "temperature_c": row.temperature_c,
            "current_a": row.current_a,
            "vibration": {
                "x_mm_s": row.vib_x_mm_s,
                "y_mm_s": row.vib_y_mm_s,
                "z_mm_s": row.vib_z_mm_s,
                "global_mm_s": row.vib_global_mm_s,
            },
        } for row in rows]
