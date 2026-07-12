import json
import os
from pathlib import Path
from typing import Any, Dict, List

from .models import AgentConfig, SourceConfig


def load_config(path: str) -> AgentConfig:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    sources = [_source_from_dict(item) for item in raw.get("sources", [])]
    if not sources:
        raise ValueError("config must contain at least one source")

    timezone = os.getenv("NEWS_AGENT_TIMEZONE", raw.get("timezone", "Asia/Tokyo"))
    languages = _load_languages(raw)
    titles = _load_titles(raw)

    return AgentConfig(
        titles=titles,
        languages=languages,
        timezone=timezone,
        lookback_hours=int(raw.get("lookback_hours", 24)),
        max_items=int(raw.get("max_items", 15)),
        max_per_source=int(raw.get("max_per_source", 20)),
        sources=sources,
    )


def _source_from_dict(item: Dict[str, Any]) -> SourceConfig:
    name = str(item.get("name", "")).strip()
    url = str(item.get("url", "")).strip()
    if not name or not url:
        raise ValueError("each source needs name and url")

    return SourceConfig(
        name=name,
        url=url,
        kind=str(item.get("kind", "rss")).strip() or "rss",
        query=str(item.get("query", "")).strip(),
        section=str(item.get("section", "general")).strip() or "general",
        weight=float(item.get("weight", 1.0)),
    )


def _load_languages(raw: Dict[str, Any]) -> List[str]:
    env_value = os.getenv("NEWS_AGENT_LANGUAGES") or os.getenv("NEWS_AGENT_LANGUAGE")
    if env_value:
        languages = [part.strip() for part in env_value.split(",")]
    else:
        configured = raw.get("languages", raw.get("language", ["ja", "en"]))
        if isinstance(configured, str):
            languages = [configured]
        else:
            languages = [str(item).strip() for item in configured]

    languages = [language for language in languages if language]
    if not languages:
        raise ValueError("config must contain at least one language")
    return languages


def _load_titles(raw: Dict[str, Any]) -> Dict[str, str]:
    titles = raw.get("titles")
    if isinstance(titles, dict):
        return {str(key): str(value) for key, value in titles.items()}

    title = str(raw.get("title", "Daily News Digest"))
    return {
        "ja": title if title != "Daily News Digest" else "デイリー・ニュース・ダイジェスト",
        "en": "Daily News Digest",
    }
