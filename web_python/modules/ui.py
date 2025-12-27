import js
from pyodide.ffi import create_proxy
from datetime import datetime

class UIManager:
    def __init__(self):
        self.doc = js.document
        self.elements = {
            'my_id': self.doc.getElementById('my-peer-id'),
            'status_dot': self.doc.getElementById('status-dot'),
            'status_text': self.doc.getElementById('status-text'),
            'peer_list': self.doc.getElementById('peer-list'),
            'msg_input': self.doc.getElementById('message-input'),
            'send_btn': self.doc.getElementById('send-btn'),
            'msg_box': self.doc.getElementById('messages-container'),
            'peer_name': self.doc.getElementById('current-peer-name'),
            'chat_status': self.doc.getElementById('chat-status'),
            'connect_btn': self.doc.getElementById('connect-btn'),
            'target_input': self.doc.getElementById('target-id-input'),
            'copy_btn': self.doc.getElementById('copy-btn')
        }
        
        self.on_chat_switch = None

    def set_identity(self, peer_id, role_text):
        self.elements['my_id'].textContent = peer_id
        self.elements['status_dot'].className = 'status-indicator online'
        self.elements['status_text'].textContent = role_text
        self.elements['msg_input'].disabled = False
        self.elements['send_btn'].disabled = False

    def render_peer_list(self, users, my_id, active_chat_id, lobby_id, app_ns):
        pc_list = self.elements['peer_list']
        pc_list.innerHTML = ''
        
        # Global Chat Item
        gl_active = 'active' if active_chat_id == 'GLOBAL_CHAT' else ''
        gl_li = self.doc.createElement('li')
        gl_li.className = f"peer-item {gl_active}"
        gl_li.innerHTML = f"""
            <div class="peer-avatar globe"><ion-icon name="earth-outline"></ion-icon></div>
            <div class="peer-info">
                <h4>Global Network</h4>
                <span>{len(users)} Online</span>
            </div>
        """
        # Note: We need to properly manage proxies to valid leaks if this renders often
        # For simplicity in this demo, we create new proxies. In prod, cache them.
        gl_li.onclick = create_proxy(lambda e: self.trigger_switch('GLOBAL_CHAT'))
        pc_list.appendChild(gl_li)

        # Divider
        div = self.doc.createElement('div')
        div.className = 'list-divider'
        div.innerText = 'Online Users'
        pc_list.appendChild(div)

        # Users
        for user in users:
            uid = user['id']
            if uid == my_id: continue
            
            display_name = "HOST SERVER" if uid == lobby_id else uid.replace(app_ns, 'User-')
            
            u_active = 'active' if active_chat_id == uid else ''
            li = self.doc.createElement('li')
            li.className = f"peer-item {u_active}"
            li.innerHTML = f"""
                <div class="peer-avatar">{display_name[:2]}</div>
                <div class="peer-info">
                    <h4>{display_name}</h4>
                    <div class="status-badge online"></div>
                </div>
            """
            li.onclick = create_proxy(lambda e, id=uid: self.trigger_switch(id))
            pc_list.appendChild(li)

    def trigger_switch(self, chat_id):
        if self.on_chat_switch:
            self.on_chat_switch(chat_id)

    def update_chat_header(self, chat_id, lobby_id, app_ns):
        if chat_id == 'GLOBAL_CHAT':
            self.elements['peer_name'].textContent = "Global Network"
            self.elements['chat_status'].textContent = "Broadcast to Python Network"
            self.elements['msg_input'].placeholder = "Broadcast message..."
        else:
            display = "HOST SERVER" if chat_id == lobby_id else chat_id.replace(app_ns, 'User-')
            self.elements['peer_name'].textContent = display
            self.elements['chat_status'].textContent = "Private P2P Channel"
            self.elements['msg_input'].placeholder = f"Message {display}..."

    def append_message(self, msg, my_id, app_ns):
        div = self.doc.createElement('div')
        
        if msg.get('direction') == 'system':
            div.className = 'message system'
            div.innerHTML = f'<small style="color:var(--text-dim); text-align:center; display:block; margin: 10px 0;">{msg["content"]}</small>'
        else:
            div.className = f"message {msg['direction']}"
            
            content = msg['content']
            time_str = datetime.fromtimestamp(msg['timestamp']/1000).strftime('%H:%M')
            
            sender_html = ""
            if msg['scope'] == 'global' and msg['direction'] == 'received':
                s_name = "Me" if msg['sender'] == my_id else msg['sender'].replace(app_ns, 'User-')
                sender_html = f'<div class="msg-sender">{s_name}</div>'

            div.innerHTML = f"""
                {sender_html}
                {content}
                <span class="meta">{time_str}</span>
            """
            
        self.elements['msg_box'].appendChild(div)
        self.elements['msg_box'].scrollTop = self.elements['msg_box'].scrollHeight

    def clear_messages(self):
        self.elements['msg_box'].innerHTML = '<div class="welcome-hero"><h2>Chat Cleared</h2></div>'

    def show_toast(self, msg):
        toast = self.doc.getElementById('toast')
        if not toast:
            toast = self.doc.createElement('div')
            toast.id = 'toast'
            toast.className = 'toast hidden'
            self.doc.body.appendChild(toast)

        toast.innerText = msg
        toast.className = 'toast'
        js.setTimeout(create_proxy(lambda: setattr(toast, 'className', 'toast hidden')), 3000)

    def bind_events(self, on_send, on_connect, on_copy):
        # Send
        self.elements['send_btn'].onclick = create_proxy(on_send)
        self.elements['msg_input'].onkeypress = create_proxy(lambda e: on_send(None) if e.key == "Enter" else None)
        
        # Connect
        self.elements['connect_btn'].onclick = create_proxy(on_connect)
        
        # Copy
        self.elements['copy_btn'].onclick = create_proxy(on_copy)
