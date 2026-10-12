# Round 3 UX and design, plan, 12 October 2026

Source is the approved round 3 spec (poster-first main page). This branch starts from the shuffle and drag-swipe branch (`cursor/shuffled-slideshow-drag-keys-bcaa`) and keeps that work.

## Ground rules

- Copy rules from [../plan.md](../plan.md) hold for every visible string, alt text, label, and calendar text. No em or en dashes, no colons except in times, no semicolons, no "not X but Y", and light theming.
- Unknown facts are never invented. They come from `assets/hh-config.js` and anything that depends on an empty value stays hidden. No brackets, "TBD", or empty labels.
- Poster files are used as they are on `main` at the end. They are not re-encoded here. Another agent is sharpening them in a separate PR.

## Config

New keys in `assets/hh-config.js`, all empty for now.

| Spec name | Config key | Format |
| --- | --- | --- |
| `hh-end-time` | `HH_END_TIME` | 24 hour `HH:MM` in Vienna time, for example `20:00` |
| `hh-address` | `HH_ADDRESS` | Plain text |
| `hh-entrance` | `HH_ENTRANCE` | Plain text |
| `hh-map-url` | `HH_MAP_URL` | `https:` link only |
| `hh-rsvp-deadline` | `HH_RSVP_DEADLINE` | Plain text as guests should read it |
| `hh-cost` | `HH_COST` | Plain text, for example `Free` |
| `hh-contact` | `HH_CONTACT` | Plain text, a name or an address |

A new shared script, `assets/hh-facts.js`, reads and validates these once for both pages. It fills elements marked `data-fact`, sets `data-fact-href` links, and shows `data-needs` elements only when every value they need is set. Markup ships hidden and empty, so nothing shows without the script either.

- End time set: "5:00 to 8:00 PM" everywhere the time appears, and `DTEND;TZID=Europe/Vienna` in both calendar files. An end after midnight becomes "5:00 PM to 12:30 AM" and ends on October 31.
- End time empty or invalid: "5:00 PM" and `DURATION:PT3H` in both calendar files.
- Address set: the calendar `LOCATION` becomes "CCR container, address".
- The invitation check validates every new value (format, `https:`, copy rules, no placeholders).

## Layout

- 1180 px and wider. Two columns. Left is the card. Right is the poster with its caption, then a Details card. The gallery spans both columns below them, at a smaller width, then the footer. Column widths are tuned so both columns end at about the same height, and the shorter one stretches to meet the other.
- Below 1180 px. One column. Card, poster, gallery, footer. The Details card is hidden there, because the facts block and the RSVP line already carry every fact. The entrance joins the place line so nothing is lost.
- Card order is header, facts block, RSVP, letter, gin tonic callout below 1180 px (the phone order in the spec), and header, facts, letter, callout, RSVP at 1180 px and wider (the desktop order in the spec). The DOM follows the desktop order, and CSS `order` moves RSVP up on narrower screens. The letter has no links or controls, so focus order is unaffected.
- The date line under the lede is removed. The facts block replaces it, and the poster caption repeats the full date sentence.
- Phone facts block. Two lines, "Fri 30 Oct · 5:00 PM (Vienna time)" and "CCR container · address · entrance · Map", aiming under 140 px. Tablet and desktop keep three cards of equal width.
- RSVP must sit in the first screen at 390 by 844. A sticky RSVP bar is added for shorter phones. It shows only on phones, only while the questionnaire is configured, and only while the main RSVP button is still below the screen, and it hides once that button is visible.

## RSVP

- Button at least 52 px tall, full width on phones, at least 16rem wide on desktop.
- Above the button, one line from config, "RSVP by deadline · cost · Questions to contact", showing only the parts that are set, and nothing at all while all three are empty.
- Below the buttons, "Short form, about 1 minute." shown only while the questionnaire link is set, so it never sits under a disabled button.
- The main page opens the questionnaire in the same tab. `?r=web` and `?r=mail` stay.
- The Details card has a second RSVP button, and the sticky bar has a third. All of them use the same link.

## Warmth and readability

- The gin tonic sentence becomes a callout card with a teal glow taken from the poster fountain and a small glass line icon that is hidden from screen readers. The text stays near-white on a dark fill.
- Letter at 18 px, near-white, line-height 1.65, more space between paragraphs. At least 7:1 contrast.
- Footer at body size with a light color.
- Lab label larger, wider letter-spacing, AA contrast.
- Header mascot and favicon become one gold glass line icon, inline SVG on the page and an SVG data URL as the favicon. `icon.png` stays in the repo because the email version still uses it.
- The poster frame takes the card border ring and corner radius. Caption in page fonts, "Science Supernova, the Barozzi & Tardito Lab happy hour poster", then a recap line with date, time, and place.

## Gallery

The slideshow code from the shuffle PR stays. Changes on top of it.

- Section titled "Gallery" after RSVP, smaller than the old hero.
- A visible pause and play button. Hover and keyboard focus pause it. Any dot, chevron, swipe, drag, or arrow key stops auto-advance until play is pressed. The pan stops with it.
- One Tab stop. The picture frame takes focus. Left and Right move, Home and End jump, and Space toggles pause and play. Arrow keys now act only while the gallery has focus, no longer page-wide as in the shuffle PR. Dots, chevrons, and the pause button stay clickable but are out of the Tab order, so the gallery is a single stop.
- Prev and next chevrons on the picture. Dots 12 px with a 44 px hit area, hollow when off and filled when on, at least 3:1 against the card.
- Pointer capture during drags stays from the shuffle PR.
- A swipe hint on touch screens, hidden after the first swipe or any other manual change.
- Slides 2 to 6 load lazily. Slide 1 of the shuffled order is switched to eager. The poster loads eagerly from 1180 px and lazily below.
- Alt text describes the art. Two are anime-style illustrations of four women in gowns on a Vienna rooftop terrace. Four are painted still lifes.
- A polite live region announces the picture after manual changes. It is silent while auto-advance runs.

## Email version

Only the shared facts and DTEND. Its time card shows the end time when set, its place card gets address, entrance, and map when set, and its calendar file gets `DTEND` or `DURATION:PT3H`. It still opens the questionnaire in a new tab and still has no Vienna time.

## Spec points that need a call

- "questions: contact" has a colon, which the copy rules forbid. The line reads "Questions to contact" instead.
- The spec mentions `?r=mail` next to the same-tab change, but the email version is out of scope apart from facts and DTEND. Only the main page changes to same tab.
- A visible pause button and a single Tab stop pull against each other. The gallery is one Tab stop, and Space on it does the same as the button.
- Arrow keys move from page-wide to gallery-only, as the single Tab stop implies.

## Checks

- `scripts/browser.mjs`, a shared headless Chrome harness with no extra packages, now used by both browser checks.
- `scripts/check_slideshow.mjs` updated for the gallery. Single Tab stop, pause and play, manual stop, chevrons, dot sizes, hint, lazy slides, alt text, plus the shuffle, drag, and touch checks it already has.
- `scripts/check_page.mjs`, new. Layout at 1280 and 390, column balance, poster and Details visible, RSVP in the first screen or sticky bar, facts block height, no horizontal scroll, no console errors, empty config shows nothing, a filled config shows every fact and writes DTEND, DURATION:PT3H otherwise, same-tab RSVP, email version facts and calendar file, and measured contrast on rendered pixels.
- `scripts/check_invitation.py` static checks updated and extended, and it runs both browser checks.
- Before and after screenshots at 1280 and 390 as PNG artifacts.
