"""CORRECTION du décalage ÉVIDENT Société ↔ BT/MT (base déjà importée).

Dans une partie du fichier du lot 3 (complément 2), les colonnes
« Société » et « BT/MT (Tension) » sont INVERSÉES : la tension
(« BT », « MT ») se retrouve en Société et le nom de la société de
réparation (« FAR », « AB », « BOM »…) en BT/MT — même type de
décalage que le swap Isolement ↔ Nature déjà corrigé.

DÉCISION CLIENT (26/09/2026) : corriger le décalage UNIQUEMENT quand
il est ÉVIDENT, c'est-à-dire quand les deux indices convergent :
  - la colonne Société contient une TENSION (« BT », « MT », « H.T »…) ;
  - ET la colonne BT/MT contient un nom (non vide, non tension).
Les cas ambigus (une seule cellule renseignée) ne sont PAS touchés.

TRANSPOSITION (2ᵉ passe, même décision) : les notations de la colonne
BT/MT qui ne sont PAS des tensions (MT/BT/HT) — donc normalement des
notations de SOCIÉTÉ — sont déplacées vers la colonne Société
SEULEMENT SI celle-ci est VIDE.

Les mêmes règles sont appliquées à l'import (voir
import_registre_reel.py) : cet outil ne sert que pour une base déjà
remplie. IDEMPOTENT : une ligne corrigée n'est plus éligible.

Usage (depuis backend/) :

    python tools/fix_societe_btmt.py --dry-run
    python tools/fix_societe_btmt.py
"""

import argparse
import re
import sys
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal  # noqa: E402
from app.models.registre import RegistreEntry  # noqa: E402
from tools.import_registre_reel import (  # noqa: E402
    deplace_btmt_vers_societe,
    deplace_societe_vers_btmt,
    echange_societe_btmt,
)


def corriger(dry_run: bool = False) -> int:
    """Corrige Société/BT-MT en base ; 0 si OK.

    Trois corrections (décisions client 26/09/2026) :
      1. ÉCHANGE ÉVIDENT (les deux cellules portent l'indice de
         l'autre) ;
      2. TRANSPOSITION BT/MT → Société : notation de société restée en
         BT/MT, déplacée vers Société SEULEMENT SI Société est vide ;
      3. TRANSPOSITION Société → BT/MT : notation de TENSION restée en
         Société, déplacée vers BT/MT SEULEMENT SI BT/MT est vide.
    Idempotent : une ligne corrigée n'est plus éligible.
    """
    db = SessionLocal()
    try:
        rows = db.scalars(select(RegistreEntry)).all()
        echanges = transpositions = 0
        for row in rows:
            societe, bt_mt = row.societe, row.bt_mt
            nouvelle_s, nouvelle_b, echange = echange_societe_btmt(societe, bt_mt)
            if echange:
                print(f"  {row.source_ref or row.id} : Société « {societe} » "
                      f"↔ BT/MT « {bt_mt} » échangées")
                societe, bt_mt = nouvelle_s, nouvelle_b
                echanges += 1
            nouvelle_s, nouvelle_b, transpose = deplace_btmt_vers_societe(societe, bt_mt)
            if transpose:
                print(f"  {row.source_ref or row.id} : « {nouvelle_s} » transposé "
                      "de BT/MT vers Société (cellule vide)")
                societe, bt_mt = nouvelle_s, nouvelle_b
                transpositions += 1
            nouvelle_s, nouvelle_b, transpose2 = deplace_societe_vers_btmt(societe, bt_mt)
            if transpose2:
                print(f"  {row.source_ref or row.id} : « {nouvelle_b} » transposé "
                      "de Société vers BT/MT (cellule vide)")
                societe, bt_mt = nouvelle_s, nouvelle_b
                transpositions += 1
            if (echange or transpose or transpose2) and not dry_run:
                row.societe = societe
                row.bt_mt = bt_mt

        if not dry_run:
            db.commit()
        print(f"Échanges évidents : {echanges} · transpositions : {transpositions}")
        if dry_run:
            print("DRY-RUN : rien n'a été écrit.")
        return 0
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Correction du décalage évident Société ↔ BT/MT (décision client).")
    parser.add_argument("--dry-run", action="store_true",
                        help="liste les lignes sans rien écrire")
    args = parser.parse_args()
    sys.exit(corriger(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
