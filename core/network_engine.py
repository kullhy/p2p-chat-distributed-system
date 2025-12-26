import socket
import threading
import json
import time
import uuid

class P2PEngine:
    def __init__(self, username, tcp_port=6000, udp_port=7000, callbacks=None):
        """
        callbacks: dict of callback functions
        {
            "on_log": func(str),
            "on_peer_update": func(peers),
            "on_message": func(msg)
        }
        """
        self.username = username
        self.tcp_port = tcp_port
        self.udp_port = udp_port
        self.peers = {}  # {ip: {"username": name, "port": port, "last_seen": time}}
        self.messages = [] 
        self.callbacks = callbacks or {}
        self.running = False
        
        # [Distributed System Concept] Lamport Logical Clock
        # Used for partial ordering of events in a distributed system without a central clock.
        self.logical_clock = 0 
        self.clock_lock = threading.Lock()

    def _log(self, message):
        if "on_log" in self.callbacks:
            self.callbacks["on_log"](message)
        else:
            print(f"[SYSTEM] {message}")

    def get_local_ip(self):
        try:
            # Dummy connection to find local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def start(self):
        self.running = True
        self.local_ip = self.get_local_ip()
        self._log(f"Starting P2P Engine on {self.local_ip} (TCP: {self.tcp_port}, UDP: {self.udp_port})")

        # 1. Broadcaster
        threading.Thread(target=self._udp_broadcaster, daemon=True).start()
        # 2. Listener
        threading.Thread(target=self._udp_listener, daemon=True).start()
        # 3. TCP Server
        threading.Thread(target=self._tcp_listener, daemon=True).start()
        # 4. Peer Cleanup
        threading.Thread(target=self._peer_cleanup, daemon=True).start()

    def _udp_broadcaster(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        while self.running:
            try:
                data = json.dumps({
                    "type": "HELLO", 
                    "user": self.username, 
                    "port": self.tcp_port
                })
                # Broadcast to a range of ports for local simulation
                for p in range(7000, 7010): # Broadcast to 7000-7009
                    sock.sendto(data.encode(), ('255.255.255.255', p))
                time.sleep(5)
            except Exception as e:
                self._log(f"Broadcast error: {e}")
                time.sleep(5)

    def _udp_listener(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Enable Reuse Port for local testing (multiple apps on same machine)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except AttributeError:
            # SO_REUSEPORT might not be available on all OS (e.g. Windows)
            pass

        # Bind to 0.0.0.0 to receive broadcasts
        try:
            sock.bind(('0.0.0.0', self.udp_port))
        except OSError as e:
            self._log(f"Error binding UDP port: {e}")
            return

        while self.running:
            try:
                data, addr = sock.recvfrom(4096)
                sender_ip = addr[0]
                
                info = json.loads(data.decode())
                if info.get("type") == "HELLO":
                    username = info.get("user", "Unknown")
                    port = info.get("port", 5000)
                    
                    # Ignore own broadcast
                    if sender_ip == self.local_ip and port == self.tcp_port:
                        continue

                    peer_key = f"{sender_ip}:{port}"

                    # Check previous status to trigger update if coming back online
                    is_new = peer_key not in self.peers
                    prev_status = self.peers[peer_key]["status"] if not is_new else None
                    
                    self.peers[peer_key] = {
                        "ip": sender_ip,
                        "username": username,
                        "port": port,
                        "last_seen": time.time(),
                        "status": "Online"
                    }
                    
                    if is_new:
                        self._log(f"Found peer: {username} ({peer_key})")
                        self._notify_peer_update()
                    elif prev_status == "Offline":
                        self._log(f"Peer {username} back online")
                        self._notify_peer_update()

            except Exception as e:
                self._log(f"UDP Listen error: {e}")

    def _peer_cleanup(self):
        """Check for offline peers"""
        while self.running:
            time.sleep(2)
            current_time = time.time()
            changed = False
            for ip in list(self.peers.keys()):
                peer = self.peers[ip]
                if current_time - peer["last_seen"] > 15:
                    if peer["status"] != "Offline":
                        peer["status"] = "Offline"
                        self._log(f"Peer {peer['username']} went offline")
                        changed = True
                else:
                    if peer["status"] == "Offline":
                        peer["status"] = "Online"
                        self._log(f"Peer {peer['username']} back online")
                        changed = True
            
            if changed:
                self._notify_peer_update()

    def _notify_peer_update(self):
        if "on_peer_update" in self.callbacks:
            self.callbacks["on_peer_update"](self.peers)

    def _increment_clock(self):
        """Thread-safe increment of logical clock (Internal Event or Send Event)"""
        with self.clock_lock:
            self.logical_clock += 1
            return self.logical_clock

    def _update_clock(self, received_time):
        """Update logical clock on Receive Event: max(local, received) + 1"""
        with self.clock_lock:
            self.logical_clock = max(self.logical_clock, received_time) + 1
            return self.logical_clock

    def _tcp_listener(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('0.0.0.0', self.tcp_port))
            sock.listen(5)
            self._log("Chat server listening...")
        except OSError as e:
            self._log(f"TCP Bind error: {e}")
            return

        while self.running:
            try:
                conn, addr = sock.accept()
                threading.Thread(target=self._handle_incoming_chat, args=(conn, addr), daemon=True).start()
            except Exception as e:
                self._log(f"TCP Accept error: {e}")

    def _handle_incoming_chat(self, conn, addr):
        with conn:
            try:
                data = conn.recv(4096)
                if data:
                    msg = json.loads(data.decode())
                    
                    # [Distributed System] Synchronization Step
                    # Updates local clock based on message's timestamp to maintain causal order
                    remote_clock = msg.get("lamport_clock", 0)
                    self._update_clock(remote_clock)
                    
                    # Add sender IP if not present or just for reference
                    msg["source_ip"] = addr[0]
                    self.messages.append(msg)
                    
                    if "on_message" in self.callbacks:
                        self.callbacks["on_message"](msg)
                    
                    # self._log(f"Received from {msg.get('sender')}: {msg.get('content')}")
            except Exception as e:
                self._log(f"Error handling chat: {e}")

    def send_message(self, target_ip, target_port, content, msg_type="CHAT"):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((target_ip, target_port))
            
            # [Distributed System] Tick before Send
            current_tick = self._increment_clock()
            
            data = json.dumps({
                "type": msg_type,
                "msg_id": str(uuid.uuid4()),
                "sender": self.username,
                "content": content,
                "timestamp": time.time(),
                "lamport_clock": current_tick
            })
            sock.send(data.encode())
            sock.close()
            
            # Log own message (only for 1-1 chat, Group chat handles its own log once)
            if "on_message" in self.callbacks and msg_type != "GROUP":
                self.callbacks["on_message"]({
                    "sender": self.username,   # Me
                    "content": content,
                    "timestamp": time.time(),
                    "lamport_clock": current_tick, # Own clock at send time
                    "source_ip": "me",         # Marker for UI
                    "type": msg_type
                })

            return True
        except Exception as e:
            self._log(f"Failed to send to {target_ip}: {e}")
            return False

    def send_group_message(self, content):
        """Gửi tin nhắn cho tất cả các Peer được tìm thấy trong mạng"""
        sent_count = 0
        current_time = time.time()
        # Duyệt qua danh sách peers (copy keys để tránh lỗi runtime khi dict thay đổi)
        for key, info in list(self.peers.items()):
            # Kiểm tra xem Peer còn online không (trong vòng 30s qua)
            if current_time - info['last_seen'] < 30:
                # Use stored IP in info, or parse key
                target_ip = info.get("ip", key.split(":")[0])
                success = self.send_message(target_ip, info['port'], content, msg_type="GROUP")
                if success:
                    sent_count += 1
            else:
                # Nếu quá lâu không thấy, đánh dấu offline hoặc xoá
                # Ở đây ta tuân theo hàm cleanup, nhưng có thể xoá nếu cần thiết theo yêu cầu user
                 pass
        
        # Log own group message once
        if "on_message" in self.callbacks:
            self.callbacks["on_message"]({
                "sender": self.username,
                "content": content,
                "timestamp": time.time(),
                "lamport_clock": self.logical_clock, # Current clock
                "source_ip": "me",
                "type": "GROUP"
            })
            
        return sent_count
