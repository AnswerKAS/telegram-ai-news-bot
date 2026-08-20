# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Telegram-бот, который каждые 6 часов собирает свежие AI/ML новости из RSS-лент, генерирует краткое резюме на русском через Claude API и постит в Telegram-канал. Запускается через GitHub Actions — постоянного сервера не требуется.

## Architecture

```
main.py               # Точка входа: оркестрирует fetch → summarize → post
bot/
  fetcher.py          # Парсит RSS-ленты, фильтрует по времени, дедуплицирует
  summarizer.py       # Вызывает Claude API, возвращает HTML-форматированное сообщение
  poster.py           # Отправляет сообщение в канал через Telegram Bot API (HTTP)
config/
  sources.yaml        # Список RSS-лент: url + name
data/
  sent_articles.json  # Список отправленных URL (не отправлять повторно)
.github/
  workflows/
    news_bot.yml      # GitHub Actions cron каждые 6 часов
```

**Поток данных:**
1. `fetcher.py` тянет все RSS-ленты из `sources.yaml`, фильтрует статьи новее 7 часов
2. `main.py` исключает URL из `sent_articles.json` и берёт не более 5 статей
3. `summarizer.py` отправляет заголовок + описание в Claude, получает 2-3 предложения на русском
4. `poster.py` постит HTML-сообщение в канал
5. `main.py` сохраняет новые URL в `sent_articles.json`
6. GitHub Actions коммитит обновлённый `sent_articles.json` обратно в репозиторий (`[skip ci]` предотвращает рекурсию)

## Development Commands

```bash
# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных (скопировать и заполнить)
cp .env.example .env

# Запустить бота локально (однократный прогон)
python main.py
```

## Configuration

Секреты хранятся в `.env` локально и в GitHub Secrets для Actions:
- `TELEGRAM_BOT_TOKEN` — токен от @BotFather
- `TELEGRAM_CHANNEL_ID` — `@username` канала или числовой ID вида `-100...`
- `ANTHROPIC_API_KEY` — ключ Anthropic API

RSS-ленты добавляются/удаляются в `config/sources.yaml` — формат: `url` + `name`.

## Key Behaviours

- Бот не хранит состояние в БД — весь трекинг в `data/sent_articles.json` (git-коммит после каждого прогона)
- Максимум 5 постов за прогон (`MAX_ARTICLES_PER_RUN` в `main.py`)
- Статьи старше 7 часов (`HOURS_BACK`) игнорируются чтобы не слать старое при первом запуске
- История обрезается до 2000 URL (`MAX_SENT_HISTORY`) чтобы файл не разрастался

## Deployment

1. Залить репозиторий на GitHub
2. В Settings → Secrets добавить три переменные выше
3. Включить Actions — workflow запустится автоматически по расписанию или через кнопку "Run workflow"
