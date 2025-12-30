from pydantic import BaseModel
from typing import Optional, Dict, Any

class Peer(BaseModel):
    peerId: str
    username: str
    status: str = "online"

class Message(BaseModel):
    type: str
    from_id: str  # mapped from 'from' in JSON
    to_id: Optional[str] = None # mapped from 'to' in JSON
    payload: Dict[str, Any]