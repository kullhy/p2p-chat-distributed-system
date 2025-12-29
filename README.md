# HTTT2025 - Python Distributed Chat System
*(Serverless Web-based Peer-to-Peer Communication Network)*

![Status](https://img.shields.io/badge/Status-Active-success)
![Tech](https://img.shields.io/badge/Core-Python%20(PyScript)-blue)
![Network](https://img.shields.io/badge/Network-WebRTC%20P2P-orange)

## 📖 Giới Thiệu
**HTTT2025** là hệ thống nhắn tin phân tán hoạt động hoàn toàn trên trình duyệt web, sử dụng ngôn ngữ **Python** làm nòng cốt (thay vì JavaScript truyền thống) thông qua công nghệ **PyScript/WebAssembly**. 

Hệ thống loại bỏ nhu cầu về Backend Server lưu trữ tin nhắn, đảm bảo tính riêng tư và khả năng hoạt động độc lập của mạng lưới người dùng.

## Báo cáo

[Báo cáo](https://docs.google.com/document/d/1IQNeMO1t5NolPEdehrXDW6q79oNTa87qrR96NHm95Hs/edit?usp=sharing)

---

## 🏗 Kiến Trúc Hệ Thống (Architecture)

Hệ thống sử dụng mô hình **Hybrid P2P (P2P Lai)** kết hợp giữa tính hiệu quả của quản lý tập trung (cho việc tìm kiếm) và tính bảo mật của phân tán (cho việc nhắn tin).

### 1. Phân Tầng Module (Modular Design)
Codebase được chia thành 4 tầng riêng biệt để đảm bảo chuẩn thiết kế phần mềm:

*   **Tầng 1: Transport Layer (`base_p2p.py`)**
    *   Chịu trách nhiệm thiết lập kết nối vật lý qua **WebRTC Data Channels**.
    *   Xử lý vấn đề "Garbage Collection" của Python trong môi trường Browser.
    *   Đóng gói/Giải nén dữ liệu JSON an toàn.
*   **Tầng 2: Global Service (`global_chat.py`)**
    *   Thực hiện thuật toán **Leader Election** (Bầu chọn Host).
    *   Quản lý danh sách người dùng Online (Membership Management) theo mô hình **Star Topology**.
    *   Cơ chế Broadcast tin nhắn toàn mạng.
*   **Tầng 3: Private Service (`private_chat.py`)**
    *   Thực hiện kết nối **Direct Mesh Topology** giữa 2 người dùng.
    *   Tin nhắn đi trực tiếp: `User A` -> `Internet` -> `User B` (Không qua Host).
*   **Tầng 4: Presentation (`ui.py` & `main.py`)**
    *   Quản lý DOM, Sự kiện người dùng và điều phối luồng dữ liệu giữa các tầng dưới.

### 2. Quy Trình Hoạt Động (Workflow)

#### A. Khởi tạo & Bầu chọn (Discovery Phase)
Hệ thống sử dụng cơ chế **"First-Come, First-Served Leader Election"**:
1.  Người dùng (Node) khởi động.
2.  Cố gắng đăng ký ID tài nguyên chung: `LOBBY_MASTER`.
3.  **Nếu thành công:** Tuyên bố là **HOST** (Leader).
4.  **Nếu thất bại (ID đã tồn tại):** Tự chuyển thành **CLIENT** (Follower) và kết nối tới `LOBBY_MASTER`.

#### B. Đồng bộ Danh sách (Synchronization)
*   **Event-based Consistency:** Khi có Client mới kết nối, Host cập nhật danh sách nội bộ và gửi gói tin `USER_LIST_UPDATE` (Broadcast) tới toàn bộ mạng lưới.
*   **Heartbeat:** Host giám sát các kết nối. Nếu Client mất kết nối (tắt tab), Host loại bỏ khỏi danh sách và thông báo cho mạng lưới.

---

## 🛠 Công Nghệ Sử Dụng

| Thành Phần | Công Nghệ | Vai Trò |
| :--- | :--- | :--- |
| **Runtime** | **PyScript (Pyodide)** | Chạy trình thông dịch Python 3.11 ngay trên trình duyệt (WASM). |
| **Networking** | **WebRTC** | Giao thức truyền tải dữ liệu P2P thời gian thực, độ trễ thấp. |
| **Signaling** | **PeerJS Cloud** | Máy chủ trung gian giúp các Peers tìm thấy IP của nhau (Handshake). |
| **UI Framework** | HTML5 / CSS3 | Giao diện Cyberpunk/Dark mode hiện đại. |

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy

### Cách 1: Chạy Online (Khuyên dùng)
Truy cập đường dẫn Vercel của dự án:
> `https://[your-project].vercel.app`

### Tạo “phiên của bạn” để máy khác không tự làm Host (Khuyên dùng)

Mặc định dự án dùng 1 `LOBBY_ID` chung nên ai vào trước sẽ làm Host. Để **máy khác join đúng phiên của bạn**, hãy dùng `room`:

- Mở trên máy bạn (Host):
  - `https://[your-project].vercel.app/?room=my_room_123`
- Gửi đúng link đó cho người khác mở (Client).

## 🧠 Lưu ý quan trọng khi test “khác mạng không connect”

Hệ thống dùng **WebRTC DataChannel**, nên sau khi “gặp nhau” qua **PeerJS Cloud (signaling)**, 2 máy vẫn phải vượt qua **NAT/Firewall** để tạo kênh P2P.

- **Nếu chỉ có STUN**: nhiều mạng (4G/5G, công ty, NAT đối xứng…) sẽ **không bắt tay được**, nên bạn sẽ thấy “không connect vào phiên host”.
- **Cách xử lý chuẩn**: thêm **TURN server** để relay khi P2P trực tiếp fail.

Dự án đã được bổ sung cấu hình TURN fallback trong `web_python/main.py` (ICE servers). Khi gặp lỗi, UI sẽ hiện toast kiểu “Conn error …” để bạn biết đang fail ở tầng kết nối.

### Cách 2: Chạy Local (Phát triển)
Yêu cầu: Python 3.x đã cài đặt.

1.  Clone repository:
    ```bash
    git clone https://github.com/kullhy/p2p-chat-distributed-system.git
    cd nexus-p2p
    ```
2.  Khởi động HTTP Server cục bộ:
    ```bash
    python3 -m http.server 8080
    ```
3.  Mở trình duyệt:
    *   Tab 1 (Làm Host): `http://localhost:8080/`
    *   Tab 2 (Làm Client): `http://localhost:8080/` (Mở incognito/ẩn danh hoặc trình duyệt khác để test tốt nhất).

---

## 🧩 Phân Tích Tính Phân Tán

1.  **Fault Tolerance (Chịu lỗi):**
    *   Nếu **Client** sập: Không ảnh hưởng đến hệ thống. Host sẽ xóa Client đó sau khi phát hiện ngắt kết nối.
    *   Nếu **Host** sập: Global Chat tạm ngừng. Tuy nhiên, các cặp **Private Chat** đang kết nối vẫn hoạt động bình thường (Partition Tolerance).

2.  **Scalability (Mở rộng):**
    *   Hệ thống hoạt động tốt nhất với nhóm < 50 người (do giới hạn băng thông của Browser Host).
    *   Mô hình Private Chat có khả năng mở rộng không giới hạn (do là kết nối trực tiếp).

