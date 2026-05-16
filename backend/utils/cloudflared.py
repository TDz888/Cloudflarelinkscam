import os
import sys
from config import CLOUDFLARED_PATH

def ensure_cloudflared():
    if os.path.exists(CLOUDFLARED_PATH):
        return
    print("[*] Đang tải cloudflared cho Linux...")
    os.makedirs(os.path.dirname(CLOUDFLARED_PATH), exist_ok=True)
    import urllib.request
    url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
    try:
        urllib.request.urlretrieve(url, CLOUDFLARED_PATH)
        os.chmod(CLOUDFLARED_PATH, 0o755)
        print("[✓] Đã tải cloudflared.")
    except Exception as e:
        print(f"[!] Lỗi tải cloudflared: {e}")
        sys.exit(1)
