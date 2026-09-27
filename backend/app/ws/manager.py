"""Hub WebSocket : pousse les événements temps réel vers les navigateurs.

- Le backend reçoit les messages MQTT des kits (dans un thread paho).
- Le hub les retransmet à TOUTES les pages connectées en WebSocket
  (page « Connexion au kit », puis « Acquisition » à l'Étape 8).

Point technique : paho appelle ses callbacks depuis un thread non-async ;
hub.broadcast() est donc « thread-safe » (elle replie le travail vers la
boucle asyncio principale de FastAPI).
"""

import asyncio
import json
import logging

from fastapi import WebSocket

logger = logging.getLogger("ws.hub")


class Hub:
    """Diffuse des messages JSON à tous les clients WebSocket connectés."""

    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()
        self._loop: asyncio.AbstractEventLoop | None = None

    def attach_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """À appeler au démarrage de FastAPI (lifespan)."""
        self._loop = loop

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._clients.add(websocket)
        logger.info("Client WebSocket connecté (%d en ligne)", len(self._clients))

    def disconnect(self, websocket: WebSocket) -> None:
        self._clients.discard(websocket)

    async def _send(self, websocket: WebSocket, payload: dict) -> None:
        try:
            await websocket.send_text(json.dumps(payload, ensure_ascii=False))
        except Exception:
            self.disconnect(websocket)  # client parti : on l'oublie

    async def _broadcast_async(self, payload: dict) -> None:
        for client in list(self._clients):
            await self._send(client, payload)

    def broadcast(self, payload: dict) -> None:
        """Diffuse un message — appelable depuis n'importe quel thread."""
        if self._loop is None or not self._clients:
            return
        asyncio.run_coroutine_threadsafe(self._broadcast_async(payload), self._loop)


hub = Hub()
