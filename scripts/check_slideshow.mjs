#!/usr/bin/env node
// Check the slideshow in a real headless Chrome at 1280 and 390 pixels wide.
// The page is served from this repository on 127.0.0.1, and Chrome cannot resolve any other host.
// Covers the shuffle, mouse drag, arrow keys, touch swipe, hover pause, reduced motion,
// console errors, and horizontal scroll. Set CHROME_PATH to pick a browser.
// HH_QUICK=1 skips the two 7.6 second autoplay waits.

import { spawn, spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, existsSync } from "node:fs";
import { createServer } from "node:http";
import { tmpdir } from "node:os";
import { extname, join, normalize, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(fileURLToPath(new URL("..", import.meta.url)));
const LOADS = 8;
const VIEWPORTS = [
  { name: "1280", width: 1280, height: 900, scale: 1, mobile: false },
  { name: "390", width: 390, height: 844, scale: 3, mobile: true },
];
const TYPES = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".jpg": "image/jpeg",
  ".png": "image/png",
  ".webp": "image/webp",
  ".avif": "image/avif",
  ".woff2": "font/woff2",
};
const problems = [];
const notes = [];

function check(ok, message) {
  if (!ok) problems.push(message);
  return ok;
}

function findChrome() {
  if (process.env.CHROME_PATH) return process.env.CHROME_PATH;
  for (const name of ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"]) {
    const found = spawnSync("sh", ["-c", `command -v ${name}`], { encoding: "utf8" });
    if (found.status === 0 && found.stdout.trim()) return found.stdout.trim();
  }
  for (const path of [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
  ]) {
    if (existsSync(path)) return path;
  }
  return "";
}

// The order of pictures and dot labels as written in index.html.
function markupSlides() {
  const html = readFileSync(join(ROOT, "index.html"), "utf8");
  const frame = html.match(/<div class="still-frame">([\s\S]*?)<\/div>/)[1];
  const nav = html.match(/<div class="still-nav">([\s\S]*?)<\/div>/)[1];
  const srcs = [...frame.matchAll(/<img\b[^>]*\bsrc="([^"]+)"/g)].map((m) => m[1]);
  const labels = [...nav.matchAll(/aria-label="([^"]+)"/g)].map((m) => m[1]);
  return { srcs, labels, labelFor: new Map(srcs.map((src, i) => [src, labels[i]])) };
}

function serve() {
  const server = createServer((req, res) => {
    const path = decodeURIComponent(new URL(req.url, "http://x").pathname);
    let file = normalize(join(ROOT, path));
    if (!file.startsWith(ROOT + sep) && file !== ROOT) {
      res.writeHead(403).end();
      return;
    }
    if (path.endsWith("/")) file = join(file, "index.html");
    try {
      const body = readFileSync(file);
      res.writeHead(200, { "content-type": TYPES[extname(file).toLowerCase()] || "application/octet-stream" });
      res.end(body);
    } catch (err) {
      res.writeHead(404).end();
    }
  });
  return new Promise((done) => server.listen(0, "127.0.0.1", () => done(server)));
}

async function launch(chromePath) {
  const profile = mkdtempSync(join(tmpdir(), "hh-chrome-"));
  const proc = spawn(chromePath, [
    "--headless=new",
    "--no-sandbox",
    "--disable-gpu",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-background-networking",
    "--disable-component-update",
    "--disable-sync",
    "--mute-audio",
    "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1",
    "--remote-debugging-port=0",
    `--user-data-dir=${profile}`,
    "about:blank",
  ], { stdio: ["ignore", "ignore", "pipe"] });
  let stderr = "";
  const wsUrl = await new Promise((done, failed) => {
    const timeout = setTimeout(() => failed(new Error(`Chrome did not start\n${stderr.slice(-2000)}`)), 60000);
    proc.stderr.on("data", (chunk) => {
      stderr += chunk;
      const match = stderr.match(/DevTools listening on (ws:\/\/\S+)/);
      if (match) {
        clearTimeout(timeout);
        done(match[1]);
      }
    });
    proc.on("exit", (code) => failed(new Error(`Chrome exited with ${code}\n${stderr.slice(-2000)}`)));
  });
  const close = () => {
    proc.kill("SIGKILL");
    try { rmSync(profile, { recursive: true, force: true }); } catch (err) { /* best effort */ }
  };
  return { wsUrl, close };
}

