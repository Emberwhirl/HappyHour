# Remove "Save on this device", 11 October 2026

The save button only stored a flag in the guest's browser. The lab never saw it, and guests could mistake it for an RSVP. It is gone from `index.html` and `drafts_helene/happy_hour_preview.html`.

## Removed from both pages

- The "Save on this device" button (`data-remind`).
- The status line under the card (`.thanks`, `data-thanks`), which only this button used, and its CSS, including the reduced-motion rules and the `--ok` colour.
- The saved and unsaved messages, the `localStorage` read and write, and the `happyhour-2026-10-30-reminder` key. Browsers that saved the flag before keep a harmless leftover entry. Nothing reads it.

## Unchanged

RSVP stays the gold primary button. Add to calendar and its `.ics` output are the same. The skip link still lands on `#rsvp`.

## Checks

`scripts/check_invitation.py` now requires the actions to be exactly RSVP and then Add to calendar. It fails if any trace of the feature returns to either page, the README, or `docs/*.md`. That covers the button, the status line, the messages, `localStorage`, and the key.
