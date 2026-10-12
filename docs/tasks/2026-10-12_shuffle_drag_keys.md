# Shuffled slideshow with mouse drag and arrow keys, 12 October 2026

All changes are in the slideshow on `index.html`. The 0.9 second crossfade, reduced motion, hover pause, the poster, the email version, the copy, and the event facts are unchanged. No visible text was added.

## Shuffle

- The six pictures are shuffled on every page load with a Fisher-Yates shuffle.
- Each picture moves together with its dot and its pan, and the dots are renumbered `0` to `5` in the new order. The lit dot and `aria-current` always match the shown picture.
- The first shuffled picture shows at once, without a fade. Without JavaScript the terrace still shows first.

## Drag, swipe, and keys

- A mouse can now click and drag the picture like a touch swipe. A press becomes a drag after 8 pixels of movement, and only then does the frame take pointer capture. A horizontal drag of 40 pixels or more goes to the next or previous picture, as before.
- A press that moves less than 8 pixels is a plain click and behaves exactly as before. The click at the end of a real drag is swallowed, so a drag can never press a dot or open anything. Pictures cannot be dragged out as images and text is not selected.
- The frame shows a grab cursor, and a grabbing cursor while it is dragged.
- On touch screens Chrome first captures the finger on the picture itself. Moving that capture to the frame fires `lostpointercapture` on the picture, which bubbles to the frame, so the frame only ends a swipe when it loses capture itself.
- Left and Right arrow keys go to the previous and next picture. They are left alone inside inputs, text areas, selects, and editable text, and when Shift, Ctrl, Alt, or Cmd is held.
- A drag or key press while the mouse is over the slides, or focus is inside them, keeps autoplay and the pan paused.

## Checks

- `scripts/check_slideshow.mjs` is new. It serves the repository on 127.0.0.1 and drives headless Chrome over the DevTools protocol with no extra packages. At 1280 and 390 pixels it checks that the order differs across eight loads and the dots match every time, mouse drag in both directions with pointer capture, swallowed clicks, no text selection and no native image drag, plain clicks and dots, arrow keys and form fields, touch swipes, vertical drags and taps, reduced motion, hover pause, console errors, and horizontal scroll.
- `scripts/check_invitation.py` runs it when node is installed, and checks the shuffle, drag, and key code in the page markup.
- In Chrome a drag that starts on the picture never selects text, even without `user-select: none` and the `selectstart` guard. Those two are kept for other browsers.
