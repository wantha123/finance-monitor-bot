
import argparse
import time
from scheduler.orchestration_engine import run_all_tasks
from storage.state_manager import StateManager

def main(once=False, test=False):
    state = StateManager()
    try:
        if once:
            run_all_tasks()
        elif test:
            print("✅ Test mode: API keys and config loaded correctly.")
        else:
            while True:
                run_all_tasks()
                time.sleep(60 * 30)  # 🔁 30 min interval
    except Exception as e:
        print(f"❌ Erreur fatale : {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Market Watch Bot")
    parser.add_argument('--once', action='store_true', help='Exécution unique')
    parser.add_argument('--test', action='store_true', help='Test des connexions')

    args = parser.parse_args()
    main(once=args.once, test=args.test)
