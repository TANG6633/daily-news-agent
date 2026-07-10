import json
import os
import re
from typing import Dict, List, Sequence, Tuple

from .models import Article


def summarize_articles(
    articles: Sequence[Article],
    language: str,
    model: str,
) -> Tuple[List[str], Dict[str, str], str]:
    if not articles:
        return [_empty_highlight(language)], {}, "no articles"

    if os.getenv("OPENAI_API_KEY"):
        try:
            return _summarize_with_openai(articles, language=language, model=model)
        except Exception as exc:  # pragma: no cover - external service
            highlights, summaries = _summarize_locally(articles, language)
            return highlights, summaries, _fallback_note(language, str(exc))

    highlights, summaries = _summarize_locally(articles, language)
    return highlights, summaries, _local_note(language)


def _summarize_with_openai(
    articles: Sequence[Article],
    language: str,
    model: str,
) -> Tuple[List[str], Dict[str, str], str]:
    from openai import OpenAI

    client = OpenAI()
    payload = [
        {
            "title": article.title,
            "source": article.source,
            "section": article.section,
            "url": article.url,
            "summary": article.summary[:700],
        }
        for article in articles
    ]
    prompt = (
        "You are a daily news briefing agent. Create a concise news digest in %s. "
        "Return strict JSON only, with this schema: "
        '{"highlights":["..."],"items":[{"url":"...","summary":"..."}]}. '
        "Highlights should explain the most important cross-story signals. "
        "Each item summary should be one or two short sentences, neutral, and based only on the supplied text.\n\n"
        "Articles:\n%s"
        % (_language_name(language), json.dumps(payload, ensure_ascii=False))
    )

    text = _call_openai(client, model, prompt)
    data = _parse_json(text)

    highlights = [str(item).strip() for item in data.get("highlights", []) if str(item).strip()]
    item_summaries = {}
    for item in data.get("items", []):
        url = str(item.get("url", "")).strip()
        summary = str(item.get("summary", "")).strip()
        if url and summary:
            item_summaries[url] = summary

    _, fallback_summaries = _summarize_locally(articles, language)
    for article in articles:
        item_summaries.setdefault(article.url, fallback_summaries[article.url])

    if not highlights:
        highlights, _ = _summarize_locally(articles, language)

    return highlights[:6], item_summaries, "openai:%s" % model


def _call_openai(client: object, model: str, prompt: str) -> str:
    if hasattr(client, "responses"):
        response = client.responses.create(model=model, input=prompt)
        text = getattr(response, "output_text", "") or ""
        if text:
            return text

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "Return strict JSON only.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )
    return response.choices[0].message.content or ""


def _summarize_locally(articles: Sequence[Article], language: str) -> Tuple[List[str], Dict[str, str]]:
    highlights = []
    for article in articles[:5]:
        if language == "ja":
            highlights.append("%s：%s" % (article.source, _shorten(article.title, 90)))
        else:
            highlights.append("%s: %s" % (article.source, _shorten(article.title, 90)))

    summaries: Dict[str, str] = {}
    for article in articles:
        seed = article.summary or article.title
        summaries[article.url] = _shorten(_first_sentence(seed), 220)

    return highlights, summaries


def _language_name(language: str) -> str:
    return {
        "ja": "Japanese",
        "en": "English",
    }.get(language, language)


def _empty_highlight(language: str) -> str:
    if language == "ja":
        return "本日は条件に合うニュースを取得できませんでした。"
    return "No eligible news articles were collected today."


def _local_note(language: str) -> str:
    if language == "ja":
        return "ローカル要約モード：より自然な日英要約には OPENAI_API_KEY を設定してください"
    return "local fallback; set OPENAI_API_KEY for richer bilingual summaries"


def _fallback_note(language: str, error: str) -> str:
    if language == "ja":
        return "OpenAI 要約に失敗したためローカル要約を使用しました：%s" % error
    return "OpenAI summary failed; used local fallback: %s" % error


def _parse_json(text: str) -> Dict[str, object]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def _first_sentence(text: str) -> str:
    parts = re.split(r"(?<=[.!?。！？])\s+", text.strip())
    return parts[0] if parts and parts[0] else text.strip()


def _shorten(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."
