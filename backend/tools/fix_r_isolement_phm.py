"""CORRECTION de la colonne R : deux valeurs « A / B » (base déjà importée).

Dans une partie du lot 4, la cellule R porte DEUX valeurs séparées
par « / » (ex. « 1,5 GΩ / 0,2 Ω », « 1,2 Ω / 4,5 Ω ») : la valeur de
gauche — souvent un isolement (GΩ/MΩ) resté dans R — est décalée vers
la colonne Isolement ph-m SEULEMENT SI celle-ci est vide ; R garde la
valeur de droite. Quand l'unité est portée une seule fois en fin de
cellule (« 1,28 / 2,2 Ω »), elle est recopiée sur la valeur déplacée
(« 1,28 Ω ») — elle vient de la cellule elle-même.

DÉCISION CLIENT (26/09/2026). Cas non traités : Isolement ph-m déjà
rempli, ou parties qui ne sont pas des mesures (libellés
« R1=C1=2 / R2=C2=2 », « R1-52/R2-51 »).

La même règle est appliquée à l'import (voir import_registre_reel.py,
fonction separe_r_deux_valeurs) : cet outil ne sert que pour une base
déjà remplie. IDEMPOTENT : une cellule corrigée n'a plus de « / ».

Usage (depuis backend/) :

    python tools/fix_r_isolement_phm.py --dry-run
    python tools/fix_r_isolement_phm.py
"""

import argparse
import sys
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal  # noqa: E402
from app.models.registre import RegistreEntry  # noqa: E402
from tools.import_registre_reel import separe_r_deux_valeurs  # noqa: E402


def corriger(dry_run: bool = False) -> int:
    """Décale la valeur de gauche de R vers Isolement ph-m ; 0 si OK."""
    db = SessionLocal()
    try:
        rows = db.scalars(
            select(RegistreEntry).where(RegistreEntry.r.like("%/%"))
        ).all()
        corrigees = ignorees = 0
        for row in rows:
            r, isolement_m, separe = separe_r_deux_valeurs(
                row.r, row.isolement_ph_m)
            if not separe:
                ignorees += 1
                continue
            print(f"  {row.source_ref or row.id} : R « {row.r} » → "
                  f"R = « {r} » · Isolement ph-m = « {isolement_m} »")
            if not dry_run:
                row.r = r
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
        description="Décale la valeur de gauche d'une cellule R à deux valeurs vers Isolement ph-m (vide).")
    parser.add_argument("--dry-run", action="store_true",
                        help="liste les lignes sans rien écrire")
    args = parser.parse_args()
    sys.exit(corriger(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
