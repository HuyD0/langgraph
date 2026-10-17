// Retake the screen gallery in docs/screens/ from a running drill-server, with the Google Chrome
// already on this Mac (headless, through its DevTools protocol). No packages to install.
//
//   DRILL_PORT=8791 DRILL_DATABASE_URL=sqlite:///.drill/screens.db uv run drill-server   # a fresh, throwaway database
//   node scripts/screenshots.mjs http://127.0.0.1:8791
//
// Each shot opens the page at one size and look, runs a few lines of the page's own functions to
// reach a screen (openLesson, setStep, ...), and saves a .webp, after effects have finished.
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

// A few saved items, so the study list has something to show on a fresh database.
const STUDY = `for (const t of ["A gate is a question that can stop an idea outright.", "terraform plan shows what would change, before anything does.", "The runbook reads the team's YAML."]) await addItem(t, "screens");`;
// Two finished lessons with their first-time marks, so the Notebook's Results tab has rows to show.
const RESULTS = `lp("use_case_score").first = { check: ["sign"], build: ["sign", "sign"], explain: ["sign", "sign"], day: 1, date: dayKey(new Date(Date.now() - 86400000)), streak: 1, gate: false };
  lp("split_requirements").first = { check: ["sign", "knot"], build: ["sign", "knot", "sign"], explain: ["sign", "curtain"], day: 2, date: today(), streak: 2, gate: false };`;

// name, size, look, then the page script that reaches the screen (it may be async).
const SHOTS = [
  ["home-phone-dusk", PHONE, "dusk", `goHome();`],
  ["home-desktop-dusk", DESKTOP, "dusk", `goHome();`],
  ["home-phone-light", PHONE, "light", `goHome();`],
  ["phase-room-phone-dusk", PHONE, "dusk", `goHome(); at(".phasebox");`],
  ["track-phone-dusk", PHONE, "dusk", `goHome(); at("#track-platform");`],
  ["track-desktop-light", DESKTOP, "light", `goHome(); at("#track-platform");`],
  ["lesson-learn-phone-dusk", PHONE, "dusk", `openLesson("use_case_score", 0);`],
  ["trust-mark-phone-dusk", PHONE, "dusk", `openLesson("redact_pii", 0); document.querySelector(".trustmark").click(); at(".trustpop");`],
  ["diagram-phone-light", PHONE, "light", `openLesson("slowest_chain", 0); at(".dgfig"); document.querySelectorAll(".grow, .pop, .late").forEach(e => e.getAnimations().forEach(a => a.finish()));`],
  ["callback-phone-dusk", PHONE, "dusk", `lp("well_architected").done = true; openLesson("backoff_delays", 0); document.querySelector(".cbmark").click(); at(".cbmark");`],
  ["look-again-phone-light", PHONE, "light", `lp("well_architected").done = true; openLesson("backoff_delays", 0); [...document.querySelectorAll("[data-again]")].find(b => !/Reliability/.test(b.textContent)).click(); at("#againCard");`],
  ["lesson-check-phone-dusk", PHONE, "dusk", `delete lp("split_requirements").checks; lp("split_requirements").checked = null; openLesson("split_requirements", 1);
     checkPick(LESSONS.split_requirements.check[2]); checkNext(); checkPick(2); checkHelp(); at(".chkhead");`],
  ["build-code-desktop-dusk", DESKTOP, "dusk", `openLesson("chunk_text", 2);`],
  ["explain-gaps-phone-dusk", PHONE, "dusk", `lp("runs_after").filled = 0; openLesson("runs_after", 3);
     [...document.querySelectorAll(".clzchip")].find(b => b.textContent === "it uses").click();
     document.querySelector("[data-clz-help]").click(); at(".cloze");`],
  ["explain-done-phone-light", PHONE, "light", `lp("runs_after").filled = 2; openLesson("runs_after", 3); at(".cloze");`],
  ["done-screen-phone-dusk", PHONE, "dusk", `progress.solved.field_status = true; lp("field_status").filled = 3;
     lp("field_status").first = { check: ["sign"], build: ["sign", "knot", "sign"], explain: ["sign", "sign", "curtain"] };
     openLesson("field_status", 3); goNext();`],
  ["walkthrough-phone-dusk", PHONE, "dusk", `openLesson("read_a_run", 0); at(".walk figure:nth-of-type(2)");`],
  ["practice-phone-dusk", PHONE, "dusk", `openLesson("folder_access", 2); at(".shead");`],
  ["study-row-phone-dusk", PHONE, "dusk", `${STUDY} goHome(); at(".next");`],
  ["study-list-phone-dusk", PHONE, "dusk", `${STUDY} goHome(); openPocket();`],
  ["search-landing-phone-dusk", PHONE, "dusk", `goHome(); openSearch();`],
  ["search-phone-dusk", PHONE, "dusk", `goHome(); openSearch(); $("searchIn").value = "leakage"; renderSearch();`],
  ["notebook-results-phone-dusk", PHONE, "dusk", `${RESULTS} openNotebook("results");`],
  ["notebook-settings-phone-light", PHONE, "light", `openNotebook("settings");`],
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
      // The look is read from storage before the page draws. Motion always plays, so shots wait it out.
      await send("Page.addScriptToEvaluateOnNewDocument", { source: `try { localStorage.setItem("drill-theme", "${look}"); } catch {}` });
      events.length = 0;
      await send("Page.navigate", { url: BASE });
      for (let i = 0; i < 100 && !events.some(e => e.method === "Page.loadEventFired"); i++) await sleep(100);
      await sleep(900);  // boot: progress and data
      const page = `(async () => { const at = sel => { const el = document.querySelector(sel); if (el) { el.scrollIntoView({ block: "start" }); scrollBy(0, -70); } };
        ${script} })()`;
      const r = await send("Runtime.evaluate", { expression: page, awaitPromise: true });
      if (r.exceptionDetails) throw new Error(`${name}: ${r.exceptionDetails.exception?.description || r.exceptionDetails.text}`);
      await sleep(1800);  // the longest effect (finishing a lesson) is 1.6 s
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
