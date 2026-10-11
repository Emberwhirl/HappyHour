# Implementation notes

## Page

`index.html` is self-contained apart from files under `assets/`. The card is an opaque dark panel on a fixed night background. Entrance motion is a short slide. `prefers-reduced-motion: reduce` turns that slide off and shows the card immediately.

A small inline script waits for fonts, decodes the images, and waits for the card animation. It then sets `document.documentElement.dataset.settled` to `true`. Screenshot and overlap checks wait for that flag.

## RSVP through SoSci Survey

Guests RSVP in a SoSci Survey questionnaire. Both pages read its link from one file, `assets/hh-config.js`:

```js
window.HH_CONFIG = Object.freeze({
  HH_SOSCI_URL: "https://s2survey.net/ccr/",
  HH_LIVE_COUNT: false,
});
```

`index.html` loads it as `assets/hh-config.js`. The email version loads it as `../assets/hh-config.js`. Neither page has the URL in its own markup.

The static markup is the not-configured state. The gold primary button is `<button data-rsvp disabled>RSVP opens soon</button>`, styled solid grey with a dashed border so it reads as unavailable. Its accessible name is its visible text. The page script keeps it that way when `HH_SOSCI_URL` is empty, still a `[PLACEHOLDER]`, not a valid URL, or not `https:`, and also when the config file fails to load.

When `HH_SOSCI_URL` is a valid `https:` link, the script replaces the button with `<a data-rsvp target="_blank" rel="noopener">RSVP</a>`. The link adds SoSci's reference parameter, `?r=web` on the main page and `?r=mail` on the email version, so the data shows where each answer came from. An `r` already in the configured URL is replaced.

Both pages say "Please RSVP using the form so we know how much to get." The skip link still targets `#rsvp`, the focusable section that holds that sentence and the buttons.

`drafts_helene/rsvp-names.html` used to be a static names list. It now forwards old links. It goes to the questionnaire with `?r=mail` when configured, or to `happy_hour_preview.html#rsvp` otherwise. Without scripts, a meta refresh and a plain link go to the invite.

`hh-page-url` is not painted on the page. The legacy sender reads it and puts it in the plain-text note. See [sending.md](sending.md).

## Live attendee count

`api/rsvp-count.mjs` is a Vercel Node function at `GET /api/rsvp-count`. All of its settings come from the Vercel env.

| Variable | Meaning |
| --- | --- |
| `SOSCI_DATA_API_URL` | Required. The SoSci "API for Data Retrieval" JSON link (`?act=...`). Secret. |
| `SOSCI_VAR_ATTENDING` | Required. Variable of the "are you coming" question, for example `AB01`. |
| `SOSCI_ATTENDING_YES` | Code for yes. Defaults to `1`. |
| `SOSCI_VAR_PLUS_ONE` | Optional. Number of extra guests, or a yes/no question. |
| `SOSCI_PLUS_ONE_YES` | Set it when the plus-one question is yes/no. It then counts one extra guest on that code. Otherwise the value is read as a number from 0 to 5. |
| `SOSCI_VAR_FIRST_NAME` | Optional. First name. |
| `SOSCI_VAR_SHOW_NAME` | Optional. Consent to show the first name. |
| `SOSCI_SHOW_NAME_YES` | Code for consent. A SoSci checkbox stores 2 when ticked. There is no default, so no names are shown until this is set. |

The function asks SoSci for `vList=FINISHED,<the variables above>` only. It counts finished cases (`FINISHED` is 1) where attending equals the yes code, adds the plus-ones, and collects first names only from guests who gave consent. The response is `{ "count": N, "names": [...] }` and nothing else, cached with `Cache-Control: public, s-maxage=60, stale-while-revalidate=300`.

When the data link or attending variable is missing, the data link is not `https:`, SoSci answers with an error status or an `errors` attribute, or the request fails or takes longer than 8 seconds, the function returns `503` with `{ "error": "unavailable" }` and `Cache-Control: no-store`. Log lines carry only a status code or an error name. They never contain the data link.

`index.html` calls the function only when `HH_LIVE_COUNT` is `true`, the RSVP link is set, and the page is served over http or https. A non-200 answer, bad JSON, or a count below 1 leaves `[data-rsvp-count]` hidden. Guests never see an error. Otherwise it shows "N people coming" under the buttons, with the consented first names on the next line. The email version never calls the function.

