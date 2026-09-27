"""Migration 0004 : référence d'origine pour les imports (Étape 15).

Ajoute « tests.source_ref » : identifiant de la ligne DANS LE FICHIER
D'ORIGINE (ex. numéro de ligne de la base historique). Il permet :
  - la TRAÇABILITÉ (retrouver d'où vient chaque fiche importée) ;
  - l'IDEMPOTENCE : un même fichier réimporté ne crée pas de doublons
    (index unique sur les valeurs non nulles).

Les fiches créées par l'application (formulaire) ont source_ref NULL :
elles ne sont pas concernées.
"""

from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tests", sa.Column("source_ref", sa.String(100), nullable=True))
    op.create_index(
        "uq_tests_source_ref",
        "tests",
        ["source_ref"],
        unique=True,
        postgresql_where=sa.text("source_ref IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_tests_source_ref", table_name="tests")
    op.drop_column("tests", "source_ref")
