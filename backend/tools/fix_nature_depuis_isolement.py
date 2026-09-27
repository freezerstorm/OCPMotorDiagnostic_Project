"""CORRECTION de la colonne Isolement : notations de NATURE (base).

Une cellule Isolement SANS AUCUN CHIFFRE n'est pas une mesure : c'est
une notation de désignation restée dans la mauvaise colonne
(« M.E », « ME », « Transfo », « Pompe Dragueuse Toyo »…). Elle est
décalée vers la colonne Nature SEULEMENT SI celle-ci est vide
(décision client 26/09/2026). Les mesures — même abrégées, elles ont
toujours un chiffre (« 740 M », « 900M », « 3G ») — restent en place.

La même règle est appliquée à l'import (voir import_registre_reel.py,
fonction deplace_notation_nature) : cet outil ne sert que pour une
base déjà remplie. IDEMPOTENT : une cellule corrigée devient vide.

Usage (depuis backend/) :

    python tools/fix_nature_depuis_isolement.py --dry-run
    python tools/fix_nature_depuis_isolement.py
"""

import argparse
import re
import sys
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal  # noqa: E402
from app.models.registre import RegistreEntry  # noqa: E402


def corriger(dry_run: bool = False) -> int:
    """Décale les notations de nature d'Isolement vers Nature ; 0 si OK."""
    db = SessionLocal()
    try:
        rows = db.scalars(
            select(RegistreEntry).where(RegistreEntry.isolement.is_not(None))
        ).all()
        corrigees = ignorees = 0
        for row in rows:
            isolement, nature = row.isolement, row.nature
            if (isolement and nature is None and not re.search(r"\d", isolement)):
                print(f"  {row.source_ref or row.id} : « {isolement} » décalé "
                      "d'Isolement vers Nature (cellule vide)")
                if not dry_run:
                    row.nature = isolement
                    row.isolement = None
                corrigees += 1
            else:
                ignorees += 1

        if not dry_run:
            db.commit()
        print(f"Lignes corrigées : {corrigees}"
              + (f" (non éligibles, conservées : {ignorees})" if ignorees else ""))
        if dry_run:
            print("DRY-RUN : rien n'a été écrit.")
        return 0
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Décale les notations de nature restées en Isolement vers Nature (vide).")
    parser.add_argument("--dry-run", action="store_true",
                        help="liste les lignes sans rien écrire")
    args = parser.parse_args()
    sys.exit(corriger(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
