#!/usr/bin/env python3
"""Check the invitation page, its assets, and the legacy sender.

Exit 0 when the guest-facing text and the send gate still match the plan.
This script does not send mail and does not open a network connection.
"""

from __future__ import annotations

import os
import re
import sys
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "drafts_helene"))

import mail_happy_hour as mail  # noqa: E402

INDEX = ROOT / "index.html"
PREVIEW = ROOT / "drafts_helene" / "happy_hour_preview.html"
PROBLEMS: list[str] = []

BANNED_WORDS = (
    "stellar",
    "spacesuit",
    "out-of-this-world",
    "among the stars",
    "prepare for launch",
)


def fail(message: str) -> None:
    PROBLEMS.append(message)


def read(path: Path) -> str:
    if not path.is_file():
        fail(f"Missing {path.relative_to(ROOT)}")
        return ""
    return path.read_text(encoding="utf-8")


def guest_text(html: str) -> str:
    body = html.split("<body>", 1)[-1].split("<script>", 1)[0]
    text = re.sub(r"<[^>]+>", " ", body)
    return unescape(re.sub(r"\s+", " ", text)).strip()


def check_copy(label: str, text: str) -> None:
    if "\u2014" in text or "\u2013" in text:
        fail(f"{label} contains a dash that guests should not see")
    if ";" in text:
        fail(f"{label} contains a semicolon")
    leftover = re.sub(r"\d:\d\d", "", text)
    if ":" in leftover:
        fail(f"{label} contains a colon outside a time")
    lowered = text.lower()
    for word in BANNED_WORDS:
        if word in lowered:
            fail(f"{label} contains {word}")
    if re.search(r"\bnot\b.+\bbut\b", lowered):
        fail(f"{label} uses a not-X-but-Y construction")


def check_page(html: str) -> None:
    required = (
        "Friday, October 30, 2026",
        "5:00 PM",
        "CCR container",
        'name="hh-rsvp-email"',
        'name="hh-page-url"',
        'data-remind',
        'data-email-rsvp',
        'aria-live="polite"',
        "font-weight: 300 700",
        "assets/images/icon.png",
        "assets/images/terrace.jpg",
        "assets/images/feast.jpg",
        "assets/images/table.jpg",
        "assets/images/party.jpg",
        "assets/images/cosmos.jpg",
        "assets/images/snacks.jpg",
        "assets/fonts/cormorant-garamond.woff2",
        "20261030T170000",
        "Europe/Vienna",
        "function foldIcs",
        "Saved in this browser. The lab will only know if you email them.",
        "The reminder could not be stored in this browser. Email the lab if you are coming.",
        "Email RSVP is unavailable until an address is set",
    )
    for item in required:
        if item not in html:
            fail(f"index.html is missing {item}")
    if 'href="mailto:' in html or "href='mailto:" in html:
        fail("index.html has a live mailto link in the markup")
    if "disabled" not in html.split("data-email-rsvp", 1)[-1][:80]:
        fail("Email RSVP is not disabled in the static markup")
    if "%05040a" in html:
        fail("favicon still uses a broken percent encoding")
    if "<svg" in html.split("<body>", 1)[-1]:
        fail("the page still embeds an illustration SVG")
    if "7:00" in html:
        fail("the page still mentions an end time")
    check_copy("invitation page", guest_text(html))
    for snippet in (
        "Saved in this browser. The lab will only know if you email them.",
        "The reminder could not be stored in this browser. Email the lab if you are coming.",
        "Drinks and snacks with the Barozzi & Tardito Lab at 5:00 PM.",
        "There will be a glowing gin tonic fountain.",
    ):
        if snippet not in html:
            fail(f"index.html is missing guest text: {snippet}")
        check_copy("page script", snippet)


def check_assets() -> None:
    for rel in (
        "assets/images/icon.png",
        "assets/images/terrace.jpg",
        "assets/images/terrace-640.jpg",
        "assets/images/feast.jpg",
        "assets/images/feast-640.jpg",
        "assets/images/table.jpg",
        "assets/images/table-640.jpg",
        "assets/images/party.jpg",
        "assets/images/party-640.jpg",
        "assets/images/cosmos.jpg",
        "assets/images/cosmos-640.jpg",
        "assets/images/snacks.jpg",
        "assets/images/snacks-640.jpg",
        "assets/fonts/cormorant-garamond.woff2",
        "assets/fonts/cormorant-garamond-italic.woff2",
        "assets/fonts/outfit.woff2",
    ):
        path = ROOT / rel
        if not path.is_file() or path.stat().st_size < 500:
            fail(f"Missing or empty asset {rel}")


