# Happy Hour invitation

A static invitation page for the Barozzi & Tardito Lab happy hour on **Friday, October 30, 2026 at 5:00 PM (Vienna time)** in the **CCR container**.

Guests RSVP through a SoSci Survey questionnaire. Its public link is `HH_SOSCI_URL` in `assets/hh-config.js`, the one config file that both `index.html` and the email version read. It is set to [https://s2survey.net/ccr/](https://s2survey.net/ccr/), so the RSVP button opens the questionnaire. If the value is emptied, both pages fall back to a disabled "RSVP opens soon" button. The live count is off until the SoSci data link and variable names are in the Vercel env. See [docs/implementation.md](docs/implementation.md) for the optional live count and its Vercel env vars.

The public page URL is still the `[PAGE_URL]` placeholder in the `hh-page-url` meta tag.

## Repository layout

| Path | What it is |
| --- | --- |
| `index.html` | The hosted invitation. |
| `assets/` | Fonts, pictures, posters, and `hh-config.js` with the RSVP settings. |
| `api/rsvp-count.mjs` | Vercel function for the optional live attendee count. |
| `assets/posters/` | `poster1.png` from the note in `drafts_helene/README.md`, and `science-supernova-3.png` with its A4 print. |
| `docs/` | Event facts, the open plan, and implementation notes. Start with `docs/overview.md`. |
| `scripts/` | `preview.sh` serves the page. `check_invitation.py` checks copy, assets, the RSVP setup, and the send gate. `check_rsvp_count.mjs` tests the count function offline. |
| `drafts_helene/` | Legacy mail drafts. They stay in this folder. |

## Preview the page

Open `index.html` in a browser, or serve the repo root and visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

```bash
./scripts/preview.sh 8000
```

`python3 -m http.server 8000` from the repo root does the same thing.

The email invite draft is `drafts_helene/happy_hour_preview.html`. It keeps the dark gold card, shows the Science Supernova poster as one static picture (the optimized `assets/images/science-supernova-4*` files), and has the same RSVP button as the main page. It is shared only as a link to the hosted page. `drafts_helene/rsvp-names.html` is retired and forwards old links to the questionnaire, or to the invite while the questionnaire is not set. Running the script below prints the email subject. It does **not** send anything, and it does not rebuild the draft from `index.html`.

```bash
python3 drafts_helene/mail_happy_hour.py
```

To host the page, upload `index.html` together with the `assets/` folder, plus `api/` if you want the live count on Vercel. The fonts and pictures are bundled. A small script in the page points them at the right folder when the address has no trailing slash.

Check the page before you hand it on.

```bash
python3 scripts/check_invitation.py
```

It also runs `node scripts/check_rsvp_count.mjs` when node is installed. That check replaces `fetch`, so it stays offline.

## Sending later

`build_email()` returns the subject and the HTML from `drafts_helene/happy_hour_preview.html`. `build_plain_text()` is the note that `--send` actually mails. That note is plain text, asks guests to RSVP with the form on the invitation page, and includes the hosted page link. It does not attach the invitation page.

`--send` stops if `[PAGE_URL]` or any similar placeholder is still present, or while `HH_SOSCI_URL` in `assets/hh-config.js` is empty. It also stops when `SMTP_PORT` is not a number, when `SMTP_USER` is set without `SMTP_PASSWORD`, or when `MAIL_TO` has no usable address. An empty `SMTP_PORT` means port 587. Port 465 uses implicit TLS. Other ports use STARTTLS.

Details, including display names that contain commas, are in `docs/sending.md`.

Set `hh-page-url` and `HH_SOSCI_URL`, then run the script with these variables set.

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
