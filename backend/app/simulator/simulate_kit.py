"""ÉMULATEUR DU PROTOTYPE ESP32 — protocole exact du sketch Arduino.

    cd backend
    python -m app.simulator.simulate_kit --broker 127.0.0.1 --port 1883

Contrat du sketch (SOURCE CLIENT, 26/09/2026) :
  START  : kit/diagnostic/start — payload = ID du test en TEXTE BRUT ;
  STOP   : kit/diagnostic/stop  — payload ignoré par le sketch ;
  STATUS : kit/diagnostic/status — {"test_id": …, "status": ready |
           acquiring | aborted | completed} (retenu/retained) ;
  DATA   : kit/diagnostic/data — {"test_id", "elapsed_s", "temperature_c",
           "current_rms_a", "vibration_rms_mm_s", "vibration_x/y/z_rms_mm_s",
           "status": "acquiring"} ~1×/s pendant 60 s. (DÉCISION CLIENT
           26/09/2026 : la vibration est publiée en mm/s — l'émulateur
           suit déjà le contrat CIBLE du sketch modifié.)

Écarts assumés par cet émulateur (outil de développement) :
- un battement « ready » périodique au repos — le sketch actuel
  n'envoie AUCUN status périodique (question posée au client) ;
- valeurs de mesure SIMULÉES (pas de capteurs réels).
"""

import argparse
import json
import logging
import math
import random
import threading
import time

import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("simulate-kit")

# Valeurs de base des mesures simulées (modifiables pour vos essais)
BASE_TEMP_C = 28.0        # température de départ (°C)
BASE_CURRENT_A = 14.0      # courant RMS « à vide » simulé (A)
VIBRATION_BASE_MM_S = 1.3  # vibration de fond simulée (mm/s — contrat cible)

STATUS_INTERVAL_S = 3.0    # battement « ready » au repos (écart émulateur)
PUBLISH_INTERVAL_S = 1.0   # sketch : PUBLISH_INTERVAL_MS = 1000
TEST_DURATION_S = 60.0     # sketch : TEST_DURATION_MS = 60000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Émulateur du prototype ESP32 (protocole kit/diagnostic/*)")
    parser.add_argument("--kit-id", default="ESP32-01",
                        help="Nom affiché dans les journaux (le backend "
                             "identifie le prototype via son réglage propre)")
    parser.add_argument("--broker", default="localhost", help="Adresse du broker MQTT")
    parser.add_argument("--port", type=int, default=1883, help="Port du broker MQTT")
    return parser.parse_args()


