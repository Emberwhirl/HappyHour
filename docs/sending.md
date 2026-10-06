# Preview and sending

The sender stays in `drafts_helene/mail_happy_hour.py`. Default runs write a preview and print the subject. They do not open a socket.

```bash
python3 drafts_helene/mail_happy_hour.py
```

## What `--send` mails

`--send` sends one plain-text message. The body is the date, the place, a short note, and the hosted page link from `hh-page-url`. It does not attach `index.html`. The HTML page is for the browser. The email is only the pointer.

`build_email()` still returns `(subject, html)` for the preview file. `build_plain_text()` is the body that is actually mailed.

## When sending stops

The script checks these before it connects:

| Condition | Result |
| --- | --- |
| `[RSVP_EMAIL]`, `[PAGE_URL]`, or any other `[A-Z0-9_]` token remains in the page text or the plain note | Stop. Script and style blocks are ignored, so code is not treated as copy. |
| `MAIL_FROM` or `MAIL_TO` is missing | Stop. |
| `MAIL_TO` has no email address | Stop. |
| `SMTP_HOST` is missing | Stop. |
| `SMTP_PORT` is set and is not a number | Stop. |
| `SMTP_USER` is set and `SMTP_PASSWORD` is empty | Stop, so a blank password cannot lock the account. |

An empty `SMTP_PORT` means port 587. Port 465 uses implicit TLS. Any other port uses STARTTLS. The TLS context is the default one.

`MAIL_TO` may mix bare addresses and `Name <address>` forms. A comma inside the display name is kept with the name. `Tardito, Lab <team@example.com>` yields one recipient, `team@example.com`. Addresses are extracted from angle brackets first, then bare emails are scanned in what remains.

Newlines in headers are rejected by `EmailMessage` before the message is sent.

## Variables

```bash
export SMTP_HOST=smtp.example.com
export SMTP_PORT=587
export SMTP_USER=you
export SMTP_PASSWORD=secret
export MAIL_FROM=you@example.com
export MAIL_TO="Tardito, Lab <team@example.com>"
python3 drafts_helene/mail_happy_hour.py --send
```

Set the two meta tags in `index.html` first. The script reads them from the page. It does not take the address from the command line.

## Legacy quiz mailer

`drafts_helene/mail_example_html.py` builds an unrelated vocabulary quiz. `build_email()` returns `(subject, html_body)`. French, English, and the date string are passed through `html.escape` before they enter the markup. This file is not part of the happy hour send path.
