#!/usr/bin/env python3
"""Check the invitation page, its assets, the RSVP setup, and the legacy sender.

Exit 0 when the guest-facing text and the send gate still match the plan.
This script does not send mail and does not open a network connection.
When node is installed it also runs scripts/check_rsvp_count.mjs, which
replaces fetch and stays offline.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "drafts_helene"))

import mail_happy_hour as mail  # noqa: E402

INDEX = ROOT / "index.html"
PREVIEW = ROOT / "drafts_helene" / "happy_hour_preview.html"
SIGNUP = ROOT / "drafts_helene" / "rsvp-names.html"
CONFIG = ROOT / "assets" / "hh-config.js"
COUNT_API = ROOT / "api" / "rsvp-count.mjs"
COUNT_CHECK = ROOT / "scripts" / "check_rsvp_count.mjs"
PROBLEMS: list[str] = []

RSVP_ASK = "Please RSVP using the form so we know how much to get."
RSVP_SOON = "RSVP opens soon"
EVENT_TEXT = "Drinks and snacks with the Barozzi & Tardito Lab at 5:00 PM. There will be a glowing gin tonic fountain."
DATA_LINK_RE = re.compile(r"[?&]act=[A-Za-z0-9_-]{6,}")
SOSCI_URL_KEY = re.compile(r"\bHH_SOSCI_URL\s*:\s*[\"']")

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


def check_skip_link(label: str, html: str) -> None:
    """The skip link must land on the RSVP section of the same document."""
    link = re.search(r'<a class="skip" href="#([\w-]+)">([^<]+)</a>', html)
    if not link:
        fail(f"{label} has no in-page skip link")
        return
    target_id, text = link.groups()
    section = re.search(rf'<section\b([^>]*\bid="{target_id}"[^>]*)>(.*?)</section>', html, re.S)
    if not section:
        fail(f"{label} skip link points at #{target_id}, which is not a section")
        return
    attrs, inner = section.groups()
    if 'tabindex="-1"' not in attrs:
        fail(f"{label} skip target #{target_id} cannot take focus")
    name = re.search(r'aria-label="([^"]+)"', attrs)
    if not name or text != f"Skip to {name.group(1)}":
        fail(f"{label} skip link text does not match the name of #{target_id}")
    if not re.search(rf"<p\b[^>]*>\s*{re.escape(RSVP_ASK)}", inner):
        fail(f"{label} skip target does not hold the request to RSVP")
    if 'class="actions"' not in inner:
        fail(f"{label} skip target does not hold the action buttons")
    if "data-rsvp " not in inner and "data-rsvp>" not in inner:
        fail(f"{label} skip target does not hold the RSVP button")
    if 'document.createElement("base")' in html and (
        'new URL(link.getAttribute("href"), document.URL)' not in html
    ):
        fail(f"{label} adds a <base> but does not keep in-page links on this document")


def check_rsvp(label: str, html: str, source: str, config_src: str) -> None:
    """Both pages share one RSVP button that ships disabled until HH_SOSCI_URL is set."""
    if f'<script src="{config_src}"></script>' not in html:
        fail(f"{label} does not load the shared config {config_src}")
    for banned in (
        "[RSVP_EMAIL]",
        "Email RSVP",
        "hh-rsvp-email",
        "data-email-rsvp",
        "data-rsvp-slot",
        "mailto:",
        "rsvp-names.html",
        "signup list",
        "Add your name",
        "s2survey.net/",
        "soscisurvey.de/",
    ):
        if banned in html:
            fail(f"{label} still contains {banned}")
    visible = guest_text(html)
    if re.search(r"\[[^\]]*\]", visible):
        fail(f"{label} shows a raw [placeholder] to guests")
    if RSVP_ASK not in visible:
        fail(f"{label} does not ask guests to RSVP with the form")

    button = re.search(r"<button\b([^>]*\bdata-rsvp\b[^>]*)>([^<]*)</button>", html)
    if not button:
        fail(f"{label} has no static RSVP button")
    else:
        attrs, text = button.groups()
        if text.strip() != RSVP_SOON:
            fail(f"{label} RSVP button does not read {RSVP_SOON} before it is configured")
        if not re.search(r"\bdisabled\b", attrs):
            fail(f"{label} RSVP button is not disabled in the static markup")
        if "aria-label" in attrs:
            fail(f"{label} RSVP button has an accessible name that differs from its text")
        if "btn-gold" not in attrs:
            fail(f"{label} RSVP button is not the primary gold button")
    actions = re.search(r'<div class="actions">(.*?)</div>', html, re.S)
    if actions:
        controls = re.findall(r"<(?:button|a)\b([^>]*)>", actions.group(1))
        order = [m.group(1) for m in re.finditer(r"\b(data-rsvp|data-ics)\b", actions.group(1))]
        if order != ["data-rsvp", "data-ics"] or len(controls) != 2:
            fail(f"{label} actions should be exactly RSVP then Add to calendar ({order})")
        calendar = re.search(r"<button\b([^>]*\bdata-ics\b[^>]*)>Add to calendar</button>", actions.group(1))
        if not calendar or "btn-line" not in calendar.group(1):
            fail(f"{label} Add to calendar is not the secondary button")
    else:
        fail(f"{label} has no action buttons")

    style = re.search(r"\.btn-rsvp:disabled[^{]*\{([^}]*)\}", html)
    if not style or "opacity: 1" not in style.group(1) or "#3a3748" not in style.group(1):
        fail(f"{label} disabled RSVP button is not clearly greyed out")

    for item in (
        f'const RSVP_ASK = "{RSVP_ASK}";',
        f'const rsvpUrl = questionnaireUrl("{source}");',
        'url.searchParams.set("r", source);',
        'if (url.protocol !== "https:") return "";',
        "if (!raw || isPlaceholder(raw)) return \"\";",
        'link.target = "_blank";',
        'link.rel = "noopener";',
        'link.textContent = "RSVP";',
        f'const EVENT_TEXT = "{EVENT_TEXT}";',
        "`${EVENT_TEXT} ${RSVP_ASK}\\n${rsvpUrl}`",
        "`${EVENT_TEXT} ${RSVP_ASK} The form opens soon.`",
        "...(EVENT.url ? [`URL:${EVENT.url}`] : []),",
    ):
        if item not in html:
            fail(f"{label} script is missing {item}")
    for snippet in (RSVP_ASK, EVENT_TEXT, "The form opens soon."):
        check_copy(f"{label} script", snippet)
    check_no_save_feature(label, html)


SAVE_FEATURE_TRACES = (
    "on this device",
    "data-remind",
    "remindbtn",
    "data-thanks",
    'class="thanks"',
    ".thanks",
    "localstorage",
    "happyhour-2026-10-30-reminder",
    "storagekey",
    "savedtext",
    "unsavedtext",
    "marksaved",
    "reminder",
)


def check_no_save_feature(label: str, text: str) -> None:
    """The "Save on this device" reminder was removed. Nothing of it may remain."""
    lowered = text.lower()
    for trace in SAVE_FEATURE_TRACES:
        if trace in lowered:
            fail(f"{label} still has the removed save feature ({trace})")


def check_page(html: str) -> None:
    required = (
        "Friday, October 30, 2026",
        "5:00 PM",
        "CCR container",
        'name="hh-page-url"',
        'data-rsvp',
        'data-rsvp-count',
        'data-ics',
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
    )
    for item in required:
        if item not in html:
            fail(f"index.html is missing {item}")
    check_rsvp("index.html", html, "web", "assets/hh-config.js")
    if 'if (HH.HH_LIVE_COUNT === true && rsvpUrl && /^https?:$/.test(location.protocol)) showCount();' not in html:
        fail("index.html does not keep the live count behind HH_LIVE_COUNT")
    if not re.search(r'<p class="rsvp-count" data-rsvp-count hidden></p>', html):
        fail("index.html does not hide the live count until it loads")
    if "%05040a" in html:
        fail("favicon still uses a broken percent encoding")
    if "<svg" in html.split("<body>", 1)[-1]:
        fail("the page still embeds an illustration SVG")
    if "7:00" in html:
        fail("the page still mentions an end time")
    check_copy("invitation page", guest_text(html))
    check_skip_link("index.html", html)
    for snippet in (
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
    if "[PAGE_URL]" not in plain:
        fail("the default plain note should still carry the page placeholder")
    if "[RSVP_EMAIL]" in plain or "Vienna time" in plain or "reply to" in plain.lower():
        fail("the plain note still asks for an email RSVP or names Vienna time")
    if "rsvp-names" in plain or "signup" in plain.lower():
        fail("the plain note still points at the retired names signup file")
    if "Please RSVP using the form on the invitation page" not in plain:
        fail("the plain note does not send guests to the RSVP form")
    try:
        mail.ensure_rsvp_configured("")
    except SystemExit as exc:
        if "HH_SOSCI_URL" not in str(exc):
            fail(f"RSVP refusal had an unexpected message: {exc}")
    else:
        fail("--send would run while HH_SOSCI_URL is empty")
    try:
        mail.ensure_rsvp_configured("https://www.soscisurvey.de/demo/")
    except SystemExit:
        fail("--send refused a real questionnaire URL")
    html = read(INDEX)
    try:
        mail.ensure_no_placeholders(html, plain)
    except SystemExit as exc:
        if "placeholder" not in str(exc).lower():
            fail(f"placeholder refusal had an unexpected message: {exc}")
    else:
        fail("ensure_no_placeholders allowed the current placeholders")

    preview = read(PREVIEW)
    check_email_draft(preview)
    if 'url("../assets/fonts/' not in preview:
        fail("preview HTML does not point fonts at ../assets/")
    if 'url("assets/' in preview or 'src="assets/' in preview or 'href="assets/' in preview:
        fail("preview HTML still has repo-root asset paths")

    example = read(ROOT / "drafts_helene" / "mail_example_html.py")
    if "escape(" not in example:
        fail("mail_example_html.py does not escape interpolated text")


def check_email_draft(preview: str) -> None:
    """The email draft is separate from production index.html."""
    if "Science%20Supernova-4.png" not in preview and "Science Supernova-4.png" not in preview:
        fail("email draft does not use Science Supernova-4.png")
    if "data-slides" in preview or "still-nav" in preview or "data-slide-to" in preview:
        fail("email draft still has a picture slideshow")
    lowered = preview.lower()
    if "vienna time" in lowered:
        fail("email draft still mentions Vienna time")
    if "mailto:" in lowered or "[RSVP_EMAIL]" in preview or "Email RSVP" in preview:
        fail("email draft still asks for an email RSVP")
    check_rsvp("email draft", preview, "mail", "../assets/hh-config.js")
    if "rsvp-count" in preview or "/api/" in preview or "fetch(" in preview:
        fail("email draft calls the live count API")
    first_lines = preview.split("<head>", 1)[0]
    if not re.search(r"<!--[^>]*only as a link to the hosted page[^>]*-->", first_lines):
        fail("email draft has no link-only comment at the top")
    image_at = preview.find("Science%20Supernova-4.png")
    if image_at < 0:
        image_at = preview.find("Science Supernova-4.png")
    title_at = preview.find("<h1>")
    if image_at < 0 or title_at < 0 or image_at > title_at:
        fail("email draft does not place the picture before the other info")
    if "Courier New" not in preview:
        fail("email draft headers do not use a computer font")
    if 'font-family: Outfit, "Segoe UI", sans-serif' not in preview:
        fail("email draft lost the basic body font")
    check_copy("email draft", guest_text(preview))
    check_skip_link("email draft", preview)
    check_retired_signup()


def check_retired_signup() -> None:
    """rsvp-names.html only forwards old links. It is never a dead end."""
    signup = read(SIGNUP)
    if not signup:
        return
    if "<pre" in signup or "Put your name" in signup:
        fail("rsvp-names.html is still a static names list")
    for item in (
        '<script src="../assets/hh-config.js"></script>',
        'url.searchParams.set("r", "mail");',
        'var target = "happy_hour_preview.html#rsvp";',
        "location.replace(target);",
        'url=happy_hour_preview.html#rsvp',
        'href="happy_hour_preview.html#rsvp"',
    ):
        if item not in signup:
            fail(f"rsvp-names.html redirect is missing {item}")
    check_copy("retired names page", guest_text(signup))


def check_config() -> str:
    """One config file feeds both pages. Filling it in is the only step to switch RSVP on."""
    config = read(CONFIG)
    if not config:
        return ""
    if "window.HH_CONFIG" not in config or not SOSCI_URL_KEY.search(config):
        fail("assets/hh-config.js does not define HH_CONFIG.HH_SOSCI_URL")
    if not re.search(r"\bHH_LIVE_COUNT\s*:\s*(true|false)\b", config):
        fail("assets/hh-config.js does not set HH_LIVE_COUNT to true or false")
    url = mail.read_sosci_url(config)
    if url:
        if not url.startswith("https://") or mail.PLACEHOLDER_RE.search(url):
            fail("HH_SOSCI_URL must be empty or an https:// questionnaire link")
        if "act=" in url:
            fail("HH_SOSCI_URL holds a data link. Use the public questionnaire link.")
    elif re.search(r"\bHH_LIVE_COUNT\s*:\s*true\b", config):
        fail("HH_LIVE_COUNT is on while HH_SOSCI_URL is empty")
    if mail.read_sosci_url('HH_SOSCI_URL: "https://www.soscisurvey.de/demo/",') != "https://www.soscisurvey.de/demo/":
        fail("read_sosci_url cannot read a configured URL")
    return url


def check_count_api() -> None:
    api = read(COUNT_API)
    if not api:
        return
    for item in (
        "process.env",
        '"SOSCI_DATA_API_URL"',
        'url.searchParams.set("vList"',
        '"FINISHED"',
        "s-maxage=60, stale-while-revalidate",
        "json(503,",
        "return json(200, summary, CACHE_OK);",
        "export async function GET(",
    ):
        if item not in api:
            fail(f"api/rsvp-count.mjs is missing {item}")
    if re.search(r"console\.\w+\([^)]*(apiUrl|requestUrl|SOSCI_DATA_API_URL)", api):
        fail("api/rsvp-count.mjs may log the data link")
    if not shutil.which("node"):
        print("node is not installed, so scripts/check_rsvp_count.mjs was skipped.")
        return
    result = subprocess.run(
        ["node", str(COUNT_CHECK)], cwd=ROOT, capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        fail(f"scripts/check_rsvp_count.mjs failed\n{result.stderr.strip() or result.stdout.strip()}")


def check_no_data_link() -> None:
    """The SoSci data link is a secret. It lives only in the Vercel env."""
    skip_dirs = {".git", "node_modules", ".vercel", "__pycache__"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or skip_dirs.intersection(path.relative_to(ROOT).parts):
            continue
        if path == COUNT_CHECK or path.suffix.lower() in {".png", ".jpg", ".woff2", ".ico"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if DATA_LINK_RE.search(text):
            fail(f"{path.relative_to(ROOT)} contains what looks like a SoSci data link")
        if re.search(r"SOSCI_DATA_API_URL\s*=\s*\S", text):
            fail(f"{path.relative_to(ROOT)} assigns SOSCI_DATA_API_URL")


def main() -> int:
    html = read(INDEX)
    if html:
        check_page(html)
    check_assets()
    check_weekday()
    for doc in (ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))):
        check_no_save_feature(str(doc.relative_to(ROOT)), read(doc))
    sosci_url = check_config()
    check_count_api()
    check_no_data_link()
    check_sender()
    if PROBLEMS:
        print(f"{len(PROBLEMS)} problem(s)")
        for item in PROBLEMS:
            print(f"- {item}")
        return 1
    print("Invitation check passed.")
    if sosci_url:
        print(f"RSVP is configured with {sosci_url}")
        print("--send will refuse until hh-page-url is set.")
    else:
        print("RSVP is not configured, so both pages show RSVP opens soon.")
        print("--send will refuse until hh-page-url is set and HH_SOSCI_URL in assets/hh-config.js is filled in.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
