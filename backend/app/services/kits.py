"""Service « kits » : registre des kits de diagnostic présents sur le broker.

Le registre vit en mémoire : il apprend la présence des kits par leurs
messages MQTT (statut + télémesure) et considère un kit « déconnecté »
si aucun message n'est reçu depuis un certain délai (timeout).
Il est volontairement indépendant de la base de données : la présence
est un état TEMPS RÉEL, pas un enregistrement historique.
"""

import threading
import time
from datetime import datetime, timezone


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class KitRegistry:
    """Mémorise l'état de présence des kits et fournit des listes à l'API."""

    def __init__(self, online_timeout_s: float = 8.0) -> None:
        self._kits: dict[str, dict] = {}
        self._lock = threading.Lock()
        self._timeout = online_timeout_s

    def upsert(self, kit_id: str, *, firmware: str | None, esp32_detected: bool | None) -> None:
        """Met à jour (ou crée) la fiche de présence d'un kit."""
        now = time.time()
        with self._lock:
            kit = self._kits.setdefault(kit_id, {"kit_id": kit_id})
            kit["last_seen"] = now
            if firmware is not None:
                kit["firmware"] = firmware
            if esp32_detected is not None:
                kit["esp32_detected"] = esp32_detected

    def note_telemetry(self, kit_id: str) -> None:
        """Un message de mesure a été reçu : le kit est vivant."""
        with self._lock:
            kit = self._kits.setdefault(kit_id, {"kit_id": kit_id})
            kit["last_seen"] = time.time()
            kit["last_telemetry_at"] = _utc_iso()

    def most_recent(self) -> str | None:
        """Identifiant du kit vu le plus récemment (prototype unique)."""
        with self._lock:
            if not self._kits:
                return None
            return max(self._kits.values(), key=lambda k: k.get("last_seen", 0))["kit_id"]

    def is_online(self, kit_id: str) -> bool:
        with self._lock:
            kit = self._kits.get(kit_id)
            if kit is None:
                return False
            return (time.time() - kit.get("last_seen", 0)) <= self._timeout

    def list(self) -> list[dict]:
        """État actuel de tous les kits connus (prêt pour l'API)."""
        now = time.time()
        with self._lock:
            result = []
            for kit in self._kits.values():
                online = (now - kit.get("last_seen", 0)) <= self._timeout
                last_seen = kit.get("last_seen")
                result.append({
                    "kit_id": kit["kit_id"],
                    "state": "online" if online else "offline",
                    "firmware": kit.get("firmware"),
                    "esp32_detected": kit.get("esp32_detected"),
                    "last_seen": _utc_iso() if last_seen else None,
                    "last_telemetry_at": kit.get("last_telemetry_at"),
                })
            return result


# --- Instance unique partagée par l'API, le client MQTT et le WebSocket ---
from app.core.config import settings  # noqa: E402

kit_registry = KitRegistry(online_timeout_s=settings.kit_online_timeout_s)
