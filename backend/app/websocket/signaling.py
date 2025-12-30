import json
import logging
from fastapi import WebSocket, WebSocketDisconnect
from ..services.connection_manager import signaling_manager

logger = logging.getLogger("SignalingHandler")


async def signaling_handler(websocket: WebSocket, peer_id: str):
    logger.info(f"[SIGNAL_WS] Handshake started for: {peer_id}")
    await signaling_manager.connect(peer_id, websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            target_id = message.get("to")
            msg_type = message.get("type")
            from_id = message.get("from")

            # Log luồng đi của gói tin
            if target_id:
                logger.info(f"[SIGNAL_ROUTE] {msg_type} | {from_id} -> {target_id}")
                success = await signaling_manager.send_personal_message(message, target_id)
                if not success:
                    logger.warning(f"[SIGNAL_FAIL] Could not deliver to {target_id}")
            else:
                logger.warning(f"[SIGNAL_ERR] Missing 'to' field from {from_id}")

    except WebSocketDisconnect:
        logger.info(f"[SIGNAL_EXIT] Closed: {peer_id}")
        signaling_manager.disconnect(peer_id)
    except Exception as e:
        logger.error(f"[SIGNAL_CRASH] {peer_id}: {e}")
        signaling_manager.disconnect(peer_id)