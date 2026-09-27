"""Tables « tests » et « measurements ».

- tests       : UNE ligne = UNE fiche de diagnostic. Même table pour
                les deux modes (manuel/automatique) : la seule
                différence est l'origine des mesures, pas la structure.
                Un même moteur peut avoir plusieurs lignes.
- measurements : mesures de la fiche (1 ligne pour 1 test) :
                  * isolement (6 valeurs) et résistance R12/R23/R31 :
                    toujours saisies manuellement ;
                  * température / courant / vibration : valeurs saisies
                    (manuel) ou issues du kit (auto). En mode auto, les
                    séries temporelles du kit seront stockées dans une
                    table dédiée à l'Étape 8 — la valeur « instantanée »
                    restera utile comme synthèse.

Statuts possibles (code) : draft, acquiring, completed, error, archived.
Modes possibles (code) : manual, auto.
Décision du technicien (code) : serviced (remis en service), repair (réparation).
"""

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Test(Base):
    __tablename__ = "tests"

    # Clé interne (auto-incrémentée par la base)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Identifiant public lisible (ex. « T-0001 »), généré via la
    # séquence SQL « test_id_seq » (voir la migration 0001).
    test_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)

    mode: Mapped[str] = mapped_column(String(10), nullable=False)  # manual | auto
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="draft"
    )
    decision: Mapped[str | None] = mapped_column(String(50))  # serviced | repair
    observation: Mapped[str | None] = mapped_column(Text)     # note libre du technicien

    # Zone administrative de la fiche papier (É16 — facultative)
    requested_by_service: Mapped[str | None] = mapped_column(String(100))  # Sce demandeur
    notice: Mapped[str | None] = mapped_column(String(200))                # AVIS
    work_order: Mapped[str | None] = mapped_column(String(100))            # ORDRE
    received_at: Mapped[date | None] = mapped_column(Date)                 # date de réception
    repair_internal: Mapped[bool | None] = mapped_column(Boolean)          # réparation interne
    repair_external: Mapped[bool | None] = mapped_column(Boolean)          # réparation externe

    motor_id: Mapped[str] = mapped_column(
        ForeignKey("motors.motor_id"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Référence d'origine (import de la base historique — Étape 15) :
    # identifiant de la ligne dans le fichier importé. NULL pour les
    # fiches créées par l'application. Index unique → pas de doublon
    # si le même fichier est réimporté.
    source_ref: Mapped[str | None] = mapped_column(String(100))

    motor: Mapped["Motor"] = relationship(back_populates="tests")  # noqa: F821
    samples: Mapped[list["AcquisitionSample"]] = relationship(
        back_populates="test", cascade="all, delete-orphan"
    )  # noqa: F821
    measurements: Mapped["Measurements | None"] = relationship(
        back_populates="test",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Measurements(Base):
    __tablename__ = "measurements"

    # Lien 1-1 vers le test (clé primaire = clé étrangère)
    test_id: Mapped[int] = mapped_column(
        ForeignKey("tests.id", ondelete="CASCADE"), primary_key=True
    )

    # --- Isolement (MΩ) : toujours saisi manuellement ---
    # Tension de test choisie (500 / 1000 / 2500 / 5000 V) : sert à la
    # règle d'isolement « 1 kΩ par volt » (Rmin = Vtest × 1 kΩ).
    insulation_test_voltage_v: Mapped[int | None] = mapped_column(Integer)
    ph1_ph2_mohm: Mapped[float | None] = mapped_column(Float)
    ph2_ph3_mohm: Mapped[float | None] = mapped_column(Float)
    ph3_ph1_mohm: Mapped[float | None] = mapped_column(Float)
    ph1_ground_mohm: Mapped[float | None] = mapped_column(Float)
    ph2_ground_mohm: Mapped[float | None] = mapped_column(Float)
    ph3_ground_mohm: Mapped[float | None] = mapped_column(Float)

    # --- Résistance des enroulements (Ω) : toujours saisie manuellement ---
    r12_ohm: Mapped[float | None] = mapped_column(Float)
    r23_ohm: Mapped[float | None] = mapped_column(Float)
    r31_ohm: Mapped[float | None] = mapped_column(Float)

    # --- Valeurs « instantanées » (saisies ou issues du kit) ---
    # Ancienne température UNIQUE (anciennes fiches / imports) — seuil 85 °C
    temperature_c: Mapped[float | None] = mapped_column(Float)
    current_a: Mapped[float | None] = mapped_column(Float)
    vibration_mm_s: Mapped[float | None] = mapped_column(Float)  # hypothèse H9
    # Tension d'alimentation mesurée pendant l'essai (décision client
    # 26/09/2026) — OBLIGATOIRE pour valider le test sous tension
    # (validate_online) ; le kit ne la mesure pas (saisie manuelle).
    supply_voltage_v: Mapped[float | None] = mapped_column(Float)

    # É16 — continuité globale (appréciation Oui/Non du technicien)
    continuity_ok: Mapped[bool | None] = mapped_column(Boolean)
    # É16 — températures PALIERS (règle < 70 °C, comme la fiche papier)
    temp_bearing_de_c: Mapped[float | None] = mapped_column(Float)   # côté accouplement
    temp_bearing_nde_c: Mapped[float | None] = mapped_column(Float)  # C.O.A (côté opposé)
    # É16 — références facultatives des appareils de mesure
    ref_meter_insulation: Mapped[str | None] = mapped_column(String(100))
    ref_meter_resistance: Mapped[str | None] = mapped_column(String(100))
    ref_meter_cl: Mapped[str | None] = mapped_column(String(100))
    ref_meter_temperature: Mapped[str | None] = mapped_column(String(100))

    test: Mapped["Test"] = relationship(back_populates="measurements")  # noqa: F821