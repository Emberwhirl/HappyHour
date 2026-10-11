// RSVP settings read by index.html and drafts_helene/happy_hour_preview.html.
// HH_SOSCI_URL is the public SoSci questionnaire link, for example https://s2survey.net/<project>/
// Leave it empty until the questionnaire is live. Both pages then show a disabled "RSVP opens soon" button.
// HH_LIVE_COUNT turns on the attendee count on index.html. It needs SOSCI_DATA_API_URL in the Vercel env.
// Never put the SoSci data link (?act=...) in this file. It is a secret.
window.HH_CONFIG = Object.freeze({
  HH_SOSCI_URL: "https://s2survey.net/ccr/",
  HH_LIVE_COUNT: false,
});
