"""Migration 0007 : REGISTRE NUMÉRIQUE des moteurs (demande client).

Table « registre_entries » : reprend les 20 colonnes du fichier Excel
« registre_moteurs_1.xlsx », dans le même ordre (les intitulés et
l'ordre sont imposés par le client).

  - 1 LIGNE PAR ESSAI : chaque essai est une entrée indépendante,
    même si le même moteur a déjà été testé — une ligne n'est jamais
    remplacée ni supprimée ;
  - les données historiques importées (tests.source_ref) et les essais
    de l'application y figurent ensemble ;
  - les champs absents restent VIDES (NULL) : rien n'est inventé.

Provenance (« source ») : « historique » = importé, « essai » = créé
par l'application après la décision du technicien.
"""

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None

# Les 20 colonnes du registre, dans l'ordre du fichier Excel.
# (la colonne « test_row_id » / « source » sont internes à l'application)
_REGISTRE_COLUMNS = [
    sa.Column("entry_date", sa.Date(), nullable=True),            # 1. Date
    sa.Column("matricule", sa.String(100), nullable=True),        # 2. Matricule
    sa.Column("di_ot", sa.String(100), nullable=True),            # 3. DI/OT
    sa.Column("couplage", sa.String(50), nullable=True),          # 4. Couplage
    sa.Column("service", sa.String(100), nullable=True),          # 5. Service
    sa.Column("un_v", sa.Float(), nullable=True),                 # 6. Un
    sa.Column("in_a", sa.Float(), nullable=True),                 # 7. In
    sa.Column("uo_v", sa.Float(), nullable=True),                 # 8. Uo
    sa.Column("io_a", sa.Float(), nullable=True),                 # 9. Io
    sa.Column("nature", sa.String(200), nullable=True),           # 10. Nature
    # 11–12. Isolement Ph/N (+ unité) — texte : les 3 mesures jointes
    sa.Column("insulation_ph_n", sa.Text(), nullable=True),
    sa.Column("insulation_ph_n_unit", sa.String(20), nullable=True),
    # 13–14. Isolement Ph/Ph (+ unité)
    sa.Column("insulation_ph_ph", sa.Text(), nullable=True),
    sa.Column("insulation_ph_ph_unit", sa.String(20), nullable=True),
    # 15. Résistance (Ω) — R12/R23/R31 jointes
    sa.Column("resistance_ohm", sa.Text(), nullable=True),
    # 16–17. Puissance (+ unité)
    sa.Column("power_value", sa.Float(), nullable=True),
    sa.Column("power_unit", sa.String(20), nullable=True),
    sa.Column("tension_v", sa.Float(), nullable=True),            # 18. Tension
    sa.Column("societe", sa.String(100), nullable=True),          # 19. Société
    sa.Column("dossier", sa.String(50), nullable=True),           # 20. Dossier
]


def upgrade() -> None:
    op.create_table(
        "registre_entries",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        # Essai à l'origine de la ligne (NULL : future import direct du
        # registre Excel). Index UNIQUE → jamais 2 lignes pour un essai,
        # et une ligne n'est jamais écrasée.
        sa.Column(
            "test_row_id", sa.Integer(),
            sa.ForeignKey("tests.id"), nullable=True, unique=True,
        ),
        sa.Column("source", sa.String(20), nullable=True),  # historique | essai
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
        *_REGISTRE_COLUMNS,
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_registre_entries_entry_date", "registre_entries", ["entry_date"]
    )


def downgrade() -> None:
    op.drop_index("ix_registre_entries_entry_date", table_name="registre_entries")
    op.drop_table("registre_entries")
