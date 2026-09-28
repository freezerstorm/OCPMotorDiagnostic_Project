"""Migration 0011 : catalogue des services OCP (champ « Service »).

Décision client (28/09/2026) : le champ « Service » du formulaire
d'identification devient une liste déroulante alimentée par UNE table
« services » (désignations uniques). Cette migration :
  1. crée la table (id, name unique, created_at) ;
  2. la seede avec les 22 désignations officielles fournies par le
     client (l'ordre d'insertion = ordre d'affichage de la liste).

Le champ « motors.service » reste un TEXTE LIBRE : les anciennes
données historiques ne sont JAMAIS retouchées. Une désignation ajoutée
plus tard par un technicien (POST /api/v1/services) est simplement
ajoutée à cette table.
"""

import sqlalchemy as sa
from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None

# Désignations officielles fournies par le client (ordre d'affichage).
SERVICES_OFFICIELS = [
    "KMB / KMB2",
    "KM03",
    "PE/RE",
    "PE/SI",
    "PE/EI",
    "KTD / ZKTD",
    "KTB",
    "KTR",
    "DS",
    "KLB",
    "KLR",
    "KL01 / KL02 / KL03",
    "LM/X / LMX / L-EXT",
    "LM/E / LME",
    "PIPE",
    "PP.ST",
    "KPPA",
    "PC/SI",
    "PC ASA",
    "PC/IE",
    "PC/ZB",
    "C M/K",
]


def upgrade() -> None:
    services = op.create_table(
        "services",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.bulk_insert(services, [{"name": name} for name in SERVICES_OFFICIELS])


def downgrade() -> None:
    op.drop_table("services")
