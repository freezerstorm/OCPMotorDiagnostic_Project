"""Schéma des données TEST de diagnostic.

Un test correspond à UNE fiche de diagnostic (§3) : même structure pour
le mode manuel et le mode automatique. La seule différence est l'origine
des valeurs température/courant/vibration (saisies ou kit).

Structure des mesures :
- insulation  : 6 mesures d'isolement en MΩ (toujours saisies manuellement) ;
- winding     : résistance des enroulements R12/R23/R31 en Ω (idem) ;
- values      : valeurs « instantanées » de fonctionnement. En mode manuel
                elles sont saisies ; en mode automatique elles seront
                remplacées par les séries temporelles du kit (Étapes 7-8).

Hypothèse d'unité (à confirmer, voir docs/PLAN_DEVELOPPEMENT.md H9) :
- vibration manuelle en mm/s (appareil du technicien) ;
- le kit ADXL345 (accélération en g, 3 axes) sera géré séparément à l'Étape 8.
"""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.motors import MotorCreate, MotorRead

# Codes machine des modes et statuts (libellés français côté frontend)
TEST_MODE_MANUAL = "manual"
TEST_MODE_AUTO = "auto"

TEST_STATUS_DRAFT = "draft"        # test créé, en cours de complétion
TEST_STATUS_OFFLINE_VALIDATED = "offline_validated"  # test hors tension validé (É16)
TEST_STATUS_ACQUIRING = "acquiring"
TEST_STATUS_COMPLETED = "completed"
TEST_STATUS_ERROR = "error"
TEST_STATUS_ARCHIVED = "archived"


class InsulationMeasurements(BaseModel):
    """Six mesures d'isolement (MΩ) + tension de test utilisée.

    La tension de test (500 / 1000 / 2500 / 5000 V) est OBLIGATOIRE
    dès qu'une mesure d'isolement est saisie : la règle « 1 kΩ par
    volt » en dépend (voir le validateur sur Measurements).
    """

    model_config = ConfigDict(extra="forbid")

    test_voltage_v: Literal[500, 1000, 2500, 5000] | None = None
    ref_meter_insulation: str | None = Field(default=None, max_length=100, description="Référence de l'appareil (mégohmmètre), facultative")
    ph1_ph2_mohm: float | None = Field(default=None, ge=0)
    ph2_ph3_mohm: float | None = Field(default=None, ge=0)
    ph3_ph1_mohm: float | None = Field(default=None, ge=0)
    ph1_ground_mohm: float | None = Field(default=None, ge=0)
    ph2_ground_mohm: float | None = Field(default=None, ge=0)
    ph3_ground_mohm: float | None = Field(default=None, ge=0)


class WindingResistanceMeasurements(BaseModel):
    """Résistance des enroulements (Ω)."""

    model_config = ConfigDict(extra="forbid")

    r12_ohm: float | None = Field(default=None, ge=0)
    r23_ohm: float | None = Field(default=None, ge=0)
    r31_ohm: float | None = Field(default=None, ge=0)
    # É16 — appréciation GLOBALE du technicien (un seul champ Oui/Non)
    continuity_ok: bool | None = Field(
        default=None,
        description="Continuité des enroulements (appréciation globale du technicien)",
    )
    ref_meter_resistance: str | None = Field(default=None, max_length=100, description="Référence de l'appareil (pont / micro-ohmmètre), facultative")


class SingleValuesMeasurements(BaseModel):
    """Valeurs de fonctionnement saisies (mode manuel) ou issues du kit."""

    model_config = ConfigDict(extra="forbid")

    temperature_c: float | None = Field(
        default=None,
        description="Température UNIQUE — ancien format (fiches historiques seulement)",
    )
    # É16 — températures de PALIERS (règle fournie : critique si ≥ 70 °C)
    temp_bearing_de_c: float | None = Field(
        default=None, description="Température palier côté accouplement (°C)"
    )
    temp_bearing_nde_c: float | None = Field(
        default=None, description="Température palier C.O.A — côté opposé (°C)"
    )
    # É16 — références facultatives des appareils
    ref_meter_cl: str | None = Field(default=None, max_length=100, description="Référence de l'appareil (pince tension/courant), facultative")
    ref_meter_temperature: str | None = Field(default=None, max_length=100, description="Référence de l'appareil (sonde / viseur température), facultative")
    # Tension d'alimentation mesurée pendant l'essai (décision client
    # 26/09/2026) — OBLIGATOIRE à la validation du test sous tension.
    supply_voltage_v: float | None = Field(
        default=None, ge=0,
        description="Tension d'alimentation mesurée pendant le test (V)",
    )
    current_a: float | None = Field(default=None, ge=0, description="Courant absorbé (A)")
    vibration_mm_s: float | None = Field(
        default=None,
        ge=0,
        description="Vibration (mm/s) — hypothèse d'unité H9, à confirmer",
    )


