# Implementation notes

## Page

`index.html` is self-contained apart from files under `assets/`. The card is an opaque dark panel on a fixed night background. Entrance motion is a short slide. `prefers-reduced-motion: reduce` turns that slide off and shows the card immediately.

A small inline script waits for fonts, decodes the images, and waits for the card animation. It then sets `document.documentElement.dataset.settled` to `true`. Screenshot and overlap checks wait for that flag.

## One place for the RSVP address and the page URL

Two meta tags in `index.html` are the source of truth:

```html
<meta name="hh-rsvp-email" content="[RSVP_EMAIL]">
<meta name="hh-page-url" content="[PAGE_URL]">
```

The page script reads them. A value is a placeholder when it matches `[A-Z0-9_]`. A value is a usable address when it looks like an email and is not a placeholder.

While the email is missing or still a placeholder:

- The reply line shows the token as text inside `[data-rsvp-slot]`.
- Email RSVP stays a disabled button with `aria-disabled="true"`.
- There is no `mailto:` link in the document.

When the meta tag holds a real address, the script replaces the slot and the button with links:

`mailto:<address>?subject=Happy hour on October 30`

`hh-page-url` is not painted on the page. The legacy sender reads it and puts it in the plain-text note. See [sending.md](sending.md).

## Personal reminder

The gold button is labeled "Save on this device". It writes `happyhour-2026-10-30-reminder` in `localStorage` on this browser only. The lab is not told.

Success text: "Saved in this browser. The lab will only know if you email them."

If storage throws or refuses the write, the click still finishes. The status line says the reminder could not be stored and points the guest at email. Reads are guarded the same way, so a blocked `localStorage` does not skip the click listener.

The status element is `role="status"` and `aria-live="polite"`. It stays in the accessibility tree when empty (clipped, not `display: none`) so a later message can be announced.

## Calendar file

"Add to calendar" builds an iCalendar document in the page.

- `DTSTART` is `20261030T170000` in `Europe/Vienna`. The page and the calendar file give that start time only.
- A `VTIMEZONE` block carries the EU rules. The last Sunday of October 2026 is October 25, so this date is already on standard time.
- `SUMMARY`, `LOCATION`, and `DESCRIPTION` are escaped for commas, semicolons, and newlines.
- The description includes the RSVP address only when that address is real.
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

`drafts_helene/happy_hour_preview.html` is the email invitation. It keeps this dark gold card and does not follow `index.html` after the draft changes. The picture is the static file `assets/images/Science Supernova-4.png`, placed first. Headers use Courier New. Body copy stays in Outfit. The draft does not mention Vienna time and does not offer an email RSVP.

Names go in `drafts_helene/rsvp-names.html`. That page is light, and each name is a line in the file.

`python3 drafts_helene/mail_happy_hour.py` prints the subject and reads the draft. It does not rebuild the draft from `index.html`, and it does not send mail.
