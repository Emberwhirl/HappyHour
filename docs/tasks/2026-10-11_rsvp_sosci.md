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

### Switching it on

1. Put the questionnaire link in `HH_SOSCI_URL` in `assets/hh-config.js`. Both pages, both `.ics` files, and `rsvp-names.html` pick it up. No other file changes.
2. For the count, add `SOSCI_DATA_API_URL`, `SOSCI_VAR_ATTENDING`, and the optional variables listed in [../implementation.md](../implementation.md) to the Vercel project env. Then set `HH_LIVE_COUNT` to `true`. Keep `SOSCI_SHOW_NAME_YES` unset until the consent question exists, because names stay hidden without it.
3. Run `python3 scripts/check_invitation.py`. It accepts an empty value or an `https://` questionnaire link, and it reports which state it found. It fails if the value is a data link (`act=`) or if the count is on while the link is empty. The not-configured state is also checked in the static markup of both pages, so it stays covered after the link is filled in.

### Decisions

- **Config file instead of a meta tag.** One meta tag would only cover one page. `assets/hh-config.js` is a plain script so it also works when a page is opened from disk, and a missing file leaves the safe disabled state.
- **Static markup is the not-configured state.** The disabled button is in the HTML. Script only upgrades it, so nothing can flash a working link before the config loads or show a placeholder if it fails.
- **Disabled look.** Solid `#3a3748` with a dashed border and `#cfcadb` text (about 7 to 1 contrast). The old `opacity: .72` rule was too faint for R2.
- **Copy.** The spec's example save message had a semicolon. It reads "Reminder saved on this device. It is not an RSVP, so please use the RSVP button too." The storage failure message used to say "Email the lab". R1 allows no email instructions, so it now points at the RSVP button. Nothing else about the save feature changed, and the storage key is the same.
- **Calendar URL.** The questionnaire link sits on its own line in `DESCRIPTION` and in a `URL` property. A URL needs `https:`, so the colon rule applies to the sentence around it. `check_invitation.py` checks that sentence.
- **Names need an explicit consent code.** A SoSci checkbox stores 2 when ticked, but a yes/no question often codes yes as 1. A wrong default could show the names of people who said no, so `SOSCI_SHOW_NAME_YES` has no default.
- **Plus-ones.** Read as a number from 0 to 5 unless `SOSCI_PLUS_ONE_YES` marks it as a yes/no question.
- **Function format.** `api/rsvp-count.mjs` exports a Web `GET` handler. The `.mjs` extension makes it an ES module without adding a `package.json` to a static site.
- **Sender.** The plain note now asks guests to RSVP with the form on the invitation page. `--send` also refuses while `HH_SOSCI_URL` is empty. No email was sent.

### Verification, 11 October 2026

A local server served the repo and ran the real `GET` handler for `/api/rsvp-count`. Chrome checked both pages at 390 by 844 and 1280 by 900 in three setups. One was the shipped config. One had `HH_SOSCI_URL` set to `https://www.soscisurvey.de/demo/` and `HH_LIVE_COUNT` on, with no SoSci env vars. The last added a stubbed SoSci response.

- Empty URL. Both pages show the grey "RSVP opens soon" button, its accessible name matches the text, and no `[...]` text appears.
- Demo URL. "RSVP" opens `https://www.soscisurvey.de/demo/?r=web` from the main page and `?r=mail` from the email version in a new tab. The invite stays open.
- `.ics` in both states and on both pages. The description ends with the RSVP sentence, plus the link and a `URL` line when set. Lines are folded at 75 octets.
- Save on this device shows the not-an-RSVP message.
- The skip link lands on `#rsvp` of the same page and focuses it.
- No horizontal scroll at 390px. The RSVP button is full width on phones.
- `/api/rsvp-count` without the env var returns `503` and `{"error":"unavailable"}` with `Cache-Control: no-store`. The main page shows no count and no error. With the stub it returns only `count` and `names`, and the page shows "4 people coming" and the consented names.
- The email version never requests `/api/`.
- `rsvp-names.html` forwards to the invite's RSVP section when the link is empty, and to the questionnaire with `?r=mail` when it is set.

### Switched on, 11 October 2026

The questionnaire is public at `https://s2survey.net/ccr/`. `HH_SOSCI_URL` is set to it. `HH_LIVE_COUNT` stays `false`, because the data link and variable names are not available yet. Only `assets/hh-config.js` changed for this step.

Checked again in Chrome at 390 by 844 and 1280 by 900. Requests to s2survey.net were answered by a local stub, so no test case reached the real questionnaire data.

- The main page RSVP opens `https://s2survey.net/ccr/?r=web` in a new tab, and the invite stays open.
- The email version RSVP opens `https://s2survey.net/ccr/?r=mail` in a new tab.
- The `.ics` description ends with the RSVP sentence and the matching link, and the `URL` property carries the same link on both pages.
- `drafts_helene/rsvp-names.html` redirects to `https://s2survey.net/ccr/?r=mail`.
- Neither page requests `/api/rsvp-count`, and no count is shown.
- The save message, skip link, full-width RSVP button on phones, and the absence of horizontal scroll and `[...]` text are unchanged.
- `--send` still refuses because `[PAGE_URL]` is a placeholder. No email was sent.

### Not done here

Acceptance criterion 8, a live deployment, is still open. The one Vercel project visible to this run was deployed from the CLI with no Git link, so this branch is not deployed anywhere yet.
