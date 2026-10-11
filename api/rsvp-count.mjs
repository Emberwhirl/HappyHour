// GET /api/rsvp-count returns { count, names } for the main page.
//
// Every setting comes from the Vercel env. SOSCI_DATA_API_URL is the SoSci
// "API for Data Retrieval" JSON link (?act=...). It is a secret, so it is never
// logged and never sent back to the client.
//
//   SOSCI_DATA_API_URL     required
//   SOSCI_VAR_ATTENDING    required, the "are you coming" question, e.g. AB01
//   SOSCI_ATTENDING_YES    code for yes, default 1
//   SOSCI_VAR_PLUS_ONE     optional, a number of extra guests or a yes/no question
//   SOSCI_PLUS_ONE_YES     optional, set it when SOSCI_VAR_PLUS_ONE is yes/no
//   SOSCI_VAR_FIRST_NAME   optional, first name
//   SOSCI_VAR_SHOW_NAME    optional, consent to show the first name
//   SOSCI_SHOW_NAME_YES    code for consent. Names stay empty until this is set.

const CACHE_OK = "public, s-maxage=60, stale-while-revalidate=300";
const VARIABLE = /^[A-Za-z][A-Za-z0-9_]*$/;
const MAX_PLUS_ONES = 5;
const MAX_NAME_LENGTH = 40;
const TIMEOUT_MS = 8000;

function json(status, body, cacheControl) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": cacheControl,
      "x-content-type-options": "nosniff",
    },
  });
}

const unavailable = () => json(503, { error: "unavailable" }, "no-store");

function readSettings(env) {
  const text = (key) => String(env[key] || "").trim();
  const variable = (key) => {
    const value = text(key);
    return VARIABLE.test(value) ? value : "";
  };
  const settings = {
    apiUrl: text("SOSCI_DATA_API_URL"),
    attending: variable("SOSCI_VAR_ATTENDING"),
    attendingYes: text("SOSCI_ATTENDING_YES") || "1",
    plusOne: variable("SOSCI_VAR_PLUS_ONE"),
    plusOneYes: text("SOSCI_PLUS_ONE_YES"),
    firstName: variable("SOSCI_VAR_FIRST_NAME"),
    showName: variable("SOSCI_VAR_SHOW_NAME"),
    showNameYes: text("SOSCI_SHOW_NAME_YES"),
  };
  if (!settings.apiUrl || !settings.attending) return null;
  return settings;
}

export function requestUrl(settings) {
  const url = new URL(settings.apiUrl);
  if (url.protocol !== "https:") throw new Error("SoSci data link must use https");
  const vList = [
    "FINISHED",
    settings.attending,
    settings.plusOne,
    settings.showName,
    settings.firstName,
  ].filter(Boolean);
  url.searchParams.set("vList", [...new Set(vList)].join(","));
  return url;
}

function plusOnes(record, settings) {
  if (!settings.plusOne) return 0;
  const value = record[settings.plusOne];
  if (settings.plusOneYes) return String(value) === settings.plusOneYes ? 1 : 0;
  const n = Number(value);
  if (!Number.isFinite(n)) return 0;
  return Math.min(Math.max(Math.trunc(n), 0), MAX_PLUS_ONES);
}

function shownName(record, settings) {
  if (!settings.firstName || !settings.showName || !settings.showNameYes) return "";
  if (String(record[settings.showName]) !== settings.showNameYes) return "";
  const name = String(record[settings.firstName] ?? "").replace(/\s+/g, " ").trim();
  return name.slice(0, MAX_NAME_LENGTH);
}

export function summarize(payload, settings) {
  if (!payload || typeof payload !== "object" || payload.errors) return null;
  const data = payload.data;
  if (!data || typeof data !== "object") return null;
  let count = 0;
  const names = [];
  for (const record of Object.values(data)) {
    if (!record || typeof record !== "object") continue;
    const finished = record.FINISHED === true || Number(record.FINISHED) === 1;
    if (!finished || String(record[settings.attending]) !== settings.attendingYes) continue;
    count += 1 + plusOnes(record, settings);
    const name = shownName(record, settings);
    if (name) names.push(name);
  }
  return { count, names };
}

export async function GET() {
  const settings = readSettings(process.env);
  if (!settings) return unavailable();
  try {
    const res = await fetch(requestUrl(settings), {
      headers: { accept: "application/json" },
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
    if (!res.ok) {
      console.error(`rsvp-count: SoSci answered ${res.status}`);
      return unavailable();
    }
    const summary = summarize(await res.json(), settings);
    if (!summary) {
      console.error("rsvp-count: SoSci response had errors or no data");
      return unavailable();
    }
    return json(200, summary, CACHE_OK);
  } catch (err) {
    console.error(`rsvp-count: SoSci request failed (${err && err.name})`);
    return unavailable();
  }
}
