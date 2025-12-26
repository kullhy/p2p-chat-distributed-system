# Hướng Dẫn Chạy Demo P2P Chat

## Yêu Cầu
- Python 3.8+
- Các thư viện: `customtkinter`, `pillow`

## Cài Đặt
Chạy lệnh sau tại thư mục gốc của dự án:
```bash
pip install -r requirements.txt
```

## Chạy Ứng Dụng
Để kiểm thử tính năng P2P, bạn cần ít nhất 2 máy tính (hoặc 2 cửa sổ terminal trên cùng máy tính, tuy nhiên cùng máy tính sẽ bị trùng Port nếu không cấu hình kỹ, tốt nhất là 2 máy mạng LAN).

Chạy lệnh:
```bash
python main.py
```

## Kịch Bản Demo (Cho Báo Cáo)
1. **Khởi động:**
   - Mở App trên Máy 1, nhập tên "Alice".
   - Mở App trên Máy 2, nhập tên "Bob".

2. **Kiểm tra Auto-Discovery:**
   - Quan sát danh sách "Discovered Peers".
   - Máy 1 sẽ thấy "Bob (IP...)".
   - Máy 2 sẽ thấy "Alice (IP...)".

3. **Kiểm tra Chat:**
   - Trên Máy 1, click vào tên "Bob".
   - Gửi tin nhắn: "Chào Bob, kết nối ổn không?".
   - Máy 2 nhận tin nhắn ngay lập tức.
   - Máy 2 trả lời: "Ổn áp lắm Alice!".

4. **Kiểm tra Offline:**
   - Tắt ứng dụng trên Máy 2.
   - Chờ khoảng 15 giây.
   - Quan sát trên Máy 1: Thẻ tên "Bob" sẽ chuyển trạng thái (dấu chấm màu xám hoặc biến mất/hiển thị Offline tuỳ logic).

## Lưu Ý Firewall
- Nếu chạy trên Windows, lần đầu chạy App sẽ hỏi quyền truy cập mạng (Firewall). Hãy chọn **Allow Access** cho cả Private và Public Network.
- Đảm bảo 2 máy ping thấy nhau.
