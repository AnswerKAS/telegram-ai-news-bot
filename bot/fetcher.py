import time
from datetime import datetime, timedelta, timezone
from typing import Any

import feedparser


def _parse_date(entry: Any) -> datetime | None:
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            return datetime(*t[:6], tzinfo=timezone.utc)
    return None


def _fetch_feed(feed_url: str, source_name: str, cutoff: datetime) -> list[dict]:
    try:
        parsed = feedparser.parse(feed_url, request_headers={"User-Agent": "Mozilla/5.0"})
        articles = []
        for entry in parsed.entries:
            url = getattr(entry, "link", "") or getattr(entry, "id", "")
            if not url:
                continue
            pub_date = _parse_date(entry)
            if pub_date and pub_date < cutoff:
                continue
            articles.append({
                "title": getattr(entry, "title", "").strip(),
                "url": url,
                "description": (getattr(entry, "summary", "") or getattr(entry, "description", "")).strip(),
                "published": pub_date,
                "source": source_name,
            })
        return articles
    except Exception as e:
        print(f"Error fetching {source_name} ({feed_url}): {e}")
        return []


def fetch_all_articles(feeds: list[dict], hours_back: int = 7) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    all_articles: list[dict] = []
    seen_urls: set[str] = set()

    for feed in feeds:
        articles = _fetch_feed(feed["url"], feed["name"], cutoff)
        for article in articles:
            if article["url"] not in seen_urls:
                seen_urls.add(article["url"])
                all_articles.append(article)
        time.sleep(0.5)

    all_articles.sort(
        key=lambda a: a["published"] or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return all_articles
