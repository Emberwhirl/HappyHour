# Poster on the main page and a smoother slideshow, 12 October 2026

Both changes are on `index.html`. RSVP, the skip link to `#rsvp`, the copy, and the event facts are unchanged.

## Poster

- `assets/images/Science Supernova-4.png` (1414 by 2000, 5.6 MB) is now exported as AVIF, WebP, and JPEG at 480, 960, and 1414 pixels wide. The names have no spaces, for example `science-supernova-4-960.avif`. The largest file is the 332 KB full-size JPEG.
- On the main page the poster is its own `<figure class="poster">` after the card, outside the slideshow. Below 1180 pixels it comes after the RSVP section. Before this change, the details were already partly below the fold at 390 by 844 and 1280 by 900, and RSVP was fully below it, so nothing may go above them. At 1180 pixels and wider it is a sticky column beside the card.
- `<picture>` with `srcset` and `sizes`, a JPEG fallback, `width`, `height`, `aspect-ratio`, `loading="lazy"`, and descriptive alt text. Tapping it opens the full-size JPEG in a new tab.
- The email version now uses the same optimized files with the same size, position, and alt text. It loads eagerly because the poster is the first thing on that page. Its look is unchanged.

## Slideshow

- The old fade never ran. `showSlide` added `is-on`, then `playKen` cancelled every animation on that picture, which included the new opacity transition, so the picture appeared at once. The pans are now tracked on their own.
- The outgoing picture stays opaque underneath while the new one fades in on top over 0.9 seconds, so the dark frame no longer flashes through.
- A horizontal swipe of 40 pixels or more on the picture goes to the next or previous slide. `touch-action: pan-y` keeps vertical scrolling. Dots work as before.
- Hover pause now listens to mouse pointers only. Touch taps fired `mouseenter` with no `mouseleave`, which would have stopped autoplay after the first swipe.
- Under `prefers-reduced-motion` there is no autoplay and no fade, and dots and swipes switch instantly.

## Checks

`scripts/check_invitation.py` covers the poster markup, files and sizes, link, alt text, and placement after `#rsvp`. It also checks that the poster is not a slide, the email version uses the optimized files, the crossfade, swipe, and reduced-motion rules are in place, and the cancel-everything pattern does not come back.
