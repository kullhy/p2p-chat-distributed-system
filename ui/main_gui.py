import customtkinter as ctk
import sys
import threading
from datetime import datetime
from PIL import Image

# Import core but we might need to adjust path in main.py or here
# Assuming main.py sets up path, but for safety in this file:
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.network_engine import P2PEngine

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class PeerCard(ctk.CTkFrame):
    def __init__(self, master, name, ip, status, on_click):
        super().__init__(master, fg_color="transparent")
        self.ip = ip
        self.on_click = on_click
        
        # Card Layout
        self.configure(fg_color=("gray85", "gray25"), corner_radius=10)
        
        # Status Indicator
        color = "#00E676" if status == "Online" else "#9E9E9E"
        self.status_indicator = ctk.CTkLabel(self, text="●", text_color=color, font=("Arial", 24))
        self.status_indicator.pack(side="left", padx=(10, 5))
        
        # Info
        self.info_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.info_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        self.name_lbl = ctk.CTkLabel(self.info_frame, text=name, font=("Roboto", 14, "bold"), anchor="w")
        self.name_lbl.pack(fill="x")
        
        self.ip_lbl = ctk.CTkLabel(self.info_frame, text=ip, font=("Roboto", 11), text_color="gray", anchor="w")
        self.ip_lbl.pack(fill="x")
        
        # Click event
        self.bind("<Button-1>", self._clicked)
        self.name_lbl.bind("<Button-1>", self._clicked)
        self.ip_lbl.bind("<Button-1>", self._clicked)
        self.status_indicator.bind("<Button-1>", self._clicked)
        self.info_frame.bind("<Button-1>", self._clicked)

    def _clicked(self, event):
        self.on_click(self.ip)

class MessageBubble(ctk.CTkFrame):
    def __init__(self, master, text, sender, is_me, timestamp):
        super().__init__(master, fg_color="transparent")
        
        # Layout based on sender
        if is_me:
            pack_side = "right"
            bg_color = "#2196F3" # Blue
            text_color = "white"
            anchor = "e"
        else:
            pack_side = "left" 
            bg_color = "#424242" # Dark Gray
            text_color = "white"
            anchor = "w"
            
        self.container = ctk.CTkFrame(self, fg_color=bg_color, corner_radius=15)
        self.container.pack(side=pack_side, padx=10, pady=5, ipadx=10, ipady=5)
        
        # Sender Name (only if not me)
        if not is_me:
            self.sender_lbl = ctk.CTkLabel(self.container, text=sender, font=("Roboto", 10, "bold"), text_color="gray80", anchor="w")
            self.sender_lbl.pack(fill="x", pady=(0, 2))
            
        # Message Text
        self.msg_lbl = ctk.CTkLabel(self.container, text=text, font=("Roboto", 13), text_color=text_color, wraplength=350, justify="left")
        self.msg_lbl.pack()
        
        # Time
        time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M")
        self.time_lbl = ctk.CTkLabel(self.container, text=time_str, font=("Roboto", 9), text_color="gray80", anchor="e")
        self.time_lbl.pack(fill="x", pady=(2, 0))

class LoginWindow(ctk.CTkToplevel):
    def __init__(self, master, on_login):
        super().__init__(master)
        self.title("Join P2P Network")
        self.geometry("300x200")
        self.resizable(False, False)
        self.on_login = on_login
        
        self.attributes("-topmost", True)
        
        self.label = ctk.CTkLabel(self, text="Enter your Username:", font=("Roboto", 16))
        self.label.pack(pady=(30, 10))
        
        self.entry = ctk.CTkEntry(self, placeholder_text="Username")
        self.entry.pack(pady=10, padx=20, fill="x")
        self.entry.bind("<Return>", lambda e: self.login())
        
        self.btn = ctk.CTkButton(self, text="Join", command=self.login)
        self.btn.pack(pady=10)
        
    def login(self):
        name = self.entry.get()
        if name:
            self.on_login(name)
            self.destroy()

