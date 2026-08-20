# Telegram AI News Bot

Бот для Telegram-канала: забирает RSS из источников про AI и технологии, пересказывает новости через OpenRouter (GLM 5.2) и постит в канал. Запускается по расписанию через GitHub Actions — без сервера и базы данных.

## Как это работает

1. `main.py` читает источники из `config/sources.yaml` и темы из `config/topics.yaml`.
2. `bot/fetcher.py` парсит RSS-ленты (`feedparser`), убирает дубликаты, фильтрует по свежести.
3. `bot/summarizer.py` отправляет каждую новость в OpenRouter: заголовок переводится на русский, генерируется краткое резюме.
4. `bot/poster.py` отправляет готовое HTML-сообщение в Telegram через Bot API.
5. Отправленные URL сохраняются в `data/sent_articles.json` — чтобы не постить одно и то же дважды.

## Топики

Темы и количество новостей по каждой настраиваются в `config/topics.yaml`:

```yaml
topics:
  - name: "LLM и нейросети"
    count: 2                    # сколько новостей за запуск
    keywords:
      - "LLM"
      - "GPT"
      - "нейросет"
      - "DeepSeek"
```

- `keywords` — поиск подстроки в заголовке/описании/источнике, без учёта регистра. Пустой список `keywords` — тема ловит все новости.
- Каждая новость публикуется один раз, для первой подошедшей темы.
- Общий лимит за запуск — `MAX_ARTICLES_PER_RUN` в `main.py`.

## Настройка

```bash
pip install -r requirements.txt
cp .env.example .env   # заполните секреты
python main.py
```

### Переменные окружения

| Переменная | Описание |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Токен бота от [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_CHANNEL_ID` | ID канала: `@username` или `-100xxxxxxxxxx` |
| `OPENROUTER_API_KEY` | Ключ [OpenRouter](https://openrouter.ai/) |

Модель задаётся в `bot/summarizer.py` (по умолчанию `z-ai/glm-5.2`).

## GitHub Actions

Workflow `.github/workflows/news_bot.yml` запускает бота ежедневно в 03:00 UTC (10:00 Новосибирск). Добавьте секреты репозитория `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHANNEL_ID`, `OPENROUTER_API_KEY`. Ручной запуск — вкладка Actions → **Run workflow**.

⚠️ `python main.py` публикует в реальный канал и тратит деньги на API. Не запускайте его «просто потестить».