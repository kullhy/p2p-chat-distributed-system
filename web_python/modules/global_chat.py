from datetime import datetime
import js

class GlobalChat:
    def __init__(self, base_ptr, config):
        self.base = base_ptr # Reference to BaseP2P instance
        self.config = config
        
        self.known_users = []
        
        # Callbacks
        self.on_user_list_update = None
        self.on_message_received = None # For UI
        
        self.heartbeat_interval = None

    # --- HOST LOGIC ---
    def start_host(self):
        print("Starting Host Logic...")
        # Add self
        self.known_users = [{'id': self.base.my_id, 'status': 'online'}]
        if self.on_user_list_update:
            self.on_user_list_update(self.known_users)
            
        # Simplistic heartbeat: just broadcast list occasionally to ensure consistency
        # In python creating interval is slightly different via js.setInterval or async loop
        # For simplicity, we trigger updates on events.

    def on_host_connection(self, peer_id):
        # New client connected
        if not any(u['id'] == peer_id for u in self.known_users):
            self.known_users.append({'id': peer_id, 'status': 'online'})
            self.broadcast_list()
        else:
            # Send list just to him
            self.base.send(peer_id, {'type': 'USER_LIST', 'users': self.known_users})
    
    def on_host_disconnect(self, peer_id):
        exists = any(u['id'] == peer_id for u in self.known_users)
        if exists:
            self.known_users = [u for u in self.known_users if u['id'] != peer_id]
            self.broadcast_list()
            # System message
            if self.on_message_received:
                self.on_message_received({
                    'content': f"{peer_id[-6:]} left.",
                    'direction': 'system',
                    'scope': 'global',
                    'timestamp': self.get_ms()
                })

    def on_host_data(self, sender_id, data):
        if data['type'] == 'GLOBAL_CHAT':
            # Broadcast to everyone else
            self.base.broadcast(data, exclude_id=sender_id)
            # Notify local UI
            if self.on_message_received:
                self.on_message_received({
                    'sender': data['sender'],
                    'content': data['content'],
                    'direction': 'received',
                    'scope': 'global',
                    'timestamp': data.get('timestamp', self.get_ms())
                })

    def broadcast_list(self):
        payload = {'type': 'USER_LIST', 'users': self.known_users}
        self.base.broadcast(payload)
        if self.on_user_list_update:
            self.on_user_list_update(self.known_users)

    # --- CLIENT LOGIC ---
    def connect_to_lobby(self):
        lobby_id = self.config['LOBBY_ID']
        print(f"GlobalChat: Connecting to Lobby {lobby_id}...")
        conn = self.base.connect(lobby_id)
        # Login is handled when connection opens. 
        # But BaseP2P abstracts connection events.
        # We need to know when lobby conn opens to send LOGIN.
        # In main.py wiring, we will check if conn is LOBBY.

    def on_client_connection_open(self, peer_id):
        if peer_id == self.config['LOBBY_ID']:
            # Send Login
            self.base.send(peer_id, {'type': 'LOGIN', 'sender': self.base.my_id})

    def on_client_data(self, data):
        dtype = data.get('type')
        if dtype == 'USER_LIST':
            # js proxy array conversion handled in main or here?
            # BaseP2P passes py dict/list processed from json?
            # BaseP2P `_on_conn_data` does `data_obj.to_py()`.
            # So `data` is python dict.
            users = data.get('users')
            # It might be a JsProxy of Array inside the dict
            # We explicitly convert if needed, but to_py usually handles recursive.
            self.known_users = [u for u in users]
            if self.on_user_list_update:
                self.on_user_list_update(self.known_users)
        
        elif dtype == 'GLOBAL_CHAT':
            if self.on_message_received:
                self.on_message_received({
                    'sender': data['sender'],
                    'content': data['content'],
                    'direction': 'received',
                    'scope': 'global',
                    'timestamp': data.get('timestamp', self.get_ms())
                })

    # --- COMMON ---
    def send_message(self, content):
        payload = {
            'type': 'GLOBAL_CHAT',
            'sender': self.base.my_id,
            'content': content,
            'timestamp': self.get_ms()
        }
        
        if self.base.is_host:
            self.base.broadcast(payload)
            # Local echo handled by return or callback?
            # Let's return the msg object to be rendered
        else:
            self.base.send(self.config['LOBBY_ID'], payload)
            
        return {
            'sender': self.base.my_id,
            'content': content,
            'direction': 'sent', 
            'scope': 'global',
            'timestamp': payload['timestamp']
        }

    def get_ms(self):
        return int(datetime.now().timestamp() * 1000)