class SimulatedKit:
    """Émule le sketch : mêmes sujets, mêmes payloads, mêmes états."""

    def __init__(self, name: str, broker: str, port: int) -> None:
        self.name = name            # journal uniquement (pas dans les messages)
        self._broker = broker
        self._port = port
        self._client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2, client_id=f"sim-ESP32-{name}")
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

        # Sujets EXACTS du sketch
        self.TOPIC_START = "kit/diagnostic/start"
        self.TOPIC_STOP = "kit/diagnostic/stop"
        self.TOPIC_STATUS = "kit/diagnostic/status"
        self.TOPIC_DATA = "kit/diagnostic/data"

        self.test_id = ""           # reçu sur START (texte brut)
        self._running = False
        self._seq = 0
        self._test_start = 0.0
        self._last_publish = 0.0
        self._stop_event = threading.Event()

    # --- cycle de vie ---
    def start(self) -> None:
        self._client.connect_async(self._broker, self._port, keepalive=15)
        self._client.loop_start()
        threading.Thread(target=self._publisher_loop, daemon=True).start()
        logger.info(
            "Émulateur « %s » prêt — status=kit/diagnostic/status, "
            "START=%s, STOP=%s (protocole du sketch).",
            self.name, self.TOPIC_START, self.TOPIC_STOP,
        )

    def _on_connect(self, client, userdata, flags, reason_code, properties=None) -> None:
        client.subscribe([(self.TOPIC_START, 1), (self.TOPIC_STOP, 1)])
        # Comme connectMQTT() du sketch : publishStatus("ready"), retenu.
        self._publish_status("ready")
        logger.info("Connecté au broker — abonné à %s et %s",
                    self.TOPIC_START, self.TOPIC_STOP)

    # --- commandes (mqttCallback du sketch) ---
    def _on_message(self, client, userdata, message) -> None:
        text = message.payload.decode("utf-8", "ignore").strip()
        if message.topic == self.TOPIC_START:
            if self._running:
                # startDiagnostic : « A diagnostic is already running »
                logger.info("START ignoré : un test est déjà en cours (sketch).")
                return
            self.test_id = text or "test_without_id"
            self._running = True
            self._seq = 0
            self._test_start = time.time()
            self._last_publish = 0.0
            self._publish_status("acquiring")
            logger.info("► START reçu — test_id=« %s » — émission des mesures.", self.test_id)
        elif message.topic == self.TOPIC_STOP:
            if not self._running:
                return
            self._running = False
            self._publish_status("aborted")
            logger.info("■ STOP reçu — status « aborted ».")

    # --- statuts (publishStatus du sketch, retained) ---
    def _publish_status(self, state: str) -> None:
        self._client.publish(self.TOPIC_STATUS, json.dumps({
            "test_id": self.test_id,
            "status": state,
        }), qos=1, retain=True)

    # --- mesures (publishMeasurements du sketch) ---
    def _sketch_data(self) -> dict:
        temp = BASE_TEMP_C + 3 * math.sin(self._seq / 40) + random.uniform(-0.4, 0.4)
        current = max(0.0, BASE_CURRENT_A + 2 * math.sin(self._seq / 25) + random.uniform(-0.5, 0.5))
        vx = round(max(0.0, VIBRATION_BASE_MM_S + 0.35 * math.sin(self._seq / 8) + random.uniform(-0.12, 0.12)), 3)
        vy = round(max(0.0, VIBRATION_BASE_MM_S + 0.25 * math.cos(self._seq / 10) + random.uniform(-0.12, 0.12)), 3)
        vz = round(max(0.0, VIBRATION_BASE_MM_S + random.uniform(-0.12, 0.12)), 3)
        vglobal = round(math.sqrt(vx * vx + vy * vy + vz * vz), 4)
        return {
            "test_id": self.test_id,
            "elapsed_s": round(time.time() - self._test_start, 1),
            "temperature_c": round(max(0.0, temp), 2),
            "current_rms_a": round(current, 3),
            "vibration_rms_mm_s": vglobal,
            "vibration_x_rms_mm_s": vx,
            "vibration_y_rms_mm_s": vy,
            "vibration_z_rms_mm_s": vz,
            "status": "acquiring",
        }

    # --- boucle principale (loop du sketch) ---
    def _publisher_loop(self) -> None:
        last_status = 0.0
        while not self._stop_event.is_set():
            now = time.time()
            if self._running:
                if now - self._last_publish >= PUBLISH_INTERVAL_S:
                    self._client.publish(self.TOPIC_DATA, json.dumps(self._sketch_data()), qos=0)
                    self._seq += 1
                    self._last_publish = now
                if now - self._test_start >= TEST_DURATION_S:
                    self._running = False
                    self._publish_status("completed")
                    logger.info("Durée du test atteinte (%.0f s) — status « completed ».", TEST_DURATION_S)
            elif now - last_status >= STATUS_INTERVAL_S:
                # ÉCART émulateur : battement « ready » (le sketch actuel
                # n'envoie rien au repos — question posée au client).
                self._publish_status("ready")
                last_status = now
            time.sleep(0.1)

    def stop(self) -> None:
        self._stop_event.set()
        time.sleep(0.2)
        self._client.loop_stop()
        self._client.disconnect()
        logger.info("Émulateur arrêté.")


def main() -> None:
    args = parse_args()
    kit = SimulatedKit(args.kit_id, args.broker, args.port)
    kit.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        kit.stop()


if __name__ == "__main__":
    main()
