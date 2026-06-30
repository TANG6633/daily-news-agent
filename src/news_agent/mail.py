import os
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import List, Mapping, Optional, Sequence, Tuple


RenderedReport = Tuple[str, str]


@dataclass(frozen=True)
class MailSettings:
    smtp_host: str
    smtp_port: int
    smtp_username: Optional[str]
    smtp_password: Optional[str]
    smtp_starttls: bool
    sender: str
    recipients: List[str]
    subject_template: str


def load_mail_settings(environ: Optional[Mapping[str, str]] = None) -> Optional[MailSettings]:
    env = environ or os.environ
    recipients = _split_addresses(env.get("NEWS_AGENT_EMAIL_TO", ""))
    if not recipients:
        return None

    smtp_host = env.get("NEWS_AGENT_SMTP_HOST", "").strip()
    if not smtp_host:
        raise ValueError("NEWS_AGENT_SMTP_HOST is required when NEWS_AGENT_EMAIL_TO is set")

    smtp_port = _parse_port(env.get("NEWS_AGENT_SMTP_PORT", "587"))
    smtp_username = env.get("NEWS_AGENT_SMTP_USERNAME", "").strip() or None
    smtp_password = env.get("NEWS_AGENT_SMTP_PASSWORD", "") or None
    if smtp_username and not smtp_password:
        raise ValueError("NEWS_AGENT_SMTP_PASSWORD is required when NEWS_AGENT_SMTP_USERNAME is set")

    sender = env.get("NEWS_AGENT_EMAIL_FROM", "").strip() or smtp_username or recipients[0]
    subject_template = (
        env.get("NEWS_AGENT_EMAIL_SUBJECT", "").strip()
        or "Daily News Digest / 每日新闻总结 - {date}"
    )

    return MailSettings(
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_username=smtp_username,
        smtp_password=smtp_password,
        smtp_starttls=_parse_bool(env.get("NEWS_AGENT_SMTP_STARTTLS", "true")),
        sender=sender,
        recipients=recipients,
        subject_template=subject_template,
    )


def build_digest_email(settings: MailSettings, report_date: str, reports: Sequence[RenderedReport]) -> EmailMessage:
    message = EmailMessage()
    message["From"] = settings.sender
    message["To"] = ", ".join(settings.recipients)
    message["Subject"] = settings.subject_template.format(date=report_date)
    message.set_content(_render_email_body(report_date, reports))
    return message


def send_digest_email(settings: MailSettings, report_date: str, reports: Sequence[RenderedReport]) -> None:
    message = build_digest_email(settings, report_date, reports)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
        if settings.smtp_starttls:
            smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password or "")
        smtp.send_message(message)


def _render_email_body(report_date: str, reports: Sequence[RenderedReport]) -> str:
    sections = [
        "Daily News Agent generated the following report(s) for %s." % report_date,
        "",
    ]
    for language, markdown in reports:
        sections.extend(
            [
                "===== %s =====" % language,
                "",
                markdown.strip(),
                "",
            ]
        )
    return "\n".join(sections).rstrip() + "\n"


def _split_addresses(value: str) -> List[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _parse_port(value: str) -> int:
    try:
        port = int(value)
    except ValueError as exc:
        raise ValueError("NEWS_AGENT_SMTP_PORT must be an integer") from exc
    if port <= 0:
        raise ValueError("NEWS_AGENT_SMTP_PORT must be positive")
    return port


def _parse_bool(value: str) -> bool:
    return value.strip().lower() not in {"0", "false", "no", "off"}
