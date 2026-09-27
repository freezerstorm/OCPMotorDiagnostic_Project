"""BACKFILL du COUPLAGE des FICHES MOTEUR depuis le registre réel.

Les lignes du registre portent une colonne Couplage (« Y », « D »,
« Δ »…) mais la fiche moteur correspondante n'était pas alimentée :
le champ Couplage du formulaire restait vide à la récupération
(demande client 26/09/2026). L'IMPORT est désormais corrigé (voir
import_registre_reel.py, couplage_fiche) ; cet outil complète les
fiches DÉJÀ en base.

Règle (rien n'est inventé) :
  - par moteur, la ligne du registre la plus RÉCENTE (import la plus
    haute) portant un couplage convertible gagne :
        « Y »  → « Étoile (Y) »
        « D » / « Δ » → « Triangle (Δ) » ;
  - seules les fiches dont le champ Couplage est VIDE sont remplies
    (une valeur saisie par le technicien n'est jamais écrasée) ;
  - notations non standard (« C », « S », composites) ignorées.

Usage (depuis backend/) :

    python tools/backfill_couplage_fiches.py --dry-run
    python tools/backfill_couplage_fiches.py
"""

import argparse
import sys
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal  # noqa: E402
from app.models.motor import Motor  # noqa: E402
from app.models.registre import RegistreEntry  # noqa: E402
from tools.import_registre_reel import couplage_fiche  # noqa: E402


def remplir(dry_run: bool = False) -> int:
    """Complète le couplage des fiches vides depuis le registre."""
    db = SessionLocal()
    try:
        lignes = db.execute(
            select(RegistreEntry.matricule, RegistreEntry.couplage, RegistreEntry.id)
            .where(RegistreEntry.matricule.is_not(None),
                   RegistreEntry.couplage.is_not(None))
            .order_by(RegistreEntry.id.desc())
        ).all()
        vus: set[str] = set()
        remplis = ignores = fiches_absentes = 0
        for matricule, couplage, _id in lignes:
            if matricule in vus:
                continue                      # déjà traité (ligne plus récente)
            vus.add(matricule)
            valeur = couplage_fiche(couplage)
            if valeur is None:
                ignores += 1                  # notation non convertible
                continue
            motor = db.scalar(select(Motor).where(Motor.motor_id == matricule))
            if motor is None:
                fiches_absentes += 1          # ligne sans fiche moteur
                continue
            if motor.coupling:
                continue                      # fiche déjà renseignée : intouchée
            print(f"  {matricule} : Couplage « {valeur} » (registre « {couplage} »)")
            if not dry_run:
                motor.coupling = valeur
            remplis += 1

        if not dry_run:
            db.commit()
        print(f"Fiches remplies : {remplis}"
              f" (notations non convertibles : {ignores}"
              f" · sans fiche moteur : {fiches_absentes})")
        if dry_run:
            print("DRY-RUN : rien n'a été écrit.")
        return 0
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Complète le Couplage des fiches moteur vides depuis le registre.")
    parser.add_argument("--dry-run", action="store_true",
                        help="liste les fiches sans rien écrire")
    args = parser.parse_args()
    sys.exit(remplir(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
