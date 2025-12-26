# Hệ Thống Chat P2P Phân Tán (Decentralized P2P Chat System)

Dự án này là một minh chứng thực nghiệm cho các khái niệm nâng cao trong **Hệ Phân Tán (Distributed Systems)**. Hệ thống được thiết kế theo kiến trúc **Mạng Ngang Hàng Thuần Túy (Pure structured/unstructured Overlay Network)**, loại bỏ hoàn toàn sự phụ thuộc vào các thành phần tập trung (Central Authority).

---

## 🏛 Kiến Trúc & Nguyên Lý Phân Tán (Distributed Principles)

### 1. Đồng Hồ Lamport & Định Thứ Tự Nhân Quả (Causal Ordering)
Trong một hệ phân tán không có bộ đếm thời gian chung (Global Clock), việc xác định thứ tự của các biến cố (events) là một thách thức lớn. Hệ thống này sử dụng **Lamport Logical Clocks** để giải quyết vấn đề đó:
- **Nguyên lý:** Mỗi Node duy trì một biến điếm thời gian logic `L_i`.
- **Quy tắc Send:** Trước khi gửi tin nhắn, node tăng bộ đếm: `L_i = L_i + 1`. Tin nhắn gửi đi kèm theo nhãn thời gian `T_m = L_i`.
- **Quy tắc Receive:** Khi nhận tin nhắn có nhãn `T_m`, node cập nhật bộ đếm local: `L_i = max(L_i, T_m) + 1`.
- **Hệ quả:** Đảm bảo tính chất **Happened-before Relationship (->)**, giúp sắp xếp tin nhắn đúng thứ tự nhân quả ngay cả khi đồng hồ hệ thống của các máy bị lệch nhau.

### 2. Eventual Consistency & Membership Protocol
Quy trình phát hiện và duy trì danh sách thành viên (Group Membership) sử dụng giao thức dựa trên **Gossip/Broadcast**:
- **Discovery:** Sử dụng UDP Broadcasting như một cơ chế "Heartbeat" (nhịp tim).
- **Failure Detection:** Sử dụng chiến lược *Timeout-based failure detector*. Nếu một node im lặng quá ngưỡng $\Delta t$, hệ thống coi node đó đã rời mạng.
- **Eventual Consistency:** Dữ liệu về danh sách Peers không được đồng bộ tức thì (Strong Consistency) mà đạt trạng thái nhất quán cuối cùng (Eventual Consistency), chấp nhận độ trễ lan truyền thông tin để đổi lấy tính sẵn sàng (Availability) cao.

### 3. Kiến Trúc Không Trạng Thái Trung Tâm (Stateless Architecture)
- Mỗi Peer là một "Autonomous Agent" (Tác tử tự trị), vừa đóng vai trò Client (gửi request) vừa là Server (xử lý request).
- Trạng thái hội thoại (Conversation State) được lưu trữ phân tán cục bộ tại mỗi node (Local Storage), đảm bảo tính riêng tư và loại bỏ Single Point of Failure.

---

## 🚀 Tính Năng Kỹ Thuật (Technical Features)

- **Decentralized Auto-Discovery:** Tự động kiến tạo mạng lưới (Network Formation) không cần cấu hình thủ công (Zero-conf).
- **Logical Timestamping:** Tin nhắn được gán nhãn thời gian logic để xử lý xung đột thứ tự.
- **Concurrent Request Handling:** Sử dụng mô hình *Thread-per-connection* hoặc *Asynchronous I/O* để xử lý đồng thời hàng loạt kết nối TCP/UDP.
- **Fault Tolerance:** Hệ thống tự phục hồi trạng thái khi các node tham gia hoặc rời bỏ mạng ngẫu nhiên.

---

## 📂 Tổ Chức Source Code

Cấu trúc dự án tuân theo các pattern thiết kế phân lớp, tách biệt phần Core Networking (Logic phân tán) và Presentation Layer:

```
├── core/
│   └── network_engine.py   # [Kernel] Implementation của Lamport Clock, TCP Server/Client, UDP Broadcaster.
├── ui/
│   └── main_gui.py         # [Interface] Giao diện người dùng, visualize trạng thái mạng.
├── main.py                 # Entry Point.
├── run_demo.py             # Script mô phỏng Cluster nhiều node trên một máy vật lý.
└── README.md               # Tài liệu kỹ thuật.
```

---

## 🛠 Hướng Dẫn Vận Hành (Operation Guide)

### Yêu cầu tiên quyết
- Python 3.8+ (Khuyến nghị 3.10+ để tối ưu hiệu năng Threading).
- Môi trường mạng LAN hỗ trợ UDP Broadcast.

### Cài đặt
```bash
pip install -r requirements.txt
```

### Kịch bản chạy Mô Phỏng (Local Cluster Simulation)
Để kiểm chứng thuật toán Lamport Clock và cơ chế Discovery, bạn có thể khởi tạo một cụm (cluster) ảo gồm 3 nodes trên cùng máy tính:

```bash
python run_demo.py
```
*Script này sẽ khởi tạo 3 tiến trình độc lập, lắng nghe trên các cổng khác nhau (6000, 6001, 6002) và tự động thiết lập liên kết ngang hàng.*

### Kịch bản chạy Thực Tế (Deployment)
Trên mỗi máy trạm (Node), thực thi lệnh:
```bash
python main.py
```

---

## 🔬 Thực Nghiệm (Experimentation)

Để quan sát "Hiệu ứng Lamport", hãy thực hiện:
1. Mở 3 Node A, B, C.
2. Ngắt kết nối mạng của B tạm thời (hoặc làm chậm đồng hồ hệ thống của B).
3. A gửi tin nhắn cho B.
4. C gửi tin nhắn cho B sau A.
5. Quan sát tại B: Nhờ Lamport Clock, tin nhắn của A và C vẫn sẽ được sắp xếp đúng thứ tự nhân quả logic, bất chấp thời gian thực nhận được gói tin là khi nào.

---

## 👨‍💻 Tác Giả & Nghiên Cứu
Dự án được xây dựng nhằm mục đích nghiên cứu học thuật về Hệ Phân Tán và Lập trình Socket nâng cao.
