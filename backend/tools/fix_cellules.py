"""CORRECTIONS PONCTUELLES de cellules (base déjà importée).

Applique à la base la table CORRECTIONS_CELLULES des décisions client
(26/09/2026) — voir import_registre_reel.py :

    « JSON-C3:181 » : Puissance « 85 / 75 GΩ » → VIDE (valeurs
    d'isolement restées dans la mauvaise colonne ; la ligne reste au
    registre) ;
    « JSON-C3:96 » : Isolement ph-m « 220 M » → « 220 MΩ » (unité
    manquante complétée).

La même table est appliquée à l'import : cet outil ne sert que pour
une base déjà remplie. IDEMPOTENT.

Usage (depuis backend/) :

    python tools/fix_cellules.py --dry-run
    python tools/fix_cellules.py
"""

import argparse
import sys
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal  # noqa: E402
from app.models.registre import RegistreEntry  # noqa: E402
from tools.import_registre_reel import CORRECTIONS_CELLULES  # noqa: E402


def corriger(dry_run: bool = False) -> int:
    """Applique CORRECTIONS_CELLULES à la base ; renvoie 0 si OK."""
    db = SessionLocal()
    try:
        rows = db.scalars(
            select(RegistreEntry)
            .where(RegistreEntry.source_ref.in_(CORRECTIONS_CELLULES.keys()))
        ).all()
        corrigees = 0
        for row in rows:
            for champ, nouvelle in CORRECTIONS_CELLULES[row.source_ref].items():
                actuelle = getattr(row, champ)
                if actuelle == nouvelle:
                    continue
                print(f"  {row.source_ref} : {champ} « {actuelle} » → "
                      f"« {nouvelle} »")
                if not dry_run:
                    setattr(row, champ, nouvelle)
                corrigees += 1

        if not dry_run:
            db.commit()
        print(f"Corrections appliquées : {corrigees}")
        if dry_run:
            print("DRY-RUN : rien n'a été écrit.")
        return 0
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Applique les corrections ponctuelles de cellules (décisions client).")
    parser.add_argument("--dry-run", action="store_true",
                        help="liste les corrections sans rien écrire")
    args = parser.parse_args()
    sys.exit(corriger(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
