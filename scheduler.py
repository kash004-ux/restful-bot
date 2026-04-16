import schedule
import time
import subprocess
import sys
from datetime import datetime

def run_bot():
    print(f"\n[{datetime.now()}] Starting daily video generation...")
    try:
        # Runs bot.py and waits for it to finish
        result = subprocess.run(
            [sys.executable, "bot.py"],
            capture_output=False,
            timeout=7200  # 2-hour timeout
        )
        if result.returncode == 0:
            print(f"[{datetime.now()}] Video generated and uploaded successfully")
        else:
            print(f"[{datetime.now()}] Bot exited with code {result.returncode}")
    except subprocess.TimeoutExpired:
        print(f"[{datetime.now()}] Bot timed out after 2 hours")
    except Exception as e:
        print(f"[{datetime.now()}] Error: {e}")

# Schedule the task for 6:00 PM local server time
schedule.every().day.at("18:00").do(run_bot)

print("RestfulTalesTunes Scheduler started")
print("Uploading 1 video daily at 6:00pm")

# Run once immediately on startup to verify it works
run_bot()

while True:
    schedule.run_pending()
    time.sleep(60)