class Cdp {
  constructor(ws) {
    this.ws = ws;
    this.nextId = 1;
    this.pending = new Map();
    this.listeners = [];
    ws.addEventListener("message", (event) => {
      const msg = JSON.parse(event.data);
      if (msg.id && this.pending.has(msg.id)) {
        const { done, failed, method } = this.pending.get(msg.id);
        this.pending.delete(msg.id);
        if (msg.error) failed(new Error(`${method}: ${msg.error.message}`));
        else done(msg.result);
        return;
      }
      for (const listener of this.listeners) listener(msg);
    });
  }

  static async connect(url) {
    const ws = new WebSocket(url);
    await new Promise((done, failed) => {
      ws.addEventListener("open", done, { once: true });
      ws.addEventListener("error", () => failed(new Error("could not reach Chrome DevTools")), { once: true });
    });
    return new Cdp(ws);
  }

  send(method, params = {}, sessionId) {
    const id = this.nextId++;
    this.ws.send(JSON.stringify({ id, method, params, ...(sessionId ? { sessionId } : {}) }));
    return new Promise((done, failed) => this.pending.set(id, { done, failed, method }));
  }

  on(listener) {
    this.listeners.push(listener);
  }

  close() {
    this.ws.close();
  }
}

const PROBE = `
  window.__probe = { clicks: 0, captures: 0, dragstarts: 0, transitions: [], pointerId: null };
  document.addEventListener("click", () => { window.__probe.clicks += 1; });
  document.addEventListener("gotpointercapture", () => { window.__probe.captures += 1; }, true);
  document.addEventListener("pointerdown", (e) => { window.__probe.pointerId = e.pointerId; }, true);
  window.addEventListener("dragstart", (e) => { if (!e.defaultPrevented) window.__probe.dragstarts += 1; });
  document.addEventListener("transitionrun", (e) => {
    if (e.target.matches && e.target.matches(".still-frame img")) {
      window.__probe.transitions.push({ src: e.target.getAttribute("src"), prop: e.propertyName, at: performance.now() });
    }
  }, true);
`;

const STATE = `(() => {
  const s = document.querySelector("[data-slides]");
  const frame = s.querySelector(".still-frame");
  const frames = [...frame.querySelectorAll("img")];
  const dots = [...s.querySelectorAll("[data-slide-to]")];
  const on = frames.findIndex((img) => img.classList.contains("is-on"));
  const pan = frames[on] && frames[on].getAnimations().find((a) => !(a instanceof CSSTransition));
  const fade = frames[on] && frames[on].getAnimations().find((a) => a instanceof CSSTransition && a.transitionProperty === "opacity");
  return {
    frames: frames.map((img) => img.getAttribute("src")),
    labels: dots.map((d) => d.getAttribute("aria-label")),
    slideTo: dots.map((d) => d.dataset.slideTo),
    on,
    onCount: frames.filter((img) => img.classList.contains("is-on")).length,
    dotOn: dots.findIndex((d) => d.classList.contains("is-on")),
    dotCurrent: dots.findIndex((d) => d.getAttribute("aria-current") === "true"),
    ariaOk: frames.every((img) => img.hasAttribute("aria-hidden") === !img.classList.contains("is-on")),
    leaving: frames.findIndex((img) => img.classList.contains("is-leaving")),
    pan: pan ? pan.playState : "none",
    fadeMs: fade ? fade.effect.getTiming().duration : 0,
    dragging: frame.classList.contains("is-dragging"),
    cursor: getComputedStyle(frame).cursor,
    selection: String(getSelection()),
    href: location.href,
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
    bodyScrollWidth: document.body.scrollWidth,
    probe: window.__probe,
  };
})()`;

const sleep = (ms) => new Promise((done) => setTimeout(done, ms));

