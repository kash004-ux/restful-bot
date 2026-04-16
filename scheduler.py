import subprocess
import sys
import time
import schedule
from datetime import datetime

def run_bot():
    print(f"[{datetime.now()}] Running bot...")
    try:
        # Runs bot.py and waits for completion
        subprocess.run([sys.executable, "bot.py"], check=True)
        print(f"[{datetime.now()}] Done!")
    except Exception as e:
        print(f"[{datetime.now()}] Error: {e}")

print("Scheduler started - running now then daily at 18:00")

# Initial run to verify connection upon startup
run_bot()

# Set schedule for 6:00 PM
schedule.every().day.at("18:00").do(run_bot)

while True:
    schedule.run_pending()
    time.sleep(60)
