// Event facts from assets/hh-config.js, shared by index.html and drafts_helene/happy_hour_preview.html.
// Empty, invalid, or placeholder values count as unknown, and everything that needs them stays hidden.
// [data-fact="key"] gets the text, [data-fact-href="key"] gets the link, and [data-needs="key key"]
// is shown only when every listed key has a value. Markup ships hidden and empty.
(function () {
  const config = window.HH_CONFIG || {};
  const DATE = "20261030";
  const NEXT_DATE = "20261031";
  const START = { hour: 17, minute: 0 };
  const UNKNOWN = /^(tbd|tba|tbc|n\/?a|unknown|-+|\?+)$/i;
  const PLACEHOLDER = /\[[^\]]*\]/;

  const text = (key) => {
    const value = String(config[key] == null ? "" : config[key]).replace(/\s+/g, " ").trim();
    if (!value || UNKNOWN.test(value) || PLACEHOLDER.test(value)) return "";
    return value;
  };

  const end = (() => {
    const match = /^([01]?\d|2[0-3]):([0-5]\d)$/.exec(text("HH_END_TIME"));
    if (!match) return null;
    const hour = Number(match[1]);
    const minute = Number(match[2]);
    const afterStart = hour * 60 + minute > START.hour * 60 + START.minute;
    // Up to 6 in the morning is read as after midnight. Any other time before the start is a typo.
    if (!afterStart && hour >= 6) return null;
    return { hour, minute, nextDay: !afterStart };
  })();

  const pad = (n) => String(n).padStart(2, "0");
  const clock = (hour, minute) => `${hour % 12 || 12}:${pad(minute)}`;
  const half = (hour) => (hour < 12 ? "AM" : "PM");
  const startLabel = `${clock(START.hour, START.minute)} ${half(START.hour)}`;
  let time = startLabel;
  if (end) {
    const endLabel = `${clock(end.hour, end.minute)} ${half(end.hour)}`;
    time = !end.nextDay && half(end.hour) === half(START.hour)
      ? `${clock(START.hour, START.minute)} to ${endLabel}`
      : `${startLabel} to ${endLabel}`;
  }

  const map = (() => {
    const raw = text("HH_MAP_URL");
    if (!raw) return "";
    try {
      const url = new URL(raw);
      return url.protocol === "https:" ? url.href : "";
    } catch (err) {
      return "";
    }
  })();

  const facts = {
    time,
    address: text("HH_ADDRESS"),
    entrance: text("HH_ENTRANCE"),
    map,
    deadline: text("HH_RSVP_DEADLINE"),
    cost: text("HH_COST"),
    contact: text("HH_CONTACT"),
  };

  const rsvpTerms = [
    facts.deadline && `RSVP by ${facts.deadline}`,
    facts.cost,
    facts.contact && `Questions to ${facts.contact}`,
  ].filter(Boolean);

  function icsTiming() {
    if (!end) return "DURATION:PT3H";
    return `DTEND;TZID=Europe/Vienna:${end.nextDay ? NEXT_DATE : DATE}T${pad(end.hour)}${pad(end.minute)}00`;
  }

  function location(place) {
    return facts.address ? `${place}, ${facts.address}` : place;
  }

  function apply(root) {
    const scope = root || document;
    scope.querySelectorAll("[data-fact]").forEach((el) => {
      const value = facts[el.dataset.fact];
      if (value) el.textContent = value;
    });
    scope.querySelectorAll("[data-fact-href]").forEach((el) => {
      const value = facts[el.dataset.factHref];
      if (value) el.href = value;
      else el.removeAttribute("href");
    });
    scope.querySelectorAll("[data-needs]").forEach((el) => {
      el.hidden = !el.dataset.needs.split(/\s+/).every((key) => facts[key]);
    });
  }

  window.HH_FACTS = Object.freeze({ ...facts, hasEnd: Boolean(end), rsvpTerms, icsTiming, location, apply });
})();
