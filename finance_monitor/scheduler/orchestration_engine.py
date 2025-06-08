from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
from storage.backblaze_backup import upload_file_to_b2
from finance_monitor.main import run_all_tasks

scheduler = BlockingScheduler()

# Tâche périodique toutes les 30 minutes
@scheduler.scheduled_job('interval', minutes=30)
def periodic_analysis():
    print(f"[{datetime.utcnow()}] ⏱ Lancement analyse périodique")
    run_all_tasks()

# Sauvegarde quotidienne à 2h00 UTC
@scheduler.scheduled_job('cron', hour=2)
def daily_backup():
    print(f"[{datetime.utcnow()}] 💾 Sauvegarde quotidienne déclenchée")
    upload_file_to_b2("supabase_export.json")  # à adapter si nécessaire

if __name__ == "__main__":
    print("🚀 Scheduler démarré...")
    scheduler.start()
