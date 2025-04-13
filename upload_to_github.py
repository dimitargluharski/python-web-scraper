import requests
import base64
import json
import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = os.getenv("REPO_OWNER")
REPO_NAME = os.getenv("REPO_NAME")
BRANCH = os.getenv("BRANCH", "main")
FILE_PATH = "events.json"
COMMIT_MESSAGE = "Auto-update events.json from Heroku"

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

with open(FILE_PATH, "rb") as f:
    new_content = f.read()
    encoded_content = base64.b64encode(new_content).decode("utf-8")

url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
params = {"ref": BRANCH}
response = requests.get(url, headers=headers, params=params)

if response.status_code == 200:
    sha = response.json()["sha"]
    existing_content = base64.b64decode(response.json()["content"]).decode("utf-8")

    if existing_content.strip() == new_content.decode("utf-8").strip():
        print("⚠️ No changes in events.json. Skipping upload.")
        exit(0)
    else:
        print("📄 Changes detected. Updating file...")
else:
    sha = None
    print("📄 File does not exist. Creating...")

payload = {
    "message": COMMIT_MESSAGE,
    "content": encoded_content,
    "branch": BRANCH
}

if sha:
    payload["sha"] = sha

response = requests.put(url, headers=headers, data=json.dumps(payload))

if response.status_code in [200, 201]:
    print("events.json uploaded to GitHub.")
else:
    print("Upload failed:", response.text)
