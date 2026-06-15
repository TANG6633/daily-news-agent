from collections import defaultdict
from typing import Dict, List

from .models import Article, Digest


def render_markdown(digest: Digest) -> str:
    lines: List[str] = [
        "# %s - %s" % (digest.title, digest.date),
        "",
        "- %s: %s (%s)" % (_label(digest.language, "generated"), digest.generated_at.isoformat(timespec="seconds"), digest.timezone),
        "- %s: %s" % (_label(digest.language, "summary_mode"), digest.summary_note),
        "",
        "## %s" % _label(digest.language, "highlights"),
        "",
    ]

    for highlight in digest.highlights:
        lines.append("- %s" % highlight)

    lines.extend(["", "## %s" % _label(digest.language, "details"), ""])

    grouped = _group_by_section(digest.articles)
    for section, articles in grouped.items():
        lines.extend(["### %s" % _section_label(digest.language, section), ""])
        for article in articles:
            lines.extend(_render_article(article, digest.article_summaries.get(article.url, article.summary), digest.language))

    if digest.fetch_errors:
        lines.extend(["## %s" % _label(digest.language, "fetch_notes"), ""])
        for error in digest.fetch_errors:
            lines.append("- %s" % error)
        lines.append("")

    lines.extend(["## %s" % _label(digest.language, "sources"), ""])
    lines.append(_source_table_header(digest.language))
    lines.append("| --- | --- | --- |")
    for article in digest.articles:
        lines.append("| %s | %s | %s |" % (article.source, _section_label(digest.language, article.section), article.url))

    lines.append("")
    return "\n".join(lines)


def _group_by_section(articles: List[Article]) -> Dict[str, List[Article]]:
    grouped: Dict[str, List[Article]] = defaultdict(list)
    for article in articles:
        grouped[article.section].append(article)
    return dict(grouped)


def _render_article(article: Article, summary: str, language: str) -> List[str]:
    published = ""
    if article.published_at is not None:
        published = " | %s: %s" % (_label(language, "published"), article.published_at.date().isoformat())

    return [
        "#### %s" % article.title,
        "",
        summary or _label(language, "no_summary"),
        "",
        "%s: %s%s" % (_label(language, "source"), article.source, published),
        "",
        "[%s](%s)" % (_label(language, "read_more"), article.url),
        "",
    ]


def _label(language: str, key: str) -> str:
    labels = {
        "zh": {
            "generated": "生成时间",
            "summary_mode": "摘要模式",
            "highlights": "今日重点",
            "details": "新闻详情",
            "fetch_notes": "抓取提示",
            "sources": "来源列表",
            "source": "来源",
            "read_more": "阅读全文",
            "published": "发布时间",
            "no_summary": "暂无摘要。",
        },
        "en": {
            "generated": "Generated",
            "summary_mode": "Summary mode",
            "highlights": "Highlights",
            "details": "News Details",
            "fetch_notes": "Fetch Notes",
            "sources": "Sources",
            "source": "Source",
            "read_more": "Read more",
            "published": "Published",
            "no_summary": "No summary available.",
        },
    }
    return labels.get(language, labels["en"]).get(key, key)


def _section_label(language: str, section: str) -> str:
    labels = {
        "zh": {
            "japan": "日本",
            "world": "国际",
            "tech": "科技",
            "general": "综合",
        },
        "en": {
            "japan": "Japan",
            "world": "World",
            "tech": "Technology",
            "general": "General",
        },
    }
    return labels.get(language, labels["en"]).get(section, section.title())


def _source_table_header(language: str) -> str:
    if language == "zh":
        return "| 来源 | 分类 | 链接 |"
    return "| Source | Section | URL |"
