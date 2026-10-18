"""Transactional email over SMTP: the "Forgot password?" link, email confirmation and Pro billing.

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


# --- other account emails ------------------------------------------------------------------------

VERIFY = {
    "en": (
        "Confirm your AlphaCouncil email",
        "Confirm that this is your email address for AlphaCouncil:\n\n{link}\n\n"
        "The link works once, for 48 hours. If you did not create an account, ignore this email.\n",
    ),
    "ar": (
        "تأكيد بريدك في AlphaCouncil",
        "أكّد أن هذا بريدك الإلكتروني في AlphaCouncil:\n\n{link}\n\n"
        "يعمل الرابط مرة واحدة خلال 48 ساعة. إن لم تنشئ حسابًا، فتجاهل هذه الرسالة.\n",
    ),
}

# Pro billing (app/billing.py). {amount} is "79.00 SAR", {date} the next renewal or end date.
BILLING = {
    "receipt": {
        "en": ("Your AlphaCouncil Pro receipt",
               "Thank you. We charged {amount} to your {card} for AlphaCouncil Pro.\n\n"
               "Payment: {payment}\nPro is paid through {date}.{renews}\n\n"
               "Manage your plan: {link}\n"),
        "ar": ("إيصال اشتراك برو في AlphaCouncil",
               "شكرًا لك. خصمنا {amount} من بطاقتك {card} لاشتراك برو في AlphaCouncil.\n\n"
               "رقم الدفعة: {payment}\nبرو مدفوع حتى {date}.{renews}\n\n"
               "إدارة اشتراكك: {link}\n"),
    },
    "reminder": {
        "en": ("Your AlphaCouncil Pro renews on {date}",
               "Your Pro plan renews on {date}: we will charge {amount} to your {card}.\n\n"
               "To stop it, cancel before then: {link}\n"),
        "ar": ("يتجدد اشتراك برو في {date}",
               "يتجدد اشتراك برو في {date}: سنخصم {amount} من بطاقتك {card}.\n\n"
               "لإيقاف التجديد، ألغِه قبل ذلك: {link}\n"),
    },
    "failed": {
        "en": ("We could not renew your AlphaCouncil Pro",
               "Your card was not charged for this month's Pro ({amount}). Pro stays on until {date}; "
               "we will try again. To pay with another card: {link}\n"),
        "ar": ("تعذّر تجديد اشتراك برو",
               "لم نتمكن من خصم رسوم برو لهذا الشهر ({amount}). يبقى برو مفعّلًا حتى {date} وسنحاول مجددًا. "
               "للدفع ببطاقة أخرى: {link}\n"),
    },
    "ended": {
        "en": ("Your AlphaCouncil Pro has ended",
               "Your Pro plan ended on {date}; your account is on the Free plan. Your portfolio and "
               "settings are kept. To come back to Pro: {link}\n"),
        "ar": ("انتهى اشتراك برو",
               "انتهى اشتراك برو في {date}، وحسابك الآن على الخطة المجانية مع الإبقاء على محفظتك وإعداداتك. "
               "للعودة إلى برو: {link}\n"),
    },
}

# Addresses that can never receive mail (RFC 2606 / 6761). The automated checks sign up such
# accounts; sending to them would only spend the mail plan's monthly allowance.
_RESERVED = (".example", ".test", ".invalid", ".localhost")
_RESERVED_DOMAINS = {"example.com", "example.net", "example.org"}


def deliverable(to: str) -> bool:
    domain = to.rsplit("@", 1)[-1].strip().lower()
    return domain not in _RESERVED_DOMAINS and not domain.endswith(_RESERVED)


def _message(settings: Settings, to: str, subject: str, body: str) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = _HEADER_BREAK.sub(" ", settings.smtp_from)
    msg["To"] = _HEADER_BREAK.sub(" ", to)
    msg["Subject"] = _HEADER_BREAK.sub(" ", subject)
    msg["Message-ID"] = make_msgid(domain="alphacouncil.tech")
    msg.set_content(body)
    return msg


def send(settings: Settings, to: str, subject: str, body: str, what: str) -> bool:
    """An account email (verification, billing). Never raises; skips undeliverable test
    addresses; logs what kind of email failed, never the recipient or the content."""
    if not configured(settings):
        log.warning("%s email not sent: email is not configured (SMTP_HOST is not set).", what)
        return False
    if not deliverable(to):
        return False
    try:
        deliver(settings, _message(settings, to, subject, body))
    except Exception as exc:  # noqa: BLE001
        log.error("%s email not sent: %s %s", what, type(exc).__name__, getattr(exc, "smtp_code", ""))
        return False
    return True


def send_verification(settings: Settings, to: str, link: str, locale: str) -> bool:
    subject, body = VERIFY.get(locale, VERIFY["en"])
    return send(settings, to, subject, body.format(link=link), "Verification")


def send_billing(settings: Settings, kind: str, to: str, locale: str, **values: str) -> bool:
    subject, body = BILLING[kind].get(locale, BILLING[kind]["en"])
    return send(settings, to, subject.format(**values), body.format(**values), f"Billing {kind}")


def deliver(settings: Settings, msg: EmailMessage) -> None:
    host, port = settings.smtp_host or "", settings.smtp_port
    smtp = smtplib.SMTP_SSL(host, port, timeout=20) if port == 465 else smtplib.SMTP(host, port, timeout=20)
    with smtp:
        if port != 465:
            smtp.starttls()
        if settings.smtp_user:
            smtp.login(settings.smtp_user, os.environ.get("SMTP_PASS", ""))
        smtp.send_message(msg)
