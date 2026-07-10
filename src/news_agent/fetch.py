import html
import calendar
import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import feedparser

from .models import Article, SourceConfig

_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")


def collect_articles(
    sources: Sequence[SourceConfig],
    since: datetime,
    max_per_source: int,
) -> Tuple[List[Article], List[str]]:
    articles: List[Article] = []
    errors: List[str] = []

    for source in sources:
        try:
            source_articles = fetch_feed(source, max_per_source=max_per_source)
            articles.extend(_filter_recent(source_articles, since))
        except Exception as exc:  # pragma: no cover - network failures vary
            errors.append("%s: %s" % (source.name, exc))

    return dedupe_articles(articles), errors


def fetch_feed(source: SourceConfig, max_per_source: int = 20) -> List[Article]:
    if source.kind == "hacker_news":
        return _fetch_hacker_news(source, max_per_source)
    if source.kind == "gdelt":
        return _fetch_gdelt(source, max_per_source)
    if source.kind != "rss":
        raise ValueError("unsupported source kind: %s" % source.kind)

    request = urllib.request.Request(
        source.url,
        headers={
            "User-Agent": (
                "daily-news-agent/0.1 "
                "(RSS digest; https://github.com/)"
            )
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        raw = response.read(2_500_000)

    parsed = feedparser.parse(raw)
    if parsed.bozo and not parsed.entries:
        raise ValueError("feed could not be parsed")

    articles: List[Article] = []
    for entry in parsed.entries[:max_per_source]:
        title = _clean_text(entry.get("title", ""))
        url = str(entry.get("link", "")).strip()
        if not title or not url:
            continue

        summary = _clean_text(
            entry.get("summary")
            or entry.get("description")
            or entry.get("subtitle")
            or ""
        )
        articles.append(
            Article(
                title=title,
                url=url,
                source=source.name,
                section=source.section,
                summary=summary,
                published_at=_entry_datetime(entry),
                weight=source.weight,
            )
        )

    return articles


def _fetch_hacker_news(source: SourceConfig, max_per_source: int) -> List[Article]:
    base_url = source.url.rstrip("/")
    story_ids = _fetch_json("%s/topstories.json" % base_url)[:max_per_source]
    articles = []
    for story_id in story_ids:
        item = _fetch_json("%s/item/%s.json" % (base_url, story_id))
        if item.get("type") != "story" or not item.get("title"):
            continue
        url = str(item.get("url") or "https://news.ycombinator.com/item?id=%s" % story_id)
        score = item.get("score", 0)
        comments = item.get("descendants", 0)
        articles.append(
            Article(
                title=_clean_text(item["title"]),
                url=url,
                source=source.name,
                section=source.section,
                summary="%s points · %s comments" % (score, comments),
                published_at=datetime.fromtimestamp(item.get("time", 0), tz=timezone.utc),
                weight=source.weight,
            )
        )
    return articles


def _fetch_gdelt(source: SourceConfig, max_per_source: int) -> List[Article]:
    query = source.query or "Japan OR technology OR \"artificial intelligence\""
    parameters = urllib.parse.urlencode(
        {
            "query": query,
            "mode": "artlist",
            "format": "json",
            "maxrecords": max_per_source,
            "timespan": "30h",
            "sort": "datedesc",
        }
    )
    payload = _fetch_json("%s?%s" % (source.url, parameters))
    articles = []
    for item in payload.get("articles", []):
        title = _clean_text(item.get("title", ""))
        url = str(item.get("url", "")).strip()
        if not title or not url:
            continue
        domain = str(item.get("domain", "")).strip()
        articles.append(
            Article(
                title=title,
                url=url,
                source="%s%s" % (source.name, " · %s" % domain if domain else ""),
                section=source.section,
                published_at=_gdelt_datetime(str(item.get("seendate", ""))),
                weight=source.weight,
            )
        )
    return articles


def _fetch_json(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": "daily-news-agent/0.1"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read(2_500_000).decode("utf-8"))


def _gdelt_datetime(value: str) -> Optional[datetime]:
    try:
        return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def dedupe_articles(articles: Iterable[Article]) -> List[Article]:
    seen: Dict[str, Article] = {}
    for article in articles:
        key = _dedupe_key(article)
        current = seen.get(key)
        if current is None or article.weight > current.weight:
            seen[key] = article
    return list(seen.values())


def rank_articles(articles: Sequence[Article], limit: int) -> List[Article]:
    now = datetime.now(timezone.utc)

    def score(article: Article) -> Tuple[float, str]:
        age_hours = 12.0
        if article.published_at is not None:
            age_seconds = max((now - article.published_at.astimezone(timezone.utc)).total_seconds(), 0)
            age_hours = age_seconds / 3600
        recency = max(0.0, 36.0 - age_hours) / 36.0
        text_bonus = min(len(article.summary) / 500.0, 1.0) * 0.15
        return (article.weight + recency + text_bonus, article.title.lower())

    return sorted(articles, key=score, reverse=True)[:limit]


def _filter_recent(articles: Iterable[Article], since: datetime) -> Iterable[Article]:
    since_utc = since.astimezone(timezone.utc)
    for article in articles:
        if article.published_at is None:
            yield article
            continue
        if article.published_at.astimezone(timezone.utc) >= since_utc:
            yield article


def _entry_datetime(entry: Dict[str, object]) -> Optional[datetime]:
    for key in ("published_parsed", "updated_parsed", "created_parsed"):
        value = entry.get(key)
        if value:
            return datetime.fromtimestamp(calendar.timegm(value), tz=timezone.utc)

    for key in ("published", "updated", "created"):
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            try:
                parsed = parsedate_to_datetime(value)
            except (TypeError, ValueError):
                continue
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
    return None


def _clean_text(value: object) -> str:
    text = html.unescape(str(value or ""))
    text = _TAG_RE.sub(" ", text)
    text = _SPACE_RE.sub(" ", text)
    return text.strip()


def _dedupe_key(article: Article) -> str:
    if article.url:
        return article.url.split("#", 1)[0].rstrip("/")
    return article.title.lower()
