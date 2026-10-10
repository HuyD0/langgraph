// Runs every exercise's reference solution through Skulpt (the in-browser Python the page uses),
// with the page's own test harness. Usage (from web/daily-drill/tools):
//   npm install && node check_in_browser_python.js
const fs = require("fs"), path = require("path"), vm = require("vm");
const ctx = { console, setTimeout, clearTimeout, Promise }; ctx.window = ctx; ctx.self = ctx; ctx.globalThis = ctx;
vm.createContext(ctx);
const sk = path.join(__dirname, "node_modules/skulpt/dist");
vm.runInContext(fs.readFileSync(path.join(sk, "skulpt.min.js"), "utf8"), ctx);
vm.runInContext(fs.readFileSync(path.join(sk, "skulpt-stdlib.js"), "utf8"), ctx);
const html = fs.readFileSync(path.join(__dirname, "../dist/daily-drill.html"), "utf8");
const data = html.slice(html.indexOf("const D = ") + 10, html.indexOf(";\nconst BANK = D.bank"));
const pyFn = html.slice(html.indexOf("function py(v)"), html.indexOf("const short ="));
const harnessFn = html.slice(html.indexOf("function harness(p, code)"), html.indexOf("async function runPython"));
vm.runInContext(`var D = ${data};\n${pyFn}\n${harnessFn}`, ctx);
async function run(src) {
  let out = "";
  ctx.Sk.configure({ output: t => { out += t; }, read: f => { if (!ctx.Sk.builtinFiles || !ctx.Sk.builtinFiles.files[f]) throw new Error("not found " + f); return ctx.Sk.builtinFiles.files[f]; }, __future__: ctx.Sk.python3, execLimit: 4000 });
  try { await ctx.Sk.misceval.asyncToPromise(() => ctx.Sk.importMainWithBody("<stdin>", false, src, true)); } catch (e) { return { out, error: e.toString() }; }
  return { out };
}
(async () => {
  let bad = 0;
  for (const p of ctx.D.bank) {
    const r = await run(ctx.harness(p, p.solution));
    const ok = r.out.split("\n").filter(l => l.startsWith("@@") && l.includes("|ok|")).length;
    if (ok !== p.cases.length || r.error) { bad++; console.log("FAIL", p.id, ok + "/" + p.cases.length, r.error || ""); }
  }
  console.log(bad ? "FAILURES: " + bad : "ALL " + ctx.D.bank.length + " SOLUTIONS PASS IN SKULPT");
  process.exit(bad ? 1 : 0);
})();
