"""IMPORT DE LA BASE HISTORIQUE — Étape 15.

Importe des relevés historiques depuis un fichier CSV dans la base,
avec :

  - les MÊMES VALIDATIONS que l'API (schémas Pydantic réutilisés :
    unités, tension de test limitée aux 4 valeurs, décision limitée
    aux 2 codes…) — une ligne invalide n'est jamais importée ;
  - l'IDEMPOTENCE : chaque ligne porte une « id_origine » (numéro ou
    référence dans ton fichier d'origine, stocké dans tests.source_ref)
    → réimporter le même fichier ne crée PAS de doublons ;
  - un mode --dry-run : VALIDE tout sans rien écrire (à faire AVANT) ;
  - un rapport d'erreurs clair, ligne par ligne, exportable en CSV.

Usage (depuis backend/) :

    python tools/import_history.py MON_FICHIER.csv --dry-run   # essai
    python tools/import_history.py MON_FICHIER.csv             # import réel
    python tools/import_history.py MON_FICHIER.csv --report erreurs.csv

Format du CSV : voir docs/IMPORT_HISTORIQUE.md et l'exemple
tools/exemple_import_historique.csv (en-têtes français, UTF-8,
séparateur , ou ; accepté, décimales avec virgule acceptées).
"""

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.repositories.sql.motor_repository import MotorRepository  # noqa: E402
from app.repositories.sql.test_repository import TestRepository  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.schemas.motors import MotorCreate  # noqa: E402
from app.schemas.tests import (  # noqa: E402
    Measurements,
    TEST_STATUS_ARCHIVED,
    TEST_STATUS_COMPLETED,
)

# ------------------------------------------------------------------
# Correspondance en-têtes du CSV (français) → champs de l'application.
# Colonnes obligatoires : id_moteur et date_test. Toutes les autres
# sont facultatives (ligne vide = information non relevée).
# ------------------------------------------------------------------
HEADER_ALIASES = {
    "id_origine": "id_origine",
    "id_moteur": "id_moteur",
    "matricule": "matricule",
    "designation": "designation",
    "marque": "marque",
    "modele": "modele",
    "n_fabrication": "serial_number",
    "date_test": "date_test",
    "mode": "mode",
    "environnement": "environnement",
    "puissance_kw": "rated_power_kw",
    "tension_v": "rated_voltage_v",
    "courant_nominal_a": "rated_current_a",
    "vitesse_tr_min": "rated_speed_rpm",
    "cos_phi": "cos_phi",
    "tension_test_isolement_v": "test_voltage_v",
    "isolement_ph1_ph2_mohm": "ph1_ph2_mohm",
    "isolement_ph2_ph3_mohm": "ph2_ph3_mohm",
    "isolement_ph3_ph1_mohm": "ph3_ph1_mohm",
    "isolement_ph1_masse_mohm": "ph1_ground_mohm",
    "isolement_ph2_masse_mohm": "ph2_ground_mohm",
    "isolement_ph3_masse_mohm": "ph3_ground_mohm",
    "r12_ohm": "r12_ohm",
    "r23_ohm": "r23_ohm",
    "r31_ohm": "r31_ohm",
    "temperature_c": "temperature_c",
    "temp_palier_couplage_c": "temp_bearing_de_c",
    "temperature_palier_couplage_c": "temp_bearing_de_c",
    "temp_palier_coa_c": "temp_bearing_nde_c",
    "temperature_palier_coa_c": "temp_bearing_nde_c",
    "continuite": "continuity_ok",
    "continuite_enroulements": "continuity_ok",
    "courant_a": "current_a",
    "vibration_mm_s": "vibration_mm_s",
    "decision": "decision",
    "observation": "observation",
}

_DECISION_FR = {
    "remis en service": "serviced",
    "remise en service": "serviced",
    "serviced": "serviced",
    "envoye en reparation": "repair",
    "envoyé en réparation": "repair",
    "reparation": "repair",
    "réparation": "repair",
    "repair": "repair",
}

_NUMBER_FIELDS = {
    "rated_power_kw", "rated_voltage_v", "rated_current_a", "rated_speed_rpm",
    "cos_phi", "test_voltage_v",
    "ph1_ph2_mohm", "ph2_ph3_mohm", "ph3_ph1_mohm",
    "ph1_ground_mohm", "ph2_ground_mohm", "ph3_ground_mohm",
    "r12_ohm", "r23_ohm", "r31_ohm",
    "temperature_c", "current_a", "vibration_mm_s",
    "temp_bearing_de_c", "temp_bearing_nde_c",
}

_ISO_FIELDS = {
    "ph1_ph2_mohm", "ph2_ph3_mohm", "ph3_ph1_mohm",
    "ph1_ground_mohm", "ph2_ground_mohm", "ph3_ground_mohm",
}


def parse_number(raw: str):
    """« 12,5 » ou « 12.5 » → 12.5 ; vide → None ; sinon ValueError."""
    text = str(raw or "").strip().replace(" ", "").replace(",", ".")
    if text == "":
        return None
    return float(text)  # peut lever ValueError → capturée par l'appelant


