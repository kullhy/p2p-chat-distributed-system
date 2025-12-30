import json
from fastapi import WebSocket, WebSocketDisconnect
from ..services.connection_manager import global_manager
from ..services.presence_service import presence_service
from ..protocols import MessageTypes
from ..models import Peer


async def global_chat_handler(websocket: WebSocket, peer_id: str):
    await global_manager.connect(peer_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            msg_type = message.get("type")

            if msg_type == MessageTypes.REGISTER:
                username = message.get("payload", {}).get("username", "Anonymous")
                new_peer = Peer(peerId=peer_id, username=username)
                presence_service.add_peer(new_peer)

                # Broadcast updated list to everyone
                await global_manager.broadcast({
                    "type": MessageTypes.PEER_LIST,
                    "from": "system",
                    "to": None,
                    "payload": {"peers": presence_service.get_all_peers()}
                })

            elif msg_type == MessageTypes.GLOBAL_MSG:
                # Relay to all connected clients
                await global_manager.broadcast(message)

    except WebSocketDisconnect:
        global_manager.disconnect(peer_id)
        presence_service.remove_peer(peer_id)
        await global_manager.broadcast({
            "type": MessageTypes.PEER_LIST,
            "from": "system",
            "to": None,
            "payload": {"peers": presence_service.get_all_peers()}
        })
