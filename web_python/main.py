import js
import random

# IMPORT MODULES
from modules.ui import UIManager
from modules.base_p2p import BaseP2P
from modules.global_chat import GlobalChat
from modules.private_chat import PrivateChat

# --- CONFIG ---
CONFIG = {
    'APP_NAMESPACE': 'httt2025-user-',
    'LOBBY_ID': 'httt2025-master-node',
    'PEER_CONFIG': {
        'host': '0.peerjs.com',
        'port': 443,
        'path': '/',
        'secure': True,
        'debug': 2,
        'config': {
            'iceServers': [
                {'urls': 'stun:stun.l.google.com:19302'},
                {'urls': 'stun:stun1.l.google.com:19302'},
                {'urls': 'stun:stun2.l.google.com:19302'},
                {'urls': 'stun:stun3.l.google.com:19302'},
                {'urls': 'stun:stun4.l.google.com:19302'},
            ]
        }
    }
}

class Main:
    def __init__(self):
        self.config = CONFIG
        
        # Initialize Modules
        self.ui = UIManager()
        self.base = BaseP2P(CONFIG['PEER_CONFIG'])
        self.global_chat = GlobalChat(self.base, CONFIG)
        self.private_chat = PrivateChat(self.base)
        
        # State
        self.active_chat = 'GLOBAL_CHAT'
        self.history = {'GLOBAL_CHAT': []}
        
        # Wiring
        self.setup_wiring()
        self.start_app()

    def setup_wiring(self):
        # BASE EVENTS
        self.base.on_open_callback = self.on_my_id_ready
        self.base.on_conn_open_callback = self.on_connection_open
        self.base.on_conn_close_callback = self.on_connection_close
        self.base.on_data_callback = self.on_incoming_data
        
        # GLOBAL EVENTS
        self.global_chat.on_user_list_update = self.on_user_list_updated
        self.global_chat.on_message_received = self.on_chat_message
        
        # PRIVATE EVENTS
        self.private_chat.on_message_received = self.on_private_message
        
        # UI EVENTS
        self.ui.bind_events(
            on_send=self.user_send_message,
            on_connect=self.user_manual_connect,
            on_copy=self.user_copy_id
        )
        self.ui.on_chat_switch = self.switch_chat_context

    def start_app(self):
        # Try to Host first
        self.ui.elements['status_text'].textContent = "Initializing..."
        
        # ERROR HANDLER
        def error_handler(err):
            if err.type == 'unavailable-id':
                print("Host ID taken. Switching to Client...")
                random_id = f"{CONFIG['APP_NAMESPACE']}{random.randint(1000,99999)}"
                # We need to destroy old peer and init new
                self.base.destroy()
                # Init as Client
                self.base.init_peer(random_id, is_host_mode=False)
        
        self.base.on_error_callback = error_handler

        try:
            self.base.init_peer(CONFIG['LOBBY_ID'], is_host_mode=True)
        except Exception as e:
            print(f"Init Exception: {e}")

    # --- EVENT HANDLERS ---
    def on_my_id_ready(self, my_id):
        role = "HOST NODE" if self.base.is_host else "Client Node"
        self.ui.set_identity(my_id, role)
        
        if self.base.is_host:
            self.global_chat.start_host()
        else:
            self.global_chat.connect_to_lobby()

    def on_connection_open(self, peer_id):
        if self.base.is_host:
            self.global_chat.on_host_connection(peer_id)
        else:
            self.global_chat.on_client_connection_open(peer_id)

    def on_incoming_data(self, sender_id, data):
        dtype = data.get('type')
        if dtype in ['GLOBAL_CHAT', 'USER_LIST', 'LOGIN']:
            if self.base.is_host:
                self.global_chat.on_host_data(sender_id, data)
            else:
                self.global_chat.on_client_data(data)
        elif dtype == 'PRIVATE_CHAT':
            self.private_chat.on_private_data(sender_id, data)

    def on_connection_close(self, peer_id):
        if self.base.is_host:
            self.global_chat.on_host_disconnect(peer_id)

    # --- UI LOGIC ---
    def on_user_list_updated(self, users):
        self.ui.render_peer_list(users, self.base.my_id, self.active_chat, CONFIG['LOBBY_ID'], CONFIG['APP_NAMESPACE'])

    def on_chat_message(self, msg):
        self.store_and_render('GLOBAL_CHAT', msg)

    def on_private_message(self, msg):
        # msg context is the sender's ID (or 'Me' but logic handles it)
        # Actually, if we receive private msg from 'User-123', the chat ID is 'User-123'.
        chat_id = msg['sender']
        self.store_and_render(chat_id, msg)

    def user_send_message(self, event):
        content = self.ui.elements['msg_input'].value.strip()
        if not content: return
        
        msg = None
        if self.active_chat == 'GLOBAL_CHAT':
            msg = self.global_chat.send_message(content)
            self.store_and_render('GLOBAL_CHAT', msg)
        else:
            msg = self.private_chat.send_message(self.active_chat, content)
            self.store_and_render(self.active_chat, msg)
        
        self.ui.elements['msg_input'].value = ""

    def store_and_render(self, chat_id, msg):
        if chat_id not in self.history:
            self.history[chat_id] = []
        self.history[chat_id].append(msg)
        
        if self.active_chat == chat_id:
            self.ui.append_message(msg, self.base.my_id, CONFIG['APP_NAMESPACE'])

    def switch_chat_context(self, chat_id):
        self.active_chat = chat_id
        self.ui.update_chat_header(chat_id, CONFIG['LOBBY_ID'], CONFIG['APP_NAMESPACE'])
        
        # Render History
        self.ui.elements['msg_box'].innerHTML = ''
        msgs = self.history.get(chat_id, [])
        if not msgs:
            self.ui.clear_messages()
            return
        for m in msgs:
            self.ui.append_message(m, self.base.my_id, CONFIG['APP_NAMESPACE'])

    def user_manual_connect(self, event):
        target = self.ui.elements['target_input'].value.strip()
        if target:
            self.base.connect(target)
            self.ui.elements['target_input'].value = ""

    def user_copy_id(self, event):
        js.navigator.clipboard.writeText(self.base.my_id)
        self.ui.show_toast(f"Copied: {self.base.my_id}")

# --- START ---
app = Main()
