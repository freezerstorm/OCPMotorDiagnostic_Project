"""Schémas Pydantic — validation des données qui entrent et sortent de l'API.

Ces schémas ne dépendent PAS de la base de données (PostgreSQL arrive à l'étape 4).
Ils servent à valider les requêtes du frontend et à façonner les réponses.

Règle de nommage simple :
- *Create  → ce que le frontend ENVOIE pour créer une ressource
- *Out     → ce que l'API RENVOIE au frontend
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
# Énumérations partagées
# =============================================================================


class TestMode(str, Enum):
    """Mode de diagnostic : manuel ou automatique."""

    manual = "manual"
    auto = "auto"


class TestStatus(str, Enum):
    """Cycle de vie d'un diagnostic.

    IDLE        → créé, rien n'a commencé
    READY       → kit connecté, en attente de START (auto) / saisie (manuel)
    ACQUIRING   → acquisition 60 s en cours (auto)
    COMPLETED   → acquisition terminée OU mesures manuelles validées
    ANALYZED    → analyse terminée
    REPORTED    → rapport généré
    ARCHIVED    → archivé
    ERROR       → erreur (perte kit, etc.)
    """

    IDLE = "idle"
    READY = "ready"
    ACQUIRING = "acquiring"
    COMPLETED = "completed"
    ANALYZED = "analyzed"
    REPORTED = "reported"
    ARCHIVED = "archived"
    ERROR = "error"


class TechnicianDecision(str, Enum):
    """Décision finale du technicien (saisie manuelle à l'étape 11)."""

    PENDING = "pending"         # pas encore décidé
    RETURN_TO_SERVICE = "return_to_service"
    SENT_TO_REPAIR = "sent_to_repair"


# =============================================================================
# Moteur
# =============================================================================


class MotorBase(BaseModel):
    """Champs communs d'un moteur (identification + plaque signalétique)."""

    # Identification
    motor_id: Optional[str] = Field(
        None,
        description="Identifiant interne du moteur (plaque atelier)",
        examples=["MTR-2024-0142"],
    )
    serial_number: Optional[str] = Field(
        None, description="Matricule du moteur", examples=["7845-21-9"]
    )
    designation: Optional[str] = Field(None, examples=["Moteur pompe de relevage"])
    brand: Optional[str] = Field(None, examples=["Leroy-Somer"])
    model: Optional[str] = Field(None, examples=["LS200L"])
    manufacturer_number: Optional[str] = Field(None, description="Numéro de fabrication")

    # Plaque signalétique
    rated_power_kw: Optional[float] = Field(None, description="Puissance nominale (kW)", ge=0)
    rated_voltage_v: Optional[float] = Field(None, description="Tension nominale (V)", ge=0)
    rated_current_a: Optional[float] = Field(None, description="Courant nominal In (A)", ge=0)
    rated_speed_rpm: Optional[int] = Field(None, description="Vitesse nominale (tr/min)", ge=0)
    cos_phi: Optional[float] = Field(None, description="Facteur de puissance", ge=0, le=1)
    coupling: Optional[str] = Field(None, description="Couplage (étoile / triangle)", examples=["Δ"])
    service: Optional[str] = Field(None, description="Service / département OCP", examples=["Phosphore-Safi"])
    di_ot: Optional[str] = Field(None, description="DI/OT", examples=["DI-2024-071"])


class MotorCreate(MotorBase):
    """Requête de création ou mise à jour d'un moteur."""
    pass


class MotorOut(MotorBase):
    """Moteur renvoyé par l'API."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Identifiant interne (base)")
    created_at: datetime
    updated_at: datetime


# =============================================================================
# Diagnostic (test)
# =============================================================================


class TestCreate(BaseModel):
    """Requête de création d'un nouveau diagnostic."""

    mode: TestMode = Field(description="manual ou auto")
    motor: MotorCreate = Field(description="Identification et données du moteur")
    kit_id: Optional[str] = Field(None, description="Identifiant du kit (si mode auto)")


class TestSummaryOut(BaseModel):
    """Résumé affiché dans le tableau d'accueil / historique."""

    id: int
    mode: TestMode
    status: TestStatus
    created_at: datetime
    updated_at: datetime
    technician_decision: TechnicianDecision
    motor_id: int
    motor_label: str = Field(description="Texte court : ID + désignation")
    motor_serial: Optional[str] = None
    motor_service: Optional[str] = None


class TestOut(BaseModel):
    """Détail complet d'un diagnostic."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    mode: TestMode
    status: TestStatus
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    kit_id: Optional[str] = None
    technician_decision: TechnicianDecision
    technician_observation: Optional[str] = None
    auto_conclusion: Optional[str] = None
    motor: MotorOut
