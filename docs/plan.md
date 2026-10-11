# Plan

## Settled

- The invitation is a static page, `index.html`, meant to be hosted and linked from a short email later.
- The page does not have to survive inside an email client. Layout, fonts, and pictures are normal web assets.
- Date, time, and place are fixed. See [overview.md](overview.md).
- Guests RSVP with the questionnaire and can download a calendar file. The page keeps nothing in the browser.
- Guests RSVP only through a SoSci Survey questionnaire on MedUni's SoSci Pro server (s2survey.net). There is no email RSVP. See [tasks/2026-10-11_rsvp_sosci.md](tasks/2026-10-11_rsvp_sosci.md).
- Both pages read the questionnaire link from `HH_SOSCI_URL` in `assets/hh-config.js`. It is `https://s2survey.net/ccr/`. If it is ever emptied, both show a disabled "RSVP opens soon" button.
- The email version is shared only as a link to the hosted page.
- The public page URL is still unknown. `--send` includes that URL and refuses to run while it is still a placeholder.
- Nothing in the default script path sends mail.

## Still open

1. Done on 11 October 2026. The questionnaire is public at `https://s2survey.net/ccr/` and set as `HH_SOSCI_URL`.
2. For the live count, add `SOSCI_DATA_API_URL` and the question variable names to the Vercel env (see [implementation.md](implementation.md)), then set `HH_LIVE_COUNT` to `true`. The data link is a secret and never goes in the repo.
3. Replace `[PAGE_URL]` in the `hh-page-url` meta tag with the hosted address, including the scheme.
4. Choose the host and upload `index.html` together with `assets/` and `api/`.
5. Send only after `hh-page-url` and `HH_SOSCI_URL` are real values, and only with `--send` plus the SMTP variables in [sending.md](sending.md).

## Copy rules for the invitation

Guest-facing sentences stay plain. That includes the page, the calendar description, the plain-text note, and any text the page script shows.

- No em dashes and no en dashes.
- No colons, except in a time such as `5:00 PM`.
- No semicolons.
- No contrast pairs such as "not X but Y".
- No science-fiction wording. The pictures may be evening light and glassware. The words stay a normal lab invitation.

`scripts/check_invitation.py` checks these rules on the guest-facing text.

## Pictures

`assets/images/icon.png` is the header picture and the browser icon. The date line cycles through `terrace.jpg`, `feast.jpg`, `table.jpg`, `party.jpg`, `cosmos.jpg`, and `snacks.jpg`. Each one also has a `*-640.jpg` sibling. Replace a file under the same name if the artwork changes, so the page paths can stay put.
