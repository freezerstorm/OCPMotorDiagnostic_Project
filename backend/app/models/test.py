"""Modèle ORM : un diagnostic (test)."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import IntPkMixin, TimestampMixin


class DiagnosticTest(IntPkMixin, TimestampMixin, Base):
    __tablename__ = "diagnostic_tests"

    mode: Mapped[str] = mapped_column(String(10), index=True)          # manual | auto
    status: Mapped[str] = mapped_column(String(20), index=True)        # idle/ready/acquiring/...
    kit_id: Mapped[Optional[str]] = mapped_column(String(80), index=True)

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    technician_decision: Mapped[str] = mapped_column(String(30), default="pending")
    technician_observation: Mapped[Optional[str]] = mapped_column(Text)
    auto_conclusion: Mapped[Optional[str]] = mapped_column(Text)

    # Clé étrangère vers moteur
    motor_id: Mapped[int] = mapped_column(ForeignKey("motors.id", ondelete="CASCADE"), index=True)
    motor: Mapped["Motor"] = relationship(back_populates="tests")

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
