import os
import random
from typing import List, Optional
from core.database import Database
from config import TEMPLATES_DIR

class TemplateService:
    def __init__(self, db: Database):
        self.db = db
        self.sync_files()   # Đồng bộ DB với thư mục

    def sync_files(self):
        """Đồng bộ file .html trong thư mục với DB."""
        existing_files = [f for f in os.listdir(TEMPLATES_DIR) if f.endswith('.html')]
        db_files = self.db.fetchall("SELECT name, filename FROM templates")
        db_names = {row['filename'] for row in db_files}

        for fname in existing_files:
            if fname not in db_names:
                # Thêm vào DB với active mặc định
                self.db.execute(
                    "INSERT INTO templates (name, title, filename, active) VALUES (?,?,?,1)",
                    (fname.replace('.html',''), fname.replace('.html',''), fname)
                )

    def get_active_templates(self) -> List[dict]:
        rows = self.db.fetchall("SELECT * FROM templates WHERE active=1")
        return [dict(r) for r in rows]

    def get_random_template(self) -> Optional[str]:
        """Chọn ngẫu nhiên một template theo trọng số conversion_rate."""
        active = self.get_active_templates()
        if not active:
            return None
        # Weighted random: ưu tiên template có conversion_rate cao
        weights = []
        for t in active:
            # conversion_rate từ 0-100, thêm 1 để tránh weight 0
            w = max(1, t['conversion_rate'])
            weights.append(w)
        chosen = random.choices(active, weights=weights, k=1)[0]
        # Tăng use_count
        self.db.execute("UPDATE templates SET use_count = use_count + 1 WHERE id=?", (chosen['id'],))
        return chosen['filename']

    def update_success(self, template_name: str):
        """Tăng success_count và tính lại conversion_rate."""
        self.db.execute(
            "UPDATE templates SET success_count = success_count + 1 WHERE filename=?",
            (template_name,)
        )
        # Cập nhật conversion_rate
        row = self.db.fetchone(
            "SELECT use_count, success_count FROM templates WHERE filename=?",
            (template_name,)
        )
        if row and row['use_count'] > 0:
            rate = (row['success_count'] / row['use_count']) * 100
            self.db.execute("UPDATE templates SET conversion_rate=? WHERE filename=?", (rate, template_name))

    def toggle_active(self, template_id: int) -> bool:
        row = self.db.fetchone("SELECT active FROM templates WHERE id=?", (template_id,))
        if not row:
            return False
        new_state = 0 if row['active'] else 1
        self.db.execute("UPDATE templates SET active=? WHERE id=?", (new_state, template_id))
        return True
