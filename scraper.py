import os
import requests
import json
import re
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime, timedelta

# Зареждаме .env
load_dotenv()
url = os.getenv('SCRAPER_URL')

if not url:
    raise ValueError("❌ SCRAPER_URL is not set in the .env file!")

print(f"🌐 Основен URL: {url}")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
response = requests.get(url, headers=headers)

if response.status_code != 200:
    raise ValueError(f"❌ Request to {url} failed. Status code: {response.status_code}")

# Selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_iframe_src_from_link(full_url: str) -> str:
    options = Options()
    options.binary_location = "/app/.apt/usr/bin/google-chrome"
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(executable_path="/app/.chromedriver/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)

    try:
        print(f"🌐 Отварям: {full_url}")
        driver.get(full_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "iframe"))
        )
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"🔍 Намерени iframe-и: {len(iframes)}")

        for iframe in iframes:
            src = iframe.get_attribute("src")
            if src and "radamel.icu" in src:
                print(f"✅ Намерен iframe src: {src}")
                return src
        print("⚠️ Не е намерен iframe с 'radamel.icu'")
        return None
    except Exception as e:
        print("❌ Грешка при iframe обработка:", e)
        return None
    finally:
        driver.quit()

# Обработка на HTML
soup = BeautifulSoup(response.text, 'html.parser')
table = soup.find('table', {'id': 'my-table'})

if not table:
    raise ValueError("❌ Table with id='my-table' was not found!")

rows = table.find_all('tr')
events = {}

# Помощни функции
def correct_time(time_str):
    try:
        time_obj = datetime.strptime(time_str, "%H:%M")
        time_obj += timedelta(hours=8)
        return time_obj.strftime("%H:%M")
    except ValueError:
        return time_str

def split_event_description(description):
    description = description.replace(" en Vivo", "")
    if "vs" in description:
        teams = description.split("vs")
        if len(teams) == 2:
            return teams[0].strip(), teams[1].strip()
    return None, description

def clean_league_name(league_name, home_team, away_team):
    if home_team and away_team:
        league_name = league_name.replace(home_team, "").replace(away_team, "").strip()
    return re.sub(r'\s*vs\s*', '', league_name).replace("en Vivo", "").strip()

def is_excluded_event(event_type):
    excluded_keywords = ["Euroleague", "ATP", "MLB", "NBA"]
    return any(keyword in event_type for keyword in excluded_keywords)

def is_valid_link(link):
    parsed_url = urlparse(link)
    if not parsed_url.netloc:
        link = urljoin(url, link)
        parsed_url = urlparse(link)
    return bool(parsed_url.scheme) and bool(parsed_url.netloc) and 'httpswww' not in link

# Обхождане на редове
for row in rows:
    cells = row.find_all('td')
    if len(cells) >= 3:
        time_raw = cells[0].get_text(strip=True)
        event_td = cells[2]

        if event_td.find(class_="evento tenis"):
            continue

        league_full_name = event_td.get_text(strip=True).split("\n")[0].strip()
        if is_excluded_event(league_full_name):
            continue

        link_tag = event_td.find('a')
        link = link_tag['href'] if link_tag else None
        if link and not is_valid_link(link):
            continue

        if link:
            link = urljoin(url, link)
            iframe_src = get_iframe_src_from_link(link)
        else:
            iframe_src = None

        description_tag = event_td.find('b')
        description = description_tag.get_text(strip=True) if description_tag else ''
        home_team, away_team = split_event_description(description)
        event_type = clean_league_name(league_full_name, home_team, away_team)
        corrected_time = correct_time(time_raw)

        match_key = (home_team, away_team, corrected_time)
        if match_key not in events:
            events[match_key] = {
                'time': corrected_time,
                'event_type': event_type,
                'home_team': home_team,
                'away_team': away_team,
                'links': [{
                    "id": 1,
                    "url": link,
                    "iframe": iframe_src
                }]
            }
        else:
            link_id = len(events[match_key]['links']) + 1
            events[match_key]['links'].append({
                "id": link_id,
                "url": link,
                "iframe": iframe_src
            })

# Запис в JSON
with open('events.json', 'w', encoding='utf-8') as f:
    json.dump(list(events.values()), f, ensure_ascii=False, indent=4)

print("✅ Scraped successfully and saved to events.json")
