"""Création du schéma initial : tables motors, tests, measurements.

Révision : 0001 — schéma de l'Étape 4.

Tables créées :
- motors       : fiche d'identification des moteurs (PK : motor_id)
- tests        : une fiche de diagnostic par ligne (PK interne auto,
                 test_id lisible « T-0001 » unique)
- measurements : mesures de la fiche (1 ligne pour 1 test)

Séquence créée :
- test_id_seq  : fournit les numéros des identifiants lisibles T-0001…
"""

from alembic import op
import sqlalchemy as sa

# Identifiants de révision
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Séquence des identifiants lisibles de tests (ex. T-0001)
    op.execute("CREATE SEQUENCE test_id_seq")

    # ---------- Table motors ----------
    op.create_table(
        "motors",
        sa.Column("motor_id", sa.String(length=50), nullable=False),
        sa.Column("matricule", sa.String(length=100), nullable=True),
        sa.Column("designation", sa.String(length=200), nullable=True),
        sa.Column("brand", sa.String(length=100), nullable=True),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("serial_number", sa.String(length=100), nullable=True),
        sa.Column("rated_power_kw", sa.Float(), nullable=True),
        sa.Column("rated_voltage_v", sa.Float(), nullable=True),
        sa.Column("rated_current_a", sa.Float(), nullable=True),
        sa.Column("rated_speed_rpm", sa.Float(), nullable=True),
        sa.Column("cos_phi", sa.Float(), nullable=True),
        sa.Column("coupling", sa.String(length=20), nullable=True),
        sa.Column("service", sa.String(length=100), nullable=True),
        sa.Column("di_ot", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("motor_id"),
    )

    # ---------- Table tests ----------
    op.create_table(
        "tests",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("test_id", sa.String(length=20), nullable=False),
        sa.Column("mode", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="draft", nullable=False),
        sa.Column("decision", sa.String(length=50), nullable=True),
        sa.Column("observation", sa.Text(), nullable=True),
        sa.Column("motor_id", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["motor_id"], ["motors.motor_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("test_id"),
    )
    op.create_index("ix_tests_motor_id", "tests", ["motor_id"])

    # ---------- Table measurements (1 ligne pour 1 test) ----------
    op.create_table(
        "measurements",
        sa.Column("test_id", sa.Integer(), nullable=False),
        # Isolement (MΩ)
        sa.Column("ph1_ph2_mohm", sa.Float(), nullable=True),
        sa.Column("ph2_ph3_mohm", sa.Float(), nullable=True),
        sa.Column("ph3_ph1_mohm", sa.Float(), nullable=True),
        sa.Column("ph1_ground_mohm", sa.Float(), nullable=True),
        sa.Column("ph2_ground_mohm", sa.Float(), nullable=True),
        sa.Column("ph3_ground_mohm", sa.Float(), nullable=True),
        # Résistance des enroulements (Ω)
        sa.Column("r12_ohm", sa.Float(), nullable=True),
        sa.Column("r23_ohm", sa.Float(), nullable=True),
        sa.Column("r31_ohm", sa.Float(), nullable=True),
        # Valeurs « instantanées »
        sa.Column("temperature_c", sa.Float(), nullable=True),
        sa.Column("current_a", sa.Float(), nullable=True),
        sa.Column("vibration_mm_s", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["test_id"], ["tests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("test_id"),
    )


def downgrade() -> None:
    """Annule la migration (ordre inverse des créations)."""
    op.drop_table("measurements")
    op.drop_index("ix_tests_motor_id", table_name="tests")
    op.drop_table("tests")
    op.drop_table("motors")
    op.execute("DROP SEQUENCE test_id_seq")
