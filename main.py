import json
import time
from pathlib import Path

import yaml
from dotenv import load_dotenv

from bot.fetcher import fetch_all_articles
from bot.poster import post_to_channel
from bot.summarizer import summarize_article

load_dotenv()

MAX_ARTICLES_PER_RUN = 5
HOURS_BACK = 7
SENT_ARTICLES_FILE = Path("data/sent_articles.json")
MAX_SENT_HISTORY = 2000


def load_sent_urls() -> set[str]:
    if SENT_ARTICLES_FILE.exists():
        return set(json.loads(SENT_ARTICLES_FILE.read_text(encoding="utf-8")))
    return set()


def save_sent_urls(urls: set[str]) -> None:
    SENT_ARTICLES_FILE.parent.mkdir(exist_ok=True)
    trimmed = list(urls)[-MAX_SENT_HISTORY:]
    SENT_ARTICLES_FILE.write_text(
        json.dumps(trimmed, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main() -> None:
    sources_path = Path("config/sources.yaml")
    with sources_path.open(encoding="utf-8") as f:
        config = yaml.safe_load(f)

    feeds = config["feeds"]
    sent_urls = load_sent_urls()

    articles = fetch_all_articles(feeds, hours_back=HOURS_BACK)
    new_articles = [a for a in articles if a["url"] not in sent_urls]

    if not new_articles:
        print("No new articles found.")
        return

    to_post = new_articles[:MAX_ARTICLES_PER_RUN]
    print(f"Found {len(new_articles)} new articles, posting {len(to_post)}")

    for article in to_post:
        try:
            message = summarize_article(article)
            post_to_channel(message)
            sent_urls.add(article["url"])
            time.sleep(3)
        except Exception as e:
            print(f"Error processing {article['url']}: {e}")

    save_sent_urls(sent_urls)
    print(f"Done. Total sent history: {len(sent_urls)}")


if __name__ == "__main__":
    main()
