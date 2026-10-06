# Happy Hour invitation

A self-contained invitation page for the Barozzi & Tardito Lab Happy Hour.

**Thursday, October 30, 2026 at 5:00 PM (Vienna time)**  
Venue and RSVP address are still placeholders: `[VENUE]`, `[RSVP_EMAIL]`.

## Preview the page

The page is static. Open `index.html` in a browser, or serve the repo root:

```bash
python3 -m http.server 8000
```

Then visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

You can also regenerate the copy under `drafts_helene/`:

```bash
python3 drafts_helene/mail_happy_hour.py
```

That writes `drafts_helene/happy_hour_preview.html` and prints the email subject. It does **not** send anything.

Host `index.html` plus the `assets/` folder on any static host (GitHub Pages, Netlify, an internal file share). Fonts are local woff2 files, so no extra CDN is required.

## Send later (do not use until ready)

The original `build_email()` helper still returns `(subject, html_body)` from `index.html`, and there is a plain-text fallback in `build_plain_text()`.

Sending is opt-in and requires environment variables:

```bash
export SMTP_HOST=smtp.example.com
export SMTP_PORT=587
export SMTP_USER=you
export SMTP_PASSWORD=secret
export MAIL_FROM=you@example.com
export MAIL_TO=crew@example.com
python3 drafts_helene/mail_happy_hour.py --send
```

Do not run `--send` until the venue and RSVP address are filled in. The default command never sends mail.
