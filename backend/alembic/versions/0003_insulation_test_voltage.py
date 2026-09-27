"""Migration 0003 : tension de test d'isolement.

Ajoute la colonne « insulation_test_voltage_v » à la table
« measurements » : la tension choisie par le technicien
(500 / 1000 / 2500 / 5000 V) est enregistrée AVEC le diagnostic,
car la règle d'isolement (1 kΩ par volt) en dépend.

Révision : 0003 — règles de diagnostic (courant / isolement / température).
"""

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "measurements",
        sa.Column("insulation_test_voltage_v", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("measurements", "insulation_test_voltage_v")
