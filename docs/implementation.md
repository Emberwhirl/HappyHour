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
- `terrace.jpg` and `feast.jpg` under the date line, each shown at a 16:9 frame. The first is the Vienna terrace with two friends looking at a phone. The second is the same terrace with food and beer on the table.

The pictures crossfade every few seconds. Two controls under the frame pick a picture directly. Hovering or focusing the frame pauses the change. With reduced motion, the terrace picture stays until a control is used. The header icon is decorative because the lab name is already beside it.

## Addresses with no trailing slash

Font and image URLs are relative (`assets/...`). If a host serves the page at a path with no trailing slash and no filename, those URLs would otherwise resolve one folder too high. A blocking script at the top of `<head>` inserts `<base href>` pointing at the page directory before the icon and the style sheet are requested.

## Preview copy

`drafts_helene/happy_hour_preview.html` is generated from `index.html`. The generator rewrites `url("assets/` , `src="assets/` , and `href="assets/` so the preview, which lives one folder down, still loads fonts and pictures. Regenerate it with `python3 drafts_helene/mail_happy_hour.py`. That command does not send mail.
