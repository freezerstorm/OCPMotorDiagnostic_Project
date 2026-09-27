"""IMPORT DU REGISTRE RÉEL (fichier Excel/CSV du client).

Importe le registre numérique réel (ex. « registre_moteurs_1.xlsx »
exporté en CSV) dans la base :

  - CHAQUE LIGNE du fichier = UN essai historique du registre :
    fiche moteur (créée ou complétée) + essai importé (statut
    « archived », source_ref = « REG:CL-<ligne> ») + ligne du registre
    avec les VALEURS BRUTES du fichier (intitulés, unités et ordre
    conservés — rien n'est converti ni inventé) ;
  - IDEMPOTENCE : la référence de ligne (source_ref) rend le
    ré-import du même fichier sans doublon ;
  - les colonnes du fichier correspondent aux 20 colonnes du registre
    (Date, Matricule, DI/OT, Couplage, Service, Un, In, Uo, Io,
    Nature, Isolement Ph/N, Unité isolement Ph/N, Isolement Ph/Ph,
    Unité isolement Ph/Ph, Résistance (Ω), Puissance, Unité puissance,
    Tension, Société, Dossier) — correspondance SOUPLE : majuscules,
    accents et espaces ignorés ;
  - une ligne invalide n'est jamais importée (rapport clair, ligne
    par ligne, exportable en CSV).

Usage (depuis backend/) :

    python tools/import_registre.py MON_FICHIER.csv --dry-run  # essai
    python tools/import_registre.py MON_FICHIER.csv            # import
    python tools/import_registre.py MON_FICHIER.csv --report erreurs.csv
"""

import argparse
import csv
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

from sqlalchemy import select, text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal  # noqa: E402
from app.models.motor import Motor  # noqa: E402
from app.models.registre import RegistreEntry  # noqa: E402
from app.models.test import Test  # noqa: E402


def next_test_id(db) -> str:
    """Nouvel identifiant lisible via la séquence (comme l'application)."""
    value = db.execute(text("SELECT nextval('test_id_seq')")).scalar_one()
    return f"T-{value:04d}"

# ------------------------------------------------------------------
# Correspondance SOUPLE : en-tête du fichier → champ du registre.
# La normalisation (minuscules, sans accents, sans espaces ni
# ponctuation) rend la correspondance tolérante aux variantes
# d'écriture de l'Excel (« Matricule », « matricule », « MATRICULE »…).
# ------------------------------------------------------------------
HEADER_ALIASES = {
    "date": "entry_date",
    "matricule": "matricule",
    "diot": "di_ot",
    "couplage": "couplage",
    "service": "service",
    "un": "un_v",
    "in": "in_a",
    "uo": "uo_v",
    "io": "io_a",
    "nature": "nature",
    "isolementphn": "insulation_ph_n",
    "uniteisolementphn": "insulation_ph_n_unit",
    "isolementphph": "insulation_ph_ph",
    "uniteisolementphph": "insulation_ph_ph_unit",
    # « MAT » de la capture réelle = le Matricule (précision client)
    "mat": "matricule",
    # « Service (Sce) » → les parenthèses sont retirées par la normalisation
    "servicesce": "service",
    # « Résistance (Ω) » → le Ω est retiré par la normalisation
    "resistance": "resistance_ohm",
    "resistanceohm": "resistance_ohm",
    "puissance": "power_value",
    "unitepuissance": "power_unit",
    "tension": "tension_v",
    "societe": "societe",
    "dossier": "dossier",
}

# Colonnes numériques du registre (les autres restent du texte brut).
NUMERIC_FIELDS = {"un_v", "in_a", "uo_v", "io_a", "power_value", "tension_v"}

REQUIRED_FIELDS = ("matricule",)  # identité minimale d'une ligne du registre


def norm_header(text: str) -> str:
    """En-tête normalisé : minuscules, sans accents/espaces/ponctuation."""
    text = unicodedata.normalize("NFKD", str(text or ""))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", text.lower())


def map_headers(fieldnames: list[str]) -> tuple[dict[str, str], list[str]]:
    """En-têtes du fichier → champs connus + liste des inconnus."""
    mapping: dict[str, str] = {}
    unknown: list[str] = []
    for name in fieldnames:
        key = norm_header(name)
        if not key:
            continue
        if key in HEADER_ALIASES:
            mapping[name] = HEADER_ALIASES[key]
        else:
            unknown.append(name)
    return mapping, unknown


