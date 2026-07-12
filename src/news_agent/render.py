from collections import defaultdict
from typing import Dict, List

from .models import Article, Digest


def render_markdown(digest: Digest) -> str:
    lines: List[str] = [
        "# %s - %s" % (digest.title, digest.date),
        "",
        "---",
        "",
        "- **%s**: %s (%s)" % (
            _label(digest.language, "generated"),
            digest.generated_at.isoformat(timespec="seconds"),
            digest.timezone,
        ),
        "- **%s**: %s" % (_label(digest.language, "summary_mode"), digest.summary_note),
        "",
        "## %s" % _label(digest.language, "highlights"),
        "",
    ]

    for idx, highlight in enumerate(digest.highlights, 1):
        lines.append("%s. %s" % (idx, highlight))

    lines.extend(["", "## %s" % _label(digest.language, "details"), ""])

    grouped = _group_by_section(digest.articles)
    for section, articles in grouped.items():
        lines.extend(["### %s" % _section_label(digest.language, section), ""])
        for idx, article in enumerate(articles, 1):
            lines.extend(
                _render_article(
                    idx,
                    article,
                    digest.article_summaries.get(article.url, article.summary),
                    digest.language,
                )
            )

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


def _render_article(index: int, article: Article, summary: str, language: str) -> List[str]:
    published = ""
    if article.published_at is not None:
        published = " | %s: %s" % (_label(language, "published"), article.published_at.date().isoformat())

    return [
        "%s) %s" % (index, article.title),
        "   - %s" % (summary or _label(language, "no_summary")),
        "   - %s: %s%s" % (_label(language, "source"), article.source, published),
        "   - %s: [%s](%s)" % (_label(language, "read_more"), _label(language, "read_more"), article.url),
        "",
    ]


def _label(language: str, key: str) -> str:
    labels = {
        "ja": {
            "generated": "生成日時",
            "summary_mode": "要約モード",
            "highlights": "今日の重要ポイント",
            "details": "ニュース詳細",
            "fetch_notes": "取得に関する注意",
            "sources": "情報源",
            "source": "情報源",
            "read_more": "続きを読む",
            "published": "公開日",
            "no_summary": "要約はありません。",
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
        "ja": {
            "japan": "日本",
            "world": "国際",
            "global": "グローバル",
            "tech": "テクノロジー",
            "general": "総合",
        },
        "en": {
            "japan": "Japan",
            "world": "World",
            "global": "Global",
            "tech": "Technology",
            "general": "General",
        },
    }
    return labels.get(language, labels["en"]).get(section, section.title())


def _source_table_header(language: str) -> str:
    if language == "ja":
        return "| 情報源 | 分類 | リンク |"
    return "| Source | Section | URL |"
