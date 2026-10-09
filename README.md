# Happy Hour invitation

A static invitation page for the Barozzi & Tardito Lab happy hour on **Friday, October 30, 2026 at 5:00 PM (Vienna time)** in the **CCR container**.

The RSVP address and the public page URL are still placeholders. Both live in `index.html` meta tags named `hh-rsvp-email` and `hh-page-url`. Change those two values when you have them. The page reads the email from that one tag. Until it is a real address, it is shown as plain text and the Email RSVP control cannot be clicked.

## Repository layout

| Path | What it is |
| --- | --- |
| `index.html` | The hosted invitation. |
| `assets/` | Fonts, pictures, and posters. |
| `assets/posters/` | `poster1.png` from the note in `drafts_helene/README.md`, and `science-supernova-3.png` with its A4 print. |
| `docs/` | Event facts, the open plan, and implementation notes. Start with `docs/overview.md`. |
| `scripts/` | `preview.sh` serves the page. `check_invitation.py` checks copy, assets, and the send gate. |
| `drafts_helene/` | Legacy mail drafts. They stay in this folder. |

## Preview the page

Open `index.html` in a browser, or serve the repo root and visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

```bash
./scripts/preview.sh 8000
```

`python3 -m http.server 8000` from the repo root does the same thing.

To refresh the copy in `drafts_helene/`, run the script below. It writes `drafts_helene/happy_hour_preview.html` and prints the email subject. It does **not** send anything.

```bash
python3 drafts_helene/mail_happy_hour.py
```

To host the page, upload `index.html` together with the `assets/` folder. The fonts and pictures are bundled. A small script in the page points them at the right folder when the address has no trailing slash.

Check the page before you hand it on.

```bash
python3 scripts/check_invitation.py
```

## Sending later

`build_email()` returns the subject and the HTML from `index.html` for the local preview. `build_plain_text()` is the note that `--send` actually mails. That note is plain text and includes the hosted page link. It does not attach the invitation page.

`--send` stops if `[RSVP_EMAIL]`, `[PAGE_URL]`, or any similar placeholder is still present. It also stops when `SMTP_PORT` is not a number, when `SMTP_USER` is set without `SMTP_PASSWORD`, or when `MAIL_TO` has no usable address. An empty `SMTP_PORT` means port 587. Port 465 uses implicit TLS. Other ports use STARTTLS.

Details, including display names that contain commas, are in `docs/sending.md`.

Replace the two meta tags, then run the script with these variables set.

```bash
export SMTP_HOST=smtp.example.com
export SMTP_PORT=587
export SMTP_USER=you
export SMTP_PASSWORD=secret
export MAIL_FROM=you@example.com
export MAIL_TO="Tardito, Lab <team@example.com>"
python3 drafts_helene/mail_happy_hour.py --send
```

Without `--send` the script never sends mail.
