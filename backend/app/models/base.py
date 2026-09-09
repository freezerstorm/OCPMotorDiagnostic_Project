"""Champs communs à tous les modèles (id + dates)."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class TimestampMixin:
    """Ajoute created_at / updated_at gérés automatiquement."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class IntPkMixin:
    """Clé primaire entière auto-incrémentée."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
