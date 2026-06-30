import argparse
import os
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from .config import load_config
from .fetch import collect_articles, rank_articles
from .mail import load_mail_settings, send_digest_email
from .models import Digest
from .render import render_markdown
from .summarize import summarize_articles


def main() -> int:
    _load_dotenv()
    parser = argparse.ArgumentParser(description="Generate a daily RSS news digest.")
    parser.add_argument("--config", default="config/feeds.json", help="Path to config JSON.")
    parser.add_argument("--output", default="reports", help="Output directory.")
    parser.add_argument("--date", default=None, help="Report date, formatted as YYYY-MM-DD.")
    parser.add_argument("--dry-run", action="store_true", help="Print the digest instead of writing it.")
    parser.add_argument("--email", action="store_true", help="Send the generated digest by email when mail settings are configured.")
    args = parser.parse_args()

    config = load_config(args.config)
    tz = ZoneInfo(config.timezone)
    now = datetime.now(tz)
    report_date = args.date or now.date().isoformat()
    since = now - timedelta(hours=config.lookback_hours)
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    articles, fetch_errors = collect_articles(
        config.sources,
        since=since,
        max_per_source=config.max_per_source,
    )
    ranked = rank_articles(articles, limit=config.max_items)
    rendered = []
    for language in config.languages:
        highlights, summaries, summary_note = summarize_articles(
            ranked,
            language=language,
            model=model,
        )

        digest = Digest(
            title=_title_for_language(config.titles, language),
            date=report_date,
            generated_at=now,
            timezone=config.timezone,
            language=language,
            highlights=highlights,
            article_summaries=summaries,
            articles=ranked,
            fetch_errors=fetch_errors,
            summary_note=summary_note,
        )
        rendered.append((language, render_markdown(digest)))

    if args.dry_run:
        for language, markdown in rendered:
            print("<!-- language: %s -->" % language)
            print(markdown)
        return 0

    output_dir = Path(args.output)
    for language, markdown in rendered:
        language_dir = output_dir / language if len(rendered) > 1 else output_dir
        language_dir.mkdir(parents=True, exist_ok=True)
        output_path = language_dir / ("%s.md" % report_date)
        output_path.write_text(markdown, encoding="utf-8")
        print("Wrote %s with %s articles." % (output_path, len(ranked)))
    if args.email:
        mail_settings = load_mail_settings()
        if mail_settings is None:
            print("Email delivery skipped because NEWS_AGENT_EMAIL_TO is not set.")
        else:
            send_digest_email(mail_settings, report_date, rendered)
            print("Sent digest email to %s." % ", ".join(mail_settings.recipients))
    return 0


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


def _title_for_language(titles: object, language: str) -> str:
    if isinstance(titles, dict) and language in titles:
        return str(titles[language])
    return "每日新闻总结" if language == "zh" else "Daily News Digest"


if __name__ == "__main__":
    raise SystemExit(main())