def parse_date(raw: str) -> datetime:
    """Accepte JJ/MM/AAAA, JJ/MM/AAAA HH:MM ou AAAA-MM-JJ."""
    text = str(raw or "").strip()
    for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise ValueError(f"date illisible : {raw!r} (formats acceptés : JJ/MM/AAAA ou AAAA-MM-JJ)")


def _normalize_header(header: str) -> str:
    """En-tête du CSV → clé interne (minuscules, sans accents/espaces)."""
    key = (
        str(header).strip().lower()
        .replace("é", "e").replace("è", "e").replace("ê", "e")
        .replace("à", "a").replace(" ", "_").replace("-", "_")
    )
    return HEADER_ALIASES.get(key, key)


def read_csv(path: Path):
    """Lit le CSV (UTF-8, BOM Excel toléré, séparateur , ou ; détecté).

    Les lignes sont RELIBELLÉES avec les clés internes normalisées :
    chaque valeur est ainsi retrouvée même quand l'en-tête du fichier
    diffère du nom de champ (ex. « tension_test_isolement_v » →
    « test_voltage_v »).
    """
    with path.open(encoding="utf-8-sig", newline="") as fh:
        sample = fh.read(4096)
        fh.seek(0)
        delimiter = ";" if sample.count(";") > sample.count(",") else ","
        reader = csv.DictReader(fh, delimiter=delimiter)
        raw_headers = reader.fieldnames or []
        headers = [_normalize_header(h) for h in raw_headers]
        rows = []
        for raw in reader:
            rows.append({
                key: raw.get(original)
                for original, key in zip(raw_headers, headers)
            })
    return headers, rows


