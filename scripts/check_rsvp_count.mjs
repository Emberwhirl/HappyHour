#!/usr/bin/env node
// Check api/rsvp-count.mjs offline. fetch is replaced, so nothing leaves this machine.

import assert from "node:assert/strict";
import { GET } from "../api/rsvp-count.mjs";

const SECRET = "https://s2survey.net/hh-test/?act=SECRETtoken123";
const KEYS = [
  "SOSCI_DATA_API_URL",
  "SOSCI_VAR_ATTENDING",
  "SOSCI_ATTENDING_YES",
  "SOSCI_VAR_PLUS_ONE",
  "SOSCI_PLUS_ONE_YES",
  "SOSCI_VAR_FIRST_NAME",
  "SOSCI_VAR_SHOW_NAME",
  "SOSCI_SHOW_NAME_YES",
];
const realFetch = globalThis.fetch;
const realError = console.error;
const logged = [];

const SAMPLE = {
  metadata: { project: "hh-test" },
  data: {
    C1: { CASE: 1, FINISHED: 1, AB01: 1, AB02: 1, AB03: 2, AB04: " Anna ", EMAIL: "anna@example.com", DIET: "vegan" },
    C2: { CASE: 2, FINISHED: 1, AB01: 1, AB02: 0, AB03: 1, AB04: "Ben" },
    C3: { CASE: 3, FINISHED: 0, AB01: 1, AB02: 3, AB03: 2, AB04: "Unfinished" },
    C4: { CASE: 4, FINISHED: 1, AB01: 2, AB02: 2, AB03: 2, AB04: "Not coming" },
    C5: { CASE: 5, FINISHED: 1, AB01: 1, AB02: 99, AB03: 2, AB04: "Chris" },
  },
};

function setEnv(values) {
  for (const key of KEYS) delete process.env[key];
  Object.assign(process.env, values);
}

async function call() {
  const res = await GET(new Request("https://example.test/api/rsvp-count"));
  const text = await res.text();
  return { res, text, body: JSON.parse(text) };
}

function assertNoSecret({ res, text }) {
  assert.ok(!text.includes("act="), "response body leaks the data link");
  assert.ok(!text.includes("SECRETtoken123"), "response body leaks the token");
  for (const [, value] of res.headers) assert.ok(!value.includes("SECRETtoken123"), "a header leaks the token");
  assert.ok(!logged.join("\n").includes("SECRETtoken123"), "a log line leaks the token");
}

const full = {
  SOSCI_DATA_API_URL: SECRET,
  SOSCI_VAR_ATTENDING: "AB01",
  SOSCI_VAR_PLUS_ONE: "AB02",
  SOSCI_VAR_SHOW_NAME: "AB03",
  SOSCI_SHOW_NAME_YES: "2",
  SOSCI_VAR_FIRST_NAME: "AB04",
};

console.error = (...args) => logged.push(args.join(" "));
let requested = null;
globalThis.fetch = async (url) => {
  requested = new URL(url);
  return new Response(JSON.stringify(SAMPLE), { status: 200, headers: { "content-type": "application/json" } });
};

try {
  setEnv({});
  let out = await call();
  assert.equal(out.res.status, 503, "missing env should be 503");
  assert.equal(out.res.headers.get("cache-control"), "no-store");
  assert.deepEqual(out.body, { error: "unavailable" });
  assert.equal(requested, null, "missing env must not call SoSci");

  setEnv({ SOSCI_DATA_API_URL: SECRET });
  out = await call();
  assert.equal(out.res.status, 503, "missing attending variable should be 503");

  setEnv(full);
  out = await call();
  assert.equal(out.res.status, 200);
  assert.equal(out.res.headers.get("cache-control"), "public, s-maxage=60, stale-while-revalidate=300");
  assert.deepEqual(Object.keys(out.body).sort(), ["count", "names"], "only count and names may be returned");
  // Anna 1+1, Ben 1+0, Chris 1+5 (capped). Unfinished and "no" are skipped.
  assert.equal(out.body.count, 9);
  assert.deepEqual(out.body.names, ["Anna", "Chris"], "only consenting guests are named");
  assert.equal(requested.searchParams.get("vList"), "FINISHED,AB01,AB02,AB03,AB04");
  assert.equal(requested.searchParams.get("act"), "SECRETtoken123");
  assert.ok(!out.text.includes("example.com") && !out.text.includes("vegan"), "extra fields leaked");
  assertNoSecret(out);

  setEnv({ ...full, SOSCI_SHOW_NAME_YES: "" });
  out = await call();
  assert.deepEqual(out.body.names, [], "names need an explicit consent code");

  setEnv({ ...full, SOSCI_PLUS_ONE_YES: "1" });
  out = await call();
  assert.equal(out.body.count, 4, "yes/no plus-one counts one extra guest");

  setEnv(full);
  globalThis.fetch = async () => new Response("down", { status: 500 });
  out = await call();
  assert.equal(out.res.status, 503, "a SoSci error should be 503");
  assertNoSecret(out);

  globalThis.fetch = async () => new Response(JSON.stringify({ errors: ["Unknown variable AB09"] }), { status: 200 });
  out = await call();
  assert.equal(out.res.status, 503, "a SoSci errors attribute should be 503");

  globalThis.fetch = async () => { throw new TypeError(`fetch failed for ${SECRET}`); };
  out = await call();
  assert.equal(out.res.status, 503, "a network error should be 503");
  assertNoSecret(out);

  setEnv({ ...full, SOSCI_DATA_API_URL: "http://s2survey.net/hh-test/?act=SECRETtoken123" });
  out = await call();
  assert.equal(out.res.status, 503, "a non-https data link should be refused");
  assertNoSecret(out);
} finally {
  globalThis.fetch = realFetch;
  console.error = realError;
  setEnv({});
}

console.log("rsvp-count check passed.");
