"""Service « acquisition » : pilote d'un test automatique (~60 s).

Rôles (cf. §11 du cahier des charges) :
- associer les mesures MQTT reçues d'un kit au test en cours ;
- stocker chaque échantillon (série temporelle) dans PostgreSQL ;
- transmettre les mesures au frontend (WebSocket) ;
- piloter la machine à états :  IDLE → READY → ACQUIRING → COMPLETED
  (ou ERROR si le kit est perdu) ;
- accepter plusieurs kits à terme (une session = un kit + un test).

Le gestionnaire est appelé :
- par les routes API (démarrage START / arrêt QUIT) — boucle asyncio ;
- par le thread MQTT (chaque télémesure reçue) — d'où le verrou et le
  fait que le SQL soit ouvert/fermé dans chaque méthode.
"""

import asyncio
import logging
import math
import threading
import time

from sqlalchemy import select

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.test import Test
from app.repositories.sql.sample_repository import SampleRepository
from app.repositories.sql.test_repository import TestRepository
from app.services.kits import kit_registry
from app.ws.manager import hub

logger = logging.getLogger("acquisition")


def _vibration_global(vib: dict) -> float | None:
    """Norme des 3 axes de vibration (mm/s) : sqrt(x² + y² + z²)."""
    if not isinstance(vib, dict):
        return None
    try:
        return round(math.sqrt(
            float(vib.get("x_mm_s", 0.0)) ** 2
            + float(vib.get("y_mm_s", 0.0)) ** 2
            + float(vib.get("z_mm_s", 0.0)) ** 2
        ), 4)
    except (TypeError, ValueError):
        return None


