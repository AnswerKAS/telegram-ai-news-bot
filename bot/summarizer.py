import os
import re

import requests

_OPENROUTER_API = "https://openrouter.ai/api/v1"
_MODEL = "z-ai/glm-5.2"

SYSTEM_PROMPT = (
    "Ты — редактор новостного Telegram-канала об AI и технологиях. "
    "Кратко перескажи новость на русском языке в 2-3 предложения. "
    "Пиши сжато и информативно. "
    "Не начинай с «Эта статья», «В данной статье» или вводных фраз. "
    "Отвечай ТОЛЬКО текстом резюме."
)


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text).strip()


def summarize_article(article: dict) -> str:
    title = article["title"]
    description = _strip_html(article.get("description") or "")
    url = article["url"]
    source = article["source"]

    if description:
        user_content = f"Заголовок: {title}\n\nОписание: {description[:1500]}"
    else:
        user_content = f"Заголовок: {title}"

    response = requests.post(
        f"{_OPENROUTER_API}/chat/completions",
        headers={
            "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
            "Content-Type": "application/json",
        },
        json={
            "model": _MODEL,
            "max_tokens": 300,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        },
        timeout=90,
    )
    response.raise_for_status()
    summary = response.json()["choices"][0]["message"]["content"].strip()

    return (
        f"<b>{title}</b>\n\n"
        f"{summary}\n\n"
        f'<a href="{url}">Читать далее →</a>  |  📡 {source}'
    )
