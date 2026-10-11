# RSVP through SoSci Survey, 11 October 2026

Spec: `PRD-rsvp-sosci.md` (approved by Yu-Tian on 2026-10-11). Both pages move to one RSVP method, a SoSci Survey questionnaire on s2survey.net. The questionnaire and its data link do not exist yet, so this change ships in the "not configured" state and switches on through config only.

## Plan

1. **One config source.** Add `assets/hh-config.js`. It sets `window.HH_CONFIG` with `HH_SOSCI_URL` (empty) and `HH_LIVE_COUNT` (false). `index.html` loads it as `assets/hh-config.js` and the email version loads it as `../assets/hh-config.js`. No page hard-codes the URL.
2. **RSVP button (R1, R2).** The static markup on both pages is the not-configured state, a disabled gold button that reads "RSVP opens soon". A page script reads the config. When `HH_SOSCI_URL` is a valid `https:` URL, it swaps the button for a link labelled "RSVP" that opens the questionnaire in a new tab, with `?r=web` on the main page and `?r=mail` on the email version. If the config is missing, empty, a `[PLACEHOLDER]`, or not `https:`, the button stays disabled.
3. **Copy (R1).** Both pages say "Please RSVP using the form so we know how much to get." Remove the `hh-rsvp-email` meta tag, the Email RSVP button, the `[RSVP_EMAIL]` slot, and all mailto logic. Remove the signup list link and the "Add your name" button.
4. **Calendar file (R1).** Both `.ics` descriptions use the same RSVP sentence. When the URL is set, the description adds the questionnaire link on its own line and the event gets a `URL` property. When it is not set, the description says the form opens soon.
5. **Save on this device (R3).** Keep the feature and its storage key. Make it a secondary button after RSVP. The saved message becomes "Reminder saved on this device. It is not an RSVP, so please use the RSVP button too." The storage failure message drops its email instruction, because R1 allows no email instructions anywhere.
6. **Live count (R4).** Add `api/rsvp-count.mjs`, a Vercel Node function. It reads `SOSCI_DATA_API_URL` and the variable names from the Vercel env only, asks SoSci for just those variables plus `FINISHED`, and returns `{ count, names }`. Missing config or a SoSci error gives a 503 with a generic body. The main page calls it only when `HH_LIVE_COUNT` is true and the RSVP URL is set. The email version never calls it.
7. **Retire `rsvp-names.html`.** Turn it into a redirect. It goes to the questionnaire with `?r=mail` when configured, and to the RSVP section of the email version otherwise. Old links never land on an empty page.
8. **Email version is link-only (R5).** Add an HTML comment at the top of `happy_hour_preview.html`.
9. **Sender note.** The plain-text note in `drafts_helene/mail_happy_hour.py` points at the signup file today. Point it at the RSVP form on the invitation page instead. `--send` also refuses while `HH_SOSCI_URL` is empty. No email is sent as part of this work.
10. **Checks.** Update `scripts/check_invitation.py` for the new behavior. That covers the not-configured markup, no placeholders or email RSVP text, the skip link still targeting `#rsvp`, the shared config, the email version never calling the count API, and no SoSci data link committed anywhere. Add `scripts/check_rsvp_count.mjs` to exercise the function offline with a fake SoSci response.
11. **Docs.** Update `README.md`, `docs/overview.md`, `docs/plan.md`, `docs/implementation.md`, and `docs/sending.md`.
12. **Verify.** Browser at 390px and desktop for both states (empty URL and `https://www.soscisurvey.de/demo/`), the `.ics` output, the save message, and `/api/rsvp-count` returning 503 with no env var.

## Out of scope

Unchanged on purpose, per the spec: venue address or map, end time and `DTEND`, RSVP deadline, cost or dress code line, poster title and size, the `drafts_helene` URL, the "Vienna time" label, the shared storage key, and accessibility items other than the R2 button label.

## Implementation notes

Filled in after the change lands.
