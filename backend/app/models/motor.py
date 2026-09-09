"""Modèle ORM : moteurs électriques.

Un moteur peut être associé à PLUSIEURS tests (plusieurs diagnostics
au fil du temps) — relation 1-n vers DiagnosticTest.
"""

from typing import Optional, List

from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import IntPkMixin, TimestampMixin


class Motor(IntPkMixin, TimestampMixin, Base):
    __tablename__ = "motors"

    # Identification
    motor_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True)
    serial_number: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True)
    designation: Mapped[Optional[str]] = mapped_column(String(255))
    brand: Mapped[Optional[str]] = mapped_column(String(100))
    model: Mapped[Optional[str]] = mapped_column(String(100))
    manufacturer_number: Mapped[Optional[str]] = mapped_column(String(100))

    # Plaque signalétique
    rated_power_kw: Mapped[Optional[float]] = mapped_column(Float)
    rated_voltage_v: Mapped[Optional[float]] = mapped_column(Float)
    rated_current_a: Mapped[Optional[float]] = mapped_column(Float)
    rated_speed_rpm: Mapped[Optional[int]] = mapped_column(Integer)
    cos_phi: Mapped[Optional[float]] = mapped_column(Float)
    coupling: Mapped[Optional[str]] = mapped_column(String(20))     # Etoile / Triangle
    service: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    di_ot: Mapped[Optional[str]] = mapped_column(String(80), index=True)

    # Relations
    tests: Mapped[List["DiagnosticTest"]] = relationship(back_populates="motor", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        """Utilisé par la couche service qui pour l'instant s'appuie sur des dictionnaires."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
