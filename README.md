Hybrid P2P Chat System
A clean-architecture implementation of a hybrid chat system using FastAPI for global coordination and WebRTC for private
peer-to-peer communication.

Architecture
Global Layer: Client-Server via WebSockets. Used for peer discovery and public broadcasting.

Private Layer: Peer-to-Peer via WebRTC DataChannels. Messages are never seen by the server.

Signaling: The backend relays encrypted WebRTC handshake data but cannot read the resulting P2P stream.

Setup & Run

1. Backend
   Bash

```
cd backend
pip install -r requirements.txt
python -m app.main
Server starts at http://localhost:8000.
```

2. Frontend
   Since this is a static frontend, you can:

Open frontend/index.html directly in multiple browser tabs.

For the best experience, serve it using a simple server:

Bash

```
cd frontend
python -m http.server 3000
How to Test
Open http://localhost:3000 in Tab A. Enter "Alice".

Open http://localhost:3000 in Tab B (Incognito). Enter "Bob".
```

Global Chat: Type in the box; both see the message.

Private Chat:

On Alice's screen, click "Bob" in the sidebar.

Status will change to "Connecting..." then "P2P Secure".

Messages sent here are green and bypass the server entirely.

Limitations
ICE/STUN: Uses Google's public STUN server. If users are behind symmetric NATs (unlikely on the same Wi-Fi), a TURN
server would be required.

Persistence: Messages are volatile and cleared on refresh to ensure privacy.