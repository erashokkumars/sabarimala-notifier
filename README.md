# Sabarimala Virtual-Q slot notifier (free tier)

Watches the public availability calendar for 4 Jan 2027 and pings your phone
when it turns green. Read-only: no login, no OTP, no booking. You book by hand.

## Setup (about 5 minutes)
1. Telegram: open your bot and press **Start** (a bot can't message you until
   you do). Then open
   `https://api.telegram.org/bot<TOKEN>/getUpdates` in a browser and copy
   `"chat":{"id": ...}` - that number is your chat id.
   (Optional backup channel: the ntfy app with a long random topic name.)
2. GitHub: create a **public** repo (public = unlimited free Actions minutes),
   upload these files keeping the folder layout.
3. Repo > Settings > Secrets and variables > Actions > New secret, add:
   `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` (optional: `NTFY_TOPIC`).
   Never put the token in a file or chat.
4. Actions > check-slots > Run workflow with **test** ticked. You should get
   a Telegram message within a minute.
5. Actions tab > check-slots > **Run workflow**. Open the run, download the
   `probe` artifact (page.png, page.html) and check what the page showed.
6. If you got a "needs a tune-up" alert, send me page.png and page.html and
   I'll fix the selectors. Otherwise you're done; it runs every ~30 minutes
   and stops by itself after 4 Jan 2027.

## Notes
- Alerts fire only when the status changes, so no spam.
- To book, open sabarimalaonline.org, pick the date and the
  Vandiperiyar-Sathram-Pulmedu route.
