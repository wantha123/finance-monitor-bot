
from typing import Dict, Optional
from datetime import datetime
from storage.supabase_client import log_event

class StateManager:
    def __init__(self):
        self.state: Dict[str, Optional[datetime]] = {
            "last_fetch": None,
            "last_analysis": None,
            "last_alert": None,
        }

    def update_state(self, key: str, timestamp: Optional[datetime] = None) -> None:
        if key in self.state:
            self.state[key] = timestamp or datetime.utcnow()
            log_event(f"State updated: {key} -> {self.state[key].isoformat()}")

    def get_state(self, key: str) -> Optional[datetime]:
        return self.state.get(key)

    def dump_state(self) -> Dict[str, Optional[datetime]]:
        return self.state.copy()
