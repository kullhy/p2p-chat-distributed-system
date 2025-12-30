from fastapi import WebSocket
from typing import Dict
import json
import logging
import time

# Cấu hình log để dễ nhìn hơn
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ConnectionManager")


class ConnectionManager:
    def __init__(self, name: str):
        self.name = name
        # Mapping peerId -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, peer_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[peer_id] = websocket
        logger.info(f"[{self.name}] Peer connected: {peer_id}. Total: {len(self.active_connections)}")

    def disconnect(self, peer_id: str):
        if peer_id in self.active_connections:
            del self.active_connections[peer_id]
            logger.info(f"[{self.name}] Peer disconnected: {peer_id}")

    async def send_personal_message(self, message: dict, peer_id: str):
        if peer_id in self.active_connections:
            ws = self.active_connections[peer_id]
            try:
                await ws.send_text(json.dumps(message))
                return True
            except Exception as e:
                logger.error(f"[{self.name}] Error sending to {peer_id}: {e}")
                return False
        logger.warning(f"[{self.name}] Target {peer_id} not found.")
        return False

    async def broadcast(self, message: dict):
        for pid, ws in list(self.active_connections.items()):
            try:
                await ws.send_text(json.dumps(message))
            except:
                continue


# Tạo 2 instance riêng biệt để tránh xung đột ID
global_manager = ConnectionManager("Global")
signaling_manager = ConnectionManager("Signaling")
