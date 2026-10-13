# Round 4 guest review notes, 13 October 2026

## What changed

The email draft now loads Cormorant Garamond from `assets/fonts/` for the headline, the italic subtitle, the large date, and the time and place lines. Outfit remains the body face. Georgia and Times New Roman are the backup serif faces if the webfont is slow.

Both calendar files include the duration property PT6H after the Vienna start time. That is six hours, from 5:00 PM to 11:00 PM. No end time, address, map, deadline, cost, or contact slots were added.

The email date line, time card, and poster caption now say Vienna time. The main poster caption is Friday, October 30, 2026, 5:00 PM, CCR container, and it sits in the same footer as Open the full-size poster.

The slideshow has a Pause button. While it reads Pause, the pictures advance. While it reads Play, they stay put. A dot click calls the same resume path as a swipe, so a hover or a focused dot keeps the pause. Arrow keys are ignored unless focus is inside the slideshow. Only the current dot has tabindex 0. The others use tabindex -1, and focus moves with the arrows. Each dot is 44 by 44 pixels and keeps its aria-label. If pointer capture is lost on release with the button up, the last drag position still chooses the direction.

The slideshow markup starts with `data-pending`, which hides it. The shuffle script removes that attribute after it reorders the pictures. Without JavaScript a small style shows the terrace again.

AVIF files are quality 50 with 4 2 0 chroma. WebP files are quality 75 with sharp YUV. At 480 pixels the AVIF is about 30 KB, down from about 125 KB. At 1414 pixels the AVIF is about 117 KB, down from about 399 KB. A face crop differed from the source by about 2 levels out of 255 on average.

The main poster image uses `fetchpriority="high"` and is not marked lazy. Its alt text describes the fountain, the container, and the nebula, and it does not say Science Supernova. The slide descriptions were checked against the pictures and left as they are. The terrace line matches four friends at dusk with two of them looking at a phone.

The header icon is a simple gold glass on a dark tile, used in the seal and the favicon, so the anime mascot is gone. On screens 1180 pixels and wider, the existing fountain sentence and Hope to see you there sit under the poster.

On the email draft, screens up to 680 pixels wide show the Happy Hour heading, then the poster, then the rest of the card.

## Checks

`scripts/check_invitation.py` covers the eager poster, the caption, the six hour duration, and Vienna time on the email draft. `scripts/check_slideshow.mjs` expects arrows to move pictures only after a dot is focused, and a dot click during hover to leave the pan paused.
