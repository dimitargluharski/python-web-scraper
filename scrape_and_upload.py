import subprocess

print("Starting scrape...")
subprocess.run(["python", "scraper.py"], check=True)

print("⬆Uploading to GitHub...")
subprocess.run(["python", "upload_to_github.py"], check=True)