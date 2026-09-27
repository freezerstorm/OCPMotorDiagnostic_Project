"""BACKFILL COUPLAGE — lots antérieurs (demande client).

Dans les lots 1 à 3, le couplage n'a pas de colonne dédiée : le
symbole étoile (« Y ») ou triangle (« D ») figure à la fin des
CELLULES DE TENSION (Un / U0), ex. « 500 Y », « 525D ». Le client a
demandé que ces symboles soient pris en considération dans la
nouvelle colonne Couplage.

Règles (rien n'est inventé) :
  - seules les lignes SANS couplage sont remplies (idempotent) ;
  - le symbole est recopié TEL QUEL depuis la cellule (« Y », « D ») ;
  - Un et U0 sont examinés ; deux symboles différents dans la même
    ligne → les deux, séparés par « / » (et signalés en log).

Usage (depuis backend/) :

    python tools/backfill_couplage.py --dry-run
    python tools/backfill_couplage.py
"""

import argparse
import re
import sys
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal  # noqa: E402
from app.models.registre import RegistreEntry  # noqa: E402

# Symbole de couplage isolé dans une cellule de tension (« 500 Y »,
# « 525D », « 400 Δ »…) : une seule lettre Y/D/Δ, entourée de
# non-lettres. Uniquement en MAJUSCULES (éviter les mots du texte).
_SYMBOLE_RE = re.compile(r"(?:^|[^A-Za-zÀ-ÿ])([YΔD])(?:$|[^A-Za-zÀ-ÿ])")


def symboles(cellule: str | None) -> list[str]:
    """Symboles de couplage d'une cellule (« 500 Y » → ['Y'])."""
    if not cellule:
        return []
    return _SYMBOLE_RE.findall(cellule)


def backfill(dry_run: bool = False) -> int:
    """Remplit la colonne Couplage depuis Un/U0 ; renvoie 0 si OK."""
    db = SessionLocal()
    try:
        rows = db.scalars(
            select(RegistreEntry).where(RegistreEntry.couplage.is_(None))
        ).all()
        rempli = 0
        for row in rows:
            trouves = symboles(row.un_v) + symboles(row.uo_v)
            if not trouves:
                continue
            # Symboles distincts dans l'ordre des cellules (Un puis U0).
            dedup = list(dict.fromkeys(trouves))
            valeur = " / ".join(dedup)
            print(f"  {row.source_ref or row.id} : Un=« {row.un_v} » "
                  f"U0=« {row.uo_v} » → Couplage « {valeur} »")
            if not dry_run:
                row.couplage = valeur
            rempli += 1

        if not dry_run:
            db.commit()
        print(f"Lignes remplies : {rempli}")
        if dry_run:
            print("DRY-RUN : rien n'a été écrit.")
        return 0
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Backfill de la colonne Couplage (symboles Y/D/Δ des cellules de tension).")
    parser.add_argument("--dry-run", action="store_true",
                        help="liste les lignes sans rien écrire")
    args = parser.parse_args()
    sys.exit(backfill(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
