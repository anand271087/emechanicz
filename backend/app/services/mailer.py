import smtplib
from email.message import EmailMessage

from app.config import settings


class MailError(Exception):
    pass


class MailNotConfigured(MailError):
    pass


def send_mail(to: list[str], cc: list[str], subject: str, body: str,
              attachments: list[tuple[str, bytes, str]]) -> None:
    """Send via the configured SMTP mailbox. attachments: (filename, bytes, mime type)."""
    if not settings.smtp_host:
        raise MailNotConfigured("Email is not configured — set SMTP_* in backend/.env")
    msg = EmailMessage()
    msg["From"] = settings.smtp_from or settings.smtp_user
    msg["To"] = ", ".join(to)
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg["Subject"] = subject
    msg.set_content(body)
    for filename, content, mime in attachments:
        maintype, subtype = mime.split("/", 1)
        msg.add_attachment(content, maintype=maintype, subtype=subtype, filename=filename)

    try:
        if settings.smtp_port == 465:
            server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=30)
        else:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30)
        with server:
            if settings.smtp_port != 465:
                server.starttls()
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
    except (smtplib.SMTPException, OSError) as e:
        raise MailError(f"Could not send email: {e}") from e
