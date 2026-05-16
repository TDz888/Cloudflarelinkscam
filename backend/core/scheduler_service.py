from apscheduler.schedulers.background import BackgroundScheduler
from core.tunnel_service import TunnelService
from core.database import Database

class SchedulerService:
    def __init__(self, tunnel_service: TunnelService, db: Database):
        self.scheduler = BackgroundScheduler()
        self.tunnel_service = tunnel_service
        self.db = db
        self._add_jobs()

    def _add_jobs(self):
        # Kiểm tra sức khỏe tunnel mỗi 5 giây
        self.scheduler.add_job(self.tunnel_service.cleanup_expired, 'interval', seconds=5)
        # Dọn tunnel hết hạn mỗi 60 giây
        self.scheduler.add_job(self.tunnel_service.cleanup_expired, 'interval', seconds=60)
        # Dọn events cũ
        self.scheduler.add_job(self._cleanup_events, 'interval', hours=1)

    def _cleanup_events(self):
        # Xóa events quá TTL
        self.db.execute(
            "DELETE FROM events WHERE created_at < datetime('now', '-1 hour')"
        )

    def start(self):
        self.scheduler.start()

    def shutdown(self):
        self.scheduler.shutdown(wait=False)
