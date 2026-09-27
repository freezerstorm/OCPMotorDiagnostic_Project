"""SERVICE REGISTRE NUMÉRIQUE — alimentation et consultation.

Le registre réunit (demande client) :
  - le REGISTRE RÉEL importé (fichier JSON/Excel du client — voir
    tools/import_registre_reel.py) ;
  - les ESSAIS de l'application, ajoutés automatiquement après la
    validation du diagnostic et la décision du technicien.

RÈGLES (non négociables) :
  - chaque essai / chaque ligne du fichier = UNE entrée indépendante ;
    on ne remplace jamais une ligne existante ;
  - les valeurs du fichier réel sont conservées BRUTES (« 525V »,
    « 1,2 GΩ ») ; les champs absents restent VIDES — rien d'inventé ;
  - ce module est le SEUL à connaître la correspondance essai ↔
    colonnes du registre (évolution isolée du reste).

CORRESPONDANCE (essai de l'application → colonne du registre réel) :

  1. Date          → date de l'essai (created_at du test)
  2. Matricule     → matricule moteur, sinon ID moteur
  3. DI/OT         → ORDRE de la session, sinon DI/OT du moteur
  4. Service (Sce) → Service / Environnement du moteur
  5. Un            → tension nominale (plaque), format « 500V »
  6. In            → courant nominal (plaque), format « 78A »
  7. U0            → (non capturée pendant l'essai) — vide
  8. I0            → courant mesuré (fiche, sinon moyenne kit), « 41A »
  9. Isolement     → mesures de la fiche jointes (« Ph/N : a / b / c MΩ »)
 10. Nature        → désignation du moteur (précision client)
 11. Puissance (P) → puissance nominale (plaque), format « 45 kW »
 12. Société       → société en charge de la réparation, saisie par
                     le technicien quand le moteur est envoyé en
                     réparation (décision client 24/09/2026) — vide sinon
 13. BT/MT         → (non capturée) — vide
 14. Observation   → observation du technicien
"""

import statistics

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.registre import RegistreEntry
from app.models.test import Test
from app.repositories.sql.registre_repository import RegistreRepository

SOURCE_HISTORIQUE = "historique"   # ligne issue d'un import du registre réel
SOURCE_ESSAI = "essai"             # ligne issue d'un essai de l'application


def _fmt_num(value) -> str | None:
    """Nombre → texte « à la française » sans zéros inutiles.

    Ex. : 310.0 → « 310 » ; 0.152 → « 0,152 » ; None → None (vide).
    """
    if value is None:
        return None
    text = f"{float(value):.4f}".rstrip("0").rstrip(".")
    return text.replace(".", ",")


def _glued(value, unit: str) -> str | None:
    """Valeur + unité collée, style du registre réel (« 500V », « 78A »)."""
    number = _fmt_num(value)
    return f"{number}{unit}" if number is not None else None


def entry_values_from_test(test: Test, societe_reparation: str | None = None) -> dict:
    """Construit les 14 colonnes du registre pour UN essai.

    `test` est la fiche ORM (avec .motor, .measurements, .samples).
    `societe_reparation` : société en charge de la réparation, saisie
    par le technicien quand sa décision est « envoyé en réparation »
    (décision client) — None = cellule vide.
    Aucune valeur n'est inventée : champ absent → None (cellule vide).
    """
    motor = test.motor
    m = test.measurements
    has_motor = motor is not None
    has_m = m is not None

    # I0 : courant de la fiche, sinon moyenne des échantillons du kit
    # (même logique que le moteur de diagnostic — source factuelle).
    io = m.current_a if has_m else None
    if io is None:
        currents = [s.current_a for s in test.samples if s.current_a is not None]
        if currents:
            io = round(statistics.fmean(currents), 2)

    # Isolement : les mesures de la fiche, jointes telles quelles.
    isolement_parts = []
    if has_m:
        ph_n = [m.ph1_ground_mohm, m.ph2_ground_mohm, m.ph3_ground_mohm]
        ph_ph = [m.ph1_ph2_mohm, m.ph2_ph3_mohm, m.ph3_ph1_mohm]
        if any(v is not None for v in ph_n):
            isolement_parts.append("Ph/N : " + " / ".join(
                t for t in (_fmt_num(v) for v in ph_n) if t is not None) + " MΩ")
        if any(v is not None for v in ph_ph):
            isolement_parts.append("Ph/Ph : " + " / ".join(
                t for t in (_fmt_num(v) for v in ph_ph) if t is not None) + " MΩ")

    return {
        "entry_date": test.created_at.date() if test.created_at else None,
        "matricule": (motor.matricule or motor.motor_id) if has_motor else None,
        "di_ot": (test.work_order or (motor.di_ot if has_motor else None)) or None,
        "service": motor.service if has_motor else None,
        "un_v": _glued(motor.rated_voltage_v, "V") if has_motor else None,
        "in_a": _glued(motor.rated_current_a, "A") if has_motor else None,
        "uo_v": None,                      # non capturée (voir correspondance)
        "io_a": _glued(io, "A"),
        "isolement": " ; ".join(isolement_parts) if isolement_parts else None,
        "nature": motor.designation if has_motor else None,
        "puissance": _glued(motor.rated_power_kw, " kW") if has_motor else None,
        "societe": societe_reparation,     # société de réparation (technicien)
        "bt_mt": None,                     # non capturée (voir correspondance)
        "observation": test.observation,
    }


def sync_entry_for_test(db: Session, test: Test,
                        societe_reparation: str | None = None) -> bool:
    """Ajoute la ligne du registre pour cet essai (si pas déjà présente).

    `societe_reparation` : société en charge de la réparation saisie
    par le technicien (décision « repair »). Si la ligne existait déjà
    et qu'une société est fournie, son champ vide est simplement
    COMPLÉTÉ (la ligne elle-même n'est jamais remplacée).
    Renvoie True si une ligne a été créée, False si elle existait déjà
    (jamais de remplacement, jamais de doublon).
    """
    repo = RegistreRepository(db)
    if repo.exists_for_test(test.id):
        if societe_reparation:
            row = db.scalar(select(RegistreEntry)
                            .where(RegistreEntry.test_row_id == test.id))
            if row is not None and not row.societe:
                row.societe = societe_reparation
                db.commit()
        return False
    source = SOURCE_HISTORIQUE if test.source_ref else SOURCE_ESSAI
    repo.add(entry_values_from_test(test, societe_reparation),
             test_row_id=test.id, source=source)
    return True


def list_entries(db: Session) -> dict:
    """Toutes les lignes du registre (ordonnées par date d'essai)."""
    repo = RegistreRepository(db)
    return {"count": repo.count(), "entries": repo.list()}


def backfill_from_existing_tests(db: Session) -> list[str]:
    """Complète le registre avec les essais déjà en base.

    Sont repris (demande client) :
      - les essais IMPORTÉS du registre réel (source_ref renseigné) ;
      - les essais DÉCIDÉS par le technicien (decision renseignée).
    Idempotent : les essais déjà inscrits sont ignorés.
    Renvoie la liste des n° de dossier ajoutés.
    """
    added: list[str] = []
    rows = db.scalars(select(Test)).all()
    for test in rows:
        if test.source_ref is None and test.decision is None:
            continue
        if sync_entry_for_test(db, test):
            added.append(test.test_id)
    return added
