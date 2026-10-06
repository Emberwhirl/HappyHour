# Plan

## Settled

- The invitation is a static page, `index.html`, meant to be hosted and linked from a short email later.
- The page does not have to survive inside an email client. Layout, fonts, and pictures are normal web assets.
- Date, time, and place are fixed. See [overview.md](overview.md).
- Guests can save a personal reminder in the browser and can download a calendar file.
- The RSVP address is still unknown. Until it is set, the page shows the placeholder as plain text and the Email RSVP control cannot be clicked.
- The public page URL is still unknown. `--send` includes that URL and refuses to run while it is still a placeholder.
- Nothing in the default script path sends mail.

## Still open

1. Replace `[RSVP_EMAIL]` in the `hh-rsvp-email` meta tag with the real address. That one tag is the only place the page reads it.
2. Replace `[PAGE_URL]` in the `hh-page-url` meta tag with the hosted address, including the scheme.
3. Choose the host and upload `index.html` together with `assets/`.
4. Send only after both tags are real values, and only with `--send` plus the SMTP variables in [sending.md](sending.md).

## Copy rules for the invitation

Guest-facing sentences stay plain. That includes the page, the calendar description, the plain-text note, and the status lines in the page script.

- No em dashes and no en dashes.
- No colons, except in a time such as `5:00 PM`.
- No semicolons.
- No contrast pairs such as "not X but Y".
- No science-fiction wording. The pictures may be evening light and glassware. The words stay a normal lab invitation.

`scripts/check_invitation.py` checks these rules on the guest-facing text.

## Pictures

`assets/images/icon.png` is the header picture and the browser icon. `assets/images/terrace.jpg` and `assets/images/feast.jpg` are the two pictures under the date line. The page switches between them. Replace a file under the same name if the artwork changes, so the page paths can stay put.
