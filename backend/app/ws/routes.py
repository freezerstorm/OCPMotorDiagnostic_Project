"""Routes WebSocket.

- /ws/kits : la page « Connexion au kit » reçoit un premier aperçu
  (snapshot) des kits, puis les changements en direct (kit_status).
"""

import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from app.services.kits import kit_registry
from app.ws.manager import hub


def attach_websocket_routes(app: FastAPI) -> None:
    """Enregistre les routes WebSocket sur l'application FastAPI."""

    @app.websocket("/ws/kits")
    async def websocket_kits(websocket: WebSocket) -> None:
        await hub.connect(websocket)
        try:
            # Aperçu immédiat de l'état actuel des kits
            await websocket.send_text(json.dumps(
                {"type": "kits_snapshot", "kits": kit_registry.list()},
                ensure_ascii=False,
            ))
            # On garde la connexion ouverte ; les messages du client ne
            # sont pas utilisés à ce stade (le hub pousse tout seul).
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            hub.disconnect(websocket)
