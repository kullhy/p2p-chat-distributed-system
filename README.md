# P2P Chat Distributed System

Hệ thống chat phân tán (Decentralized Peer-to-Peer Chat) sử dụng Python và CustomTkinter. 
Dự án được thiết kế cho môn học Hệ Phân Tán / Lập trình Mạng, minh hoạ cơ chế Auto-Discovery và Direct TCP Messaging.

## Tính Năng
- **Phân tán hoàn toàn:** Không cần server trung tâm.
- **Tự động phát hiện (Auto-Discovery):** Tìm kiếm người dùng trong mạng LAN qua UDP Broadcast.
- **Chat riêng tư:** Gửi tin nhắn trực tiếp qua giao thức TCP tin cậy.
- **Giao diện hiện đại:** UI đẹp mắt với chế độ Dark Mode, danh sách Peer động.
- **Logs hệ thống:** Theo dõi trực quan quá trình gửi/nhận gói tin.

## Cấu Trúc Dự Án
```
/P2P-Chat-Distributed
├── core/
│   └── network_engine.py   # Xử lý Logic mạng (UDP/TCP/Threading)
├── ui/
│   └── main_gui.py         # Giao diện người dùng (CustomTkinter)
├── docs/                   # Tài liệu báo cáo
├── main.py                 # File chạy chính
└── requirements.txt        # Thư viện phụ thuộc
```

## Cài đặt và Chạy
Cài đặt thư viện:
```bash
pip install -r requirements.txt
```

Chạy ứng dụng:
```bash
python main.py
```
Xem chi tiết hướng dẫn tại `docs/huong_dan_chay_demo.md`.
