"""CORRECTION des isolements NÉGATIFS (base déjà importée).

DÉCISION CLIENT (26/09/2026) : les isolements négatifs deviennent
POSITIFS — le signe « - » de tête est retiré (« -2 GΩ » → « 2 GΩ »).
S'applique aux colonnes Isolement (ph-ph) et Isolement ph-m.
Un tiret à l'intérieur d'un libellé (« R1-52 ») n'est pas concerné,
et la règle ne touche PAS la colonne R.

La même règle est appliquée à l'import (voir import_registre_reel.py,
fonction absolu_isolement) : cet outil ne sert que pour une base déjà
remplie. IDEMPOTENT : une valeur corrigée n'a plus de signe.

Usage (depuis backend/) :

    python tools/fix_isolement_negatifs.py --dry-run
    python tools/fix_isolement_negatifs.py
"""

import argparse
import sys
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal  # noqa: E402
from app.models.registre import RegistreEntry  # noqa: E402
from tools.import_registre_reel import absolu_isolement  # noqa: E402


def corriger(dry_run: bool = False) -> int:
    """Rend les isolements négatifs positifs ; renvoie 0 si OK."""
    db = SessionLocal()
    try:
        rows = db.scalars(select(RegistreEntry)).all()
        corrigees = 0
        for row in rows:
            avant_iso, avant_m = row.isolement, row.isolement_ph_m
            apres_iso = absolu_isolement(avant_iso)
            apres_m = absolu_isolement(avant_m)
            if apres_iso == avant_iso and apres_m == avant_m:
                continue
            print(f"  {row.source_ref or row.id} : "
                  f"Isolement « {avant_iso} » → « {apres_iso} » · "
                  f"ph-m « {avant_m} » → « {apres_m} »")
            if not dry_run:
                row.isolement = apres_iso
                row.isolement_ph_m = apres_m
            corrigees += 1

        if not dry_run:
            db.commit()
        print(f"Lignes corrigées : {corrigees}")
        if dry_run:
            print("DRY-RUN : rien n'a été écrit.")
        return 0
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Retire le signe « - » des isolements négatifs (décision client).")
    parser.add_argument("--dry-run", action="store_true",
                        help="liste les lignes sans rien écrire")
    args = parser.parse_args()
    sys.exit(corriger(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
