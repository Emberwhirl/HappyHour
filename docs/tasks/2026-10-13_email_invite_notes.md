# Email safe invite notes, 13 October 2026

## Files

`email/invite.html` is a full document for the hosted page. Once this branch is deployed, that page is at https://sonic-beryl-7zlowfy.vercel.app/email/invite.html

`email/invite-paste.html` is the same table, style block and preheader, without the document wrapper. Paste that file into the Outlook HTML source field.

## Images and links

The poster is `email/poster-1200.jpg`, 1200 by 1697 pixels, about 213 KB, shown near 536 pixels wide inside the frame. Its address is https://sonic-beryl-7zlowfy.vercel.app/email/poster-1200.jpg

The mascot is the existing file at https://sonic-beryl-7zlowfy.vercel.app/assets/images/icon.png and is 74 by 74 pixels in the header.

The RSVP button uses a table cell with a gold background, plus an Outlook round rectangle, both opening https://s2survey.net/ccr/?r=mail

Add to calendar points at https://sonic-beryl-7zlowfy.vercel.app/email/happy-hour.ics

View on the web points at https://sonic-beryl-7zlowfy.vercel.app/

## Calendar file

The file uses the same Vienna timezone block as the pages. The event starts at 17:00 on 30 October 2026 and carries the duration property PT6H, so it ends at 23:00. The summary, place and description reuse the page wording, including the fountain sentence and the RSVP request.

## Checks

`scripts/check_invitation.py` still covers the main page and the older email draft. This new file is separate, so those checks stay in place. The HTML of the paste snippet is under 100 KB. Visible sentences avoid a dash, a semicolon, and a colon outside 17:00, 23:00 and 5:00 PM.
