import os

import requests

_TELEGRAM_API = "https://api.telegram.org"


def post_to_channel(text: str) -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    channel_id = os.environ["TELEGRAM_CHANNEL_ID"]

    url = f"{_TELEGRAM_API}/bot{token}/sendMessage"
    payload = {
        "chat_id": channel_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
        "link_preview_options": {"show_above_text": False},
    }
    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()
    print(f"Posted: {text[:80].splitlines()[0]}...")
