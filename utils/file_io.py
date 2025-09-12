import uuid
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
except ImportError:
    # Fallback for Python < 3.9
    from datetime import timezone, timedelta
    class ZoneInfo:
        def __init__(self, name):
            if name == "Asia/Kolkata":
                self.offset = timedelta(hours=5, minutes=30)
            else:
                self.offset = timedelta(0)
        
        def __call__(self):
            return timezone(self.offset)


def generate_session_id(prefix: str = "session") -> str:
    try:
        ist = ZoneInfo("Asia/Kolkata")
        return f"{prefix}-{datetime.now(ist).strftime('%Y%m%d_%H%M%S')}-{uuid.uuid4().hex[:8]}"
    except:
        # Fallback to UTC if timezone handling fails
        return f"{prefix}-{datetime.now().strftime('%Y%m%d_%H%M%S')}-{uuid.uuid4().hex[:8]}"