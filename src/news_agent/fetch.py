import html
import calendar
import re
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
