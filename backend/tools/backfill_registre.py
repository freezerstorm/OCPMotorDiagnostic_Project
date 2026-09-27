"""COMPLÉTER LE REGISTRE avec les essais déjà en base (outil).

Ajoute au registre numérique :
  - les essais IMPORTÉS de l'historique (source_ref renseigné) ;
  - les essais DÉCIDÉS par le technicien (decision renseignée).

Idempotent : les essais déjà inscrits sont ignorés — réexécuter
l'outil ne crée jamais de doublon et ne remplace aucune ligne.

Usage (depuis backend/) :

    python tools/backfill_registre.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal  # noqa: E402
from app.services.registre import backfill_from_existing_tests  # noqa: E402


def main() -> None:
    db = SessionLocal()
    try:
        added = backfill_from_existing_tests(db)
        print(f"Lignes ajoutées au registre : {len(added)}")
        for test_id in added:
            print(f"  - {test_id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
