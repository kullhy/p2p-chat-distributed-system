from fastapi import WebSocket
from typing import Dict, List
import json

class ConnectionManager:
    def __init__(self):
        # Maps peerId -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, peer_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[peer_id] = websocket

    def disconnect(self, peer_id: str):
        if peer_id in self.active_connections:
            del self.active_connections[peer_id]

    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_text(json.dumps(message))

    async def send_personal_message(self, message: dict, peer_id: str):
        if peer_id in self.active_connections:
            await self.active_connections[peer_id].send_text(json.dumps(message))

global_manager = ConnectionManager()
signaling_manager = ConnectionManager()