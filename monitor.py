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


def get_latest_offers(limit=3):
    res = requests.get(URL)
    soup = BeautifulSoup(res.text, "html.parser")
    offer_tags = soup.select("div.items-leading h2 > a")
    if not offer_tags:
        logging.warning("⚠️ Could not locate offers on the page.")
        return []

    offers = []
    for tag in offer_tags[:limit]:
        title = tag.get_text(strip=True)
        link = f"https://www.wi.zut.edu.pl{tag['href']}"
        offers.append(f"{title} | {link}")
    return offers


def notify_telegram(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        logging.error("❌ Missing TELEGRAM_TOKEN or CHAT_ID")
        return
    api = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message[:4000]}
    res = requests.post(api, data=data)
    logging.info(f"📤 Telegram response: {res.status_code}, {res.text}")


def check_for_update():
    logging.info("🚀 Checking for updates...")
    offers = get_latest_offers()
    if not offers:
        notify_telegram("⚠️ Could not read offers from ZUT site.")
        return

    combined = "\n".join(offers)
    offer_hash = hashlib.sha256(combined.encode()).hexdigest()

    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            prev_hash = f.read().strip()
    else:
        prev_hash = ''

    logging.info(f"🔁 Previous hash: {prev_hash}")
    logging.info(f"🆕 Current hash:  {offer_hash}")

    if offer_hash != prev_hash:
        try:
            with open(HASH_FILE, "w") as f:
                f.write(offer_hash)
            notify_telegram("📢 New internship/practice offers detected on ZUT page:\n\n" + combined)
        except Exception as e:
            logging.error(f"❌ Failed to write hash file: {e}")
    else:
        logging.info("✅ No new offers detected.")
       


check_for_update()
