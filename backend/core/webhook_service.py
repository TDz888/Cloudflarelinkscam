import requests
import threading
from core.database import Database
from utils.sse_manager import SSEManager

class WebhookService:
    def __init__(self, db: Database):
        self.db = db

    def send_all(self, data: dict):
        """Gửi đến tất cả webhook đang active."""
        webhooks = self.db.fetchall("SELECT * FROM webhooks WHERE active=1")
        for wh in webhooks:
            threading.Thread(target=self._send_one, args=(wh, data), daemon=True).start()

    def _send_one(self, webhook: dict, data: dict):
        platform = webhook['platform']
        url = webhook['url']
        try:
            if platform == 'discord':
                self._send_discord(url, data)
            elif platform == 'telegram':
                self._send_telegram(url, data)
            # Có thể thêm các platform khác
            # Cập nhật last_sent_at, reset error_count
            self.db.execute(
                "UPDATE webhooks SET last_sent_at=CURRENT_TIMESTAMP, error_count=0 WHERE id=?",
                (webhook['id'],)
            )
        except Exception as e:
            # Tăng error_count
            new_err = webhook['error_count'] + 1
            self.db.execute("UPDATE webhooks SET error_count=? WHERE id=?", (new_err, webhook['id']))
            if new_err >= webhook['max_errors']:
                self.db.execute("UPDATE webhooks SET active=0 WHERE id=?", (webhook['id'],))
                SSEManager.emit('webhook_error', {
                    'platform': platform,
                    'url': url,
                    'error': f'Disabled after {new_err} errors'
                })

    def _send_discord(self, url, data):
        embed = {
            "title": "📍 Vị trí mới",
            "color": 0xCA8A04,
            "fields": [
                {"name": "Vĩ độ", "value": str(data.get('lat','')), "inline": True},
                {"name": "Kinh độ", "value": str(data.get('lng','')), "inline": True},
                {"name": "Độ chính xác", "value": f"{data.get('accuracy','')}m", "inline": True},
                {"name": "User-Agent", "value": data.get('ua','')[:256]},
            ],
            "footer": {"text": data.get('ts','')}
        }
        requests.post(url, json={"embeds":[embed]}, timeout=5)

    def _send_telegram(self, url, data):
        # Telegram Bot API
        message = f"📍 Vị trí mới: {data.get('lat')}, {data.get('lng')}\nĐộ chính xác: {data.get('accuracy')}m\nUser-Agent: {data.get('ua','')[:100]}"
        requests.post(url, json={
            "chat_id": self._extract_chat_id(url),
            "text": message
        }, timeout=5)

    def _extract_chat_id(self, url):
        # Giả định URL dạng https://api.telegram.org/bot<token>/sendMessage?chat_id=...
        if 'chat_id=' in url:
            return url.split('chat_id=')[-1]
        return ''
