// ---------- backends: claude.ai's capabilities, or the local server (uv run drill-server) ----------
// Both return the same four things: `s` (ask the tutor model), `db` (documents), `user` (an id) and
// `board` (the leaderboard's rows), so the rest of the page never knows where it is running.
async function claudeBackend() {
  // Each one on its own: if one fails (not granted, or a hiccup), the others still work, so a
  // tutor problem can't also switch off saving, and the other way round.
  const got = await Promise.allSettled(["sample", "db", "user"].map(name => Promise.resolve().then(() => claude.use(name))));
  const [s, db, user] = got.map(r => r.status === "fulfilled" ? r.value : null);
  // The leaderboard: one row per person at board/<id>, everyone reads, each writes only their own
  // (the artifact's db rules). Rows hold no names: the names are looked up as the board is shown.
  const board = db && user ? {
    list: async () => {
      const me = await user.id(), snap = await db.collection("board").get();
      const rows = snap.docs.map(d => ({ id: d.id, row: d.data() }));
      let names = {};
      try { names = await user.profiles(rows.map(r => r.id)); } catch {}
      return { me, rows: rows.map(r => ({ ...r, name: (names[r.id] || {}).name || "" })) };
    },
    save: async row => db.doc("board/" + await user.id()).set(row),
    leave: async () => db.doc("board/" + await user.id()).delete(),
  } : null;
  return { s, db, user, board };
}
// One MLflow session per visit, so every request from this visit groups together; an Ask thread
// or a study item sends its own session instead.
const VISIT = "visit-" + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
async function localBackend() {
  if (!/^https?:$/.test(location.protocol)) return null;
  let health;
  try { const r = await fetch("/api/health", { cache: "no-store" }); if (!r.ok) return null; health = await r.json(); } catch { return null; }
  if (!health || !health.ok) return null;
  // A stopped app (after its idle stop) or the proxy in front of it answers with a web page, not
  // JSON: say so, instead of blaming the hint or the save.
  const ASLEEP = "The app has gone to sleep. Reload in a minute, or ask whoever runs it to start it.";
  const jsonOf = async res => { try { return await res.json(); } catch { throw Object.assign(new Error("asleep"), { code: "asleep", text: ASLEEP }); } };
  const fail = async (res) => {
    const body = await jsonOf(res);
    const d = (body && body.detail) || body || {};
    throw Object.assign(new Error(d.text || res.statusText), { code: d.code || (res.status === 429 ? "rate_limited" : "error"), text: d.text });
  };
  // A request that goes quiet for 2 minutes, or runs past 4, is given up on, so a dropped
  // connection or a stopped app can't leave the tutor's buttons stuck until a reload.
  // (The server tries two models for up to 45 s each before the first word.)
  const QUIET_MS = 120000, MAX_MS = 240000;
  async function ask(body, onText) {
    body = { ...body, trace: { session: VISIT, ...(body.trace || {}) } };
    const ctl = new AbortController();
    let quiet = setTimeout(() => ctl.abort(), QUIET_MS);
    const whole = setTimeout(() => ctl.abort(), MAX_MS);
    const awake = () => { clearTimeout(quiet); quiet = setTimeout(() => ctl.abort(), QUIET_MS); };
    try {
      const res = await fetch("/api/ask", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), signal: ctl.signal });
      if (!res.ok) await fail(res);
      if (body.json) return (await jsonOf(res)).value;
      const reader = res.body.getReader(), dec = new TextDecoder();
      let text = "";
      for (;;) {
        const { value, done } = await reader.read(); if (done) break;
        awake();
        text += dec.decode(value, { stream: true });
        if (onText) onText({ text, delta: text });
      }
      return { text, truncated: false };
    } catch (e) {
      if (ctl.signal.aborted) throw Object.assign(new Error("timeout"), { code: "timeout", text: "The tutor took too long to answer. Try again in a moment." });
      throw e;
    } finally { clearTimeout(quiet); clearTimeout(whole); }
  }
  const s = !health.ai ? null : Object.assign(
    (prompt, opts = {}) => ask({ prompt, tier: opts.modelTier || "default", trace: opts.trace }, opts.onText),
    { json: (prompt, opts = {}) => ask({ prompt, tier: opts.modelTier || "default", json: true, trace: opts.trace }), local: true });
  // Feedback on one answer (attached in MLflow to the trace the page tagged with `request`), and a
  // prepared answer the page showed: both work with no model running.
  const post = (path, body) => fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...body, trace: body.trace ? { session: VISIT, ...body.trace } : undefined }) });
  const call = async (method, path, body) => {
    const res = await fetch("/api/docs/" + path, { method, headers: { "Content-Type": "application/json" }, body: body === undefined ? undefined : JSON.stringify(body) });
    if (!res.ok) await fail(res);
    return jsonOf(res);
  };
  const doc = path => ({
    get: async () => { const r = await call("GET", path); return { exists: r.exists, data: () => r.data }; },
    set: d => call("PUT", path, d), update: p => call("PATCH", path, p), delete: () => call("DELETE", path),
  });
  const db = {
    doc,
    collection: name => ({
      doc: id => doc(name + "/" + id),
      orderBy: (field, dir) => ({
        onSnapshot: (cb, onErr) => {
          const load = async () => {
            try {
              const r = await (await fetch("/api/collections/" + name, { cache: "no-store" })).json();
              const docs = r.docs.slice().sort((a, b) => ((a.data[field] || 0) - (b.data[field] || 0)) * (dir === "desc" ? -1 : 1));
              cb({ docs: docs.map(d => ({ id: d.id, data: () => d.data })) });
            } catch (e) { if (onErr) onErr(e); }
          };
          load();
          // Another device may have added to the list meanwhile: refresh when you come back to the tab.
          document.addEventListener("visibilitychange", () => { if (!document.hidden) load(); });
          return () => {};
        },
      }),
    }),
  };
  const board = {  // drill-server keeps everyone's rows in its board table (see /api/board)
    list: async () => { const res = await fetch("/api/board", { cache: "no-store" }); if (!res.ok) await fail(res); return jsonOf(res); },
    save: async row => { const res = await fetch("/api/board", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(row) }); if (!res.ok) await fail(res); },
    leave: async () => { const res = await fetch("/api/board", { method: "DELETE" }); if (!res.ok) await fail(res); },
  };
  return { s, db, user: { id: async () => health.user }, board, local: true, team: !!health.team, app: !!health.app,
    feedback: body => post("/api/feedback", body), served: body => post("/api/served", body) };  // team: at work, a manager sees progress
}
