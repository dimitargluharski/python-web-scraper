import subprocess
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def send_discord_message(content: str):
    webhook_url = os.getenv("DISCORD_WEBHOOK")
    if not webhook_url:
        print("⚠️ DISCORD_WEBHOOK is not set.")
        return

    try:
        response = requests.post(webhook_url, json={"content": content})
        if response.status_code in [200, 204]:
            print("📬 Discord notification sent successfully.")
        else:
            print(f"⚠️ Discord webhook failed with status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Error while sending to Discord: {e}")

# 🚀 Start message
send_discord_message("🚀 Automatic update of `events.json` started...")

try:
    print("🔍 Running scraper...")
    subprocess.run(["python", "scraper.py"], check=True)

    print("⬆ Uploading to GitHub...")
    subprocess.run(["python", "upload_to_github.py"], check=True)

    # ✅ Success message
    send_discord_message("✅ `events.json` was successfully updated and pushed to GitHub!")

except subprocess.CalledProcessError as e:
    print(f"❌ Script execution error: {e}")
    # ❌ Error message
    send_discord_message("❌ An error occurred while updating `events.json`!")
