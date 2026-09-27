"""Client MQTT du backend (paho-mqtt).

Rôles (§5 du cahier des charges) :
- s'abonner aux messages des kits (présence + mesures) ;
- vérifier leur validité (JSON bien formé) ;
- tenir le registre des kits et prévenir les navigateurs (hub WebSocket).

Architecture du PROTOTYPE MATÉRIEL (client, 26/09/2026) — sujets
PLATS, sans identifiant de kit dans le sujet (un seul prototype) :
    kit/diagnostic/status  ← l'ESP32 annonce sa présence (+ son id)
    kit/diagnostic/data    ← mesures (mêmes JSON que le simulateur)
    kit/diagnostic/error   ← erreurs du kit
    kit/diagnostic/start   → démarrage d'un test
    kit/diagnostic/stop    → arrêt/abandon

Le sketch Arduino n'envoie PAS de kit_id : l'application affiche
l'identifiant fixe mqtt_prototype_kit_id (« ESP32-01 ») ; un champ
« kit_id » présent dans un status reste accepté (évolution future).
Les mesures « data » sont rattachées au kit vu le plus récemment
(prototype unique). Commandes : START = id du test en TEXTE BRUT
(publish_start), STOP = payload vide ignoré par le sketch.
"""

import json
import logging

import paho.mqtt.client as mqtt

from app.core.config import settings
from app.services.acquisition import acquisition_manager
from app.services.kits import kit_registry
from app.ws.manager import hub

logger = logging.getLogger("mqtt.client")

# --- Sujets du prototype (architecture client, 26/09/2026) -----------------
TOPIC_STATUS = "kit/diagnostic/status"
TOPIC_DATA = "kit/diagnostic/data"
TOPIC_ERROR = "kit/diagnostic/error"
TOPIC_START = "kit/diagnostic/start"
TOPIC_STOP = "kit/diagnostic/stop"


# --- Traitement des messages reçus -----------------------------------------
def _handle_status(kit_id: str, payload: dict) -> None:
    """Un kit annonce sa présence (état, firmware, ESP32 détecté)."""
    firmware = payload.get("firmware") if isinstance(payload.get("firmware"), str) else None
    esp32 = payload.get("esp32_detected")
    esp32 = esp32 if isinstance(esp32, bool) else None

    kit_registry.upsert(kit_id, firmware=firmware, esp32_detected=esp32)
    logger.info("Kit %s → présent (firmware %s)", kit_id, firmware or "?")
    hub.broadcast({
        "type": "kit_status",
        "kit": {"kit_id": kit_id, "state": "online", "firmware": firmware, "esp32_detected": esp32},
    })


def _handle_error(kit_id: str | None, payload: dict) -> None:
    """Le kit signale une erreur : journalisée et poussée aux navigateurs.

    La session d'acquisition en cours bascule en erreur par le chien de
    garde (perte des mesures) ; ici on transmet l'information telle quelle.
    """
    # Sketch : la clé est « error » (« publishError ») ; « message » accepté.
    raw = payload.get("error") or payload.get("message")
    message = raw if isinstance(raw, str) else json.dumps(payload, ensure_ascii=False)
    logger.warning("Kit %s : ERREUR signalée (%s)", kit_id or "?", message)
    hub.broadcast({
        "type": "kit_error",
        "kit_id": kit_id,
        "message": message,
    })


def _handle_telemetry(kit_id: str, payload: dict) -> None:
    """Le kit envoie des mesures : validées puis liées à l'acquisition."""
    # Validation minimale : un horodatage ou un numéro de séquence est attendu
    has_data = any(
        k in payload for k in (
            "ts", "seq", "elapsed_s",
            "temperature_c", "current_a", "current_rms_a",
            "vibration", "vibration_rms_g", "vibration_rms_mm_s",
        )
    )
    if not has_data:
        logger.warning("Kit %s : télémesure invalide ignorée (%s)", kit_id, payload)
        return
    kit_registry.note_telemetry(kit_id)
    # Si une acquisition est en cours pour ce kit, l'échantillon est
    # stocké et transmis au frontend (WebSocket) par le gestionnaire.
    acquisition_manager.record_telemetry(kit_id, payload)


