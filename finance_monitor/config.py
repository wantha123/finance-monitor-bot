
import os
from dotenv import load_dotenv

load_dotenv()

# ✅ Secrets sensibles depuis .env
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TARGET = os.getenv("EMAIL_TARGET")
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# 🧪 Modes
IS_TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"
RUN_MODE = os.getenv("RUN_MODE", "continuous")

# 📈 Seuils par défaut (en backup statique)
DEFAULT_THRESHOLDS = {
    "change_percent": 7.0,
    "high": 1000,
    "low": 300
}

# 🔄 Heures du marché (Paris)
HOURS_PARIS = {
    "open": 9,
    "close": 17,
    "report_morning": 10,
    "report_evening": 18
}
