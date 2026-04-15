#!/usr/bin/env python3
"""
Mailer: sends the HTML digest via Gmail SMTP using an App Password.
"""

import logging
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

log = logging.getLogger(__name__)


def send_digest(html_content: str, run_time: datetime) -> None:
    gmail_user = os.environ["GMAIL_USER"]
    gmail_password = os.environ["GMAIL_APP_PASSWORD"]
    to_email = os.environ["DIGEST_TO_EMAIL"]

    subject = f"MR Digest — {run_time.strftime('%B %-d, %Y')}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"MR Digest <{gmail_user}>"
    msg["To"] = to_email

    msg.attach(MIMEText(html_content, "html", "utf-8"))

    log.info("Sending digest to %s via Gmail SMTP...", to_email)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, to_email, msg.as_string())

    log.info("Email sent: %s", subject)


if __name__ == "__main__":
    # Quick test: send a dummy email
    logging.basicConfig(level=logging.INFO)
    test_html = "<h1>Test</h1><p>Mailer is working.</p>"
    send_digest(test_html, datetime.now())
