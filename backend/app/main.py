from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from .websocket.global_chat import global_chat_handler
from .websocket.signaling import signaling_handler

app = FastAPI(title="P2P Hybrid Chat")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/ws/global/{peer_id}")
async def ws_global_endpoint(websocket: WebSocket, peer_id: str):
    await global_chat_handler(websocket, peer_id)


@app.websocket("/ws/signaling/{peer_id}")
async def ws_signaling_endpoint(websocket: WebSocket, peer_id: str):
    await signaling_handler(websocket, peer_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
