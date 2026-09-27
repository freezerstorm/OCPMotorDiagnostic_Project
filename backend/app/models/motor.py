"""Table « motors » : fiche d'identification d'un moteur.

Champs alignés sur le formulaire du §9 (aucune donnée fictive : les
caractéristiques nominales sont celles de la plaque du moteur, saisies
par le technicien). La clé primaire est le motor_id (identifiant
saisi, ex. « M-1042 ») : c'est la clé de l'auto-remplissage.

Conception « temporelle » : created_at permet déjà de dater chaque
enregistrement ; on pourra ajouter des champs ou tables de séries
temporelles plus tard (Étape 8) sans réécrire ce modèle.
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Motor(Base):
    __tablename__ = "motors"

    # --- Identification ---
    motor_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    matricule: Mapped[str | None] = mapped_column(String(100))
    designation: Mapped[str | None] = mapped_column(String(200))
    brand: Mapped[str | None] = mapped_column(String(100))
    model: Mapped[str | None] = mapped_column(String(100))
    serial_number: Mapped[str | None] = mapped_column(String(100))

    # --- Caractéristiques nominales (plaque) ---
    rated_power_kw: Mapped[float | None] = mapped_column(Float)
    rated_voltage_v: Mapped[float | None] = mapped_column(Float)
    rated_current_a: Mapped[float | None] = mapped_column(Float)
    rated_speed_rpm: Mapped[float | None] = mapped_column(Float)
    cos_phi: Mapped[float | None] = mapped_column(Float)
    coupling: Mapped[str | None] = mapped_column(String(20))
    service: Mapped[str | None] = mapped_column(String(100))
    di_ot: Mapped[str | None] = mapped_column(String(100))

    # --- Métadonnées ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Un moteur possède plusieurs tests (historique des diagnostics)
    tests: Mapped[list["Test"]] = relationship(back_populates="motor")  # noqa: F821
