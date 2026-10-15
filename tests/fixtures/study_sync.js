// Runs page/study-list.js in node against a fake account database, and checks that study-list
// changes made while the page connects (and after) are never silently dropped.
// Used by tests/test_study.py: `node study_sync.js path/to/study-list.js`; exit code 1 on a failure.
const fs = require("fs");
const src = fs.readFileSync(process.argv[2], "utf8");

// Just enough of a browser for the study list's own functions.
const saved = {};
global.localStorage = { getItem: k => (k in saved ? saved[k] : null), setItem: (k, v) => { saved[k] = String(v); }, removeItem: k => { delete saved[k]; } };
global.toast = () => {};
global.cur = null;
global.document = { querySelectorAll: () => [] };
const anything = new Proxy(function () {}, { get: () => anything, apply: () => anything, set: () => true });
global.$ = () => anything;

const checks = `
renderStudy = () => {};
const wait = ms => new Promise(r => setTimeout(r, ms));
function fakeAccount(down) {  // a database that answers slowly, and not at all for ids in "down"
  const docs = {};
  let listener = null;
  const col = {
    doc: id => ({
      set: async d => { await wait(20); if (down.has(id)) throw new Error("down"); docs[id] = JSON.parse(JSON.stringify(d)); },
      update: async p => { await wait(5); if (down.has(id)) throw new Error("down"); docs[id] = Object.assign({}, docs[id] || {}, JSON.parse(JSON.stringify(p))); },
      delete: async () => { await wait(5); delete docs[id]; },
    }),
    orderBy: () => ({ onSnapshot: cb => { listener = cb; } }),
  };
  const read = list => listener({ docs: Object.entries(list).map(([id, d]) => ({ id, data: () => d })) });
  return { docs, db: { collection: () => col }, read };
}
(async () => {
  const results = [];
  const check = (name, ok) => results.push([name, !!ok]);
  studyItems = [
    { id: "a", text: "A", note: "", createdAt: 1, updatedAt: 1 },
    { id: "b", text: "B", note: "", createdAt: 2, updatedAt: 2 },
    { id: "x", text: "X", note: "", createdAt: 3, updatedAt: 3 },
  ];
  const account = fakeAccount(new Set(["b"]));
  const connecting = connectStudy(account.db);
  await wait(30);  // "a" has been sent by now
  await updateItem("a", { note: "typed while connecting" });
  await addItem("C, saved while connecting", "test", "text");
  await removeItem("x");
  await connecting;
  account.read(account.docs);
  check("an edit made while connecting reaches the account", account.docs.a && account.docs.a.note === "typed while connecting");
  check("an item saved while connecting reaches the account", Object.values(account.docs).some(d => d.text === "C, saved while connecting"));
  check("an item removed while connecting is removed from the account", !("x" in account.docs));
  check("an item that couldn't be sent stays on screen", studyItems.some(i => i.id === "b"));
  check("and stays on this device", JSON.parse(localStorage.getItem("drill-study") || "[]").some(i => i.id === "b"));

  await updateItem("b", { note: "edited while the account is down" });
  check("a later edit to it is kept on this device too", JSON.parse(localStorage.getItem("drill-study")).find(i => i.id === "b").note === "edited while the account is down");

  const stale = JSON.parse(JSON.stringify(account.docs));
  await updateItem("a", { note: "newer" });
  account.read(stale);  // a read that started before the edit arrives after it
  check("a read that is older than an edit doesn't undo the edit", studyItems.find(i => i.id === "a").note === "newer");

  for (const [name, ok] of results) console.log((ok ? "ok    " : "FAIL  ") + name);
  process.exit(results.every(([, ok]) => ok) ? 0 : 1);
})();
`;
eval(src + "\n" + checks);
