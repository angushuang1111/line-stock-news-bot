from dataclasses import dataclass
from typing import List
import time
import feedparser

from config import RSS_URLS, MAX_RSS_ITEMS_PER_SOURCE
from news.news_cleaner import clean_html, short_text


@dataclass
class NewsItem:
    title: str
    link: str
    summary: str
    source: str
    published: str


def _entry_text(entry) -> str:
    title = getattr(entry, "title", "") or ""
    summary = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
    return f"{title} {clean_html(summary)}"


def _published_text(entry) -> str:
    if hasattr(entry, "published"):
        return entry.published
    if hasattr(entry, "updated"):
        return entry.updated
    return ""


def _source_name(feed, url: str) -> str:
    title = getattr(feed.feed, "title", "") if hasattr(feed, "feed") else ""
    if title:
        return title
    if "yahoo" in url:
        return "Yahoo 股市 RSS"
    return url


def fetch_market_news(limit_per_source: int = MAX_RSS_ITEMS_PER_SOURCE) -> List[NewsItem]:
    """抓取一般財經 RSS 新聞。"""
    items: List[NewsItem] = []
    seen_links = set()

    for url in RSS_URLS:
        try:
            feed = feedparser.parse(url)
            source = _source_name(feed, url)
            for entry in feed.entries[:limit_per_source]:
                link = getattr(entry, "link", "") or ""
                if not link or link in seen_links:
                    continue
                seen_links.add(link)
                summary = clean_html(getattr(entry, "summary", "") or getattr(entry, "description", "") or "")
                items.append(
                    NewsItem(
                        title=clean_html(getattr(entry, "title", "") or "無標題"),
                        link=link,
                        summary=summary,
                        source=source,
                        published=_published_text(entry),
                    )
                )
        except Exception as exc:
            print(f"[RSS ERROR] {url}: {exc}")
        time.sleep(0.2)

    return items


def fetch_stock_news(stock_code: str, stock_name: str = "", max_items: int = 5) -> List[NewsItem]:
    """從 RSS 裡面找出跟個股相關的新聞。"""
    all_items = fetch_market_news()
    keywords = [stock_code]
    if stock_name:
        keywords.append(stock_name)

    matched: List[NewsItem] = []
    for item in all_items:
        text = f"{item.title} {item.summary}"
        if any(k and k in text for k in keywords):
            matched.append(item)
        if len(matched) >= max_items:
            break

    return matched


def news_item_to_line(item: NewsItem) -> str:
    return f"{item.title}\n{short_text(item.summary, 100)}\n來源：{item.source}\n{item.link}"
