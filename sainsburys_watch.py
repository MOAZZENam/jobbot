import json
import os
import hashlib
import requests
from bs4 import BeautifulSoup

URL = "https://sainsburys.jobs/jobs?full_time=&part_time=on&fixed_term=&filter_by=&location=eh14+4as&keywords="
STATE_FILE = "seen_jobs.json"

TELEGRAM_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TG_CHAT_ID")


def send_telegram(text: str):
    api = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(api, data={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=25)


def load_seen():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_seen(seen):
    with open(STATE_FILE, "w") as f:
        json.dump(list(seen), f)


def fetch_jobs():
    r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")

    jobs = []
    for a in soup.select("a[href]"):
        href = a.get("href", "")
        if "/jobs/" in href:
            link = href
            if link.startswith("/"):
                link = "https://sainsburys.jobs" + link
            title = a.get_text(strip=True)
            key = hashlib.sha1((title + link).encode()).hexdigest()
            jobs.append((title, link, key))

    return jobs


def main():
    seen = load_seen()
    jobs = fetch_jobs()
    new_jobs = [j for j in jobs if j[2] not in seen]

    if new_jobs:
        message = "✅ New Sainsbury’s Job Found:\n\n"
        for title, link, key in new_jobs[:5]:
            message += f"{title}\n{link}\n\n"
            seen.add(key)

        send_telegram(message)
        save_seen(seen)


if __name__ == "__main__":
    main()
