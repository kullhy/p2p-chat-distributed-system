from typing import Dict
from ..models import Peer

class PresenceService:
    def __init__(self):
        self.peers: Dict[str, Peer] = {}

    def add_peer(self, peer: Peer):
        self.peers[peer.peerId] = peer

    def remove_peer(self, peer_id: str):
        if peer_id in self.peers:
            del self.peers[peer_id]

    def get_all_peers(self):
        return [p.dict() for p in self.peers.values()]

presence_service = PresenceService()