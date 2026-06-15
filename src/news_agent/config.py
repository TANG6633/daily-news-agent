import json
import os
from pathlib import Path
from typing import Any, Dict

from .models import AgentConfig, SourceConfig


def load_config(path: str) -> AgentConfig:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    sources = [_source_from_dict(item) for item in raw.get("sources", [])]
    if not sources:
        raise ValueError("config must contain at least one source")

    timezone = os.getenv("NEWS_AGENT_TIMEZONE", raw.get("timezone", "Asia/Tokyo"))
    language = os.getenv("NEWS_AGENT_LANGUAGE", raw.get("language", "zh"))

    return AgentConfig(
        title=str(raw.get("title", "Daily News Digest")),
        language=language,
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
        section=str(item.get("section", "general")).strip() or "general",
        weight=float(item.get("weight", 1.0)),
    )
