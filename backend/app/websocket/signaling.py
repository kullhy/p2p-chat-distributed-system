import json
import logging
import time
from fastapi import WebSocket, WebSocketDisconnect
from ..services.connection_manager import signaling_manager

logger = logging.getLogger("SignalingForensics")


async def signaling_handler(websocket: WebSocket, peer_id: str):
    logger.info(f"[SIGNAL_WS][INIT] TS:{time.time()} | Peer:{peer_id}")
    await signaling_manager.connect(peer_id, websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            ts = time.time()
            target_id = message.get("to")
            from_id = message.get("from")
            msg_type = message.get("type")

            # Diagnostic: Log every single signaling packet passing through the server
            logger.info(f"[SIGNAL_TRACE] TS:{ts} | {msg_type} | From:{from_id} | To:{target_id}")

            if target_id:
                success = await signaling_manager.send_personal_message(message, target_id)
                if not success:
                    logger.error(f"[SIGNAL_DROP] TS:{ts} | {msg_type} dropped. Target {target_id} offline.")
            else:
                logger.warning(f"[SIGNAL_MALFORMED] TS:{ts} | From:{from_id} | Missing target ID")

    except WebSocketDisconnect:
        logger.info(f"[SIGNAL_WS][EXIT] TS:{time.time()} | Peer:{peer_id}")
        signaling_manager.disconnect(peer_id)
    except Exception as e:
        logger.error(f"[SIGNAL_WS][CRASH] TS:{time.time()} | Peer:{peer_id} | {e}")
        signaling_manager.disconnect(peer_id)
