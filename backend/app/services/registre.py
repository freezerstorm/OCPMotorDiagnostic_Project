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
  9. PH_PH         → isolements ENTRE PHASES de la fiche
                     (Ph1-Ph2 / Ph2-Ph3 / Ph3-Ph1, « 145 / 138 / 141 MΩ »)
     PH_m          → isolements PHASE-MASSE de la fiche
                     (Ph1-M / Ph2-M / Ph3-M, « 310 / 298 / 305 MΩ »)
     R             → résistances des enroulements
                     (R12 / R23 / R31, « 0,152 / 0,152 / 0,153 Ω »)
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

# ------------------------------------------------------------------
# CELLULES EN DÉFAUT (décision client 28/09/2026) : dans le registre,
# la cellule d'une mesure signalée par les règles du test est AFFICHÉE
# EN ROUGE. Correspondance règle → colonne du registre :
#   courant à vide      → I0
#   résistances         → R
#   isolement (6 mesures, jugées UNE PAR UNE par la règle) :
#     Ph1-Ph2/Ph2-Ph3/Ph3-Ph1 en défaut → PH_PH
#     Ph1-M/Ph2-M/Ph3-M en défaut       → PH_m
# L'anomalie des règles est « problematique » ou « critique » (code
# « critique » : température/vibration, sans colonne au registre).
# ------------------------------------------------------------------
EVALUATIONS_ANOMALIE = ("problematique", "critique")

_CELLULES_PARAMETRE = {
    "current_no_load": ("io_a",),
    "winding_resistance": ("r",),
}

_GROUPES_ISOLEMENT = {
    "isolement": ("ph1_ph2", "ph2_ph3", "ph3_ph1"),          # PH_PH
    "isolement_ph_m": ("ph1_ground", "ph2_ground", "ph3_ground"),  # PH_m
}


def cellules_critiques_du_test(analysis: dict) -> list[str]:
    """Cellules du registre (clés API) dont la mesure est en défaut.

    - courant / résistances : anomalie sur la règle entière ;
    - isolement : le résultat d'isolement porte le détail PAR MESURE
      (« items ») → seul le groupe en défaut est signalé (PH_PH ou
      PH_m) ; sans détail disponible, repli sur l'évaluation globale.
    Renvoie une liste de clés parmi : io_a, r, isolement, isolement_ph_m.
    """
    cells: list[str] = []
    results = analysis.get("results", [])
    for result in results:
        cells.extend(_CELLULES_PARAMETRE.get(result.get("parameter"), ())
                     if result.get("evaluation") in EVALUATIONS_ANOMALIE else ())

    insulation = next(
        (r for r in results if r.get("parameter") == "insulation"), None)
    if insulation is not None:
        items = insulation.get("items") or []
        for cellule, cles in _GROUPES_ISOLEMENT.items():
            if items:
                en_defaut = any(
                    item.get("evaluation") in EVALUATIONS_ANOMALIE
                    for item in items if item.get("key") in cles
                )
            else:
                en_defaut = insulation.get("evaluation") in EVALUATIONS_ANOMALIE
            if en_defaut:
                cells.append(cellule)
    return cells


def annotate_cellules_critiques(db: Session, entries: list[dict]) -> None:
    """Ajoute à chaque ligne d'essai sa liste « cellules_critiques ».

    Seuls les essais de l'application sont annotés (source « essai ») :
    les lignes importées du registre réel sont des valeurs VERBATIM sans
    test évaluable — jamais annotées, jamais modifiées.
    """
    from app.repositories.sql.sample_repository import SampleRepository
    from app.services.diagnostic_engine import evaluate_test

    for entry in entries:
        entry["cellules_critiques"] = []
        if entry.get("source") != SOURCE_ESSAI or not entry.get("test_row_id"):
            continue
        test = db.get(Test, entry["test_row_id"])
        if test is None:
            continue
        samples = SampleRepository(db).list_for_test(test.id)
        entry["cellules_critiques"] = cellules_critiques_du_test(
            evaluate_test(test, samples))


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

    # PH_PH / PH_m / R (décision client 28/09/2026) : trois colonnes
    # DÉDIÉES remplies depuis les mesures du test —
    #   PH_PH = isolements ENTRE PHASES (Ph1-Ph2 / Ph2-Ph3 / Ph3-Ph1) ;
    #   PH_m  = isolements PHASE-MASSE (Ph1-M / Ph2-M / Ph3-M) ;
    #   R     = résistances des enroulements (R12 / R23 / R31).
    # Style du registre réel : valeurs jointes par « / », unité en fin
    # de cellule. Champ absent → cellule vide (rien d'inventé).
    def _joint(values, unit: str) -> str | None:
        parts = [t for t in (_fmt_num(v) for v in values) if t is not None]
        return " / ".join(parts) + f" {unit}" if parts else None

    isolement_ph_ph = _joint(
        [m.ph1_ph2_mohm, m.ph2_ph3_mohm, m.ph3_ph1_mohm] if has_m else [], "MΩ")
    isolement_ph_m = _joint(
        [m.ph1_ground_mohm, m.ph2_ground_mohm, m.ph3_ground_mohm] if has_m else [], "MΩ")
    resistance_r = _joint(
        [m.r12_ohm, m.r23_ohm, m.r31_ohm] if has_m else [], "Ω")

    return {
        "entry_date": test.created_at.date() if test.created_at else None,
        "matricule": (motor.matricule or motor.motor_id) if has_motor else None,
        "di_ot": (test.work_order or (motor.di_ot if has_motor else None)) or None,
        "service": motor.service if has_motor else None,
        "un_v": _glued(motor.rated_voltage_v, "V") if has_motor else None,
        "in_a": _glued(motor.rated_current_a, "A") if has_motor else None,
        "uo_v": None,                      # non capturée (voir correspondance)
        "io_a": _glued(io, "A"),
        "isolement": isolement_ph_ph,          # colonne PH_PH
        "isolement_ph_m": isolement_ph_m,      # colonne PH_m
        "r": resistance_r,                     # colonne R
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
    """Toutes les lignes du registre (ordonnées par date d'essai).

    Chaque ligne d'essai porte en plus « cellules_critiques » : les
    clés des cellules dont la mesure est signalée par les règles du
    test (affichées en rouge par la page Registre).
    """
    repo = RegistreRepository(db)
    entries = repo.list()
    annotate_cellules_critiques(db, entries)
    return {"count": repo.count(), "entries": entries}


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
