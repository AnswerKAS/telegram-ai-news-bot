import re

from anthropic import Anthropic

client = Anthropic()

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

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )
    summary = response.content[0].text.strip()

    return (
        f"<b>{title}</b>\n\n"
        f"{summary}\n\n"
        f'<a href="{url}">Читать далее →</a>  |  📡 {source}'
    )
