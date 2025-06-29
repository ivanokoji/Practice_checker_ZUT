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
PREV_HASH_FILE = "prev_hash.txt"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


def get_page_content():
    try:
        res = requests.get(URL, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        item = soup.find("div", id="main-content")
        return item.get_text(strip=True) if item else None
    except Exception as e:
        logging.error(f"❌ Error fetching page: {e}")
        return None


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
    content = get_page_content()

    if not content:
        notify_telegram("⚠️ Could not read offer from ZUT site.")
        return

    current_hash = hashlib.sha256(content.encode()).hexdigest()
    previous_hash = ""

    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            previous_hash = f.read().strip()

    logging.info(f"🔁 Previous hash: {previous_hash}")
    logging.info(f"🆕 Current hash:  {current_hash}")

    if current_hash != previous_hash:
        try:
            # Save previous to backup file
            if previous_hash:
                with open(PREV_HASH_FILE, "w") as f:
                    f.write(previous_hash)

            # Write new hash
            with open(HASH_FILE, "w") as f:
                f.write(current_hash)

            notify_telegram(f"""📢 Detected change in ZUT page content.

🔗 {URL}""")

        except Exception as e:
            logging.error("❌ Failed to write hash files: %s", e)
    else:
        notify_telegram("🔁 No change today on the ZUT practice page.")


check_for_update()
