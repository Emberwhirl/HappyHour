"""Build the Happy Hour invitation page and (optionally) a sendable message.

The invitation itself is the static page at the repo root: ``index.html``.
This script keeps the original ``build_email()`` flow: it returns a subject
and HTML, writes a local preview, and never sends mail unless you pass
``--send`` with SMTP environment variables.
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
DEFAULT_PLACE = "[VENUE]"
DEFAULT_RSVP = "[RSVP_EMAIL]"


def build_plain_text(
    date_str: str = DEFAULT_DATE,
    time_str: str | None = DEFAULT_TIME,
    place_str: str | None = DEFAULT_PLACE,
    rsvp_email: str = DEFAULT_RSVP,
) -> str:
    """Plain-text fallback for a later multipart email."""
    return (
        "Happy Hour — Barozzi & Tardito Lab\n"
        "An out-of-this-world evening among the stars\n\n"
        f"Date: {date_str}\n"
        f"Time: {time_str or DEFAULT_TIME}\n"
        f"Place: {place_str or DEFAULT_PLACE}\n\n"
        "Dear crew,\n\n"
        "Prepare for launch! The Barozzi & Tardito labs are aligning their "
        "orbits for a cosmic Happy Hour. Come float by for drinks, snacks "
        "and stellar company — no spacesuit required.\n\n"
        f"RSVP: {rsvp_email}\n\n"
        "See you among the stars!\n"
        "Barozzi & Tardito Lab\n"
    )


def build_email(
    date_str: str = DEFAULT_DATE,
    time_str: str | None = DEFAULT_TIME,
    place_str: str | None = DEFAULT_PLACE,
) -> tuple[str, str]:
    """Return ``(subject, html_body)`` from the static invitation page."""
    if not INVITE_PATH.is_file():
        raise FileNotFoundError(f"Invitation page not found: {INVITE_PATH}")

    html = INVITE_PATH.read_text(encoding="utf-8")
    subject = f"🪐 Happy Hour — Barozzi & Tardito Lab — {date_str}"
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
        raise SystemExit("Refusing to send: SMTP_HOST is not set.")
    with smtplib.SMTP(host, port, timeout=30) as smtp:
        smtp.starttls()
        if user:
            smtp.login(user, password or "")
        smtp.send_message(msg)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Preview the Happy Hour invitation. Does not send by default.")
    parser.add_argument(
        "--send",
        action="store_true",
        help="Actually send via SMTP (requires SMTP_HOST, MAIL_FROM, MAIL_TO). Default is preview only.",
    )
    args = parser.parse_args(argv)

    subject, html = build_email()
    preview = write_preview(html)
    print(subject)
    print(f"Invitation page: {INVITE_PATH}")
    print(f"Preview written to {preview}")

    if not args.send:
        print("No email sent (preview only).")
        return 0

    from_addr = os.environ.get("MAIL_FROM")
    to_raw = os.environ.get("MAIL_TO")
    if not from_addr or not to_raw:
        raise SystemExit("Refusing to send: set MAIL_FROM and MAIL_TO.")
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
