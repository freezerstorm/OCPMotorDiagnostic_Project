"""Importe tous les modèles pour qu'Alembic les découvre.

Il faut importer explicitement chaque modèle pour que Base.metadata
les voie et qu'Alembic puisse générer les migrations automatiquement.
"""

from app.models.base import IntPkMixin, TimestampMixin  # noqa: F401
from app.models.motor import Motor                      # noqa: F401
from app.models.test import DiagnosticTest              # noqa: F401
from app.models.measurements import ManualMeasurements, TimeSeriesPoint  # noqa: F401
from app.db.session import Base                         # noqa: F401