async function openPage(cdp, viewport, url, { reduce = false, touch = false } = {}) {
  const { targetId } = await cdp.send("Target.createTarget", { url: "about:blank" });
  const { sessionId } = await cdp.send("Target.attachToTarget", { targetId, flatten: true });
  const send = (method, params) => cdp.send(method, params, sessionId);
  const errors = [];
  let loaded = null;
  cdp.on((msg) => {
    if (msg.sessionId !== sessionId) return;
    if (msg.method === "Runtime.exceptionThrown") {
      errors.push(msg.params.exceptionDetails.exception?.description || msg.params.exceptionDetails.text);
    } else if (msg.method === "Runtime.consoleAPICalled" && ["error", "assert"].includes(msg.params.type)) {
      errors.push(msg.params.args.map((a) => a.value ?? a.description).join(" "));
    } else if (msg.method === "Log.entryAdded" && msg.params.entry.level === "error") {
      errors.push(`${msg.params.entry.text} ${msg.params.entry.url || ""}`.trim());
    } else if (msg.method === "Page.loadEventFired" && loaded) {
      loaded();
    }
  });
  await send("Page.enable");
  await send("Runtime.enable");
  await send("Log.enable");
  await send("Emulation.setDeviceMetricsOverride", {
    width: viewport.width,
    height: viewport.height,
    deviceScaleFactor: viewport.scale,
    mobile: viewport.mobile,
  });
  await send("Emulation.setEmulatedMedia", {
    features: [{ name: "prefers-reduced-motion", value: reduce ? "reduce" : "no-preference" }],
  });
  if (touch) await send("Emulation.setTouchEmulationEnabled", { enabled: true, maxTouchPoints: 5 });
  await send("Page.addScriptToEvaluateOnNewDocument", { source: PROBE });

  const evaluate = async (expression) => {
    const result = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
    if (result.exceptionDetails) throw new Error(`${expression.slice(0, 80)}: ${result.exceptionDetails.text}`);
    return result.result.value;
  };
  const frames = () => evaluate("new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)))");
  const load = async () => {
    const done = new Promise((r) => { loaded = r; });
    await send("Page.navigate", { url });
    await done;
    await evaluate("document.fonts.ready.then(() => true)");
    await frames();
  };
  const state = () => evaluate(STATE);
  const rect = (selector, scroll = true) => evaluate(`(() => {
    const el = document.querySelector(${JSON.stringify(selector)});
    if (${scroll}) el.scrollIntoView({ block: "center", behavior: "instant" });
    const r = el.getBoundingClientRect();
    return { x: r.left + r.width / 2, y: r.top + r.height / 2, left: r.left, right: r.right, top: r.top, bottom: r.bottom, width: r.width, height: r.height };
  })()`);
  const mouse = (type, x, y, pressed) => send("Input.dispatchMouseEvent", {
    type, x, y, button: type === "mouseMoved" && !pressed ? "none" : "left", buttons: pressed ? 1 : 0, clickCount: type === "mouseMoved" ? 0 : 1,
  });
  const drag = async (from, to, { steps = 8, during } = {}) => {
    await mouse("mouseMoved", from.x, from.y, false);
    await mouse("mousePressed", from.x, from.y, true);
    for (let i = 1; i <= steps; i += 1) {
      await mouse("mouseMoved", from.x + ((to.x - from.x) * i) / steps, from.y + ((to.y - from.y) * i) / steps, true);
    }
    const mid = during ? await during() : null;
    await mouse("mouseReleased", to.x, to.y, false);
    await frames();
    return mid;
  };
  const touchSwipe = async (from, to, steps = 8) => {
    await send("Input.dispatchTouchEvent", { type: "touchStart", touchPoints: [{ x: from.x, y: from.y, id: 1 }] });
    for (let i = 1; i <= steps; i += 1) {
      await send("Input.dispatchTouchEvent", {
        type: "touchMove",
        touchPoints: [{ x: from.x + ((to.x - from.x) * i) / steps, y: from.y + ((to.y - from.y) * i) / steps, id: 1 }],
      });
      await sleep(16);
    }
    await send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
    await frames();
  };
  const key = async (name, code) => {
    const base = { key: name, code: name, windowsVirtualKeyCode: code, nativeVirtualKeyCode: code };
    await send("Input.dispatchKeyEvent", { type: "rawKeyDown", ...base });
    await send("Input.dispatchKeyEvent", { type: "keyUp", ...base });
    await frames();
  };
  const close = () => cdp.send("Target.closeTarget", { targetId });
  return { send, evaluate, frames, load, state, rect, mouse, drag, touchSwipe, key, errors, close };
}