def parse_number(raw: str) -> float | None:
    """Nombre « à la française » ou anglais ; vide → None (rien d'inventé)."""
    text = str(raw or "").strip().replace("\u00a0", "").replace(" ", "")
    if text == "":
        return None
    text = text.replace(",", ".")
    try:
        return float(text)
    except ValueError:
        raise ValueError(f"nombre invalide : {raw!r}")


# Nombre éventuellement suivi d'une unité collée (« 6,6 kW », « 400V »)
_NUMBER_UNIT_RE = re.compile(r"^([0-9][0-9\s\u00a0.,]*)\s*([A-Za-zΩ²/]*)$")


def parse_number_and_unit(raw: str) -> tuple[float | None, str | None]:
    """« 6,6 kW » → (6.6, « kW ») ; « 45 » → (45.0, None) ; vide → (None, None).

    L'unité lue dans la cellule est restituée telle quelle (rien
    d'inventé, rien de converti).
    """
    text = str(raw or "").strip().replace("\u00a0", " ")
    if text == "":
        return None, None
    match = _NUMBER_UNIT_RE.match(text)
    if not match:
        raise ValueError(f"nombre invalide : {raw!r}")
    value = float(match.group(1).replace(" ", "").replace(",", "."))
    unit = match.group(2).strip() or None
    return value, unit


# Mois en lettres (export Excel FR/EN) → numéro
_MONTHS = {
    "jan": 1, "fev": 2, "feb": 2, "mar": 3, "avr": 4, "apr": 4,
    "mai": 5, "may": 5, "juin": 6, "jun": 6, "juil": 7, "jul": 7,
    "aou": 8, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}
_MONTH_DATE_RE = re.compile(r"^(\d{1,2})[\s\-.]+([^\W\d_]+)[\s\-.]+(\d{2,4})$")


def _month_number(token: str) -> int | None:
    """« Feb » / « févr. » / « Février »… → numéro du mois (None si inconnu)."""
    key = norm_header(token)[:4]
    return _MONTHS.get(key[:3]) or _MONTHS.get(key)


def parse_date(raw: str):
    """Date JJ/MM/AAAA, AAAA-MM-JJ ou « 05-Feb-24 » (mois en lettres) ; vide → None."""
    text = str(raw or "").strip()
    if text == "":
        return None
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%d-%m-%y", "%d-%m-%Y", "%Y-%m-%d",
                "%d-%b-%y", "%d-%b-%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    # « 05-Feb-24 », « 28-nov-24 », « 5 février 2024 »… (mois en lettres)
    match = _MONTH_DATE_RE.match(text)
    if match:
        day, month_token, year = match.groups()
        month = _month_number(month_token)
        if month is not None:
            year = int(year)
            if year < 100:
                year += 2000
            return datetime(year, month, int(day)).date()
    raise ValueError(
        f"date invalide : {raw!r} (formats acceptés : JJ/MM/AAAA, AAAA-MM-JJ, JJ-MMM-AA)"
    )


def read_rows(path: Path) -> tuple[list[dict], dict[str, str], list[str]]:
    """Lit le CSV (séparateur , ou ; ; UTF-8 ou Windows) → lignes mappées."""
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            with open(path, newline="", encoding=encoding) as fh:
                sample = fh.read(4096)
                fh.seek(0)
                sep = ";" if sample.count(";") > sample.count(",") else ","
                reader = csv.DictReader(fh, delimiter=sep)
                mapping, unknown = map_headers(reader.fieldnames or [])
                rows = []
                for raw in reader:
                    rows.append({field: raw.get(header, "") for header, field in mapping.items()})
                return rows, mapping, unknown
        except UnicodeDecodeError:
            continue
    raise ValueError("encodage non reconnu (essayer UTF-8 ou Windows)")


def missing_in_file(mapping: dict[str, str]) -> list[str]:
    """Champs obligatoires absents des en-têtes du fichier."""
    present = set(mapping.values())
    return [f for f in REQUIRED_FIELDS if f not in present]


