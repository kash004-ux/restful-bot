import subprocess
import sys
import time
import schedule
from datetime import datetime

def run_bot():
    print(f"[{datetime.now()}] Running bot...")
    try:
        subprocess.run([sys.executable, "bot.py"], check=True)
        print(f"[{datetime.now()}] Done!")
    except Exception as e:
        print(f"[{datetime.now()}] Error: {e}")

print("Nightfall Audio Co Scheduler started")
print("Uploading 1 video daily at 6:00 PM")

schedule.every().day.at("18:00").do(run_bot)

while True:
    schedule.run_pending()
    time.sleep(60)