function checkConsistent(label, s, markup) {
  check(s.frames.length === markup.srcs.length, `${label}: expected ${markup.srcs.length} pictures, found ${s.frames.length}`);
  check([...s.frames].sort().join() === [...markup.srcs].sort().join(), `${label}: the pictures are not the same set as the markup`);
  check(s.labels.every((l, i) => markup.labelFor.get(s.frames[i]) === l), `${label}: a dot label does not match its picture (${s.labels.join(" | ")})`);
  check(s.slideTo.every((to, i) => to === String(i)), `${label}: dot data-slide-to is not 0 to ${s.frames.length - 1} in order`);
  check(s.onCount === 1, `${label}: ${s.onCount} pictures are showing`);
  check(s.dotOn === s.on && s.dotCurrent === s.on, `${label}: the lit dot (${s.dotOn}, aria-current ${s.dotCurrent}) is not the shown picture (${s.on})`);
  check(s.ariaOk, `${label}: aria-hidden does not follow the shown picture`);
}

function checkLayout(label, s) {
  check(s.scrollWidth <= s.clientWidth && s.bodyScrollWidth <= s.clientWidth,
    `${label}: horizontal scroll (scrollWidth ${s.scrollWidth}, body ${s.bodyScrollWidth}, width ${s.clientWidth})`);
}

const next = (i, n) => (i + 1) % n;
const prev = (i, n) => (i - 1 + n) % n;

async function shuffleChecks(page, vp, markup) {
  const orders = new Set();
  for (let i = 0; i < LOADS; i += 1) {
    await page.load();
    const s = await page.state();
    const label = `${vp.name}px load ${i + 1}`;
    checkConsistent(label, s, markup);
    checkLayout(label, s);
    check(s.on === 0, `${label}: the first shuffled picture is not the one showing`);
    check(s.probe.transitions.length === 0, `${label}: the first picture faded in on load`);
    orders.add(s.frames.join(","));
  }
  check(orders.size > 1, `${vp.name}px: the picture order was the same on all ${LOADS} loads`);
  notes.push(`${vp.name}px shuffle, ${orders.size} different orders in ${LOADS} loads, dots matched every time`);
}

