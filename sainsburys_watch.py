import json
import os
import hashlib
import requests
from bs4 import BeautifulSoup

URL = "https://sainsburys.jobs/jobs?full_time=&part_time=on&fixed_term=&filter_by=&location=eh14+4as&keywords="
STATE_FILE = "seen_jobs.json"

TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "").strip()
TG_CHAT_ID = os.environ.get("TG_CHAT_ID", "").strip()

# اگر این = 1 باشد، هر بار یک پیام تست می‌فرستد
ALWAYS_SEND_TEST = os.environ.get("ALWAYS_SEND_TEST", "0").strip() == "1"


def send_telegram(text: str):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        raise RuntimeError("Missing TG_BOT_TOKEN or TG_CHAT_ID. Check GitHub Secrets.")

    api = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    r = requests.post(api, data={"chat_id": TG_CHAT_ID, "text": text}, timeout=25)

    if r.status_code != 200:
        # متن دقیق خطای تلگرام را نشان می‌دهد
        raise RuntimeError(f"Telegram error {r.status_code}: {r.text}")


def load_seen():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()
    except Exception as e:
        raise RuntimeError(f"Failed to read {STATE_FILE}: {e}")


def save_seen(seen):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(sorted(list(seen)), f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise RuntimeError(f"Failed to write {STATE_FILE}: {e}")


def fetch_jobs():
    r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=25)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    jobs = []
    for a in soup.select("a[href]"):
        href = a.get("href", "")
        if "/jobs/" in href:
            link = href
            if link.startswith("/"):
                link = "https://sainsburys.jobs" + link

            title = a.get_text(" ", strip=True) or "New role"
            key = hashlib.sha1((title + "|" + link).encode("utf-8")).hexdigest()
            jobs.append((title, link, key))

    # یکتا
    uniq = []
    keys = set()
    for title, link, key in jobs:
        if key not in keys:
            keys.add(key)
            uniq.append((title, link, key))

    return uniq


def main():
    # پیام تست اختیاری
    if ALWAYS_SEND_TEST:
        send_telegram("✅ Jobbot TEST: GitHub Actions can message you.")

    seen = load_seen()
    jobs = fetch_jobs()

    new_items = [j for j in jobs if j[2] not in seen]

    if new_items:
        lines = ["✅ New Sainsbury’s job(s) found:"]
        for title, link, key in new_items[:10]:
            lines.append(f"- {title}\n{link}")
            seen.add(key)

        send_telegram("\n".join(lines))
        save_seen(seen)
    else:
        # فقط لاگ برای اینکه بفهمیم اجرا شده
        print("No new jobs.")


if __name__ == "__main__":
    main()
