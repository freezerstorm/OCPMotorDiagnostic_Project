"""Table du REGISTRE NUMÉRIQUE — structure RÉELLE du fichier client.

Les 14 colonnes reprennent le fichier réel (JSON « p1 » fourni par le
client) : Date, Matricule (« Mat »), DI/OT, Service (Sce), Un, In,
U0, I0, Isolement, Nature (= désignation du moteur, précision client),
Puissance (P), Société, BT/MT (Tension), Observation.

Règles :
  - 1 ligne PAR ESSAI / PAR LIGNE du fichier — jamais remplacée ;
  - valeurs électriques en TEXTE BRUT (« 525V », « 1,2 GΩ ») :
    rien n'est converti ni inventé ;
  - champs absents / tirets « - » « ~ » = NULL (cellule vide) ;
  - « source_ref » (unique) rend les imports idempotents.
"""

from datetime import date

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class RegistreEntry(Base):
    """Une ligne du registre numérique = UN essai de moteur."""

    __tablename__ = "registre_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Essai de l'application à l'origine de la ligne (unique) ;
    # NULL pour les lignes importées directement du registre réel.
    test_row_id: Mapped[int | None] = mapped_column(
        ForeignKey("tests.id"), nullable=True, unique=True
    )
    # Provenance : « historique » (import) ou « essai » (application).
    source: Mapped[str | None] = mapped_column(String(20))
    # Référence d'import (ex. « JSON:12 ») — unique : ré-importer le
    # même fichier ne crée pas de doublon.
    source_ref: Mapped[str | None] = mapped_column(String(50), unique=True)

    created_at: Mapped[date] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # --- Les 14 colonnes réelles (valeurs brutes, champs vides = NULL) ---
    entry_date: Mapped[date | None] = mapped_column(Date)          # Date
    matricule: Mapped[str | None] = mapped_column(String(100))     # Matricule (« Mat »)
    di_ot: Mapped[str | None] = mapped_column(String(100))         # DI/OT
    # Couplage du moteur (étoile « Y », triangle « Δ »…) — lot 4 ;
    # rempli quand la ligne en a un, vide sinon (demande client).
    couplage: Mapped[str | None] = mapped_column(String(20))
    service: Mapped[str | None] = mapped_column(String(100))       # Service (Sce)
    un_v: Mapped[str | None] = mapped_column(Text)                 # Un
    in_a: Mapped[str | None] = mapped_column(Text)                 # In
    uo_v: Mapped[str | None] = mapped_column(Text)                 # U0
    io_a: Mapped[str | None] = mapped_column(Text)                 # I0
    isolement: Mapped[str | None] = mapped_column(Text)            # Isolement (ph-ph)
    # Isolement phase-masse (format 4 du lot 4, distinct du ph-ph).
    isolement_ph_m: Mapped[str | None] = mapped_column(Text)
    # Résistance mesurée (format 4 du lot 4, texte brut « 0,6 Ω »).
    r: Mapped[str | None] = mapped_column(Text)
    nature: Mapped[str | None] = mapped_column(Text)               # Nature (désignation)
    puissance: Mapped[str | None] = mapped_column(Text)            # Puissance (P)
    societe: Mapped[str | None] = mapped_column(String(100))       # Société
    bt_mt: Mapped[str | None] = mapped_column(String(20))          # BT/MT (Tension)
    observation: Mapped[str | None] = mapped_column(Text)          # Observation
