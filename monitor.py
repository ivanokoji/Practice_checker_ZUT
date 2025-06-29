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
    container = soup.select_one("div.items-leading")
    if not container:
        logging.warning("No 'items-leading' div found.")
        return None

    title_tag = container.select_one("h2 > a")
    if not title_tag:
        logging.warning("No offer link found inside 'items-leading'.")
        return None

    title = title_tag.get_text(strip=True)
    link = f"https://www.wi.zut.edu.pl{title_tag['href']}"
    return f"{title}\n{link}"


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
            prev_hash = f.read().strip()
    else:
        prev_hash = ''

    logging.info(f"🔁 Previous hash: {prev_hash}")
    logging.info(f"🆕 Current hash:  {offer_hash}")

    if offer_hash != prev_hash:
        try:
            with open(HASH_FILE, "w") as f:
                f.write(offer_hash)
            notify_telegram(f"📢 Detected change in ZUT page content:\n\n{latest}")
        except Exception as e:
            logging.error(f"❌ Failed to write hash file: {e}")
    else:
        notify_telegram("🔁 No change today on the ZUT practice page.")


check_for_update()
