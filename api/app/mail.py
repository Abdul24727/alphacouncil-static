"""Transactional email: the "Forgot password?" link, sent over SMTP.

Configured by the environment only (settings.py): SMTP_HOST, SMTP_PORT (587 = STARTTLS,
465 = TLS), SMTP_USER, SMTP_FROM, and SMTP_PASS, which is read here from the process
environment and never kept in settings. Without SMTP_HOST nothing is sent and the log says
email is not configured; the API answers the same either way. Neither the link nor the
recipient is ever logged.
"""

import logging
import os
import re
import smtplib
from email.message import EmailMessage
from email.utils import make_msgid

from .settings import Settings

log = logging.getLogger(__name__)

# CR, LF and NUL end a header line; none of them may reach one.
_HEADER_BREAK = re.compile(r"[\r\n\x00]")

RESET = {
    "en": (
        "Reset your AlphaCouncil password",
        "Someone asked to reset the password of the AlphaCouncil account for this email address.\n\n"
        "Choose a new password here. The link works once, for one hour:\n\n{link}\n\n"
        "If it was not you, ignore this email. Your password stays as it is.\n",
    ),
    "ar": (
        "إعادة تعيين كلمة مرور AlphaCouncil",
        "طلب أحدهم إعادة تعيين كلمة مرور حساب AlphaCouncil المسجّل بهذا البريد الإلكتروني.\n\n"
        "اختر كلمة مرور جديدة من هذا الرابط. يعمل الرابط مرة واحدة خلال ساعة:\n\n{link}\n\n"
        "إن لم تكن أنت، فتجاهل هذه الرسالة. تبقى كلمة مرورك كما هي.\n",
    ),
}


def configured(settings: Settings) -> bool:
    return bool(settings.smtp_host)


def reset_message(settings: Settings, to: str, link: str, locale: str) -> EmailMessage:
    subject, body = RESET.get(locale, RESET["en"])
    msg = EmailMessage()
    msg["From"] = _HEADER_BREAK.sub(" ", settings.smtp_from)
    msg["To"] = _HEADER_BREAK.sub(" ", to)
    msg["Subject"] = subject
    msg["Message-ID"] = make_msgid(domain="alphacouncil.tech")
    msg.set_content(body.format(link=link))
    return msg


def send_password_reset(settings: Settings, to: str, link: str, locale: str) -> bool:
    """True when the mail server accepted the message. Never raises: it runs after the
    response has gone (a background task), and a mail failure must not show to the visitor."""
    if not configured(settings):
        log.warning("Password reset email not sent: email is not configured (SMTP_HOST is not set).")
        return False
    try:
        deliver(settings, reset_message(settings, to, link, locale))
    except Exception as exc:  # noqa: BLE001
        log.error("Password reset email not sent: %s %s", type(exc).__name__, getattr(exc, "smtp_code", ""))
        return False
    return True


def deliver(settings: Settings, msg: EmailMessage) -> None:
    host, port = settings.smtp_host or "", settings.smtp_port
    smtp = smtplib.SMTP_SSL(host, port, timeout=20) if port == 465 else smtplib.SMTP(host, port, timeout=20)
    with smtp:
        if port != 465:
            smtp.starttls()
        if settings.smtp_user:
            smtp.login(settings.smtp_user, os.environ.get("SMTP_PASS", ""))
        smtp.send_message(msg)
