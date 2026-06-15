from collections import defaultdict
from typing import Dict, List

from .models import Article, Digest


def render_markdown(digest: Digest) -> str:
    lines: List[str] = [
        "# %s - %s" % (digest.title, digest.date),
        "",
        "- Generated: %s (%s)" % (digest.generated_at.isoformat(timespec="seconds"), digest.timezone),
        "- Summary mode: %s" % digest.summary_note,
        "",
        "## 今日重点",
        "",
    ]

    for highlight in digest.highlights:
        lines.append("- %s" % highlight)

    lines.extend(["", "## 新闻详情", ""])

    grouped = _group_by_section(digest.articles)
    for section, articles in grouped.items():
        lines.extend(["### %s" % section.title(), ""])
        for article in articles:
            lines.extend(_render_article(article, digest.article_summaries.get(article.url, article.summary)))

    if digest.fetch_errors:
        lines.extend(["## 抓取提示", ""])
        for error in digest.fetch_errors:
            lines.append("- %s" % error)
        lines.append("")

    lines.extend(["## Sources", ""])
    lines.append("| Source | Section | URL |")
    lines.append("| --- | --- | --- |")
    for article in digest.articles:
        lines.append("| %s | %s | %s |" % (article.source, article.section, article.url))

    lines.append("")
    return "\n".join(lines)


def _group_by_section(articles: List[Article]) -> Dict[str, List[Article]]:
    grouped: Dict[str, List[Article]] = defaultdict(list)
    for article in articles:
        grouped[article.section].append(article)
    return dict(grouped)


def _render_article(article: Article, summary: str) -> List[str]:
    published = ""
    if article.published_at is not None:
        published = " | Published: %s" % article.published_at.date().isoformat()

    return [
        "#### %s" % article.title,
        "",
        summary or "暂无摘要。",
        "",
        "Source: %s%s" % (article.source, published),
        "",
        "[Read more](%s)" % article.url,
        "",
    ]
