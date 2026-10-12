// RSVP settings and event facts read by index.html and drafts_helene/happy_hour_preview.html.
// HH_SOSCI_URL is the public SoSci questionnaire link, for example https://s2survey.net/<project>/
// Leave it empty until the questionnaire is live. Both pages then show a disabled "RSVP opens soon" button.
// HH_LIVE_COUNT turns on the attendee count on index.html. It needs SOSCI_DATA_API_URL in the Vercel env.
// Never put the SoSci data link (?act=...) in this file. It is a secret.
//
// The facts below are not known yet. Leave a value empty and everything that needs it stays hidden.
// Never write a guess, "TBD", or a [PLACEHOLDER] here. assets/hh-facts.js reads them for both pages.
// HH_END_TIME       24 hour time in Vienna, for example "20:00". Shows "5:00 to 8:00 PM" and writes DTEND.
//                   While empty, the calendar file uses a 3 hour DURATION.
// HH_ADDRESS        Street address of the CCR container.
// HH_ENTRANCE       How to find the way in, as a short sentence.
// HH_MAP_URL        https link to a map. Shown as "Map".
// HH_RSVP_DEADLINE  As guests should read it, for example "Friday, October 23".
// HH_COST           For example "Free".
// HH_CONTACT        Who to ask, a name or an email address.
window.HH_CONFIG = Object.freeze({
  HH_SOSCI_URL: "https://s2survey.net/ccr/",
  HH_LIVE_COUNT: false,
  HH_END_TIME: "",
  HH_ADDRESS: "",
  HH_ENTRANCE: "",
  HH_MAP_URL: "",
  HH_RSVP_DEADLINE: "",
  HH_COST: "",
  HH_CONTACT: "",
});
