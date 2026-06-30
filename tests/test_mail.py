import unittest
from unittest.mock import MagicMock, patch

from news_agent.mail import (
    build_digest_email,
    load_mail_settings,
    send_digest_email,
)


class MailSettingsTest(unittest.TestCase):
    def test_settings_are_disabled_without_recipient(self):
        settings = load_mail_settings({})

        self.assertIsNone(settings)

    def test_settings_parse_recipients_and_defaults(self):
        settings = load_mail_settings(
            {
                "NEWS_AGENT_EMAIL_TO": "one@example.com, two@example.com",
                "NEWS_AGENT_SMTP_HOST": "smtp.example.com",
                "NEWS_AGENT_SMTP_USERNAME": "sender@example.com",
                "NEWS_AGENT_SMTP_PASSWORD": "secret",
            }
        )

        self.assertIsNotNone(settings)
        assert settings is not None
        self.assertEqual(settings.smtp_port, 587)
        self.assertEqual(settings.sender, "sender@example.com")
        self.assertEqual(settings.recipients, ["one@example.com", "two@example.com"])

    def test_email_body_contains_each_rendered_report(self):
        settings = load_mail_settings(
            {
                "NEWS_AGENT_EMAIL_TO": "reader@example.com",
                "NEWS_AGENT_SMTP_HOST": "smtp.example.com",
                "NEWS_AGENT_SMTP_USERNAME": "sender@example.com",
                "NEWS_AGENT_SMTP_PASSWORD": "secret",
            }
        )
        assert settings is not None

        message = build_digest_email(
            settings,
            "2026-06-29",
            [("zh", "# 中文日报"), ("en", "# English Digest")],
        )

        self.assertEqual(message["Subject"], "Daily News Digest / 每日新闻总结 - 2026-06-29")
        body = message.get_content()
        self.assertIn("===== zh =====", body)
        self.assertIn("# 中文日报", body)
        self.assertIn("===== en =====", body)
        self.assertIn("# English Digest", body)


class SendDigestEmailTest(unittest.TestCase):
    def test_send_uses_smtp_settings(self):
        settings = load_mail_settings(
            {
                "NEWS_AGENT_EMAIL_TO": "reader@example.com",
                "NEWS_AGENT_SMTP_HOST": "smtp.example.com",
                "NEWS_AGENT_SMTP_PORT": "2525",
                "NEWS_AGENT_SMTP_USERNAME": "sender@example.com",
                "NEWS_AGENT_SMTP_PASSWORD": "secret",
            }
        )
        assert settings is not None

        with patch("news_agent.mail.smtplib.SMTP") as smtp_cls:
            smtp = MagicMock()
            smtp_cls.return_value.__enter__.return_value = smtp

            send_digest_email(settings, "2026-06-29", [("zh", "# 中文日报")])

        smtp_cls.assert_called_once_with("smtp.example.com", 2525, timeout=30)
        smtp.starttls.assert_called_once_with()
        smtp.login.assert_called_once_with("sender@example.com", "secret")
        smtp.send_message.assert_called_once()


if __name__ == "__main__":
    unittest.main()