class AcquisitionManager:
    """Gère la ou les sessions d'acquisition en cours (mémoire)."""

    def __init__(self) -> None:
        self._sessions: dict[str, dict] = {}   # test_id -> session
        self._lock = threading.Lock()
        self._duration_s = settings.acquisition_duration_s
        self._lost_timeout_s = settings.acquisition_lost_timeout_s

    # ------------------------------------------------------------------
    # État
    # ------------------------------------------------------------------
    def get_session(self, test_id: str) -> dict | None:
        with self._lock:
            session = self._sessions.get(test_id)
            return dict(session) if session else None

    def active_for_kit(self, kit_id: str) -> dict | None:
        """Session en cours pour un kit (le kit peut changer de test)."""
        with self._lock:
            for session in self._sessions.values():
                if session["kit_id"] == kit_id:
                    return dict(session)
        return None

    # ------------------------------------------------------------------
    # Démarrage / arrêt (appelés par les routes, boucle asyncio)
    # ------------------------------------------------------------------
    async def start(self, test_id: str, kit_id: str) -> dict:
        """Démarre l'acquisition pour un test + un kit (START)."""
        with self._lock:
            if self._sessions.get(test_id) is not None:
                raise ValueError(f"Une acquisition est déjà en cours pour le test {test_id}.")
            if any(s["kit_id"] == kit_id for s in self._sessions.values()):
                raise ValueError(f"Le kit {kit_id} est déjà en acquisition sur un autre test.")

            # Enregistre la session (le test passe à « acquiring » ensuite)
            session = {
                "test_id": test_id,
                "kit_id": kit_id,
                "started_at": time.time(),
                "last_sample_at": time.time(),
                "samples_count": 0,
            }
            self._sessions[test_id] = session

        # Test → acquiring (une session SQL dédiée)
        db = SessionLocal()
        try:
            row = db.scalar(select(Test).where(Test.test_id == test_id))
            if row is None:
                with self._lock:
                    self._sessions.pop(test_id, None)
                raise KeyError(f"Test {test_id} inconnu.")
            # É16 : une session terminée ou archivée ne redémarre pas
            if row.status in ("completed", "archived"):
                with self._lock:
                    self._sessions.pop(test_id, None)
                raise ValueError(
                    f"Session {row.test_id} déjà terminée "
                    f"(statut : {row.status}) : démarrage refusé."
                )
            # CAS LIMITE : seul un test AUTOMATIQUE a une acquisition.
            # (l'interface ne le permet pas, mais l'API doit se défendre)
            if row.mode != "auto":
                with self._lock:
                    self._sessions.pop(test_id, None)
                raise ValueError(
                    f"Le test {test_id} est un test manuel : l'acquisition "
                    "automatique ne s'applique qu'aux tests automatiques."
                )
            row.status = "acquiring"
            db.commit()
        finally:
            db.close()

        # Commande MQTT « start » au kit (import différé : évite un cycle
        # mqtt.client → services.acquisition → mqtt.client)
        from app.mqtt.client import mqtt_client

        mqtt_client.publish_start(test_id)

        # Programme la fin automatique après ~60 s
        asyncio.get_running_loop().create_task(self._complete_after_delay(test_id))

        hub.broadcast({
            "type": "acquisition_started",
            "test_id": test_id,
            "kit_id": kit_id,
            "duration_s": self._duration_s,
        })
        logger.info("Acquisition démarrée — test %s, kit %s (%ss)", test_id, kit_id, self._duration_s)
        return {"test_id": test_id, "kit_id": kit_id, "status": "acquiring", "duration_s": self._duration_s}

    async def stop(self, test_id: str, reason: str = "user_quit") -> None:
        """Arrête une acquisition (QUIT). reason : user_quit | error | completed."""
        with self._lock:
            session = self._sessions.pop(test_id, None)
        if session is None:
            return

        # Commande MQTT « stop » au kit (fin de l'émission de mesures)
        from app.mqtt.client import mqtt_client

        mqtt_client.publish_stop()

        db = SessionLocal()
        try:
            row = db.scalar(select(Test).where(Test.test_id == test_id))
            if row is not None:
                # error (kit perdu) ; sinon retour à « hors tension validé » :
                # la validation du test sous tension reste un geste EXPLICITE
                # du technicien (POST /tests/{id}/validate-online, É16).
                row.status = "error" if reason == "error" else "offline_validated"
                db.commit()
        finally:
            db.close()

        event_type = {
            "completed": "acquisition_completed",
            "user_quit": "acquisition_stopped",
            "error": "acquisition_error",
        }.get(reason, "acquisition_stopped")
        hub.broadcast({
            "type": event_type,
            "test_id": test_id,
            "reason": reason,
            "samples_count": session["samples_count"],
        })
        logger.info("Acquisition arrêtée — test %s (%s)", test_id, reason)

    # ------------------------------------------------------------------
    # Fin automatique (~60 s) et surveillance de perte du kit
    # ------------------------------------------------------------------
    async def _complete_after_delay(self, test_id: str) -> None:
        await asyncio.sleep(self._duration_s)
        # Si la session existe toujours (pas d'arrêt manuel entre-temps)
        with self._lock:
            still = test_id in self._sessions
        if still:
            await self.stop(test_id, reason="completed")

    async def watchdog(self) -> None:
        """Tourne en permanence : détecte les kits perdus en plein test.

        Si aucun échantillon n'arrive depuis plus de lost_timeout_s,
        l'acquisition passe en erreur (perte du kit → §8).
        """
        while True:
            await asyncio.sleep(2)
            now = time.time()
            lost = []
            with self._lock:
                for test_id, session in self._sessions.items():
                    if now - session["last_sample_at"] > self._lost_timeout_s:
                        lost.append(test_id)
            for test_id in lost:
                logger.warning("Kit perdu pendant l'acquisition du test %s", test_id)
                await self.stop(test_id, reason="error")

    # ------------------------------------------------------------------
    # Télémesure reçue (appelée par le thread MQTT)
    # ------------------------------------------------------------------
    def record_telemetry(self, kit_id: str, payload: dict) -> None:
        """Enregistre un échantillon si le kit est en acquisition."""
        with self._lock:
            session = next((s for s in self._sessions.values() if s["kit_id"] == kit_id), None)
            if session is None:
                return  # le kit envoie mais aucun test n'est en cours

            test_id = session["test_id"]
            t_s = round(time.time() - session["started_at"], 2)
            session["last_sample_at"] = time.time()
            session["samples_count"] += 1

        # Instant : l'HORLOGE DU KIT fait foi (champ « elapsed_s » du
        # sketch) ; repli sur l'horloge du backend si absent.
        elapsed = payload.get("elapsed_s")
        if isinstance(elapsed, (int, float)) and 0 <= elapsed < 3600:
            t_s = round(float(elapsed), 2)

        temperature = payload.get("temperature_c")
        # Sketch : « current_rms_a » (ancien format « current_a » accepté).
        current = payload.get("current_rms_a", payload.get("current_a"))
        # Vibration — DÉCISION CLIENT 26/09/2026 : le sketch sera
        # modifié pour publier la VITESSE vibratoire en mm/s. Champs
        # attendus : « vibration_rms_mm_s » (global) et
        # « vibration_x/y/z_rms_mm_s ». Les anciens champs en g
        # (« *_rms_g ») ne sont PAS convertis (aucune invention) :
        # ils laissent les colonnes mm/s vides.
        v_global = payload.get("vibration_rms_mm_s")
        v_x = payload.get("vibration_x_rms_mm_s")
        v_y = payload.get("vibration_y_rms_mm_s")
        v_z = payload.get("vibration_z_rms_mm_s")
        if any(isinstance(v, (int, float)) and v >= 0 for v in (v_global, v_x, v_y, v_z)):
            vib = {
                "x_mm_s": v_x if isinstance(v_x, (int, float)) and v_x >= 0 else None,
                "y_mm_s": v_y if isinstance(v_y, (int, float)) and v_y >= 0 else None,
                "z_mm_s": v_z if isinstance(v_z, (int, float)) and v_z >= 0 else None,
            }
            vib_global = (
                v_global
                if isinstance(v_global, (int, float)) and v_global >= 0
                else _vibration_global(vib)
            )
        else:
            vib = None
            vib_global = None

        db = SessionLocal()
        try:
            row = db.scalar(select(Test).where(Test.test_id == test_id))
            if row is None:
                return
            samples = SampleRepository(db)
            samples.add(row.id, t_s, {
                "temperature_c": temperature if isinstance(temperature, (int, float)) else None,
                "current_a": current if isinstance(current, (int, float)) else None,
                "vib_x_mm_s": vib.get("x_mm_s") if isinstance(vib, dict) else None,
                "vib_y_mm_s": vib.get("y_mm_s") if isinstance(vib, dict) else None,
                "vib_z_mm_s": vib.get("z_mm_s") if isinstance(vib, dict) else None,
                "vib_global_mm_s": vib_global,
            })
            samples.commit()
        except Exception as exc:  # ne jamais faire tomber le thread MQTT
            logger.exception("Échantillon non enregistré : %s", exc)
            db.rollback()
        finally:
            db.close()

        # Transmission temps réel au frontend (thread-safe)
        hub.broadcast({
            "type": "sample",
            "test_id": test_id,
            "t_s": t_s,
            "temperature_c": temperature,
            "current_a": current,
            "vibration": vib,
            "vib_global_mm_s": vib_global,
        })


acquisition_manager = AcquisitionManager()
