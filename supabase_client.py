
import os
import json
from supabase import create_client, Client
from typing import List, Dict, Any
from datetime import datetime

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Les variables d'environnement SUPABASE_URL et SUPABASE_KEY doivent être définies.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def insert_price_history(data: Dict[str, Any]) -> Dict:
    response = supabase.table("price_history").insert(data).execute()
    return response.data

def fetch_alerts_sent(limit: int = 100) -> List[Dict]:
    response = supabase.table("alerts_sent").select("*").order("timestamp", desc=True).limit(limit).execute()
    return response.data

def insert_alert(alert_data: Dict[str, Any]) -> Dict:
    response = supabase.table("alerts_sent").insert(alert_data).execute()
    return response.data

def update_threshold(symbol: str, new_thresholds: Dict[str, float]) -> Dict:
    response = supabase.table("thresholds").update({"thresholds": json.dumps(new_thresholds)}).eq("symbol", symbol).execute()
    return response.data

def fetch_thresholds() -> List[Dict[str, Any]]:
    response = supabase.table("thresholds").select("*").execute()
    return response.data

def log_event(message: str) -> Dict:
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "message": message
    }
    response = supabase.table("event_logs").insert(log_data).execute()
    return response.data
