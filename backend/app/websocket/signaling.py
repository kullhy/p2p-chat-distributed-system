import json
from fastapi import WebSocket, WebSocketDisconnect
from ..services.connection_manager import signaling_manager
from ..protocols import MessageTypes


async def signaling_handler(websocket: WebSocket, peer_id: str):
    await signaling_manager.connect(peer_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Extract target
            target_id = message.get("to")
            if target_id and message.get("type") == MessageTypes.SIGNAL:
                # Routing signaling message specifically to the 'to' peer
                await signaling_manager.send_personal_message(message, target_id)

    except WebSocketDisconnect:
        signaling_manager.disconnect(peer_id)