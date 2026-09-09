"""Modèles ORM : mesures manuelles et séries temporelles (mesures automatiques).

Ces tables seront PLEINEMENT utilisées aux étapes 5 à 9.
Elles sont créées ici (étape 4) pour que la base soit complète dès le départ.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import IntPkMixin


class ManualMeasurements(IntPkMixin, Base):
    """Mesures électriques saisies manuellement (isolement + résistances).

    Un diagnostic = une seule ligne de mesures manuelles (relation 1-1 logique).
    """
    __tablename__ = "manual_measurements"

    test_id: Mapped[int] = mapped_column(ForeignKey("diagnostic_tests.id", ondelete="CASCADE"), unique=True, index=True)

    # Isolement en MΩ
    iso_ph1_ph2_mohm: Mapped[Optional[float]] = mapped_column(Float)
    iso_ph2_ph3_mohm: Mapped[Optional[float]] = mapped_column(Float)
    iso_ph3_ph1_mohm: Mapped[Optional[float]] = mapped_column(Float)
    iso_ph1_ground_mohm: Mapped[Optional[float]] = mapped_column(Float)
    iso_ph2_ground_mohm: Mapped[Optional[float]] = mapped_column(Float)
    iso_ph3_ground_mohm: Mapped[Optional[float]] = mapped_column(Float)

    # Résistance des enroulements en Ω
    r12_ohm: Mapped[Optional[float]] = mapped_column(Float)
    r23_ohm: Mapped[Optional[float]] = mapped_column(Float)
    r31_ohm: Mapped[Optional[float]] = mapped_column(Float)


class TimeSeriesPoint(IntPkMixin, Base):
    """Un point de mesure automatique (température, courant, vibration).

    Les points sont horodatés côté serveur (ts). Chaque point est lié à un test.
    Plusieurs dizaines de lignes par test (60 s × ~5 échantillons/s).
    La table est conçue pour pouvoir être convertie en hypertable TimescaleDB
    plus tard (pas d'obligation pour le MVP).
    """
    __tablename__ = "time_series"

    test_id: Mapped[int] = mapped_column(ForeignKey("diagnostic_tests.id", ondelete="CASCADE"), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Trois grandeurs acquises par le kit
    temperature_c: Mapped[Optional[float]] = mapped_column(Float)
    current_a: Mapped[Optional[float]] = mapped_column(Float)
    vibration_x_g: Mapped[Optional[float]] = mapped_column(Float)
    vibration_y_g: Mapped[Optional[float]] = mapped_column(Float)
    vibration_z_g: Mapped[Optional[float]] = mapped_column(Float)
    vibration_magnitude_g: Mapped[Optional[float]] = mapped_column(Float)
