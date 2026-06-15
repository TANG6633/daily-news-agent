from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Sequence
from urllib.parse import urlparse


@dataclass(frozen=True)
class SourceConfig:
    name: str
    url: str
    section: str = "general"
    weight: float = 1.0


@dataclass(frozen=True)
class AgentConfig:
    title: str
    language: str
    timezone: str
    lookback_hours: int
    max_items: int
    max_per_source: int
    sources: Sequence[SourceConfig]


@dataclass(frozen=True)
class Article:
    title: str
    url: str
    source: str
    section: str
    summary: str = ""
    published_at: Optional[datetime] = None
    weight: float = 1.0

    @property
    def domain(self) -> str:
        return urlparse(self.url).netloc.replace("www.", "")


@dataclass(frozen=True)
class Digest:
    title: str
    date: str
    generated_at: datetime
    timezone: str
    language: str
    highlights: List[str]
    article_summaries: Dict[str, str]
    articles: Sequence[Article]
    fetch_errors: Sequence[str] = field(default_factory=list)
    summary_note: str = ""
