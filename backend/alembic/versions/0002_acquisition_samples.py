"""Table « acquisition_samples » : échantillons mesurés par le kit.

Révision : 0002 — ajoutée à l'Étape 8 (acquisition automatique).

- Une ligne = un échantillon reçu du kit pendant l'acquisition ;
- t_s = secondes écoulées depuis le début de l'acquisition ;
- test_id → tests.id (les échantillons suivent la fiche de diagnostic).
"""

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "acquisition_samples",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("test_id", sa.Integer(), nullable=False),
        sa.Column("t_s", sa.Float(), nullable=False),
        sa.Column("temperature_c", sa.Float(), nullable=True),
        sa.Column("current_a", sa.Float(), nullable=True),
        sa.Column("vib_x_g", sa.Float(), nullable=True),
        sa.Column("vib_y_g", sa.Float(), nullable=True),
        sa.Column("vib_z_g", sa.Float(), nullable=True),
        sa.Column("vib_global_g", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["test_id"], ["tests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_acquisition_samples_test_id", "acquisition_samples", ["test_id"])


def downgrade() -> None:
    op.drop_index("ix_acquisition_samples_test_id", table_name="acquisition_samples")
    op.drop_table("acquisition_samples")
