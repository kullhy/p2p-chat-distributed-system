from fastapi import WebSocket
from typing import Dict
import json
import logging
import time

# Enhanced logging for forensics
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Forensics")


class ConnectionManager:
    def __init__(self, name: str):
        self.name = name
        # Mapping peerId -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, peer_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[peer_id] = websocket
        logger.info(
            f"[{self.name}][CONN] TS:{time.time()} | Peer:{peer_id} connected. Pool size: {len(self.active_connections)}")

    def disconnect(self, peer_id: str):
        if peer_id in self.active_connections:
            del self.active_connections[peer_id]
            logger.info(f"[{self.name}][DISCONN] TS:{time.time()} | Peer:{peer_id} removed.")

    async def send_personal_message(self, message: dict, peer_id: str):
        ts = time.time()
        m_type = message.get("type", "unknown")
        if peer_id in self.active_connections:
            ws = self.active_connections[peer_id]
            try:
                await ws.send_text(json.dumps(message))
                logger.info(f"[{self.name}][ROUTE] TS:{ts} | Type:{m_type} | To:{peer_id} | SUCCESS")
                return True
            except Exception as e:
                logger.error(f"[{self.name}][ROUTE_ERR] TS:{ts} | Type:{m_type} | To:{peer_id} | ERR:{e}")
                return False
        logger.warning(
            f"[{self.name}][ROUTE_MISS] TS:{ts} | Type:{m_type} | To:{peer_id} | REASON: Peer not in registry")
        return False

    async def broadcast(self, message: dict):
        for pid, ws in list(self.active_connections.items()):
            try:
                await ws.send_text(json.dumps(message))
            except:
                continue


global_manager = ConnectionManager("Global")
signaling_manager = ConnectionManager("Signaling")
