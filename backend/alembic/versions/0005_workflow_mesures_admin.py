"""Migration 0005 : workflow en étapes, continuité, paliers, appareils, admin (É16).

NOUVEAUTÉS (décisions client du 15/09/2026) :
  - table « tests » (la SESSION de diagnostic) — zone administrative
    de la fiche papier (Sce demandeur, AVIS, ORDRE, date de réception,
    réparation interne / externe) ;
  - table « measurements » :
      * continuité des enroulements (appréciation globale Oui/Non) ;
      * températures PALIERS (côté accouplement / C.O.A) — la règle
        fournie devient « critique si ≥ 70 °C » par palier ;
      * références des APPAREILS de mesure (facultatives).
  - « temperature_c » est CONSERVÉ : colonne historique pour les
    anciennes fiches (démo, imports) — évaluée avec l'ancien seuil
    85 °C et étiquetée « valeur unique (ancien format) ».

La vitesse n'est PAS ajoutée aux mesures (décision client : retirée
des mesures ; elle reste sur la plaque signalétique du moteur).
"""

from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Zone administrative (table tests) ---
    op.add_column("tests", sa.Column("requested_by_service", sa.String(100), nullable=True))
    op.add_column("tests", sa.Column("notice", sa.String(200), nullable=True))
    op.add_column("tests", sa.Column("work_order", sa.String(100), nullable=True))
    op.add_column("tests", sa.Column("received_at", sa.Date(), nullable=True))
    op.add_column("tests", sa.Column("repair_internal", sa.Boolean(), nullable=True))
    op.add_column("tests", sa.Column("repair_external", sa.Boolean(), nullable=True))

    # --- Continuité + paliers + appareils (table measurements) ---
    op.add_column("measurements", sa.Column("continuity_ok", sa.Boolean(), nullable=True))
    op.add_column("measurements", sa.Column("temp_bearing_de_c", sa.Float(), nullable=True))
    op.add_column("measurements", sa.Column("temp_bearing_nde_c", sa.Float(), nullable=True))
    op.add_column("measurements", sa.Column("ref_meter_insulation", sa.String(100), nullable=True))
    op.add_column("measurements", sa.Column("ref_meter_resistance", sa.String(100), nullable=True))
    op.add_column("measurements", sa.Column("ref_meter_cl", sa.String(100), nullable=True))
    op.add_column("measurements", sa.Column("ref_meter_temperature", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column("measurements", "ref_meter_temperature")
    op.drop_column("measurements", "ref_meter_cl")
    op.drop_column("measurements", "ref_meter_resistance")
    op.drop_column("measurements", "ref_meter_insulation")
    op.drop_column("measurements", "temp_bearing_nde_c")
    op.drop_column("measurements", "temp_bearing_de_c")
    op.drop_column("measurements", "continuity_ok")
    op.drop_column("tests", "repair_external")
    op.drop_column("tests", "repair_internal")
    op.drop_column("tests", "received_at")
    op.drop_column("tests", "work_order")
    op.drop_column("tests", "notice")
    op.drop_column("tests", "requested_by_service")
