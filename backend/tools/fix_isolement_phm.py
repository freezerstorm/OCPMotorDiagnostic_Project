"""CORRECTION de la colonne Isolement : deux valeurs « A / B » (base).

Dans les lots 1 à 3, la cellule Isolement (ph-ph) porte souvent DEUX
valeurs séparées par « / » (ex. « 2,9 GΩ / 25 GΩ », « 2,75 / 2,9 GΩ ») :
la valeur de DROITE est décalée vers la colonne Isolement ph-m
SEULEMENT SI celle-ci est vide ; Isolement garde la valeur de gauche.
Quand l'unité est portée une seule fois en fin de cellule
(« 2,75 / 2,9 GΩ »), elle est recopiée sur la valeur de gauche
(« 2,75 GΩ ») — elle vient de la cellule elle-même.

DÉCISION CLIENT (26/09/2026). Cas non traités : Isolement ph-m déjà
rempli ; parties qui ne sont pas des valeurs (« MT/BT = 2,4 GΩ » :
une seule mesure avec préfixe ; étiquettes sans nombre ; 3 valeurs
et plus).

La même règle est appliquée à l'import (voir import_registre_reel.py,
fonction separe_isolement_deux_valeurs) : cet outil ne sert que pour
une base déjà remplie. IDEMPOTENT : une cellule corrigée n'a plus
de « / ».

Usage (depuis backend/) :

    python tools/fix_isolement_phm.py --dry-run
    python tools/fix_isolement_phm.py
"""

import argparse
import sys
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal  # noqa: E402
from app.models.registre import RegistreEntry  # noqa: E402
from tools.import_registre_reel import separe_isolement_deux_valeurs  # noqa: E402


def corriger(dry_run: bool = False) -> int:
    """Décale la valeur de droite d'Isolement vers Isolement ph-m ; 0 si OK."""
    db = SessionLocal()
    try:
        rows = db.scalars(
            select(RegistreEntry).where(RegistreEntry.isolement.like("%/%"))
        ).all()
        corrigees = ignorees = 0
        for row in rows:
            isolement, isolement_m, separe = separe_isolement_deux_valeurs(
                row.isolement, row.isolement_ph_m)
            if not separe:
                ignorees += 1
                continue
            print(f"  {row.source_ref or row.id} : Isolement « {row.isolement} » → "
                  f"Isolement = « {isolement} » · Isolement ph-m = « {isolement_m} »")
            if not dry_run:
                row.isolement = isolement
                row.isolement_ph_m = isolement_m
            corrigees += 1

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
        description="Décale la valeur de droite d'une cellule Isolement à deux valeurs vers Isolement ph-m (vide).")
    parser.add_argument("--dry-run", action="store_true",
                        help="liste les lignes sans rien écrire")
    args = parser.parse_args()
    sys.exit(corriger(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