def build_record(row_number: int, headers: list, row: dict) -> dict:
    """Transforme UNE ligne du CSV en fiche validée (lève ValueError)."""
    data = {}
    for header, value in zip(headers, [row.get(h) for h in headers]):
        if header in HEADER_ALIASES.values():
            data[header] = value

    # --- Champs obligatoires ---
    motor_id = str(data.get("id_moteur") or "").strip()
    if not motor_id:
        raise ValueError("colonne « id_moteur » vide (obligatoire)")
    if not data.get("date_test"):
        raise ValueError("colonne « date_test » vide (obligatoire)")
    test_date = parse_date(data["date_test"])

    # --- Mode (manuel par défaut : la base historique est manuelle) ---
    mode_raw = str(data.get("mode") or "").strip().lower()
    mode = "auto" if mode_raw in ("auto", "automatique") else "manual"

    # --- Décision (libellés français acceptés) ---
    decision_raw = str(data.get("decision") or "").strip().lower()
    decision = None
    if decision_raw:
        decision = _DECISION_FR.get(decision_raw)
        if decision is None:
            raise ValueError(
                f"décision inconnue : {decision_raw!r} "
                "(attendu : « remis en service » ou « envoyé en réparation »)"
            )

    # --- Nombres (virgule décimale acceptée) ---
    numbers = {}
    for field in _NUMBER_FIELDS:
        try:
            numbers[field] = parse_number(data.get(field))
        except ValueError:
            raise ValueError(f"valeur illisible pour {field} : {data.get(field)!r}")

    # --- Continuité globale (É16 : Oui/Non, facultative) ---
    continuity_raw = str(data.get("continuity_ok") or "").strip().lower()
    continuity_ok = None
    if continuity_raw:
        if continuity_raw in ("oui", "o", "yes", "y", "true", "1"):
            continuity_ok = True
        elif continuity_raw in ("non", "n", "no", "false", "0"):
            continuity_ok = False
        else:
            raise ValueError(
                f"continuité illisible : {continuity_raw!r} (attendu : Oui ou Non)"
            )

    # --- Statut : archivé si la décision est prise (traçabilité historique) ---
    status = TEST_STATUS_ARCHIVED if decision else TEST_STATUS_COMPLETED

    # --- Validation par les MÊMES schémas que l'API ---
    motor_payload = {
        "motor_id": motor_id,
        "matricule": str(data.get("matricule") or "").strip() or None,
        "designation": str(data.get("designation") or "").strip() or None,
        "brand": str(data.get("marque") or "").strip() or None,
        "model": str(data.get("modele") or "").strip() or None,
        "serial_number": str(data.get("serial_number") or "").strip() or None,
        "rated_power_kw": numbers["rated_power_kw"],
        "rated_voltage_v": numbers["rated_voltage_v"],
        "rated_current_a": numbers["rated_current_a"],
        "rated_speed_rpm": numbers["rated_speed_rpm"],
        "cos_phi": numbers["cos_phi"],
        "service": str(data.get("environnement") or "").strip() or None,
    }
    try:
        MotorCreate.model_validate(motor_payload)
    except ValidationError as exc:
        raise ValueError(
            "caractéristiques moteur invalides : "
            + (exc.errors()[0].get("msg", str(exc)) if exc.errors() else str(exc))
        )

    measurements_payload = {
        "insulation": {
            "test_voltage_v": numbers["test_voltage_v"],
            "ph1_ph2_mohm": numbers["ph1_ph2_mohm"],
            "ph2_ph3_mohm": numbers["ph2_ph3_mohm"],
            "ph3_ph1_mohm": numbers["ph3_ph1_mohm"],
            "ph1_ground_mohm": numbers["ph1_ground_mohm"],
            "ph2_ground_mohm": numbers["ph2_ground_mohm"],
            "ph3_ground_mohm": numbers["ph3_ground_mohm"],
        },
        "winding": {
            "r12_ohm": numbers["r12_ohm"],
            "r23_ohm": numbers["r23_ohm"],
            "r31_ohm": numbers["r31_ohm"],
            "continuity_ok": continuity_ok,
        },
        "values": {
            "temperature_c": numbers["temperature_c"],
            "temp_bearing_de_c": numbers["temp_bearing_de_c"],
            "temp_bearing_nde_c": numbers["temp_bearing_nde_c"],
            "current_a": numbers["current_a"],
            "vibration_mm_s": numbers["vibration_mm_s"],
        },
    }
    try:
        Measurements.model_validate(measurements_payload)
    except ValidationError as exc:
        raw = str(exc)
        if "literal_error" in raw and "test_voltage_v" in raw:
            raise ValueError(
                "tension de test d'isolement invalide "
                "(valeurs admises : 500 / 1000 / 2500 / 5000 V)"
            )
        if "Tension de test d'isolement obligatoire" in raw:
            raise ValueError(
                "tension de test d'isolement obligatoire lorsque des mesures "
                "d'isolement sont saisies"
            )
        raise ValueError(f"mesures invalides : {raw.splitlines()[1].strip()}")

    # --- id_origine : fournie, ou construite (moteur + date) ---
    source_ref = str(data.get("id_origine") or "").strip() or f"{motor_id}:{test_date:%Y%m%d}"

    observation = str(data.get("observation") or "").strip() or None

    return {
        "motor_payload": motor_payload,
        "record": {
            "mode": mode,
            "status": status,
            "decision": decision,
            "observation": observation,
            "motor_id": motor_id,
            "measurements": measurements_payload,
            "source_ref": source_ref,
            "created_at": test_date,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Import de la base historique (CSV).")
    parser.add_argument("csv_file", help="fichier CSV à importer (voir docs/IMPORT_HISTORIQUE.md)")
    parser.add_argument("--dry-run", action="store_true",
                        help="valide le fichier SANS rien écrire dans la base")
    parser.add_argument("--report", help="chemin d'un rapport d'erreurs CSV (facultatif)")
    args = parser.parse_args()

    path = Path(args.csv_file)
    if not path.is_file():
        print(f"Fichier introuvable : {path}")
        return 1

    headers, rows = read_csv(path)
    print(f"Fichier : {path.name} — {len(rows)} ligne(s), séparateur détecté.")

    # ---------- 1. Validation de TOUTES les lignes ----------
    valid, errors = [], []
    seen_refs = set()
    for index, row in enumerate(rows, start=2):  # ligne 1 = en-têtes
        try:
            prepared = build_record(index, headers, row)
        except ValueError as exc:
            errors.append((index, str(exc)))
            continue
        ref = prepared["record"]["source_ref"]
        if ref in seen_refs:
            errors.append((index, f"id_origine en double dans le fichier : {ref}"))
            continue
        seen_refs.add(ref)
        valid.append(prepared)

    print(f"Validation : {len(valid)} ligne(s) valide(s), {len(errors)} erreur(s).")
    for line, message in errors:
        print(f"  ligne {line} : {message}")

    if args.report and errors:
        with Path(args.report).open("w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["ligne", "erreur"])
            writer.writerows(errors)
        print(f"Rapport d'erreurs écrit : {args.report}")

    if args.dry_run:
        print("DRY-RUN : aucune écriture dans la base (relance sans --dry-run pour importer).")
        return 1 if errors else 0

    if errors:
        print("Import annulé : corrige les lignes en erreur (ou relance avec --dry-run pour vérifier).")
        return 1

    # ---------- 2. Import (moteurs créés s'ils sont inconnus) ----------
    db = SessionLocal()
    motor_repo, test_repo = MotorRepository(db), TestRepository(db)
    created, skipped = 0, 0
    try:
        for prepared in valid:
            ref = prepared["record"]["source_ref"]
            if test_repo.get_by_source_ref(ref) is not None:
                skipped += 1
                continue
            motor = motor_repo.get(prepared["motor_payload"]["motor_id"])
            if motor is None:
                motor_repo.create(prepared["motor_payload"])
            record = {**prepared["record"], "test_id": test_repo.next_id()}
            test_repo.add(record)
            created += 1
    except Exception as exc:  # noqa: BLE001 — on arrête tout et on explique
        db.rollback()
        print(f"ERREUR pendant l'import (rien de partiel n'est conservé) : {exc}")
        return 1
    finally:
        db.close()

    print(f"Import terminé : {created} fiche(s) créée(s), {skipped} déjà présente(s) (ignorée(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
