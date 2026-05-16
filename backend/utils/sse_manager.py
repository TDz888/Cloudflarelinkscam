import queue
import threading
import json
import time
from core.database import Database

class SSEManager:
    _instance = None
    _queues = []
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, q):
        with cls._lock:
            cls._queues.append(q)

    @classmethod
    def unregister(cls, q):
        with cls._lock:
            if q in cls._queues:
                cls._queues.remove(q)

    @classmethod
    def emit(cls, event_type, data):
        """Phát sự kiện đến tất cả client và lưu vào DB."""
        # Lưu vào DB để replay (nếu có db instance)
        # Ở đây ta cần truy cập DB, có thể lấy từ config app sau.
        # Tạm thời bỏ qua, nhưng có thể lưu bằng cách gọi database từ bên ngoài.
        payload = {
            "type": event_type,
            "data": data,
            "timestamp": time.time()
        }
        with cls._lock:
            for q in cls._queues:
                try:
                    q.put_nowait(payload)
                except queue.Full:
                    pass
        # Lưu vào DB nếu có kết nối (sẽ được gọi từ ngoài)
        # Để đơn giản, ta có thể bỏ qua hoặc gọi callback
        if hasattr(cls, '_db'):
            cls._db.execute("INSERT INTO events (type, data) VALUES (?,?)",
                            (event_type, json.dumps(data)))