def process_row(index: int, row: dict) -> tuple[str, dict]:
    """Valide une ligne → (clé source, valeurs du registre prêtes à écrire)."""
    for field in REQUIRED_FIELDS:
        if not str(row.get(field) or "").strip():
            raise ValueError(f"colonne « {field} » vide (obligatoire)")

    values = {}
    for field, raw in row.items():
        text = str(raw or "").strip()
        if field == "entry_date":
            values[field] = parse_date(text)
        elif field == "power_value":
            # « 6,6 kW » : l'unité collée au nombre alimente la colonne
            # « Unité puissance » (si elle n'est pas déjà remplie).
            values[field], unit = parse_number_and_unit(text)
            if unit:
                values.setdefault("__power_unit", unit)
        elif field in NUMERIC_FIELDS:
            values[field] = parse_number_and_unit(text)[0]
        else:
            values[field] = text or None

    # Unité lue sur le nombre : utilisée seulement si la colonne
    # « Unité puissance » du fichier est vide pour cette ligne.
    unit_from_number = values.pop("__power_unit", None)
    if unit_from_number and not values.get("power_unit"):
        values["power_unit"] = unit_from_number
    return f"REG:CL-{index}", values


def import_file(path: Path, dry_run: bool = False, report_path: Path | None = None) -> int:
    """Importe le fichier ; renvoie le nombre de lignes importées."""
    rows, mapping, unknown = read_rows(path)
    print(f"Fichier : {path}")
    print(f"Colonnes reconnues : {len(mapping)} / {len(mapping) + len(unknown)}"
          + (f" — IGNORÉES : {', '.join(unknown)}" if unknown else ""))
    missing = missing_in_file(mapping)
    if missing:
        print(f"ERREUR : colonnes obligatoires absentes du fichier : {', '.join(missing)}")
        return 1

    parsed: list[tuple[str, dict]] = []
    errors: list[tuple[int, str]] = []
    for index, row in enumerate(rows, start=2):  # ligne 1 = en-têtes
        try:
            parsed.append(process_row(index, row))
        except ValueError as exc:
            errors.append((index, str(exc)))

    print(f"Lignes valides : {len(parsed)} — erreurs : {len(errors)}")
    for index, message in errors:
        print(f"  ligne {index} : {message}")

    if dry_run:
        print("DRY-RUN : rien n'a été écrit.")
    elif parsed:
        db = SessionLocal()
        try:
            added = 0
            for source_ref, values in parsed:
                if db.scalar(select(Test.id).where(Test.source_ref == source_ref)) is not None:
                    continue  # déjà importé (idempotence)

                # Fiche moteur (le Matricule est l'identité du registre)
                motor_id = values["matricule"]
                motor = db.scalar(select(Motor).where(Motor.motor_id == motor_id))
                if motor is None:
                    motor = Motor(motor_id=motor_id)
                    db.add(motor)
                motor.matricule = motor_id
                if values.get("couplage"):
                    motor.coupling = values["couplage"]
                if values.get("service"):
                    motor.service = values["service"]
                if values.get("un_v") is not None:
                    motor.rated_voltage_v = values["un_v"]
                if values.get("in_a") is not None:
                    motor.rated_current_a = values["in_a"]
                if values.get("power_value") is not None:
                    motor.rated_power_kw = values["power_value"]
                if values.get("di_ot"):
                    motor.di_ot = values["di_ot"]
                # Précision client : la colonne « Nature » du registre
                # est la DÉSIGNATION du moteur.
                if values.get("nature"):
                    motor.designation = values["nature"]

                # Essai importé (historique) : 1 ligne fichier = 1 essai
                test = Test(
                    test_id=next_test_id(db),
                    mode="manual",
                    status="archived",
                    source_ref=source_ref,
                    motor_id=motor_id,
                )
                db.add(test)
                db.flush()  # attribue test.id

                db.add(RegistreEntry(
                    test_row_id=test.id, source="historique", **values
                ))
                added += 1
            db.commit()
            print(f"Import terminé : {added} ligne(s) de registre créée(s).")
        finally:
            db.close()

    if report_path and errors:
        with open(report_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["ligne_fichier", "erreur"])
            writer.writerows(errors)
        print(f"Rapport d'erreurs : {report_path}")
    return 1 if errors and not parsed else 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Import du registre réel (CSV).")
    parser.add_argument("fichier", type=Path, help="fichier CSV du registre réel")
    parser.add_argument("--dry-run", action="store_true",
                        help="valide tout sans rien écrire (à faire AVANT)")
    parser.add_argument("--report", type=Path, default=None,
                        help="exporte les erreurs ligne par ligne (CSV)")
    args = parser.parse_args()
    sys.exit(import_file(args.fichier, dry_run=args.dry_run, report_path=args.report))


if __name__ == "__main__":
    main()
