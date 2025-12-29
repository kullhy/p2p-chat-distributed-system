import js
from pyodide.ffi import create_proxy
import json

class BaseP2P:
    def __init__(self, config):
        self.config = config
        self.peer = None
        self.my_id = None
        self.is_host = False
        
        self.connections = {}
        self.pending_connections = [] # Keep refs to prevent GC before open
        
        # Callbacks
        self.on_open_callback = None
        self.on_data_callback = None
        self.on_conn_close_callback = None
        self.on_conn_open_callback = None
        self.on_conn_error_callback = None
        self.on_error_callback = None
        
        # Proxies (keep refs)
        self.proxy_open = create_proxy(self._on_peer_open)
        self.proxy_conn = create_proxy(self._on_incoming_conn)
        self.proxy_error = create_proxy(self._on_peer_error)

    def init_peer(self, peer_id, is_host_mode):
        """Khởi tạo PeerJS với ID và cấu hình mạng. Đăng ký các sự kiện chính (open, connection, error)."""
        try:
            self.is_host = is_host_mode
            # Create JS Peer Configuration safely using JSON
            # This avoids proxy issues with nested dicts
            config_json = json.dumps(self.config)
            js_config = js.JSON.parse(config_json)
            
            self.peer = js.Peer.new(peer_id, js_config)
            
            self.peer.on('open', self.proxy_open)
            self.peer.on('connection', self.proxy_conn)
            self.peer.on('error', self.proxy_error)
            
        except Exception as e:
            print(f"BaseP2P Init Error: {e}")
            raise e

    def connect(self, target_id):
        """Chủ động kết nối tới một peer khác. Lưu kết nối vào pending để tránh GC."""
        if target_id in self.connections and self.connections[target_id].open:
            return self.connections[target_id]
        
        print(f"Connecting to {target_id}...")
        conn = self.peer.connect(target_id, js.JSON.parse('{"reliable": true}'))
        
        # KEY FIX: Store in pending to prevent Garbage Collection
        self.pending_connections.append(conn)
        
        self._setup_conn_events(conn)
        return conn

    def send(self, target_id, payload_dict):
        """Gửi dữ liệu JSON tới một peer cụ thể."""
        conn = self.connections.get(target_id)
        if conn and conn.open:
            # Safe JSON serialization
            payload_json = json.dumps(payload_dict)
            js_payload = js.JSON.parse(payload_json)
            conn.send(js_payload)
            return True
        return False

    def broadcast(self, payload_dict, exclude_id=None):
        """Gửi dữ liệu tới TẤT CẢ các peer đang kết nối (trừ exclude_id)."""
        payload_json = json.dumps(payload_dict)
        js_payload = js.JSON.parse(payload_json)
        
        count = 0
        for pid, conn in self.connections.items():
            if pid != exclude_id and conn.open:
                conn.send(js_payload)
                count += 1
        return count

    def destroy(self):
        """Hủy Peer và đóng mọi kết nối."""
        if self.peer:
            self.peer.destroy()

    # --- INTERNAL HANDLERS ---
    def _on_peer_open(self, pid):
        """Callback: Peer đã online và có ID."""
        self.my_id = pid
        print(f"Peer Open: {pid}")
        if self.on_open_callback:
            self.on_open_callback(pid)

    def _on_peer_error(self, err):
        """Callback: Lỗi liên quan đến Peer (ví dụ: mất mạng, trùng ID)."""
        print(f"Peer Error: {err.type}")
        if self.on_error_callback:
            self.on_error_callback(err)

    def _on_incoming_conn(self, conn):
        """Callback: Có người khác kết nối đến."""
        self._setup_conn_events(conn)

    def _setup_conn_events(self, conn):
        """Thiết lập lắng nghe sự kiện cho từng kết nối riêng biệt."""
        # Create unique proxies for each connection
        conn.proxy_open = create_proxy(lambda: self._on_conn_open(conn))
        conn.proxy_data = create_proxy(lambda d: self._on_conn_data(conn, d))
        conn.proxy_close = create_proxy(lambda: self._on_conn_close(conn))
        conn.proxy_error = create_proxy(lambda e: self._on_conn_error(conn, e))
        
        conn.on('open', conn.proxy_open)
        conn.on('data', conn.proxy_data)
        conn.on('close', conn.proxy_close)
        conn.on('error', conn.proxy_error)

    def _on_conn_open(self, conn):
        """Callback: Kết nối đã sẵn sàng (Open)."""
        print(f"Connection OPENED with {conn.peer}")
        self.connections[conn.peer] = conn
        
        # Remove from pending if exists
        try:
            if conn in self.pending_connections:
                self.pending_connections.remove(conn)
        except ValueError:
            pass
            
        if self.on_conn_open_callback:
            self.on_conn_open_callback(conn.peer)

    def _on_conn_data(self, conn, data_obj):
        """Callback: Nhận được dữ liệu (tin nhắn) từ peer."""
        # data_obj is JS Object. to_py might return dict directly?
        # If it's pure JSON parsed object from peerjs, to_py works great.
        data = data_obj.to_py()
        if self.on_data_callback:
            self.on_data_callback(conn.peer, data)

    def _on_conn_close(self, conn):
        """Callback: Kết nối bị đóng."""
        print(f"Connection CLOSED: {conn.peer}")
        if conn.peer in self.connections:
            del self.connections[conn.peer]
        if self.on_conn_close_callback:
            self.on_conn_close_callback(conn.peer)

    def _on_conn_error(self, conn, err):
        """Callback: Lỗi trên một kết nối cụ thể."""
        print(f"Connection ERROR with {conn.peer}: {err}")
        # Clean up pending
        try:
            if conn in self.pending_connections:
                self.pending_connections.remove(conn)
        except ValueError:
            pass
        if self.on_conn_error_callback:
            self.on_conn_error_callback(conn.peer, err)
