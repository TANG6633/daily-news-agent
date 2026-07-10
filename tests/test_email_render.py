import unittest
from datetime import datetime, timezone

from news_agent.email_render import render_email_html, render_email_text
from news_agent.models import Article, Digest


def _digest(language, highlights):
    article = Article(
        title="Sample <story>",
        url="https://example.com/story",
        source="Example News",
        section="world",
        summary="Summary",
        published_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
    )
    return Digest(
        title="Brief",
        date="2026-07-10",
        generated_at=datetime(2026, 7, 10, 8, 30, tzinfo=timezone.utc),
        timezone="Asia/Tokyo",
        language=language,
        highlights=highlights,
        article_summaries={article.url: "Summary"},
        articles=[article],
        summary_note="openai:test",
    )


class EmailRenderTest(unittest.TestCase):
    def test_html_contains_two_language_cards_and_report_links(self):
        japanese = _digest("ja", ["日本語の重要事項", "<unsafe>"])
        english = _digest("en", ["English key signal"])

        html = render_email_html(japanese, english)

        self.assertIn("DAILY INTELLIGENCE BRIEF", html)
        self.assertIn("日本語版", html)
        self.assertIn("ENGLISH EDITION", html)
        self.assertIn("&lt;unsafe&gt;", html)
        self.assertIn("reports/ja/2026-07-10.md", html)
        self.assertIn("reports/en/2026-07-10.md", html)

    def test_plain_text_fallback_contains_both_languages(self):
        text = render_email_text(_digest("ja", ["日本語の重要事項"]), _digest("en", ["English key signal"]))

        self.assertIn("日本語版", text)
        self.assertIn("English edition", text)
        self.assertIn("reports/ja/2026-07-10.md", text)


if __name__ == "__main__":
    unittest.main()
