"""Initial schema — tables Moteurs, Diagnostics, Mesures manuelles, Séries temporelles.

Revision ID: 0001
Revises:
Create Date: 2026-09-09
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Moteurs ---
    op.create_table(
        "motors",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("motor_id", sa.String(length=100), nullable=True),
        sa.Column("serial_number", sa.String(length=100), nullable=True),
        sa.Column("designation", sa.String(length=255), nullable=True),
        sa.Column("brand", sa.String(length=100), nullable=True),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("manufacturer_number", sa.String(length=100), nullable=True),
        sa.Column("rated_power_kw", sa.Float(), nullable=True),
        sa.Column("rated_voltage_v", sa.Float(), nullable=True),
        sa.Column("rated_current_a", sa.Float(), nullable=True),
        sa.Column("rated_speed_rpm", sa.Integer(), nullable=True),
        sa.Column("cos_phi", sa.Float(), nullable=True),
        sa.Column("coupling", sa.String(length=20), nullable=True),
        sa.Column("service", sa.String(length=100), nullable=True),
        sa.Column("di_ot", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_motors_motor_id", "motors", ["motor_id"], unique=True)
    op.create_index("ix_motors_serial_number", "motors", ["serial_number"], unique=True)
    op.create_index("ix_motors_service", "motors", ["service"])
    op.create_index("ix_motors_di_ot", "motors", ["di_ot"])

    # --- Diagnostics ---
    op.create_table(
        "diagnostic_tests",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("mode", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("kit_id", sa.String(length=80), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("technician_decision", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("technician_observation", sa.Text(), nullable=True),
        sa.Column("auto_conclusion", sa.Text(), nullable=True),
        sa.Column("motor_id", sa.Integer(), sa.ForeignKey("motors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_diagnostic_tests_mode", "diagnostic_tests", ["mode"])
    op.create_index("ix_diagnostic_tests_status", "diagnostic_tests", ["status"])
    op.create_index("ix_diagnostic_tests_kit_id", "diagnostic_tests", ["kit_id"])
    op.create_index("ix_diagnostic_tests_motor_id", "diagnostic_tests", ["motor_id"])

    # --- Mesures manuelles ---
    op.create_table(
        "manual_measurements",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("test_id", sa.Integer(), sa.ForeignKey("diagnostic_tests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("iso_ph1_ph2_mohm", sa.Float(), nullable=True),
        sa.Column("iso_ph2_ph3_mohm", sa.Float(), nullable=True),
        sa.Column("iso_ph3_ph1_mohm", sa.Float(), nullable=True),
        sa.Column("iso_ph1_ground_mohm", sa.Float(), nullable=True),
        sa.Column("iso_ph2_ground_mohm", sa.Float(), nullable=True),
        sa.Column("iso_ph3_ground_mohm", sa.Float(), nullable=True),
        sa.Column("r12_ohm", sa.Float(), nullable=True),
        sa.Column("r23_ohm", sa.Float(), nullable=True),
        sa.Column("r31_ohm", sa.Float(), nullable=True),
    )
    op.create_index("ix_manual_measurements_test_id", "manual_measurements", ["test_id"], unique=True)

    # --- Séries temporelles ---
    op.create_table(
        "time_series",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("test_id", sa.Integer(), sa.ForeignKey("diagnostic_tests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("temperature_c", sa.Float(), nullable=True),
        sa.Column("current_a", sa.Float(), nullable=True),
        sa.Column("vibration_x_g", sa.Float(), nullable=True),
        sa.Column("vibration_y_g", sa.Float(), nullable=True),
        sa.Column("vibration_z_g", sa.Float(), nullable=True),
        sa.Column("vibration_magnitude_g", sa.Float(), nullable=True),
    )
    op.create_index("ix_time_series_test_id", "time_series", ["test_id"])
    op.create_index("ix_time_series_ts", "time_series", ["ts"])


def downgrade() -> None:
    op.drop_index("ix_time_series_ts", table_name="time_series")
    op.drop_index("ix_time_series_test_id", table_name="time_series")
    op.drop_table("time_series")

    op.drop_index("ix_manual_measurements_test_id", table_name="manual_measurements")
    op.drop_table("manual_measurements")

    op.drop_index("ix_diagnostic_tests_motor_id", table_name="diagnostic_tests")
    op.drop_index("ix_diagnostic_tests_kit_id", table_name="diagnostic_tests")
    op.drop_index("ix_diagnostic_tests_status", table_name="diagnostic_tests")
    op.drop_index("ix_diagnostic_tests_mode", table_name="diagnostic_tests")
    op.drop_table("diagnostic_tests")

    op.drop_index("ix_motors_di_ot", table_name="motors")
    op.drop_index("ix_motors_service", table_name="motors")
    op.drop_index("ix_motors_serial_number", table_name="motors")
    op.drop_index("ix_motors_motor_id", table_name="motors")
    op.drop_table("motors")
