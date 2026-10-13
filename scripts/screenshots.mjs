// Retake the screen gallery in docs/screens/ from a running drill-server, with the Google Chrome
// already on this Mac (headless, through its DevTools protocol). No packages to install.
//
//   DRILL_PORT=8791 DRILL_DATABASE_URL=sqlite:///.drill/screens.db uv run drill-server   # a fresh, throwaway database
//   node scripts/screenshots.mjs http://127.0.0.1:8791
//
// Each shot opens the page at one size and look, runs a few lines of the page's own functions to
// reach a screen (openLesson, setStep, ...), and saves a .webp. Motion is off so shots are stable.
// Add a shot here and a row in docs/screens/README.md together.

import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const BASE = process.argv[2] || "http://127.0.0.1:8791";
const OUT = new URL("../docs/screens/", import.meta.url).pathname;
const CHROME = process.env.CHROME || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const PORT = 9333;
const PHONE = { width: 375, height: 812, mobile: true };
const DESKTOP = { width: 1366, height: 860, mobile: false };

// name, size, look, then the page script that reaches the screen (it may be async).
const SHOTS = [
  ["home-phone-dusk", PHONE, "dusk", `goHome();`],
  ["home-desktop-dusk", DESKTOP, "dusk", `goHome();`],
  ["home-phone-light", PHONE, "light", `goHome();`],
  ["phase-room-phone-dusk", PHONE, "dusk", `goHome(); at(".phasebox");`],
  ["track-phone-dusk", PHONE, "dusk", `goHome(); at("#track-platform");`],
  ["track-desktop-light", DESKTOP, "light", `goHome(); at("#track-platform");`],
  ["lesson-learn-phone-dusk", PHONE, "dusk", `openLesson("use_case_score", 0);`],
  ["lesson-check-phone-dusk", PHONE, "dusk", `openLesson("can_read_table", 1); lp("can_read_table").checked = 1; setStep(1, true); at(".verdict");`],
  ["build-code-desktop-dusk", DESKTOP, "dusk", `openLesson("runs_after", 2);`],
  ["sorting-board-phone-dusk", PHONE, "dusk", `openLesson("use_case_score", 2);`],
  ["explain-gaps-phone-dusk", PHONE, "dusk", `lp("runs_after").filled = 0; openLesson("runs_after", 3);
     [...document.querySelectorAll(".clzchip")].find(b => b.textContent === "it uses").click();
     document.querySelector("[data-clz-help]").click(); at(".cloze");`],
  ["explain-done-phone-light", PHONE, "light", `lp("runs_after").filled = 2; openLesson("runs_after", 3); at(".cloze");`],
  ["done-screen-phone-dusk", PHONE, "dusk", `progress.solved.field_status = true; lp("field_status").filled = 3;
     openLesson("field_status", 3); goNext();`],
  ["walkthrough-phone-dusk", PHONE, "dusk", `openLesson("read_a_run", 0); at(".walk figure:nth-of-type(2)");`],
  ["study-tray-phone-dusk", PHONE, "dusk", `goHome(); openPocket();`],
  ["search-phone-dusk", PHONE, "dusk", `goHome(); openSearch();`],
];

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  mkdirSync(OUT, { recursive: true });
  const profile = mkdtempSync(join(tmpdir(), "drill-shots-"));
  const chrome = spawn(CHROME, ["--headless=new", `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`,
    "--hide-scrollbars", "--force-color-profile=srgb", "about:blank"], { stdio: "ignore" });
  try {
    let target;
    for (let i = 0; i < 50 && !target; i++) {
      try { target = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find(t => t.type === "page"); } catch { await sleep(200); }
    }
    if (!target) throw new Error("Chrome did not start: set CHROME to its path");
    const ws = new WebSocket(target.webSocketDebuggerUrl);
    await new Promise((ok, bad) => { ws.onopen = ok; ws.onerror = bad; });
    let id = 0; const waiting = new Map(), events = [];
    ws.onmessage = m => { const d = JSON.parse(m.data); if (d.id && waiting.has(d.id)) { waiting.get(d.id)(d); waiting.delete(d.id); } else events.push(d); };
    const send = (method, params = {}) => new Promise((ok, bad) => {
      const n = ++id; waiting.set(n, d => d.error ? bad(new Error(`${method}: ${d.error.message}`)) : ok(d.result));
      ws.send(JSON.stringify({ id: n, method, params }));
    });
    await send("Page.enable");
    for (const [name, size, look, script] of SHOTS) {
      await send("Emulation.setDeviceMetricsOverride", { ...size, deviceScaleFactor: 2 });
      await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "reduce" }] });
      // The look and Motion off are read from storage before the page draws.
      await send("Page.addScriptToEvaluateOnNewDocument", { source: `try { localStorage.setItem("drill-theme", "${look}"); localStorage.setItem("drill-motion", "off"); } catch {}` });
      events.length = 0;
      await send("Page.navigate", { url: BASE });
      for (let i = 0; i < 100 && !events.some(e => e.method === "Page.loadEventFired"); i++) await sleep(100);
      await sleep(900);  // boot: progress and data
      const page = `(async () => { const at = sel => { const el = document.querySelector(sel); if (el) { el.scrollIntoView({ block: "start" }); scrollBy(0, -70); } };
        ${script} })()`;
      const r = await send("Runtime.evaluate", { expression: page, awaitPromise: true });
      if (r.exceptionDetails) throw new Error(`${name}: ${r.exceptionDetails.exception?.description || r.exceptionDetails.text}`);
      await sleep(500);
      const { data } = await send("Page.captureScreenshot", { format: "webp", quality: 82 });
      writeFileSync(join(OUT, `${name}.webp`), Buffer.from(data, "base64"));
      console.log(`saved docs/screens/${name}.webp`);
    }
    ws.close();
  } finally {
    const gone = new Promise(r => chrome.once("exit", r));
    chrome.kill();
    await gone;  // Chrome writes to its profile until it exits
    try { rmSync(profile, { recursive: true, force: true }); } catch {}
  }
}

main().catch(e => { console.error(e.message); process.exit(1); });
