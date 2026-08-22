import html
import os
import re

import requests

_OPENROUTER_API = "https://openrouter.ai/api/v1"
_MODEL = "z-ai/glm-5.2"

SYSTEM_PROMPT = (
    "Ты — редактор новостного Telegram-канала об AI и технологиях. "
    "Переведи заголовок новости на русский язык и кратко перескажи новость в 2-3 предложения. "
    "Формат ответа строго такой:\n"
    "Первая строка: заголовок на русском языке.\n"
    "Вторая строка: пустая.\n"
    "Далее: резюме на русском.\n"
    "Пиши сжато и информативно. "
    "Не начинай резюме с «Эта статья», «В данной статье» или вводных фраз."
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
            "reasoning": {"effort": "none"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        },
        timeout=90,
    )
    response.raise_for_status()
    message = response.json()["choices"][0]["message"]
    content = message.get("content") or message.get("reasoning")
    if isinstance(content, list):
        content = " ".join(
            part.get("text", "") for part in content if isinstance(part, dict)
        ).strip()
    if not content:
        raise RuntimeError("OpenRouter вернул пустой ответ без content и reasoning")
    summary = content.strip()
    lines = summary.split("\n", 1)
    russian_title = lines[0].strip()
    body = lines[1].strip() if len(lines) > 1 else summary

    return (
        f"<b>{html.escape(russian_title)}</b>\n\n"
        f"{html.escape(body)}\n\n"
        f'<a href="{html.escape(url, quote=True)}">Читать далее →</a>  |  📡 {html.escape(source)}'
    )