async function mouseChecks(page, vp, markup) {
  await page.load();
  let s = await page.state();
  const n = s.frames.length;
  let frame = await page.rect(".still-frame");
  const left = { x: frame.left + frame.width * 0.75, y: frame.y };
  const right = { x: frame.left + frame.width * 0.25, y: frame.y };
  check(s.cursor === "grab", `${vp.name}px: the frame cursor is ${s.cursor}, not grab`);

  // Hovering pauses the pan.
  await page.mouse("mouseMoved", frame.x, frame.y, false);
  await page.frames();
  s = await page.state();
  check(s.pan === "paused", `${vp.name}px: hover did not pause the pan (${s.pan})`);

  // A plain click, and one with a small wobble, does nothing to the slides and still reaches the page.
  let before = await page.state();
  await page.mouse("mousePressed", frame.x, frame.y, true);
  await page.mouse("mouseReleased", frame.x, frame.y, false);
  await page.drag(frame, { x: frame.x + 4, y: frame.y + 2 }, { steps: 2 });
  s = await page.state();
  check(s.on === before.on, `${vp.name}px: a plain click changed the slide`);
  check(s.probe.clicks === before.probe.clicks + 2, `${vp.name}px: a plain click on the picture was swallowed (${s.probe.clicks - before.probe.clicks} of 2 arrived)`);
  check(s.probe.captures === before.probe.captures, `${vp.name}px: a plain click captured the pointer`);

  // Drag left goes forward, with pointer capture and the grabbing cursor while it moves.
  before = await page.state();
  const mid = await page.drag(left, right, {
    during: () => page.evaluate(`({
      captured: document.querySelector(".still-frame").hasPointerCapture(window.__probe.pointerId),
      dragging: document.querySelector(".still-frame").classList.contains("is-dragging"),
      cursor: getComputedStyle(document.querySelector(".still-frame")).cursor,
    })`),
  });
  s = await page.state();
  check(mid.captured, `${vp.name}px: the frame did not capture the pointer during a drag`);
  check(mid.dragging, `${vp.name}px: the frame was not marked as dragging`);
  check(mid.cursor === "grabbing", `${vp.name}px: cursor during a drag is ${mid.cursor}`);
  check(!s.dragging, `${vp.name}px: the frame stayed marked as dragging after release`);
  check(s.on === next(before.on, n), `${vp.name}px: mouse drag left did not go to the next picture (${before.on} to ${s.on})`);
  check(s.probe.clicks === before.probe.clicks, `${vp.name}px: the click after a drag was not swallowed`);
  check(s.leaving === before.on, `${vp.name}px: the old picture did not stay underneath during the fade`);
  check(s.fadeMs === 900, `${vp.name}px: the crossfade is ${s.fadeMs} ms, not 900`);
  check(s.pan === "paused", `${vp.name}px: the new pan runs while the mouse is still over the slides (${s.pan})`);
  checkConsistent(`${vp.name}px after drag left`, s, markup);

  // Drag right goes back.
  before = s;
  await page.drag(right, left);
  s = await page.state();
  check(s.on === prev(before.on, n), `${vp.name}px: mouse drag right did not go back (${before.on} to ${s.on})`);

  // A short drag is not a swipe, and its click is still swallowed.
  before = s;
  await page.drag(frame, { x: frame.x - 20, y: frame.y });
  s = await page.state();
  check(s.on === before.on, `${vp.name}px: a 20 px drag changed the slide`);
  check(s.probe.clicks === before.probe.clicks, `${vp.name}px: the click after a short drag was not swallowed`);

  // A drag whose first move already leaves the frame still counts.
  frame = await page.rect(".still-frame");
  before = await page.state();
  const low = frame.bottom - 6;
  await page.drag({ x: frame.x + 75, y: low }, { x: frame.x - 75, y: frame.bottom + 40 }, { steps: 1 });
  s = await page.state();
  check(s.on === next(before.on, n), `${vp.name}px: a drag that left the frame on its first move did not go forward (${before.on} to ${s.on})`);
  check(s.probe.clicks === before.probe.clicks, `${vp.name}px: the click after a drag that left the frame was not swallowed`);
  await page.drag({ x: frame.x - 75, y: low }, { x: frame.x + 75, y: frame.bottom + 40 }, { steps: 1 });
  s = await page.state();
  check(s.on === before.on, `${vp.name}px: a drag that left the frame on its first move did not go back`);

  // Dragging from the picture onto a dot does not press the dot.
  before = await page.state();
  frame = await page.rect(".still-frame");
  const dot = await page.rect(`[data-slide-to="${(before.on + 2) % n}"]`, false);
  await page.drag({ x: dot.x, y: frame.y }, dot);
  s = await page.state();
  check(s.on === before.on, `${vp.name}px: a drag that ended on a dot pressed it (${before.on} to ${s.on})`);

  // Dragging from the picture straight up across the text above it selects nothing.
  frame = await page.rect(".still-frame");
  const lede = await page.rect(".lede", false);
  const across = Math.min(frame.x, lede.right - 10);
  before = await page.state();
  await page.drag({ x: across, y: frame.top + 10 }, { x: across, y: lede.y });
  s = await page.state();
  check(s.selection === "", `${vp.name}px: a drag selected text (${JSON.stringify(s.selection.slice(0, 40))})`);
  check(s.on === before.on, `${vp.name}px: an upward drag changed the slide`);
  check(s.probe.dragstarts === 0, `${vp.name}px: a native image drag started`);
  check(s.href === before.href, `${vp.name}px: a drag navigated to ${s.href}`);

  // Dots still pick a picture.
  before = s;
  const pick = (before.on + 3) % n;
  const pickDot = await page.rect(`[data-slide-to="${pick}"]`);
  await page.mouse("mouseMoved", pickDot.x, pickDot.y, false);
  await page.mouse("mousePressed", pickDot.x, pickDot.y, true);
  await page.mouse("mouseReleased", pickDot.x, pickDot.y, false);
  await page.frames();
  s = await page.state();
  check(s.on === pick, `${vp.name}px: clicking dot ${pick} showed ${s.on}`);
  checkConsistent(`${vp.name}px after a dot`, s, markup);

  // Leaving the slides lets the pan run again.
  await page.mouse("mouseMoved", 2, 2, false);
  await page.evaluate("document.activeElement && document.activeElement.blur()");
  await page.frames();
  s = await page.state();
  check(s.pan === "running", `${vp.name}px: the pan did not resume after the mouse left (${s.pan})`);
  checkLayout(`${vp.name}px after mouse`, s);
  check(page.errors.length === 0, `${vp.name}px console errors: ${page.errors.join(" | ")}`);
  notes.push(`${vp.name}px mouse, plain click kept, drag left and right, capture, click swallowed, no selection, hover pause`);
}

