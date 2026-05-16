from core.database import Database

class ConfigService:
    def __init__(self, db: Database):
        self.db = db

    def get(self, key: str, default=None):
        row = self.db.fetchone("SELECT value FROM config WHERE key=?", (key,))
        return row['value'] if row else default

    def set(self, key: str, value: str):
        self.db.execute(
            "INSERT INTO config (key, value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=?, updated_at=CURRENT_TIMESTAMP",
            (key, value, value)
        )

    def get_all(self) -> dict:
        rows = self.db.fetchall("SELECT * FROM config")
        return {r['key']: r['value'] for r in rows}
