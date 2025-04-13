import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin, urlparse
from datetime import datetime, timedelta

load_dotenv()

url = os.getenv('SCRAPER_URL')

if not url:
    raise ValueError("SCRAPER_URL is not set in the .env file!")

print(f"URL: {url}")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
response = requests.get(url, headers=headers)

if response.status_code != 200:
    print(f"Request to {url} failed. Status code: {response.status_code}")
    print(f"Response: {response.text}") 
    raise ValueError(f"Request to {url} failed. Status code: {response.status_code}")

soup = BeautifulSoup(response.text, 'html.parser')

table = soup.find('table', {'id': 'my-table'})

if not table:
    print("Table not found. Please check the HTML structure:")
    print(soup.prettify()) 
    raise ValueError("Table with id='my-table' was not found on the page!")

rows = table.find_all('tr')

events = {}

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
            home_team = teams[0].strip()
            away_team = teams[1].strip()
            return home_team, away_team
    
    return None, description

def clean_league_name(league_name, home_team, away_team):
    if home_team and away_team:
        league_name = league_name.replace(home_team, "").replace(away_team, "").strip()
    
    league_name = re.sub(r'\s*vs\s*', '', league_name).replace("en Vivo", "").strip()
    return league_name

def is_excluded_event(event_type):
    excluded_keywords = ["Euroleague", "ATP", "MLB", "NBA"]
    for keyword in excluded_keywords:
        if keyword in event_type:
            return True
    return False

def is_valid_link(link):
    parsed_url = urlparse(link)
    
    if not parsed_url.netloc:
        link = urljoin(url, link)
        parsed_url = urlparse(link)

    is_valid = bool(parsed_url.scheme) and bool(parsed_url.netloc)
    
    if link.startswith(url) and 'httpswww' in link:
        is_valid = False
    
    return is_valid

for row in rows:
    cells = row.find_all('td')
    if len(cells) >= 3:
        time = cells[0].get_text(strip=True)
        event_type = cells[1].get_text(strip=True)
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

        description_tag = event_td.find('b')
        description = description_tag.get_text(strip=True) if description_tag else ''

        home_team, away_team = split_event_description(description)
        
        event_type = clean_league_name(league_full_name, home_team, away_team)

        corrected_time = correct_time(time)
      
        match_key = (home_team, away_team, corrected_time)
        if match_key not in events:
            events[match_key] = {
                'time': corrected_time,
                'event_type': event_type,
                'home_team': home_team,
                'away_team': away_team,
                'links': [{"id": i+1, "url": link} for i, link in enumerate({link})]
            }
        else:
            link_id = len(events[match_key]['links']) + 1
            events[match_key]['links'].append({"id": link_id, "url": link})

with open('events.json', 'w', encoding='utf-8') as f:
    json.dump(list(events.values()), f, ensure_ascii=False, indent=4)

print("Scraped successfully and saved to events.json")