<!-- Bắt đầu khung copy -->
# ⚔️ GPS Tunnel Admin – Quest Edition

<div align="center">

![Version](https://img.shields.io/badge/Phiên_bản-2.0.0-vàng?style=flat-square&logo=undertale)
![Python](https://img.shields.io/badge/Python-3.8+-lam?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-đỏ?style=flat-square&logo=flask)
![SQLite](https://img.shields.io/badge/SQLite-3-xám?style=flat-square&logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-xanh?style=flat-square)

**Quản lý hàng loạt Cloudflare Tunnel • Thu thập vị trí GPS • Giao diện RPG giả tưởng**  
*Mượt mà – Chuyên nghiệp – Tự động hoá hoàn toàn*

</div>

---

## 📜 Giới thiệu

**GPS Tunnel Admin – Quest Edition** là công cụ tự động hoá việc tạo và quản lý các **Cloudflare Tunnel** (trycloudflare.com) phục vụ cho mục đích kiểm thử bảo mật, nghiên cứu hành vi người dùng và đào tạo an ninh mạng.

Hệ thống bao gồm:
- 🧠 **Backend mạnh mẽ** viết bằng Python/Flask, quản lý tunnel qua SQLite, hỗ trợ SSE real-time.
- 🎨 **Dashboard trực quan** theo phong cách Red Broadcast Dark Theme, cập nhật không giật lag.
- 🎣 **10+ mẫu phishing** (Quest UI) mang chủ đề RPG giả tưởng, tăng tỉ lệ tương tác.

> ⚠️ **Tuyên bố từ chối trách nhiệm:** Dự án chỉ dành cho mục đích giáo dục và kiểm thử an ninh hợp pháp. Tác giả không chịu trách nhiệm cho bất kỳ hành vi sử dụng sai mục đích nào.

---

## ✨ Tính năng chính

### 🔗 Quản lý Cloudflare Tunnel
- **Tạo nhiều tunnel cùng lúc** chỉ với một click.
- **Giám sát thời gian thực**: trạng thái running/error/stopped.
- **Auto-restart** khi tunnel gặp sự cố.
- **Tự động dừng** sau thời gian chỉ định (auto-stop).
- **Tối ưu tài nguyên** – mọi tunnel dùng chung một phishing server.

### 🎯 Thu thập vị trí GPS
- Nhận tọa độ thông qua **Geolocation API** của trình duyệt.
- Lọc vị trí ảo, trùng lặp.
- Ghi dữ liệu vào **SQLite + file log**.
- Gửi thông báo qua **Discord/Telegram webhook**.
- Hiển thị marker trên **bản đồ Leaflet** trực tiếp trong dashboard.

### 📜 Template Phishing (Quest UI)
- 10 mẫu giao diện RPG: **Nhận Thánh Kiếm**, **Kho Báu Rồng**, **Ngân Khố Vương Quốc**,…
- CSS riêng với **Cinzel & Spectral** font, hiệu ứng ánh vàng glow.
- Đếm ngược thời gian tạo áp lực.
- **Xoay vòng thông minh** dựa trên tỉ lệ chuyển đổi (conversion rate).
- Upload template mới qua dashboard.

### 🖥️ Dashboard Admin
- Giao diện **Single Page App**, 4 tab chính: Tổng quan, Tunnel, Nạn nhân, Templates, Cài đặt.
- Cập nhật **real-time qua SSE**.
- Responsive, dark theme.
- Tích hợp **QR Code** cho từng link.
- **Sao chép link** 1 click.
- **Xuất dữ liệu** nạn nhân.

---

## 🏗️ Kiến trúc hệ thống
┌─────────────────────────────────────────────────────────┐
│ GPS TUNNEL ADMIN v2.0 │
├─────────────────────────────────────────────────────────┤
│ [Trình duyệt] ──► Admin Server (port 4467) │
│ [Nạn nhân] ──► Phishing Server (port ngẫu nhiên) │
│ │ │
│ ┌──────────────────────┴───────────────────────────┐ │
│ │ SERVICE LAYER │ │
│ ├────────────┬──────────┬──────────┬───────────────┤ │
│ │ Tunnel │ Victim │ Template │ Webhook │ │
│ │ Manager │ Service │ Service │ Service │ │
│ └────────────┴──────────┴──────────┴───────────────┘ │
│ │ │
│ ┌──────────────────────┴───────────────────────────┐ │
│ │ DATA LAYER │ │
│ ├────────────┬──────────┬──────────┬───────────────┤ │
│ │ SQLite │ File Log │ SSE Queue│ Cloudflared │ │
│ └────────────┴──────────┴──────────┴───────────────┘ │
└─────────────────────────────────────────────────────────┘

**Luồng hoạt động chính:**
1. Admin tạo tunnel qua dashboard → Backend gọi `cloudflared` → Sinh link `*.trycloudflare.com`.
2. Nạn nhân click link → Phishing server phục vụ template Quest → Yêu cầu định vị.
3. Nạn nhân đồng ý → JavaScript gửi GPS về `/location` → Lưu vào database + log.
4. Backend gửi SSE sự kiện → Dashboard cập nhật bảng, bản đồ ngay lập tức.

---

## 🧰 Công nghệ sử dụng

| Thành phần | Công nghệ |
|------------|-----------|
| Backend | Python 3.8+, Flask, SQLite |
| Realtime | Server-Sent Events (SSE) |
| Tunnel | Cloudflare Tunnel (`cloudflared`) |
| Quét vị trí | HTML5 Geolocation API |
| Bản đồ | Leaflet.js |
| Giao diện | Vanilla JS, CSS3, Red Broadcast Dark Theme |
| Font | Roboto, Roboto Mono (Admin) / Cinzel, Spectral (Phishing) |
| Webhook | Discord, Telegram |
| Mã QR | `qrcode` + `Pillow` |

---

## 📁 Cấu trúc dự án
gps_tunnel_admin/
│
├── run.py # Khởi động chỉ 1 lệnh
├── backend/
│ ├── app.py # Entry point
│ ├── config.py # Cấu hình hệ thống
│ ├── core/ # Tầng dịch vụ
│ │ ├── database.py # Kết nối SQLite
│ │ ├── tunnel_service.py # Quản lý tunnel
│ │ ├── victim_service.py # Xử lý nạn nhân
│ │ ├── template_service.py # Quản lý template phishing
│ │ ├── webhook_service.py # Gửi thông báo đa kênh
│ │ ├── config_service.py # Cấu hình runtime
│ │ └── scheduler_service.py # Tác vụ định kỳ
│ ├── servers/ # Flask Blueprint
│ │ ├── admin_server.py # Dashboard API + giao diện
│ │ └── phishing_server.py # Phục vụ trang phishing
│ └── utils/
│ ├── sse_manager.py # Quản lý SSE tập trung
│ ├── cloudflared.py # Tự động tải cloudflared
│ ├── qr_code.py # Tạo QR code
│ └── fingerprint.py # Fingerprint JS
│
├── frontend/ # Dashboard giao diện
│ ├── index.html
│ ├── css/
│ │ └── style.css
│ └── js/
│ └── app.js
│
├── phishing_templates/ # Các template Quest (tự sinh)
├── downloads/ # Chứa binary cloudflared
└── data/ # SQLite DB + logs

---

## 🚀 Cài đặt & Chạy

### Yêu cầu hệ thống
- **OS**: Linux (Ubuntu 20.04+ khuyên dùng)
- **Python**: 3.8 trở lên
- **Kết nối Internet** để tải `cloudflared` và tạo tunnel

### Các bước cài đặt


# 1. Clone hoặc tải mã nguồn
git clone https://github.com/your-repo/gps-tunnel-admin.git
cd gps_tunnel_admin

# 2. Cài đặt thư viện
pip install -r backend/requirements.txt

# 3. (Tuỳ chọn) Cấu hình webhook Discord trong file backend/config.py
# DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/..."

# 4. Chạy hệ thống
python run.py
Dashboard sẽ tự động mở tại địa chỉ: http://127.0.0.1:4467

Chạy ngầm với nohup
bash
nohup python run.py > output.log 2>&1 &
⚙️ Cấu hình
Mở file backend/config.py để tuỳ chỉnh:

python
ADMIN_PORT = 4467              # Cổng dashboard
PHISHING_PORT = 0              # 0 = tự động chọn cổng trống
MAX_TUNNELS = 20               # Giới hạn số tunnel đồng thời
TUNNEL_AUTO_STOP_MINUTES = 0   # 0 = không giới hạn thời gian
DISCORD_WEBHOOK_URL = ""       # Webhook Discord
Các cài đặt khác có thể được thay đổi trực tiếp trong Tab Settings của dashboard mà không cần sửa file.

📡 API Reference (dành cho admin)
Endpoint	Method	Mô tả
/api/tunnels	GET	Lấy danh sách tunnel
/api/tunnels	POST	Tạo tunnel mới {quantity, auto_stop_minutes, template_id}
/api/tunnels/<id>	DELETE	Dừng tunnel
/api/tunnels	DELETE	Dừng tất cả tunnel
/api/tunnels/<id>/restart	POST	Khởi động lại tunnel
/api/victims	GET	Danh sách nạn nhân (giới hạn 100)
/api/victims/stats	GET	Thống kê nạn nhân (tổng, hôm nay)
/api/templates	GET	Danh sách template phishing
/api/templates/upload	POST	Upload template mới (multipart)
/api/templates/<id>/toggle	POST	Bật/tắt template
/api/qr	POST	Tạo mã QR {url} → base64 PNG
/api/settings	GET/POST	Đọc/ghi cấu hình
/stream	GET	SSE endpoint (real-time)
Tất cả phản hồi đều tuân theo format:

json
{
  "success": true/false,
  "data": ...,
  "error": "thông báo lỗi" // nếu thất bại
}
🖼️ Ảnh chụp màn hình (Dashboard)
Dưới đây là một số ảnh minh hoạ giao diện. Vui lòng thay thế bằng ảnh thực tế của bạn.

<div align="center"> <img src="screenshots/dashboard_overview.png" width="45%" alt="Tab Tổng quan"/> <img src="screenshots/dashboard_tunnels.png" width="45%" alt="Tab Quản lý Tunnel"/> </div><div align="center"> <img src="screenshots/dashboard_victims.png" width="45%" alt="Tab Nạn nhân với bản đồ"/> <img src="screenshots/phishing_quest_sample.png" width="45%" alt="Mẫu phishing Quest"/> </div>
❓ Câu hỏi thường gặp (FAQ)
1. Tool có hoạt động trên Windows/macOS không?
Backend Python hoàn toàn có thể chạy trên Windows/macOS nếu bạn tải đúng binary cloudflared. Tuy nhiên, hướng dẫn và file cấu hình được tối ưu cho Linux/Ubuntu.

2. Làm sao để dừng tất cả tunnel?
Trong dashboard: bấm nút "Dừng tất cả" hoặc gọi API DELETE /api/tunnels. Khi tắt chương trình, graceful shutdown sẽ tự động dừng tất cả.

3. Tại sao không lấy được vị trí?
Trình duyệt của nạn nhân phải hỗ trợ Geolocation API (hầu hết đều có).

Nạn nhân phải cho phép chia sẻ vị trí.

Một số trình duyệt yêu cầu HTTPS; link trycloudflare.com đã có HTTPS.

4. Làm sao để thêm template phishing mới?
Truy cập tab "Templates" → bấm "Upload Template Mới", chọn file .html có chứa nút id="locBtn" và script gọi /location. Hệ thống sẽ tự động đồng bộ.

5. Tôi có thể thay đổi giao diện dashboard không?
Có, sửa file CSS trong frontend/css/style.css và HTML trong frontend/index.html.

🧭 Lộ trình phát triển (Roadmap)
Quản lý tunnel qua SQLite

SSE real-time cập nhật dashboard

10 template Quest UI

Webhook Discord & Telegram

Bản đồ Leaflet trong dashboard

Graceful shutdown

Hỗ trợ nhiều phishing server (nhiều cổng)

Xác thực người dùng (login)

Xuất báo cáo PDF/Excel

Tích hợp rút gọn link (Bitly)

Docker hoá dự án

🤝 Đóng góp
Mọi đóng góp đều được hoan nghênh! Vui lòng tạo Issue hoặc gửi Pull Request.

Fork dự án

Tạo nhánh tính năng (git checkout -b feat/ten-tinh-nang)

Commit thay đổi (git commit -m 'Thêm tính năng X')

Push lên nhánh (git push origin feat/ten-tinh-nang)

Mở Pull Request

📝 Giấy phép
Dự án được phân phối theo giấy phép MIT. Xem file LICENSE để biết thêm chi tiết.

⚠️ Tuyên bố miễn trừ trách nhiệm
Công cụ này được tạo ra chỉ nhằm mục đích giáo dục, kiểm thử bảo mật hợp pháp và nghiên cứu.
Người dùng phải tuân thủ luật pháp địa phương và chỉ sử dụng trên hệ thống mà mình có quyền kiểm tra.
Tác giả không chịu bất kỳ trách nhiệm pháp lý nào phát sinh từ việc sử dụng sai mục đích.

<div align="center">
By Janus & Tesavek⚡️👾



