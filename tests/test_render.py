import unittest
from datetime import datetime, timezone

from news_agent.models import Article, Digest
from news_agent.render import render_markdown


class RenderMarkdownTest(unittest.TestCase):
    def test_render_contains_japanese_sections_and_links(self):
        article = Article(
            title="Sample title",
            url="https://example.com/story",
            source="Example",
            section="world",
            summary="Original summary.",
            published_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
        )
        digest = Digest(
            title="デイリー・インテリジェンス・ブリーフ",
            date="2026-06-15",
            generated_at=datetime(2026, 6, 15, 7, 0, tzinfo=timezone.utc),
            timezone="Asia/Tokyo",
            language="ja",
            highlights=["Important item"],
            article_summaries={article.url: "Rendered summary."},
            articles=[article],
            summary_note="test",
        )

        markdown = render_markdown(digest)

        self.assertIn("# デイリー・インテリジェンス・ブリーフ - 2026-06-15", markdown)
        self.assertIn("## 今日の重要ポイント", markdown)
        self.assertIn("Rendered summary.", markdown)
        self.assertIn("[続きを読む](https://example.com/story)", markdown)

    def test_render_contains_english_sections_and_links(self):
        article = Article(
            title="Sample title",
            url="https://example.com/story",
            source="Example",
            section="world",
            summary="Original summary.",
            published_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
        )
        digest = Digest(
            title="Daily News Digest",
            date="2026-06-15",
            generated_at=datetime(2026, 6, 15, 7, 0, tzinfo=timezone.utc),
            timezone="Asia/Tokyo",
            language="en",
            highlights=["Important item"],
            article_summaries={article.url: "Rendered summary."},
            articles=[article],
            summary_note="test",
        )

        markdown = render_markdown(digest)

        self.assertIn("# Daily News Digest - 2026-06-15", markdown)
        self.assertIn("## Highlights", markdown)
        self.assertIn("Rendered summary.", markdown)
        self.assertIn("[Read more](https://example.com/story)", markdown)


if __name__ == "__main__":
    unittest.main()
