"""Table « acquisition_samples » : série temporelle d'un test automatique.

Un test automatique (~60 s) produit un échantillon par message du kit
(ex. 2 par seconde → ~120 lignes par test). Chaque ligne contient
l'instant (t_s = secondes depuis le début de l'acquisition) et les
trois grandeurs mesurées par le kit : température, courant, vibration.

Vibration : l'ADXL345 mesure une accélération sur 3 axes (g). On garde
les axes x/y/z et une valeur globale (norme) calculée par le backend.
Hypothèses H1/H9 — à confirmer avec le kit réel.

Les tests manuels n'ont PAS d'échantillons : leurs valeurs « uniques »
vivent dans la table measurements (fiche de diagnostic).
"""

from sqlalchemy import Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AcquisitionSample(Base):
    __tablename__ = "acquisition_samples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Lien vers la fiche de diagnostic (supprimée → échantillons supprimés)
    test_id: Mapped[int] = mapped_column(
        ForeignKey("tests.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Instant : secondes écoulées depuis le début de l'acquisition
    t_s: Mapped[float] = mapped_column(Float, nullable=False)

    # Grandeurs mesurées (nullables : un message peut être partiel)
    temperature_c: Mapped[float | None] = mapped_column(Float)
    current_a: Mapped[float | None] = mapped_column(Float)
    # Vibration du kit en mm/s (décision client : le kit publie la
    # vitesse vibratoire directement, comme la saisie manuelle).
    vib_x_mm_s: Mapped[float | None] = mapped_column(Float)
    vib_y_mm_s: Mapped[float | None] = mapped_column(Float)
    vib_z_mm_s: Mapped[float | None] = mapped_column(Float)
    # Norme des 3 axes, calculée par le backend (racine de la somme des carrés)
    vib_global_mm_s: Mapped[float | None] = mapped_column(Float)

    test: Mapped["Test"] = relationship(back_populates="samples")  # noqa: F821
