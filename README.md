# Happy Hour invitation

A static invitation page for the Barozzi & Tardito Lab happy hour on **Thursday, October 30, 2026 at 5:00 PM (Vienna time)** in the **CCR container**.

The RSVP address is still a placeholder (`[RSVP_EMAIL]`). It appears in `index.html` (page text, the Email RSVP link and the calendar file) and in `drafts_helene/mail_happy_hour.py`.

## Preview the page

Open `index.html` in a browser, or serve the repo root and visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

```bash
python3 -m http.server 8000
```

To refresh the copy in `drafts_helene/`, run the script below. It writes `drafts_helene/happy_hour_preview.html` and prints the email subject. It does **not** send anything.

```bash
python3 drafts_helene/mail_happy_hour.py
```

To host the page, upload `index.html` together with the `assets/` folder to any static host (GitHub Pages, Netlify or an internal file share). The fonts are bundled, so nothing else needs to load.

## Sending later

`build_email()` returns the subject and the HTML from `index.html`, and `build_plain_text()` gives a plain-text version for the same email.

Sending only happens with `--send` and these environment variables set.

```bash
export SMTP_HOST=smtp.example.com
export SMTP_PORT=587
export SMTP_USER=you
export SMTP_PASSWORD=secret
export MAIL_FROM=you@example.com
export MAIL_TO=team@example.com
python3 drafts_helene/mail_happy_hour.py --send
```

Please replace `[RSVP_EMAIL]` with a real address before anyone runs `--send`. Without the flag the script never sends mail.
