"""Build the Happy Hour invitation and, only if asked, send it.

The invitation itself is the static page ``index.html`` at the repo root.
``build_email()`` returns a subject and that HTML, the script writes a local
preview, and nothing is sent unless you pass ``--send`` with SMTP settings.
"""

from __future__ import annotations

import argparse
import os
import smtplib
import sys
from email.message import EmailMessage
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
INVITE_PATH = ROOT / "index.html"
PREVIEW_PATH = HERE / "happy_hour_preview.html"

DEFAULT_DATE = "Thursday, October 30, 2026"
DEFAULT_TIME = "5:00 PM (Vienna time)"
DEFAULT_PLACE = "CCR container"
DEFAULT_RSVP = "[RSVP_EMAIL]"


def build_plain_text(
    date_str: str = DEFAULT_DATE,
    time_str: str | None = DEFAULT_TIME,
    place_str: str | None = DEFAULT_PLACE,
    rsvp_email: str = DEFAULT_RSVP,
) -> str:
    """Plain-text version of the invitation for a multipart email."""
    return (
        "Happy Hour with the Barozzi & Tardito Lab\n\n"
        f"{date_str} at {time_str or DEFAULT_TIME}\n"
        f"{place_str or DEFAULT_PLACE}\n\n"
        "Hi everyone,\n\n"
        "The Barozzi & Tardito Lab is having a happy hour and we'd love for "
        "you to come. There will be drinks and snacks in the "
        f"{place_str or DEFAULT_PLACE}.\n\n"
        f"Please reply to {rsvp_email} if you can make it, so we know how "
        "much to get.\n\n"
        "Hope to see you there!\n"
        "Barozzi & Tardito Lab\n"
    )


def build_email(
    date_str: str = DEFAULT_DATE,
    time_str: str | None = DEFAULT_TIME,
    place_str: str | None = DEFAULT_PLACE,
) -> tuple[str, str]:
    """Return ``(subject, html_body)`` from the static invitation page."""
    if not INVITE_PATH.is_file():
        raise FileNotFoundError(f"Could not find the invitation page at {INVITE_PATH}")

    html = INVITE_PATH.read_text(encoding="utf-8")
    subject = f"Happy hour with the Barozzi & Tardito Lab on {date_str}"
    # Keep unused kwargs in the original signature so existing call sites work.
    _ = (time_str, place_str)
    return subject, html


def write_preview(html: str) -> Path:
    """Write a drafts_helene preview that can resolve the shared font files."""
    preview_html = html.replace('url("assets/fonts/', 'url("../assets/fonts/')
    PREVIEW_PATH.write_text(preview_html, encoding="utf-8")
    return PREVIEW_PATH


def compose_message(
    subject: str,
    html_body: str,
    text_body: str,
    from_addr: str,
    to_addrs: list[str],
) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs)
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")
    return msg


def send_email(msg: EmailMessage) -> None:
    host = os.environ.get("SMTP_HOST")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    if not host:
        raise SystemExit("Not sending because SMTP_HOST is not set.")
    with smtplib.SMTP(host, port, timeout=30) as smtp:
        smtp.starttls()
        if user:
            smtp.login(user, password or "")
        smtp.send_message(msg)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Preview the happy hour invitation. Nothing is sent unless you pass --send."
    )
    parser.add_argument(
        "--send",
        action="store_true",
        help="Send the email over SMTP. Needs SMTP_HOST, MAIL_FROM and MAIL_TO.",
    )
    args = parser.parse_args(argv)

    subject, html = build_email()
    preview = write_preview(html)
    print(subject)
    print(f"Invitation page is at {INVITE_PATH}")
    print(f"Preview written to {preview}")

    if not args.send:
        print("No email was sent.")
        return 0

    from_addr = os.environ.get("MAIL_FROM")
    to_raw = os.environ.get("MAIL_TO")
    if not from_addr or not to_raw:
        raise SystemExit("Not sending because MAIL_FROM or MAIL_TO is missing.")
    msg = compose_message(
        subject,
        html,
        build_plain_text(),
        from_addr,
        [addr.strip() for addr in to_raw.split(",") if addr.strip()],
    )
    send_email(msg)
    print(f"Sent to {to_raw}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
