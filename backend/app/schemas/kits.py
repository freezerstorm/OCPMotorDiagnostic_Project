"""Schéma de l'état d'un KIT (présence temps réel, pas une table SQL)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class KitStatus(BaseModel):
    """État de présence d'un kit sur le broker."""

    kit_id: str
    state: Literal["online", "offline"]
    firmware: str | None = None
    esp32_detected: bool | None = None
    last_seen: datetime | None = None
    last_telemetry_at: datetime | None = None
