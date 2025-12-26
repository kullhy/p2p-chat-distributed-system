# Kiến Trúc Hệ Thống P2P Chat

## 1. Tổng Quan
Hệ thống chat P2P (Peer-to-Peer) hoạt động dựa trên mô hình phi tập trung, không sử dụng server trung gian. Các node (máy người dùng) tự động phát hiện nhau trong mạng LAN và thiết lập kết nối trực tiếp để trao đổi tin nhắn.

## 2. Các Thành Phần Chính

### A. Lớp Discovery (UDP)
- **Giao thức:** UDP (User Datagram Protocol)
- **Cổng:** 5005
- **Chức năng:**
  - **Broadcast:** Mỗi node định kỳ (5s) gửi gói tin "HELLO" tới địa chỉ broadcast `255.255.255.255`.
  - **Listen:** Mỗi node lắng nghe cổng 5005 để nhận thông báo từ các node khác.
  - **Cập nhật danh sách:** Duy trì `peers` dictionary chứa thông tin IP, Username, Port và Timestamp.

### B. Lớp Transport (TCP)
- **Giao thức:** TCP (Transmission Control Protocol)
- **Cổng:** 5000 (Mặc định)
- **Chức năng:**
  - **Reliable Messaging:** Đảm bảo tin nhắn chat được gửi tin cậy, đúng thứ tự.
  - **Kết nối:** Khi người dùng gửi tin nhắn, một socket TCP được tạo để kết nối tới IP đích, gửi dữ liệu JSON và đóng kết nối ngay sau đó (Short-lived connection).

## 3. Luồng Dữ Liệu

1. **Khởi động:**
   - Người dùng nhập tên.
   - Ứng dụng khởi tạo 3 luồng: UDP Broadcast, UDP Listener, TCP Listener.

2. **Phát hiện:**
   - Node A gửi UDP Broadcast -> Node B nhận được.
   - Node B thêm A vào danh sách Peer -> Node B hiển thị A trên UI.

3. **Gửi tin nhắn:**
   - Node A chọn Node B trên UI -> Nhập tin nhắn -> "Send".
   - Node A kết nối TCP tới IP của Node B (Port 5000).
   - Node A gửi JSON chứa tin chat.
   - Node B nhận, parse JSON, hiển thị lên khung chat.

## 4. Cấu Trúc Gói Tin JSON

**Dạng Hello (UDP):**
```json
{
  "type": "HELLO",
  "user": "NguyenVanA",
  "port": 5000
}
```

**Dạng Chat (TCP):**
```json
{
  "type": "CHAT",
  "sender": "NguyenVanA",
  "content": "Xin chao!",
  "timestamp": 1700000000.0,
  "source_ip": "192.168.1.5" (Added by receiver)
}
```

## 5. Xử Lý Đa Luồng (Concurrency)
Hệ thống sử dụng thư viện `threading` của Python để đảm bảo giao diện (UI) không bị treo khi mạng xử lý chậm.
- **Main Thread:** Vẽ UI (CustomTkinter) và xử lý sự kiện người dùng.
- **Network Threads (Daemon):** Chạy ngầm việc gửi/nhận gói tin mạng và cập nhật trạng thái peer.
