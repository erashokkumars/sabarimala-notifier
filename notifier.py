"""Alerts you when the Virtual-Q calendar shows TARGET_DATE as available.

Read-only: it loads the public availability page once per run, never logs in,
never submits anything. You book manually on sabarimalaonline.org.
"""
import datetime as dt
import json
import os
import pathlib
import re
import urllib.request

from playwright.sync_api import sync_playwright

URL = os.getenv("PORTAL_URL", "https://sabarimalaonline.org/#/darshanAvailability")
TARGET = dt.date.fromisoformat(os.getenv("TARGET_DATE", "2027-01-04"))
TOPIC = os.getenv("NTFY_TOPIC", "")  # optional second channel
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TG_CHAT = os.getenv("TELEGRAM_CHAT_ID", "")
STATE = pathlib.Path("state.json")
PROBE_DIR = pathlib.Path("probe")


def _ntfy(title: str, msg: str, high: bool) -> None:
    req = urllib.request.Request(
        f"https://ntfy.sh/{TOPIC}",
        data=msg.encode(),
        headers={
            "Title": title,
            "Priority": "high" if high else "default",
            "Click": "https://sabarimalaonline.org/",
        },
        method="POST",
    )
    urllib.request.urlopen(req, timeout=15)


def _telegram(title: str, msg: str) -> None:
    body = json.dumps(
        {
            "chat_id": TG_CHAT,
            "text": f"{title}\n{msg}\nhttps://sabarimalaonline.org/",
            "disable_web_page_preview": True,
        }
    ).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    urllib.request.urlopen(req, timeout=15)


def notify(title: str, msg: str, high: bool = False) -> None:
    sent = False
    if TG_TOKEN and TG_CHAT:
        try:
            _telegram(title, msg)
            sent = True
        except Exception as e:  # never print the token
            print("Telegram failed:", type(e).__name__, getattr(e, "code", ""))
    if TOPIC:
        try:
            _ntfy(title, msg, high)
            sent = True
        except Exception as e:
            print("ntfy failed:", type(e).__name__)
    if not sent:
        print("NOTIFY (no channel worked):", title, "-", msg)


def classify(rgb: str) -> str:
    m = re.match(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", rgb or "")
    if not m:
        return "unknown"
    r, g, b = map(int, m.groups())
    if g > r + 30 and g > b + 30:
        return "available"  # green
    if r > g + 30 and r > b + 30:
        return "full"  # red
    return "unknown"


def read_status(page) -> str:
    """Returns available | full | unknown | login_required.

    BEST GUESS: assumes an Angular Material calendar whose day cells carry
    aria-label="January 4, 2027". Tune after running probe mode.
    """
    if page.locator("input[type=password]").count():
        return "login_required"

    label = f"{TARGET:%B} {TARGET.day}, {TARGET.year}"
    cell = page.locator(f'[aria-label="{label}"]')
    for _ in range(14):  # step forward through months
        if cell.count():
            break
        nxt = page.locator("button.mat-calendar-next-button")
        if not nxt.count() or nxt.first.is_disabled():
            return "unknown"
        nxt.first.click()
        page.wait_for_timeout(300)
    else:
        return "unknown"

    colours = cell.first.evaluate(
        """e => [e, e.querySelector('.mat-calendar-body-cell-content')]
              .filter(Boolean).map(n => getComputedStyle(n).backgroundColor)"""
    )
    for c in colours:
        s = classify(c)
        if s != "unknown":
            return s
    return "unknown"


def main() -> None:
    if os.getenv("TEST_NOTIFY") == "1":
        notify("Test alert", "Sabarimala notifier is connected.", high=True)
        return

    if dt.date.today() > TARGET:
        print("Target date has passed; nothing to do.")
        return

    PROBE_DIR.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 1600})
        try:
            page.goto(URL, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(3000)
            status = read_status(page)
        except Exception as e:  # network blocks, timeouts, etc.
            print("Error:", e)
            status = "error"
        page.screenshot(path=str(PROBE_DIR / "page.png"), full_page=True)
        (PROBE_DIR / "page.html").write_text(page.content())
        browser.close()

    print("Status:", status)
    if status == "error":
        return  # transient; keep previous state, no alert

    prev = json.loads(STATE.read_text())["status"] if STATE.exists() else None
    if status != prev:
        day = f"{TARGET:%d %b %Y}"
        if status == "available":
            notify(f"Slots open for {day}", "Virtual-Q shows green. Book now (Vandiperiyar route).", high=True)
        elif status == "login_required":
            notify("Notifier needs a tune-up", "Calendar needs login; open the probe artifact.")
        elif status == "unknown":
            notify("Notifier needs a tune-up", "Could not read the calendar; open the probe artifact.")
        elif prev == "available":
            notify(f"{day} slots gone", "Calendar now shows full.")
        STATE.write_text(json.dumps({"status": status}))


if __name__ == "__main__":
    main()