def check_weekday() -> None:
    """October 30, 2026 is a Friday. No file should name a different weekday."""
    roots = [INDEX, ROOT / "README.md", PREVIEW]
    roots.extend((ROOT / "docs").glob("*.md"))
    roots.extend((ROOT / "drafts_helene").glob("*.py"))
    roots.extend((ROOT / "scripts").glob("*.py"))
    wrong_weekday = "thurs" + "day"
    for path in roots:
        text = read(path)
        if re.search(wrong_weekday, text, re.I):
            fail(f"{path.relative_to(ROOT)} names the wrong weekday")


def check_sender() -> None:
    recipients = mail.parse_recipients(
        "Tardito, Lab <team@example.com>, other@example.com"
    )
    if recipients != ["team@example.com", "other@example.com"]:
        fail(f"parse_recipients returned {recipients}")
    try:
        mail.parse_recipients("not an address")
    except SystemExit:
        pass
    else:
        fail("parse_recipients accepted a string with no address")

    previous_port = os.environ.get("SMTP_PORT")
    try:
        os.environ.pop("SMTP_PORT", None)
        if mail.smtp_port() != 587:
            fail("an empty SMTP_PORT should mean 587")
        os.environ["SMTP_PORT"] = "465"
        if mail.smtp_port() != 465:
            fail("SMTP_PORT 465 was not kept")
        os.environ["SMTP_PORT"] = "nope"
        try:
            mail.smtp_port()
        except SystemExit:
            pass
        else:
            fail("a non-numeric SMTP_PORT should stop the script")
    finally:
        if previous_port is None:
            os.environ.pop("SMTP_PORT", None)
        else:
            os.environ["SMTP_PORT"] = previous_port

    saved = {key: os.environ.get(key) for key in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "SMTP_PORT")}
    try:
        os.environ["SMTP_HOST"] = "127.0.0.1"
        os.environ["SMTP_USER"] = "someone"
        os.environ["SMTP_PASSWORD"] = ""
        os.environ["SMTP_PORT"] = "587"
        message = mail.compose_message("Subject", "Body", "a@b.c", ["c@d.e"])
        try:
            mail.send_email(message)
        except SystemExit as exc:
            if "SMTP_PASSWORD" not in str(exc):
                fail(f"empty password stopped for the wrong reason: {exc}")
        else:
            fail("empty SMTP_PASSWORD was allowed to continue")
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    plain = mail.build_plain_text()
    check_copy("plain text note", plain)
    if "[PAGE_URL]" not in plain or "[RSVP_EMAIL]" not in plain:
        fail("the default plain note should still carry the placeholders")
    html = read(INDEX)
    try:
        mail.ensure_no_placeholders(html, plain)
    except SystemExit as exc:
        if "placeholder" not in str(exc).lower():
            fail(f"placeholder refusal had an unexpected message: {exc}")
    else:
        fail("ensure_no_placeholders allowed the current placeholders")

    preview = read(PREVIEW)
    for name in ("icon.png", "terrace.jpg", "feast.jpg", "table.jpg", "party.jpg", "cosmos.jpg", "snacks.jpg", "terrace-640.jpg"):
        if f"../assets/images/{name}" not in preview:
            fail(f"preview HTML does not point at {name}")
    if 'url("../assets/fonts/' not in preview:
        fail("preview HTML does not point fonts at ../assets/")
    if 'url("assets/' in preview or 'src="assets/' in preview:
        fail("preview HTML still has repo-root asset paths")

    example = read(ROOT / "drafts_helene" / "mail_example_html.py")
    if "escape(" not in example:
        fail("mail_example_html.py does not escape interpolated text")


def main() -> int:
    html = read(INDEX)
    if html:
        check_page(html)
    check_assets()
    check_weekday()
    check_sender()
    if PROBLEMS:
        print(f"{len(PROBLEMS)} problem(s)")
        for item in PROBLEMS:
            print(f"- {item}")
        return 1
    print("Invitation check passed.")
    print("Placeholders remain, so --send will refuse until hh-rsvp-email and hh-page-url are set.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
