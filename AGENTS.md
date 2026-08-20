# AGENTS.md

Single-file Python bot: fetch RSS → summarize via OpenRouter (GLM 5.2) → post to Telegram. Runs on a GitHub Actions cron; no server, no DB.

## Commands

```bash
pip install -r requirements.txt
cp .env.example .env   # then fill in secrets
python main.py         # full run, from repo root
```

There is **no test suite, linter, or typecheck config** in this repo. Do not invent one or add CI for it unless asked. Verify changes by running `python main.py`.

## Critical gotchas

- **`python main.py` has real side effects.** It posts to the live Telegram channel, calls the OpenRouter API (costs money), and mutates `data/sent_articles.json` (dedup state). There is no `--dry-run` flag. Never run it to "just test" unless you want it to actually post.
- **`data/sent_articles.json` is git-tracked.** The workflow auto-commits it back with `[skip ci]`. A test run permanently marks articles as sent. Only commit intentional changes to it.
- Bot messages are **HTML** (`parse_mode: "HTML"`) in Russian, with the `SYSTEM_PROMPT` in `bot/summarizer.py`. Keep the response format intact: GLM translates the title to Russian (used as `<b>` header), then a 2-3 sentence summary; the code splits the first line into the title. No intro phrases in the summary.
- Paths are resolved from CWD — always run from the repo root.
- Env vars come from `.env` (`load_dotenv()` in `main.py`) or CI secrets. `bot/poster.py` reads `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHANNEL_ID` via `os.environ`; `bot/summarizer.py` reads `OPENROUTER_API_KEY`; never commit real secrets.

## Architecture notes

- Entrypoint `main.py` orchestrates: constants there are the tuning knobs — `MAX_ARTICLES_PER_RUN=5`, `HOURS_BACK=7` (articles older than this are skipped), `MAX_SENT_HISTORY=2000`.
- `bot/fetcher.py` — parses feeds with `feedparser`, de-dups URLs, sorts newest-first, filters by `HOURS_BACK`.
- `bot/summarizer.py` — model `z-ai/glm-5.2` on OpenRouter is hardcoded here (`summarizer.py:7`), reasoning disabled via `{"reasoning": {"effort": "none"}}`; renders the HTML message (Russian title in `<b>`, "Читать далее →" link, source).
- `bot/poster.py` — raw `requests` to Telegram Bot API (`sendMessage`).
- RSS sources live in `config/sources.yaml` under the top-level `feeds:` key (`url` + `name`).
- Workflow `.github/workflows/news_bot.yml` runs daily at 03:00 UTC (10:00 Novosibirsk) on Python 3.12, then commits `data/sent_articles.json` back. Manual trigger via `workflow_dispatch`.