class P2PChatApp(ctk.CTk):
    def __init__(self, tcp_port=6000):
        super().__init__()
        self.tcp_port = tcp_port
        
        self.title("Decentralized P2P Chat")
        self.geometry("1000x700")
        
        # State
        self.engine = None
        self.selected_peer_ip = None
        self.chat_history = {} # {ip: [msgs]}
        
        # Layout definition
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # --- Sidebar (Left) ---
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="P2P NETWORK", font=("Montserrat", 20, "bold"))
        self.logo_label.pack(pady=20)
        
        self.peer_list_label = ctk.CTkLabel(self.sidebar, text="Discovered Peers:", anchor="w")
        self.peer_list_label.pack(fill="x", padx=10)
        
        self.peer_scroll = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        self.peer_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Log Console (Bottom of Sidebar)
        self.log_label = ctk.CTkLabel(self.sidebar, text="System Log:", anchor="w")
        self.log_label.pack(fill="x", padx=10, pady=(10, 0))
        
        self.log_box = ctk.CTkTextbox(self.sidebar, height=150, font=("Consolas", 10), text_color="gray")
        self.log_box.pack(fill="x", padx=5, pady=10)
        self.log_box.configure(state="disabled")
        
        # --- Chat Area (Right) ---
        self.header = ctk.CTkFrame(self, height=60, corner_radius=0, fg_color=("gray95", "gray20"))
        self.header.grid(row=0, column=1, sticky="new")
        
        self.chat_title = ctk.CTkLabel(self.header, text="Select a peer to start chatting", font=("Roboto", 16, "bold"))
        self.chat_title.pack(side="left", padx=20, pady=15)
        
        self.messages_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.messages_scroll.grid(row=0, column=1, sticky="nsew", pady=(60, 0)) # Offset for header
        
        # Input Area
        self.input_frame = ctk.CTkFrame(self, height=60, corner_radius=0)
        self.input_frame.grid(row=1, column=1, sticky="ew")
        
        self.msg_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Type message...", height=40)
        self.msg_entry.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        self.msg_entry.bind("<Return>", lambda e: self.send_message())
        
        self.send_btn = ctk.CTkButton(self.input_frame, text="Send", width=80, height=40, command=self.send_message)
        self.send_btn.pack(side="right", padx=10, pady=10)
        
        # Ask for Username
        self.withdraw()
        LoginWindow(self, self.start_engine)
        
    def start_engine(self, username):
        self.deiconify()
        callbacks = {
            "on_log": self.on_log,
            "on_peer_update": self.on_peer_update,
            "on_message": self.on_message
        }
        udp_port = 7000 + (self.tcp_port - 6000)
        self.engine = P2PEngine(username, tcp_port=self.tcp_port, udp_port=udp_port, callbacks=callbacks)
        self.engine.start()
        self.title(f"Decentralized P2P Chat - {username} ({self.engine.local_ip})")
        
    def on_log(self, message):
        self.after(0, self._append_log, message)
        
    def _append_log(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")
        
    def on_peer_update(self, peers):
        self.after(0, self._update_peer_list, peers)
        
    def _update_peer_list(self, peers):
        # Clear existing
        for widget in self.peer_scroll.winfo_children():
            widget.destroy()
            
        # Add "Group Chat" Item
        group_card = PeerCard(self.peer_scroll, "All Peers (Group Chat)", "GROUP", "Online", self.select_peer)
        group_card.pack(fill="x", pady=5)
            
        # Re-populate peers
        for ip, info in peers.items():
            card = PeerCard(self.peer_scroll, info['username'], ip, info.get('status', 'Online'), self.select_peer)
            card.pack(fill="x", pady=5)
            
    def select_peer(self, ip):
        self.selected_peer_ip = ip
        if ip == "GROUP":
            self.chat_title.configure(text=f"Group Chat - All Peers")
        else:
            peer = self.engine.peers.get(ip, {})
            name = peer.get('username', 'Unknown')
            self.chat_title.configure(text=f"Chatting with {name} ({ip})")
        self.render_chat()
        
    def on_message(self, msg):
        msg_type = msg.get("type", "CHAT")
        content = msg.get("content")
        timestamp = msg.get("timestamp", 0)
        
        # Determine storage key
        target_key = None
        
        if msg_type == "GROUP":
            target_key = "GROUP"
        else:
            # 1-1 Chat logic
            source_ip = msg.get("source_ip")
            if source_ip == "me":
                # For 1-1 own msg, we need to know who we sent it to to store correctly?
                # Actually previously we handled it in send_message local storage.
                # But engine callback now sends it back. 
                # Wait, engine callback for 1-1 'me' doesn't tell us target. 
                # So we ignore 'me' 1-1 msg from callback (we handle it in send_message UI), 
                # OR we fix engine. 
                # Let's rely on send_message UI logic for own 1-1 history, and ignore callback for own 1-1.
                return 
            else:
                target_key = source_ip

        if not target_key:
            return

        if target_key not in self.chat_history:
            self.chat_history[target_key] = []
            
        # Avoid duplicates if msg_id exists? (Optional consistency check)
        # For now just append
        self.chat_history[target_key].append(msg)
        
        # Sort by timestamp (Lamport/consistency requirement)
        self.chat_history[target_key].sort(key=lambda x: x.get("timestamp", 0))

        # Refresh if looking at it
        if self.selected_peer_ip == target_key:
            self.after(0, self.render_chat)
        elif self.selected_peer_ip is None and target_key != "GROUP":
            # notification logic
            pass
                
    def send_message(self):
        if not self.selected_peer_ip:
            self.on_log("Select a peer first!")
            return
            
        content = self.msg_entry.get().strip()
        if not content:
            return
            
        if self.selected_peer_ip == "GROUP":
            count = self.engine.send_group_message(content)
            self.on_log(f"Sent group message to {count} peers.")
            # Local echo handled by callback now? 
            # Engine send_group_message triggers callback 'on_message' with type GROUP and source 'me'.
            # Our on_message above handles GROUP + me correctly.
            pass
        else:
            # 1-1 Legacy logic
            peer = self.engine.peers.get(self.selected_peer_ip)
            if not peer:
                self.on_log("Peer not found!")
                return
            target_port = peer.get("port", 5000)
            success = self.engine.send_message(self.selected_peer_ip, target_port, content)
            
            if success:
                # Store locally (Engine callback disabled for 1-1 to avoid ambiguity, so we store here)
                msg_obj = {
                    "sender": "Me",
                    "content": content,
                    "timestamp": datetime.now().timestamp(),
                    "source_ip": "me",
                    "type": "CHAT"
                }
                if self.selected_peer_ip not in self.chat_history:
                    self.chat_history[self.selected_peer_ip] = []
                self.chat_history[self.selected_peer_ip].append(msg_obj)
                self.render_chat()
            else:
                self.on_log("Failed to send message.")

        self.msg_entry.delete(0, "end")

    def render_chat(self):
        # Clear
        for widget in self.messages_scroll.winfo_children():
            widget.destroy()
            
        if not self.selected_peer_ip:
            return
            
        msgs = self.chat_history.get(self.selected_peer_ip, [])
        for msg in msgs:
            is_me = (msg.get("source_ip") == "me") or (msg.get("sender") == self.engine.username)
            sender_name = "Toi" if is_me else msg.get("sender")
            
            bubble = MessageBubble(self.messages_scroll, msg.get("content"), sender_name, is_me, msg.get("timestamp"))
            bubble.pack(fill="x", pady=5)
            
        # Scroll to bottom
        # CTk scrollable frame doesn't have easy 'see' method, usually auto-expands.
        # We can try update_idletasks but it might not auto-scroll.
        # Workaround:
        self.messages_scroll._parent_canvas.yview_moveto(1.0)

if __name__ == "__main__":
    app = P2PChatApp()
    app.mainloop()
