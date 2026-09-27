"""Migration 0009 : colonnes du LOT 4 (format 4 du registre réel).

Le client a fourni un 4ᵉ format de fichier qui ajoute trois mesures :

  - « Couplage » : couplage du moteur (étoile « Y », triangle « Δ ») —
    demandé par le client, rempli quand la ligne en a un, vide sinon ;
    pour les lots antérieurs, les symboles étoile/triangle des cellules
    de tension sont repris dans cette colonne (backfill) ;
  - « R » : résistance mesurée (texte brut « 0,6 Ω ») ;
  - « Isolement ph-m » : isolement phase-masse, distinct de
    « Isolement » (phase-phase) dans le format 4.

Trois colonnes TEXTuelles ajoutées, NULL autorisé (les lots 1 à 3 et
les essais de l'application n'ont pas ces valeurs) — aucune donnée
existante n'est modifiée. RESTART uvicorn requis après migration.

 ATTENTION : vider les chaînes « R » / « couplage » : « r » est un nom
 SQL valide ; rien à échapper.
"""

import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "registre_entries",
        sa.Column("couplage", sa.String(20), nullable=True),
    )
    op.add_column(
        "registre_entries",
        sa.Column("r", sa.Text(), nullable=True),
    )
    op.add_column(
        "registre_entries",
        sa.Column("isolement_ph_m", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("registre_entries", "isolement_ph_m")
    op.drop_column("registre_entries", "r")
    op.drop_column("registre_entries", "couplage")
