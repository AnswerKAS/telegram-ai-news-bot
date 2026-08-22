import json
import time
from datetime import datetime, timezone
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
TOPICS_FILE = Path("config/topics.yaml")


def load_sent_urls() -> list[str]:
    if SENT_ARTICLES_FILE.exists():
        return json.loads(SENT_ARTICLES_FILE.read_text(encoding="utf-8"))
    return []


def save_sent_urls(urls: list[str]) -> None:
    SENT_ARTICLES_FILE.parent.mkdir(exist_ok=True)
    trimmed = urls[-MAX_SENT_HISTORY:]
    SENT_ARTICLES_FILE.write_text(
        json.dumps(trimmed, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _article_matches_topic(article: dict, topic: dict) -> bool:
    keywords = [k for k in topic.get("keywords") or [] if k]
    if not keywords:
        return True
    text = " ".join(
        [
            article["title"],
            article.get("description") or "",
            article["source"],
        ]
    ).lower()
    return any(kw.lower() in text for kw in keywords)


def pick_for_topics(articles: list[dict], topics: list[dict], sent_urls: set[str]) -> list[dict]:
    available = [a for a in articles if a["url"] not in sent_urls]
    chosen: list[dict] = []
    claimed: set[str] = set()

    for topic in topics:
        count = int(topic.get("count") or 1)
        matched = [a for a in available if a["url"] not in claimed and _article_matches_topic(a, topic)]
        for article in matched[:count]:
            chosen.append(article)
            claimed.add(article["url"])
        print(f"Topic '{topic['name']}': {len(matched)} matched, picked {min(count, len(matched))}")

    chosen.sort(
        key=lambda a: a["published"] or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return chosen[:MAX_ARTICLES_PER_RUN]


def main() -> None:
    sources_config = _load_yaml(Path("config/sources.yaml"))
    topics_config = _load_yaml(TOPICS_FILE)

    feeds = sources_config["feeds"]
    topics = topics_config["topics"]
    sent_urls = load_sent_urls()
    sent_urls_set = set(sent_urls)

    articles = fetch_all_articles(feeds, hours_back=HOURS_BACK)

    if not topics:
        print("No topics configured in config/topics.yaml.")
        return

    to_post = pick_for_topics(articles, topics, sent_urls_set)

    if not to_post:
        print("No new articles for the configured topics.")
        return

    print(f"Posting {len(to_post)} articles")

    for article in to_post:
        try:
            message = summarize_article(article)
            post_to_channel(message)
            sent_urls.append(article["url"])
            time.sleep(3)
        except Exception as e:
            print(f"Error processing {article['url']}: {e}")

    save_sent_urls(sent_urls)
    print(f"Done. Total sent history: {len(sent_urls[-MAX_SENT_HISTORY:])}")


if __name__ == "__main__":
    main()
