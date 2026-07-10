from html import escape
from typing import Dict, Iterable, List

from .models import Digest


_REPORT_URL = "https://github.com/TANG6633/daily-news-agent/blob/main/reports/{language}/{date}.md"


def render_email_html(japanese: Digest, english: Digest) -> str:
    """Render a compact, Gmail-friendly HTML briefing from two language digests."""
    report_urls = _report_urls(japanese.date)
    source_count = len({article.source for article in japanese.articles})
    generated = japanese.generated_at.strftime("%Y-%m-%d · %H:%M %Z")

    return """<!doctype html>
<html lang="ja">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f3f5f8;color:#172033;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;">
  <div style="display:none;max-height:0;overflow:hidden;opacity:0;">Your Japanese and English daily intelligence brief.</div>
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#f3f5f8;">
    <tr><td align="center" style="padding:28px 12px;">
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width:680px;background:#ffffff;border-radius:18px;overflow:hidden;box-shadow:0 8px 24px rgba(15,23,42,0.08);">
        <tr><td style="padding:34px 36px 30px;background:#101b32;color:#ffffff;">
          <div style="font-size:11px;letter-spacing:1.5px;font-weight:700;color:#9cc7ff;">DAILY INTELLIGENCE BRIEF</div>
          <div style="margin-top:9px;font-size:27px;line-height:1.25;font-weight:700;">デイリー・インテリジェンス・ブリーフ</div>
          <div style="margin-top:12px;font-size:14px;line-height:1.5;color:#c8d6ee;">{date} &nbsp;·&nbsp; {generated} &nbsp;·&nbsp; {sources} sources</div>
        </td></tr>
        <tr><td style="padding:28px 28px 6px;">
          {japanese_section}
          {english_section}
        </td></tr>
        <tr><td style="padding:12px 36px 32px;color:#77839a;font-size:12px;line-height:1.6;">
          Generated from cited source material with OpenAI summaries. Open the full reports for all articles and original links.
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>""".format(
        date=escape(japanese.date),
        generated=escape(generated),
        sources=source_count,
        japanese_section=_language_section(
            kicker="日本語版",
            title="今日の重要ポイント",
            highlights=japanese.highlights,
            button_label="レポートを開く",
            button_url=report_urls["ja"],
            accent="#2563eb",
        ),
        english_section=_language_section(
            kicker="ENGLISH EDITION",
            title="Key signals today",
            highlights=english.highlights,
            button_label="Open full report",
            button_url=report_urls["en"],
            accent="#0f766e",
        ),
    )


def render_email_text(japanese: Digest, english: Digest) -> str:
    """Return a readable plain-text fallback for email clients that disable HTML."""
    report_urls = _report_urls(japanese.date)
    lines = [
        "DAILY INTELLIGENCE BRIEF / デイリー・インテリジェンス・ブリーフ",
        japanese.date,
        "",
        "日本語版｜今日の重要ポイント",
    ]
    lines.extend("- %s" % item for item in japanese.highlights)
    lines.extend(["", "English edition | Key signals today"])
    lines.extend("- %s" % item for item in english.highlights)
    lines.extend(
        [
            "",
            "日本語版: %s" % report_urls["ja"],
            "English version: %s" % report_urls["en"],
            "",
        ]
    )
    return "\n".join(lines)


def _language_section(
    kicker: str,
    title: str,
    highlights: Iterable[str],
    button_label: str,
    button_url: str,
    accent: str,
) -> str:
    items: List[str] = []
    for index, highlight in enumerate(list(highlights)[:5], 1):
        items.append(
            "<tr><td style=\"padding:0 0 12px;vertical-align:top;\">"
            "<span style=\"display:inline-block;width:21px;height:21px;line-height:21px;border-radius:50%;"
            "background:{accent};color:#ffffff;text-align:center;font-size:11px;font-weight:700;\">{index}</span>"
            "<span style=\"padding-left:10px;font-size:14px;line-height:1.55;color:#25324a;\">{highlight}</span>"
            "</td></tr>".format(accent=accent, index=index, highlight=escape(highlight))
        )

    return """
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin:0 0 22px;border:1px solid #e5eaf2;border-radius:14px;">
  <tr><td style="padding:22px 22px 8px;">
    <div style="font-size:11px;letter-spacing:1.2px;font-weight:700;color:{accent};">{kicker}</div>
    <div style="margin-top:5px;font-size:20px;line-height:1.35;font-weight:700;color:#172033;">{title}</div>
  </td></tr>
  <tr><td style="padding:12px 22px 5px;"><table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">{items}</table></td></tr>
  <tr><td style="padding:8px 22px 24px;">
    <a href="{button_url}" style="display:inline-block;background:{accent};border-radius:8px;padding:11px 16px;color:#ffffff;text-decoration:none;font-size:13px;font-weight:700;">{button_label} →</a>
  </td></tr>
</table>""".format(
        accent=accent,
        kicker=escape(kicker),
        title=escape(title),
        items="".join(items),
        button_url=escape(button_url, quote=True),
        button_label=escape(button_label),
    )


def _report_urls(report_date: str) -> Dict[str, str]:
    return {
        language: _REPORT_URL.format(language=language, date=report_date)
        for language in ("ja", "en")
    }
