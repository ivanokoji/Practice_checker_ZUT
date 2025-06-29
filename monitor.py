import requests
from bs4 import BeautifulSoup
import hashlib
import os
from dotenv import load_dotenv
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
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
    logging.info(f"🟡 Extracted HTML element: {item}")
    return item.get_text(strip=True) if item else None


def notify_telegram(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        logging.error("❌ Missing TELEGRAM_TOKEN or CHAT_ID")
        return

    api = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    res = requests.post(api, data=data)
    logging.info(f"📤 Telegram response: {res.status_code}, {res.text}")


def check_for_update():
    logging.info("🚀 Checking for updates...")
    latest = get_latest_offer()

    if not latest:
        notify_telegram("⚠️ Could not read offer from ZUT site.")
        return

    offer_hash = hashlib.sha256(latest.encode()).hexdigest()

    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            prev_hash = f.read()
    else:
        prev_hash = ''

    if offer_hash != prev_hash:
        try:
            with open(HASH_FILE, "w") as f:
                f.write(offer_hash)
            notify_telegram(f"""📢 New offer on ZUT site:


🔗 {URL}""")
        except Exception as e:
            logging.error("❌ Failed to write hash file: %s", e)
    else:
        notify_telegram("🔁 No change today on the ZUT practice page.")


check_for_update()
