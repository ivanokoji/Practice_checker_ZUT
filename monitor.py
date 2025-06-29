
import requests
from bs4 import BeautifulSoup
import hashlib
import os
from dotenv import load_dotenv
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,  # 👈 explicitly sends logs to stdout
    format="%(levelname)s: %(message)s"
)

load_dotenv()

URL = "https://www.wi.zut.edu.pl/pl/dla-studenta/sprawy-studenckie/oferty-pracy-i-praktyk?limitstart=0"
HASH_FILE = "last_hash.txt"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def get_latest_offer():
    res = requests.get(URL)
    soup = BeautifulSoup(res.text, "html.parser")
    item = soup.find("div", id="main-content")
    logging.info(f"Start,{item}!")
    return item.get_text(strip=True) if item else None

def notify_telegram(message):
    api = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    requests.post(api, data=data)

def check_for_update():
    logging.info(f"Start!")
    latest = get_latest_offer()
    logging.info(f"Start,{latest}!")
    if not latest:
        notify_telegram("⚠️ Could not read offer from ZUT site.")
        return

    offer_hash = hashlib.sha256(latest.encode()).hexdigest()

    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            prev_hash = f.read()
    else:
        prev_hash = ''
        
    logging.info(f"Start,{prev_hash}!")
    if offer_hash != prev_hash:
        with open(HASH_FILE, "w") as f:
            f.write(offer_hash)
        notify_telegram(f"""📢 New offer on ZUT site:
{latest}

🔗 {URL}""")
    else:
        notify_telegram("🔁 No change today on the ZUT practice page.")

check_for_update()
