"""Schéma des données MOTEUR.

Correspond à l'identification et aux caractéristiques « plaque » du moteur
(§9 du cahier des charges). Les champs numériques restent facultatifs :
lors d'un premier test, on ne connaît pas encore toutes les valeurs.

Conventions :
- seuls les champs listés sont acceptés (extra='forbid' → une faute de
  frappe côté client est refusée, pas silencieusement ignorée) ;
- les codes machine sont en anglais (ex. motor_id), les libellés
  affichés à l'utilisateur restent en français côté frontend.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MotorBase(BaseModel):
    """Champs d'identification et caractéristiques du moteur."""

    model_config = ConfigDict(extra="forbid")

    @field_validator("*", mode="before")
    @classmethod
    def strip_text_fields(cls, value):
        """Nettoie les espaces en début/fin de chaque champ texte.

        Ex. «  M-1042  » devient « M-1042 » ; un ID composé uniquement
        d'espaces devient vide → refusé par les règles de longueur.
        """
        return value.strip() if isinstance(value, str) else value

    # --- Identification ---
    motor_id: str = Field(min_length=1, max_length=50, description="Identifiant unique du moteur (ex. M-1042)")
    matricule: str | None = Field(default=None, max_length=100, description="Matricule atelier")
    designation: str | None = Field(default=None, max_length=200, description="Désignation (ex. Moteur broyeur ciment)")
    brand: str | None = Field(default=None, max_length=100, description="Marque")
    model: str | None = Field(default=None, max_length=100, description="Modèle")
    serial_number: str | None = Field(default=None, max_length=100, description="N° de fabrication")

    # --- Caractéristiques nominales (plaque) ---
    rated_power_kw: float | None = Field(default=None, gt=0, description="Puissance nominale (kW)")
    rated_voltage_v: float | None = Field(default=None, gt=0, description="Tension nominale (V)")
    rated_current_a: float | None = Field(default=None, gt=0, description="Courant nominal In (A)")
    rated_speed_rpm: float | None = Field(default=None, gt=0, description="Vitesse nominale (tr/min)")
    cos_phi: float | None = Field(default=None, gt=0, le=1, description="Facteur de puissance cos φ")
    coupling: str | None = Field(default=None, max_length=20, description="Couplage : Étoile (Y) ou Triangle (Δ)")
    service: str | None = Field(default=None, max_length=100, description="Service / atelier d'utilisation")
    di_ot: str | None = Field(default=None, max_length=100, description="DI / OT (champ libre OCP)")


class MotorCreate(MotorBase):
    """Données attendues pour créer un moteur (aucune donnée ajoutée)."""


class MotorRead(MotorBase):
    """Données renvoyées par l'API : les champs du moteur + sa date de création."""

    created_at: datetime
