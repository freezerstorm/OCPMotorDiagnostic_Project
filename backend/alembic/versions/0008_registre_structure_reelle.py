"""Migration 0008 : le registre reprend la structure RÉELLE du fichier
du client (JSON « p1 », 14 colonnes).

La table précédente (0007, colonnes prévues avant réception du fichier
réel) est REMPLACÉE — elle était vide partout (données de démonstration
purgées à la demande du client). Nouvelles colonnes = intitulés réels :
  Date, Matricule, DI/OT, Service (Sce), Un, In, U0, I0, Isolement,
  Nature (désignation du moteur), Puissance (P), Société,
  BT/MT (Tension), Observation.

Les valeurs électriques sont conservées en TEXTE BRUT (« 525V »,
« 1,2 GΩ », « 28,5A / 15A ») : rien n'est converti ni inventé.
« source_ref » (unique) rend les imports idempotents.
"""

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_registre_entries_entry_date", table_name="registre_entries")
    op.drop_table("registre_entries")
    op.create_table(
        "registre_entries",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        # Essai de l'application à l'origine de la ligne (NULL : import
        # direct du registre réel). Unique : 1 ligne max par essai.
        sa.Column(
            "test_row_id", sa.Integer(),
            sa.ForeignKey("tests.id"), nullable=True, unique=True,
        ),
        sa.Column("source", sa.String(20), nullable=True),  # historique | essai
        sa.Column("source_ref", sa.String(50), nullable=True, unique=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
        # --- Les 14 colonnes réelles du registre client ---
        sa.Column("entry_date", sa.Date(), nullable=True),        # Date
        sa.Column("matricule", sa.String(100), nullable=True),    # Mat
        sa.Column("di_ot", sa.String(100), nullable=True),        # DIT/OT
        sa.Column("service", sa.String(100), nullable=True),      # Service (Sce)
        sa.Column("un_v", sa.Text(), nullable=True),              # Un (brut : « 525V »)
        sa.Column("in_a", sa.Text(), nullable=True),              # In (brut : « 260A »)
        sa.Column("uo_v", sa.Text(), nullable=True),              # U0
        sa.Column("io_a", sa.Text(), nullable=True),              # I0
        sa.Column("isolement", sa.Text(), nullable=True),         # Isolement (brut : « 1,2 GΩ »)
        sa.Column("nature", sa.Text(), nullable=True),            # Nature = désignation
        sa.Column("puissance", sa.Text(), nullable=True),         # Puissance (P)
        sa.Column("societe", sa.String(100), nullable=True),      # Société
        sa.Column("bt_mt", sa.String(20), nullable=True),         # BT/MT (Tension)
        sa.Column("observation", sa.Text(), nullable=True),       # Observation
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_registre_entries_entry_date", "registre_entries", ["entry_date"])


def downgrade() -> None:
    op.drop_index("ix_registre_entries_entry_date", table_name="registre_entries")
    op.drop_table("registre_entries")