async function keyChecks(page, vp) {
  await page.load();
  let s = await page.state();
  const n = s.frames.length;
  let before = s;
  await page.key("ArrowRight", 39);
  s = await page.state();
  check(s.on === next(before.on, n), `${vp.name}px: ArrowRight did not go forward`);
  check(s.pan === "running", `${vp.name}px: ArrowRight left the slides paused (${s.pan})`);
  before = s;
  await page.key("ArrowLeft", 37);
  await page.key("ArrowLeft", 37);
  s = await page.state();
  check(s.on === prev(prev(before.on, n), n), `${vp.name}px: ArrowLeft twice did not go back twice`);

  // Arrows inside form fields stay with the field.
  for (const field of [
    '<input type="text" value="hello world">',
    "<textarea>hello world</textarea>",
    '<div contenteditable="true">hello world</div>',
    "<select><option>a</option><option>b</option></select>",
  ]) {
    await page.evaluate(`(() => {
      const box = document.createElement("div");
      box.id = "probe-field";
      box.innerHTML = ${JSON.stringify(field)};
      document.querySelector(".rsvp").append(box);
      const el = box.firstElementChild;
      el.focus();
      if (el.setSelectionRange) el.setSelectionRange(5, 5);
      return true;
    })()`);
    before = await page.state();
    const caretBefore = await page.evaluate("document.activeElement.selectionStart ?? null");
    await page.key("ArrowLeft", 37);
    await page.key("ArrowRight", 39);
    await page.key("ArrowRight", 39);
    s = await page.state();
    const caretAfter = await page.evaluate("document.activeElement.selectionStart ?? null");
    check(s.on === before.on, `${vp.name}px: arrows inside ${field} changed the slide`);
    if (caretBefore !== null) check(caretAfter === caretBefore + 1, `${vp.name}px: arrows inside ${field} did not move the caret (${caretBefore} to ${caretAfter})`);
    await page.evaluate('document.getElementById("probe-field").remove(), document.activeElement.blur(), true');
  }

  // Modified arrows are left to the browser.
  before = await page.state();
  await page.send("Input.dispatchKeyEvent", { type: "rawKeyDown", key: "ArrowRight", code: "ArrowRight", windowsVirtualKeyCode: 39, modifiers: 8 });
  await page.send("Input.dispatchKeyEvent", { type: "keyUp", key: "ArrowRight", code: "ArrowRight", windowsVirtualKeyCode: 39, modifiers: 8 });
  await page.frames();
  s = await page.state();
  check(s.on === before.on, `${vp.name}px: Shift+ArrowRight changed the slide`);

  // With a dot focused, arrows still switch and focus keeps the slides paused.
  await page.evaluate('document.querySelector("[data-slide-to]").focus(), true');
  before = await page.state();
  await page.key("ArrowRight", 39);
  s = await page.state();
  check(s.on === next(before.on, n), `${vp.name}px: ArrowRight with a dot focused did not go forward`);
  check(s.pan === "paused", `${vp.name}px: the pan runs while focus is inside the slides (${s.pan})`);
  await page.evaluate("document.activeElement.blur(), true");
  checkLayout(`${vp.name}px after keys`, s);
  check(page.errors.length === 0, `${vp.name}px console errors: ${page.errors.join(" | ")}`);
  notes.push(`${vp.name}px keys, Left and Right switch, form fields keep their arrows, modifiers ignored`);
}