`node scripts/check_rsvp_count.mjs` tests the function with a stubbed `fetch`.

## Personal reminder

"Save on this device" is a secondary button after RSVP. It writes `happyhour-2026-10-30-reminder` in `localStorage` on this browser only. The lab is not told.

Success text: "Reminder saved on this device. It is not an RSVP, so please use the RSVP button too."

If storage throws or refuses the write, the click still finishes. The status line says the reminder could not be saved and points the guest at the RSVP button. Reads are guarded the same way, so a blocked `localStorage` does not skip the click listener.

The status element is `role="status"` and `aria-live="polite"`. It stays in the accessibility tree when empty (clipped, not `display: none`) so a later message can be announced.

## Calendar file

"Add to calendar" builds an iCalendar document in the page.

- `DTSTART` is `20261030T170000` in `Europe/Vienna`. The page and the calendar file give that start time only.
- A `VTIMEZONE` block carries the EU rules. The last Sunday of October 2026 is October 25, so this date is already on standard time.
- `SUMMARY`, `LOCATION`, and `DESCRIPTION` are escaped for commas, semicolons, and newlines.
- The description ends with "Please RSVP using the form so we know how much to get." When `HH_SOSCI_URL` is set, the questionnaire link follows on its own line and the event also gets a `URL` property. When it is not set, the description says the form opens soon. Both pages build the same description, with their own `r` value.
- Lines longer than 75 octets are folded. Continuation lines start with a space. The fold does not split a UTF-8 sequence.

Desktop browsers get a temporary `<a download>` appended to the document. iPhone, iPad, and iPadOS (Mac platform with a touch screen) navigate to the blob so the system calendar sheet can open. The blob URL is revoked after 4 seconds, not on the same tick as the click.

## Fonts

| File | Face |
| --- | --- |
| `assets/fonts/cormorant-garamond.woff2` | Variable roman, weight axis 300 to 700. |
| `assets/fonts/cormorant-garamond-italic.woff2` | Static italic, weight 400. |
| `assets/fonts/outfit.woff2` | Variable, used for interface text. |

The roman `@font-face` rule sets `font-weight: 300 700` so the axis can move. The italic file has no axis, so its rule stays at 400.

The big date uses lining figures and a line height of 1, with space between the day, the number, and the month. That keeps the old-style "3" from sitting on the month line.

## Pictures

The page uses these files in `assets/images/`:

- `icon.png` in the header and as the browser icon. The same file is linked after the base-URL script so it resolves next to the page.
- Six pictures under the date line. `terrace.jpg` is the Vienna terrace with two friends looking at a phone. `feast.jpg` is that terrace with food and beer. `table.jpg` is glasses, olives, crackers, and cheese. `party.jpg` is mugs and glasses under warm lights. `cosmos.jpg` is drinks under a starry sky. `snacks.jpg` is beer, pretzels, cheese, olives, and bread. Each large file has a 640 pixel sibling for narrower screens.

The frame crossfades, and the picture eases across the frame while it is showing. The dots under the frame pick a picture. Hovering or focusing the frame pauses the change and the drift. With reduced motion, the terrace picture stays still until a dot is used. The header icon is decorative because the lab name is already beside it.

## Addresses with no trailing slash

Font and image URLs are relative (`assets/...`). If a host serves the page at a path with no trailing slash and no filename, those URLs would otherwise resolve one folder too high. A blocking script at the top of `<head>` inserts `<base href>` pointing at the page directory before the icon and the style sheet are requested.

## Email draft

`drafts_helene/happy_hour_preview.html` is the email invitation. It keeps this dark gold card and does not follow `index.html` after the draft changes. The picture is the static file `assets/images/Science Supernova-4.png`, placed first. Headers use Courier New. Body copy stays in Outfit. The draft does not mention Vienna time and does not offer an email RSVP. It has the same RSVP button, save button, and calendar file as the main page, with `?r=mail`. It has no live count.

The draft is shared only as a link to the hosted page. A comment at the top of the file says so.

`python3 drafts_helene/mail_happy_hour.py` prints the subject and reads the draft. It does not rebuild the draft from `index.html`, and it does not send mail.