# --- Client paho -------------------------------------------------------------
class MqttClient:
    """Enveloppe paho-mqtt : connexion auto, abonnement, dispatch."""

    def __init__(self) -> None:
        self._client: mqtt.Client | None = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    # --- cycle de vie ---
    def start(self) -> None:
        """Démarre le client et la boucle réseau (thread paho)."""
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="ocp-backend")
        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.on_message = self._on_message
        client.reconnect_delay_set(min_delay=1, max_delay=10)

        try:
            client.connect_async(settings.mqtt_broker_host, settings.mqtt_broker_port, keepalive=15)
            client.loop_start()
        except Exception as exc:  # broker injoignable → on réessaiera tout seul
            logger.warning("Connexion MQTT impossible (%s) — nouvel essai automatique.", exc)
        self._client = client

    def stop(self) -> None:
        if self._client is not None:
            self._client.loop_stop()
            try:
                self._client.disconnect()
            except Exception:
                pass
            self._client = None
            self._connected = False

    def publish_start(self, test_id: str) -> None:
        """START sur kit/diagnostic/start — CONTRAT DU SKETCH : l'ID du
        test en TEXTE BRUT (mqttCallback le lit comme testId)."""
        if self._client is not None and self._connected:
            self._client.publish(TOPIC_START, test_id, qos=1)

    def publish_stop(self) -> None:
        """STOP sur kit/diagnostic/stop — le sketch ignore le payload."""
        if self._client is not None and self._connected:
            self._client.publish(TOPIC_STOP, "", qos=1)

    # --- callbacks paho ---
    def _on_connect(self, client, userdata, flags, reason_code, properties=None) -> None:
        if reason_code == 0 or getattr(reason_code, "is_failure", False) is False:
            self._connected = True
            client.subscribe([
                (TOPIC_STATUS, 1),
                (TOPIC_DATA, 0),
                (TOPIC_ERROR, 0),
            ])
            logger.info("Connecté au broker MQTT %s:%s — abonné aux sujets du prototype (kit/diagnostic/*).", settings.mqtt_broker_host, settings.mqtt_broker_port)
        else:
            logger.warning("Échec de connexion MQTT (code %s)", reason_code)

    def _on_disconnect(self, client, userdata, flags, reason_code, properties=None) -> None:
        self._connected = False
        logger.warning("Déconnexion du broker MQTT — reconnexion automatique.")

    def _on_message(self, client, userdata, message) -> None:
        suffix = message.topic.rsplit("/", 1)[-1]

        try:
            payload = json.loads(message.payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            logger.warning("Sujet %s : message non-JSON ignoré.", message.topic)
            return
        if not isinstance(payload, dict):
            logger.warning("Sujet %s : message JSON non-objet ignoré.", message.topic)
            return

        if suffix == "status":
            # Sketch : {"test_id": …, "status": …} — SANS kit_id →
            # identifiant fixe du prototype (config). Un « kit_id »
            # présent reste accepté (évolution future du sketch).
            kit_id = payload.get("kit_id")
            if not isinstance(kit_id, str) or not kit_id.strip():
                kit_id = settings.mqtt_prototype_kit_id
            _handle_status(kit_id.strip(), payload)
        elif suffix == "data":
            # Prototype unique : les mesures vont au kit vu le plus récemment.
            kit_id = kit_registry.most_recent()
            if kit_id is None:
                logger.warning("data reçue avant tout status — ignorée.")
                return
            _handle_telemetry(kit_id, payload)
        elif suffix == "error":
            _handle_error(kit_registry.most_recent(), payload)


# Instance unique utilisée par toute l'application
mqtt_client = MqttClient()
