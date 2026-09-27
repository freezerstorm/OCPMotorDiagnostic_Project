"""Migration 0006 : vibration du kit publiée en mm/s (décision client).

Le kit publie désormais la vibration directement en mm/s (vitesse
vibratoire, comme la saisie manuelle du technicien) au lieu de
l'accélération en g. Les 4 colonnes sont RENOMMÉES ; les valeurs déjà
enregistrées (données de démonstration) ne sont PAS converties.
"""

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

_RENAMES = [
    ("vib_x_g", "vib_x_mm_s"),
    ("vib_y_g", "vib_y_mm_s"),
    ("vib_z_g", "vib_z_mm_s"),
    ("vib_global_g", "vib_global_mm_s"),
]


def upgrade() -> None:
    for old, new in _RENAMES:
        op.alter_column(
            "acquisition_samples", old,
            new_column_name=new, existing_type=sa.Float(), existing_nullable=True,
        )


def downgrade() -> None:
    for old, new in _RENAMES:
        op.alter_column(
            "acquisition_samples", new,
            new_column_name=old, existing_type=sa.Float(), existing_nullable=True,
        )
