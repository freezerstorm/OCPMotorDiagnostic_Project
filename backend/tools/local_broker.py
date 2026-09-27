"""Broker MQTT de DÉVELOPPEMENT — à utiliser SANS Docker.

Sur votre poste de travail, utilisez Mosquitto via Docker Compose
(à la racine du projet : `docker compose up -d`) : c'est la
configuration de référence du cahier des charges.

Dans les environnements où Docker n'est pas disponible, ce petit
broker Python (amqtt) joue le même rôle sur le port 1883 :

    cd backend
    python tools/local_broker.py

Il écoute sur 0.0.0.0:1883, sans mot de passe (DEV uniquement).
"""

import asyncio
import logging

from amqtt.broker import Broker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("local-broker")


async def main() -> None:
    config = {
        "listeners": {
            "default": {
                "type": "tcp",
                "bind": "0.0.0.0:1883",
            }
        },
        "sys_interval": 0,           # pas de métriques système (dev)
        "auth": {"allow-anonymous": True},  # DEV uniquement
    }
    broker = Broker(config)
    await broker.start()
    logger.info("Broker MQTT de développement prêt sur le port 1883 (Ctrl+C pour arrêter).")
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        await broker.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