async function touchChecks(page, vp) {
  await page.load();
  let s = await page.state();
  const n = s.frames.length;
  const frame = await page.rect(".still-frame");
  const a = { x: frame.left + frame.width * 0.8, y: frame.y };
  const b = { x: frame.left + frame.width * 0.2, y: frame.y };
  let before = s;
  await page.touchSwipe(a, b);
  s = await page.state();
  check(s.on === next(before.on, n), `${vp.name}px: touch swipe left did not go forward (${before.on} to ${s.on})`);
  check(s.pan === "running", `${vp.name}px: a touch swipe paused the slides (${s.pan})`);
  before = s;
  await page.touchSwipe(b, a);
  s = await page.state();
  check(s.on === prev(before.on, n), `${vp.name}px: touch swipe right did not go back`);
  before = s;
  await page.touchSwipe({ x: frame.x, y: frame.y + 40 }, { x: frame.x + 10, y: frame.y - 120 });
  s = await page.state();
  check(s.on === before.on, `${vp.name}px: a vertical touch drag changed the slide`);
  before = s;
  await page.touchSwipe(frame, frame, 1);
  s = await page.state();
  check(s.on === before.on, `${vp.name}px: a tap changed the slide`);
  check(s.pan === "running", `${vp.name}px: a tap paused the slides (${s.pan})`);
  checkLayout(`${vp.name}px after touch`, s);
  check(page.errors.length === 0, `${vp.name}px console errors: ${page.errors.join(" | ")}`);
  notes.push(`${vp.name}px touch, swipe left and right, vertical drag and tap ignored`);
}

async function reducedChecks(page, vp, markup) {
  await page.load();
  let s = await page.state();
  const n = s.frames.length;
  checkConsistent(`${vp.name}px reduced motion`, s, markup);
  let before = s;
  const frame = await page.rect(".still-frame");
  await page.drag({ x: frame.left + frame.width * 0.75, y: frame.y }, { x: frame.left + frame.width * 0.25, y: frame.y });
  await page.key("ArrowRight", 39);
  s = await page.state();
  check(s.on === (before.on + 2) % n, `${vp.name}px reduced motion: drag and key did not switch`);
  check(s.fadeMs === 0 && s.leaving === -1, `${vp.name}px reduced motion: the switch faded`);
  check(s.probe.transitions.length === 0, `${vp.name}px reduced motion: a picture transition ran`);
  check(s.pan === "none", `${vp.name}px reduced motion: the picture pans (${s.pan})`);
  check(page.errors.length === 0, `${vp.name}px console errors: ${page.errors.join(" | ")}`);
  notes.push(`${vp.name}px reduced motion, instant switch, no pan`);
}

async function autoplayChecks(page, vp) {
  await page.load();
  const frame = await page.rect(".still-frame");
  await page.mouse("mouseMoved", frame.x, frame.y, false);
  let before = await page.state();
  await sleep(7600);
  let s = await page.state();
  check(s.on === before.on, `${vp.name}px: autoplay advanced while the mouse was over the slides`);
  await page.mouse("mouseMoved", 2, 2, false);
  before = await page.state();
  await sleep(7600);
  s = await page.state();
  check(s.on === next(before.on, s.frames.length), `${vp.name}px: autoplay did not advance after the mouse left`);
  notes.push(`${vp.name}px autoplay, held while hovered, advances after 7 s`);
}

async function main() {
  const chromePath = findChrome();
  if (!chromePath) {
    console.log("Chrome is not installed, so scripts/check_slideshow.mjs was skipped.");
    return 0;
  }
  const markup = markupSlides();
  const server = await serve();
  const url = `http://127.0.0.1:${server.address().port}/`;
  const chrome = await launch(chromePath);
  const cdp = await Cdp.connect(chrome.wsUrl);
  try {
    for (const vp of VIEWPORTS) {
      const page = await openPage(cdp, vp, url);
      await shuffleChecks(page, vp, markup);
      await mouseChecks(page, vp, markup);
      await keyChecks(page, vp);
      await page.close();
      const phone = await openPage(cdp, vp, url, { touch: true });
      await touchChecks(phone, vp);
      await phone.close();
      const calm = await openPage(cdp, vp, url, { reduce: true });
      await reducedChecks(calm, vp, markup);
      await calm.close();
    }
    if (!process.env.HH_QUICK) {
      const page = await openPage(cdp, VIEWPORTS[0], url);
      await autoplayChecks(page, VIEWPORTS[0]);
      await page.close();
    }
  } finally {
    cdp.close();
    chrome.close();
    server.close();
  }
  if (problems.length) {
    console.error(`${problems.length} slideshow problem(s)`);
    for (const item of problems) console.error(`- ${item}`);
    return 1;
  }
  for (const item of notes) console.log(item);
  console.log("Slideshow browser check passed.");
  return 0;
}

main().then((code) => { process.exitCode = code; }, (err) => {
  console.error(err.stack || String(err));
  process.exitCode = 1;
});
