"""PURGE DES DONNÉES DE DIAGNOSTIC (demande client).

Supprime TOUTES les données de démonstration / d'essai de la base :

  - les lignes du registre numérique (registre_entries) ;
  - les échantillons du kit (acquisition_samples) ;
  - les mesures (measurements) ;
  - les sessions de diagnostic (tests) ;
  - les fiches moteurs (motors).

La NUMÉROTATION repart de zéro : le prochain test créé sera « T-0001 ».

SERT À : remplacer les données fictives par le registre réel (import
du fichier Excel/CSV du client). L'opération est irréversible — les
essais réellement réalisés doivent être exportés avant.

Usage (depuis backend/) :

    python tools/purge_donnees.py            # purge effective
    python tools/purge_donnees.py --dry-run  # compte seulement
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete, func, select, text  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402
from app.models.motor import Motor  # noqa: E402
from app.models.registre import RegistreEntry  # noqa: E402
from app.models.sample import AcquisitionSample  # noqa: E402
from app.models.test import Measurements, Test  # noqa: E402

# Ordre de suppression : tables liées d'abord (clés étrangères).
# Chaque entrée : (modèle, libellé pour le rapport).
_TARGETS = [
    (RegistreEntry, "registre (lignes du registre numérique)"),
    (AcquisitionSample, "échantillons du kit"),
    (Measurements, "mesures"),
    (Test, "sessions de diagnostic"),
    (Motor, "fiches moteurs"),
]

_RESET_SEQUENCE = text("ALTER SEQUENCE test_id_seq RESTART WITH 1")


def main() -> None:
    parser = argparse.ArgumentParser(description="Purge des données de diagnostic.")
    parser.add_argument("--dry-run", action="store_true",
                        help="compte les lignes sans rien supprimer")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        counts = {
            label: db.scalar(select(func.count()).select_from(model)) or 0
            for model, label in _TARGETS
        }
        total = sum(counts.values())
        print("Lignes concernées :")
        for label, count in counts.items():
            print(f"  - {label:45s} {count}")

        if args.dry_run:
            print("DRY-RUN : rien n'a été supprimé.")
            return
        if total == 0:
            print("Base déjà vide : rien à faire.")
            return

        for model, _ in _TARGETS:
            db.execute(delete(model))
        db.execute(_RESET_SEQUENCE)
        db.commit()
        print(f"Purge effectuée : {total} ligne(s) supprimée(s) ; "
              "prochain test = T-0001.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
