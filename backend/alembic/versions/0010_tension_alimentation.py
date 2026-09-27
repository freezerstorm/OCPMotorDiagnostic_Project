"""Migration 0010 : tension d'alimentation du test sous tension.

Décision client (26/09/2026) : le formulaire du test sous tension
gagne le champ « Tension d'alimentation (V) » — OBLIGATOIRE pour
valider le test (le kit ne mesure pas la tension : saisie manuelle
dans les deux modes). La valeur sert de contexte à la lecture du
courant à vide (causes « surtension / sous-tension » fournies par le
client), sans changer la règle I0 ∈ [In/3 ; 2·In/3].

Colonne FLOAT ajoutée à « measurements » (1-1 avec « tests »), NULL
autorisé : les fiches historiques importées n'ont pas cette valeur et
ne sont jamais retouchées. L'obligation ne s'applique qu'à la
VALIDATION d'un test sous tension (validate_online). RESTART uvicorn
requis après migration.
"""

import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "measurements",
        sa.Column("supply_voltage_v", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("measurements", "supply_voltage_v")
