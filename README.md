# Hệ Thống Chat P2P Phân Tán (Decentralized P2P Chat System)

Hệ thống nhắn tin thời gian thực hoạt động hoàn toàn trên kiến trúc **Phi tập trung (Decentralized)**, không phụ thuộc vào bất kỳ máy chủ trung gian nào. Dự án minh họa rõ nét các nguyên lý cốt lõi của **Hệ Phân Tán (Distributed Systems)** như Auto-Discovery (Tự động phát hiện), Direct Messaging (Giao tiếp trực tiếp) và Fault Tolerance (Khả năng chịu lỗi cơ bản).

---

## 🏗 Kiến Trúc Hệ Thống (Distributed Architecture)

He thống được xây dựng theo mô hình **Pure P2P (Mạng ngang hàng thuần túy)**. Mỗi node (người dùng) trong mạng đóng vai trò vừa là Client vừa là Server.

### 1. Cơ Chế Tự Động Phát Hiện (Auto-Discovery - UDP)
Thay vì sử dụng một máy chủ định danh (Directory Server) để lưu danh sách người dùng, hệ thống sử dụng giao thức **UDP Broadcast** để:
- **Quảng bá sự hiện diện:** Mỗi node định kỳ gửi gói tin `HELLO` chứa thông tin định danh (Username, IP, Port) tới địa chỉ Broadcast của mạng.
- **Lắng nghe mạng lưới:** Mỗi node mở một cổng UDP lắng nghe để cập nhật danh sách các peer đang hoạt động xung quanh mình (Local Peer Discovery).
- **Trạng thái (Liveness):** Nếu một peer ngừng gửi tín hiệu broadcast trong khoảng thời gian quy định (15s), hệ thống sẽ tự động đánh dấu peer đó là "Offline".

### 2. Giao Tiếp Trực Tiếp (Direct Communication - TCP)
Khi hai peer đã phát hiện ra nhau, quá trình trao đổi tin nhắn diễn ra **trực tiếp 1-1** thông qua kết nối **TCP Socket** tin cậy:
- Đảm bảo tính toàn vẹn của dữ liệu tin nhắn.
- Không có nút thắt cổ chai (bottleneck) hay điểm lỗi duy nhất (Single Point of Failure) như mô hình Client-Server truyền thống.

### 3. Chat Nhóm Phân Tán (Distributed Group Chat)
Chat nhóm được thực hiện bằng cơ chế **Flooding/Multicast** ở tầng ứng dụng (Application Layer Multicast):
- Người gửi thiết lập kết nối TCP tới *từng* peer trong danh sách hoạt động của mình để gửi tin nhắn.
- Không lưu trữ lịch sử chat tập trung, mỗi peer tự quản lý dữ liệu của riêng mình.

---

## 🚀 Tính Năng Nổi Bật

- **Zero-Configuration:** Không cần cài đặt server, chỉ cần kết nối cùng mạng LAN là thấy nhau.
- **Phân tán hoàn toàn:** Hệ thống vẫn hoạt động bình thường kể cả khi một số máy tính trong mạng bị ngắt kết nối.
- **Real-time UI:** Giao diện trực quan cập nhật danh sách Peer Online/Offline theo thời gian thực.
- **Hỗ trợ mô phỏng:** Tích hợp công cụ để chạy nhiều node ảo trên cùng một máy tính để kiểm thử kịch bản phân tán.

---

## 📂 Cấu Trúc Dự Án

```
├── core/
│   └── network_engine.py   # [Core] Bộ xử lý mạng (UDP Discovery & TCP Messaging)
├── ui/
│   ├── main_gui.py         # [Presentation] Giao diện Chat (CustomTkinter)
│   └── __init__.py
├── main.py                 # Entry point cho GUI App
├── main_cli.py             # Phiên bản dòng lệnh (CLI) để test server không giao diện
├── run_demo.py             # Script tự động chạy mô phỏng 3 node trên localhost
├── requirements.txt        # Các thư viện Python cần thiết
└── README.md               # Tài liệu hệ thống
```

---

## 🛠 Yêu Cầu & Cài Đặt

### Yêu cầu
- **Python 3.8+**
- Hệ điều hành: Windows, macOS, hoặc Linux.

### Cài đặt
1. Clone dự án:
   ```bash
   git clone <repo_url>
   cd p2p-chat-distributed-system
   ```

2. Tạo môi trường ảo (Khuyên dùng):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # macOS/Linux
   # venv\Scripts\activate   # Windows
   ```

3. Cài đặt thư viện phụ thuộc:
   ```bash
   pip install -r requirements.txt
   ```

---

## 📖 Hướng Dẫn Sử Dụng

### 1. Chạy trên môi trường thực (Nhiều máy tính trong LAN)
Chỉ cần chạy lệnh sau trên mỗi máy tính:
```bash
python main.py [PORT]
```
*(Mặc định Port là 6000 nếu không điền. Hệ thống sẽ tự tìm các máy khác trong LAN)*

### 2. Chạy mô phỏng trên 1 máy (Localhost Simulation)
Để kiểm tra tính phân tán ngay trên một máy tính duy nhất, bạn có thể sử dụng script demo. Script này sẽ thực hiện:
- Mở **3 cửa sổ ứng dụng** riêng biệt.
- Gán các port khác nhau (TCP: 6000, 6001, 6002).
- Giả lập môi trường mạng để các app tự tìm thấy nhau qua localhost.

Chạy lệnh:
```bash
python run_demo.py
```
*Lưu ý: Nhập Username khác nhau cho mỗi cửa sổ để dễ phân biệt.*

---

## 🔍 Kịch Bản Test (Testing Scenarios)

1. **Test Discovery:**
   - Mở App A và App B.
   - Quan sát danh sách Peer bên trái. App B sẽ xuất hiện trên App A và ngược lại trong vòng 5 giây.

2. **Test Messaging:**
   - App A click vào tên App B -> Gửi tin nhắn.
   - App B nhận tin nhắn tức thời.

3. **Test Fault Tolerance (Offline detection):**
   - Tắt App B đột ngột (hoặc ngắt mạng).
   - Quan sát App A: Sau khoảng 15 giây, trạng thái của User B sẽ chuyển sang chấm xám (Offline) hoặc biến mất.

4. **Test Group Chat:**
   - Chọn "All Peers (Group Chat)".
   - Gửi tin nhắn, tất cả các máy đang online đều sẽ nhận được.

---

## 👨‍💻 Tác Giả & Đóng Góp
Dự án được phát triển nhằm mục đích nghiên cứu mô hình Hệ Phân Tán. Mọi ý kiến đóng góp xin vui lòng tạo Pull Request hoặc Issue.
