"""Build the Happy Hour email draft and, only if asked, send a plain note.

The email invitation is ``happy_hour_preview.html`` in this folder.
Production ``index.html`` stays separate and is not rewritten.
``build_email()`` returns a subject and the draft HTML.
Nothing is sent unless you pass ``--send``.

Names go in ``rsvp-names.html`` beside the draft.
``hh-page-url`` in the draft is the hosted invitation link.
``--send`` refuses while a ``[PLACEHOLDER]`` remains.
The message is plain text plus the hosted page link. It does not attach the
invitation HTML.
"""

from __future__ import annotations

import argparse
import os
import re
import smtplib
import ssl
import sys
from email.message import EmailMessage
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
INVITE_PATH = HERE / "happy_hour_preview.html"
PREVIEW_PATH = INVITE_PATH
SIGNUP_FILE = "drafts_helene/rsvp-names.html"

DEFAULT_DATE = "Friday, October 30, 2026"
DEFAULT_START = "5:00 PM"
DEFAULT_PLACE = "CCR container"
DEFAULT_PAGE_URL = "[PAGE_URL]"
PLACEHOLDER_RE = re.compile(r"\[[A-Z][A-Z0-9_]*\]")
ANGLE_ADDR_RE = re.compile(r"<([^<>\s]+@[^<>\s]+)>")
BARE_ADDR_RE = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")


def build_plain_text(
    date_str: str = DEFAULT_DATE,
    time_str: str | None = None,
    place_str: str | None = DEFAULT_PLACE,
    page_url: str = DEFAULT_PAGE_URL,
) -> str:
    """Plain-text note with the signup file and a link to the hosted invitation."""
    when = time_str or f"at {DEFAULT_START}"
    place = place_str or DEFAULT_PLACE
    return (
        "Happy Hour with the Barozzi & Tardito Lab\n\n"
        f"{date_str} {when}\n"
        f"{place}\n\n"
        "Hi everyone,\n\n"
        "The Barozzi & Tardito Lab is having a happy hour and we'd love for "
        f"you to come. There will be drinks and snacks in the {place}. "
        "There will be a glowing gin tonic fountain.\n\n"
        "Add your name in the signup file "
        f"{SIGNUP_FILE} "
        "if you can make it, so we know how much to get.\n\n"
        f"The invitation page is at {page_url}\n\n"
        "Hope to see you there!\n"
        "Barozzi & Tardito Lab\n"
    )


def build_email(
    date_str: str = DEFAULT_DATE,
    time_str: str | None = DEFAULT_START,
    place_str: str | None = DEFAULT_PLACE,
) -> tuple[str, str]:
    """Return ``(subject, html_body)`` from the email draft."""
    if not INVITE_PATH.is_file():
        raise FileNotFoundError(f"Could not find the invitation page at {INVITE_PATH}")

    html = INVITE_PATH.read_text(encoding="utf-8")
    subject = f"Happy hour with the Barozzi & Tardito Lab on {date_str}"
    _ = (time_str, place_str)
    return subject, html


def read_meta(html: str, name: str) -> str | None:
    """Read one meta tag from the invitation page."""
    pattern = rf'<meta\s+name="{re.escape(name)}"\s+content="([^"]*)"\s*/?>'
    match = re.search(pattern, html)
    return match.group(1) if match else None


def invitation_text_for_placeholders(html: str) -> str:
    """HTML with scripts and styles removed, so code is not treated as copy."""
    without_script = re.sub(r"<script\b[^>]*>.*?</script>", " ", html, flags=re.S | re.I)
    return re.sub(r"<style\b[^>]*>.*?</style>", " ", without_script, flags=re.S | re.I)


def find_placeholders(*parts: str) -> list[str]:
    found: list[str] = []
    for part in parts:
        for item in PLACEHOLDER_RE.findall(part or ""):
            if item not in found:
                found.append(item)
    return found


def ensure_no_placeholders(html: str, plain: str) -> None:
    found = find_placeholders(invitation_text_for_placeholders(html), plain)
    if not found:
        return
    listed = ", ".join(found)
    raise SystemExit(
        "Not sending because a placeholder is still in the invitation. "
        f"Still present are {listed}."
    )


def parse_recipients(raw: str) -> list[str]:
    """Accept display names that contain commas, then keep the bare addresses."""
    found: list[str] = []
    for match in ANGLE_ADDR_RE.finditer(raw or ""):
        addr = match.group(1).strip()
        if addr not in found:
            found.append(addr)
    without_angles = ANGLE_ADDR_RE.sub(" ", raw or "")
    for match in BARE_ADDR_RE.finditer(without_angles):
        addr = match.group(0)
        if addr not in found:
            found.append(addr)
    if not found:
        raise SystemExit("Not sending because MAIL_TO has no usable address.")
    return found


def smtp_port() -> int:
    raw = os.environ.get("SMTP_PORT", "").strip()
    if not raw:
        return 587
    try:
        return int(raw)
    except ValueError:
        raise SystemExit("Not sending because SMTP_PORT is not a number.") from None


def write_preview(html: str) -> Path:
    """Save the email draft. Asset paths already point at ``../assets/``.

    Production ``index.html`` is not read or rewritten here.
    """
    PREVIEW_PATH.write_text(html, encoding="utf-8")
    return PREVIEW_PATH


def compose_message(
    subject: str,
    text_body: str,
    from_addr: str,
    to_addrs: list[str],
) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs)
    msg.set_content(text_body)
    return msg


def send_email(msg: EmailMessage) -> None:
    host = os.environ.get("SMTP_HOST", "").strip()
    if not host:
        raise SystemExit("Not sending because SMTP_HOST is not set.")
    port = smtp_port()
    user = os.environ.get("SMTP_USER", "").strip()
    password = os.environ.get("SMTP_PASSWORD")
    if user and not password:
        raise SystemExit("Not sending because SMTP_USER is set and SMTP_PASSWORD is empty.")
    context = ssl.create_default_context()
    if port == 465:
        smtp_cm = smtplib.SMTP_SSL(host, port, timeout=30, context=context)
    else:
        smtp_cm = smtplib.SMTP(host, port, timeout=30)
    with smtp_cm as smtp:
        if port != 465:
            smtp.starttls(context=context)
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
        help="Send a plain text note with the signup file and the page link. Needs SMTP_HOST, MAIL_FROM and MAIL_TO. Refuses while a placeholder remains.",
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

    page_url = read_meta(html, "hh-page-url") or DEFAULT_PAGE_URL
    plain = build_plain_text(page_url=page_url)
    ensure_no_placeholders(html, plain)

    from_addr = os.environ.get("MAIL_FROM", "").strip()
    to_raw = os.environ.get("MAIL_TO", "")
    if not from_addr or not to_raw.strip():
        raise SystemExit("Not sending because MAIL_FROM or MAIL_TO is missing.")
    msg = compose_message(subject, plain, from_addr, parse_recipients(to_raw))
    send_email(msg)
    print(f"Sent to {to_raw.strip()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