class Measurements(BaseModel):
    """Toutes les mesures d'une fiche de diagnostic."""

    model_config = ConfigDict(extra="forbid")

    insulation: InsulationMeasurements = Field(default_factory=InsulationMeasurements)
    winding: WindingResistanceMeasurements = Field(default_factory=WindingResistanceMeasurements)
    values: SingleValuesMeasurements = Field(default_factory=SingleValuesMeasurements)

    @model_validator(mode="after")
    def _test_voltage_required_with_insulation(self):
        """Règle de saisie : tension de test obligatoire avec l'isolement."""
        iso = self.insulation
        has_measure = any(
            getattr(iso, field) is not None
            for field in (
                "ph1_ph2_mohm", "ph2_ph3_mohm", "ph3_ph1_mohm",
                "ph1_ground_mohm", "ph2_ground_mohm", "ph3_ground_mohm",
            )
        )
        if has_measure and iso.test_voltage_v is None:
            raise ValueError(
                "Tension de test d'isolement obligatoire lorsque des mesures "
                "d'isolement sont saisies (500 / 1000 / 2500 / 5000 V)."
            )
        return self


class SessionAdmin(BaseModel):
    """Zone administrative de la fiche papier (É16 — facultative)."""

    model_config = ConfigDict(extra="forbid")

    requested_by_service: str | None = Field(default=None, max_length=100, description="Service demandeur")
    notice: str | None = Field(default=None, max_length=200, description="AVIS")
    work_order: str | None = Field(default=None, max_length=100, description="ORDRE")
    received_at: date | None = Field(default=None, description="Date de réception (AAAA-MM-JJ)")
    repair_internal: bool | None = Field(default=None, description="Réparation interne")
    repair_external: bool | None = Field(default=None, description="Réparation externe")


class TestCreate(BaseModel):
    """Données nécessaires pour créer un test (moteur + mesures + admin)."""

    model_config = ConfigDict(extra="forbid")

    mode: Literal[TEST_MODE_MANUAL, TEST_MODE_AUTO]
    motor: MotorCreate
    measurements: Measurements = Field(default_factory=Measurements)
    admin: SessionAdmin | None = None


class TestRead(BaseModel):
    """Fiche de diagnostic renvoyée par l'API (avec les infos moteur)."""

    test_id: str
    mode: Literal[TEST_MODE_MANUAL, TEST_MODE_AUTO]
    status: Literal[
        TEST_STATUS_DRAFT,
        TEST_STATUS_OFFLINE_VALIDATED,
        TEST_STATUS_ACQUIRING,
        TEST_STATUS_COMPLETED,
        TEST_STATUS_ERROR,
        TEST_STATUS_ARCHIVED,
    ]
    # Décision du technicien / conclusion — remplis aux Étapes 10-11
    decision: str | None = None
    observation: str | None = None
    # Zone administrative (fiche papier, facultative)
    admin: SessionAdmin | None = None

    created_at: datetime
    # Référence d'origine si la fiche vient d'un import historique
    # (Étape 15) — None pour les fiches créées par l'application.
    source_ref: str | None = None
    motor: MotorRead
    measurements: Measurements


class TestUpdate(BaseModel):
    """Mise à jour PARTIELLE d'une fiche de diagnostic.

    Seuls les champs fournis sont modifiés (PATCH). À l'Étape 6,
    on archive un test (status='archived') ; la décision et
    l'observation seront posées à l'Étape 11 via ce même schéma.
    """

    model_config = ConfigDict(extra="forbid")

    status: Literal[
        TEST_STATUS_DRAFT,
        TEST_STATUS_OFFLINE_VALIDATED,
        TEST_STATUS_ACQUIRING,
        TEST_STATUS_COMPLETED,
        TEST_STATUS_ERROR,
        TEST_STATUS_ARCHIVED,
    ] | None = None
    # Zone administrative modifiable (É16)
    admin: SessionAdmin | None = None

    # Décision du technicien : code 'serviced' (remis en service)
    # ou 'repair' (envoyé en réparation) — null pour « pas encore décidé ».
    decision: Literal["serviced", "repair"] | None = None

    # Société en charge de la réparation (décision client 24/09/2026) :
    # saisie par le technicien quand la décision est « repair » ; elle
    # alimente la colonne « Société » de la ligne du registre.
    repair_company: str | None = Field(default=None, max_length=200)

    observation: str | None = Field(default=None, max_length=5000)

    # É17 — parcours en étapes : le mode ne devient « auto » que si le
    # technicien choisit « CONTINUER AVEC LE KIT » au test sous tension.
    mode: Literal[TEST_MODE_MANUAL, TEST_MODE_AUTO] | None = None

    # É17 — mesures du test sous tension (mode manuel) ajoutées APRÈS la
    # création de la session : seuls les champs fournis (non nuls) sont
    # enregistrés, les autres ne sont pas écrasés.
    measurements: Measurements | None = None
