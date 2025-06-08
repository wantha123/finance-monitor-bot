
import json
from typing import Dict, Optional
from storage.supabase_client import fetch_thresholds, update_threshold

class ConfigStore:
    def __init__(self):
        self.cache: Dict[str, Dict] = {}
        self.refresh_cache()

    def refresh_cache(self) -> None:
        self.cache.clear()
        data = fetch_thresholds()
        for item in data:
            symbol = item.get("symbol")
            thresholds = json.loads(item.get("thresholds", "{}")) if isinstance(item.get("thresholds"), str) else item.get("thresholds")
            if symbol and thresholds:
                self.cache[symbol] = thresholds

    def get_thresholds(self, symbol: str) -> Optional[Dict[str, float]]:
        return self.cache.get(symbol)

    def set_thresholds(self, symbol: str, thresholds: Dict[str, float]) -> bool:
        result = update_threshold(symbol, thresholds)
        if result:
            self.cache[symbol] = thresholds
            return True
        return False

    def list_all(self) -> Dict[str, Dict]:
        return self.cache.copy()
