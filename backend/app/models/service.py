"""Table « services » : catalogue des désignations de services OCP.

Décision client (28/09/2026) : le champ « Service » du formulaire
d'identification est une liste déroulante alimentée par CE catalogue
(22 désignations officielles, seedées par la migration 0011). Le
technicien peut ajouter une nouvelle désignation depuis le formulaire :
elle est persistée ici et proposée dans les futures listes déroulantes.

Le champ « motors.service » reste un TEXTE LIBRE sans clé étrangère :
les anciennes désignations déjà enregistrées ne sont jamais retouchées
(données historiques préservées).
"""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
