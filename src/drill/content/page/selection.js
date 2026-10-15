// ---------- selection toolbar ----------
let pendingSel = null, lastPointer = null;
const ed = $("code");
function sourceFor(node) {
  const el = node && (node.nodeType === 1 ? node : node.parentElement);
  const t = cur ? (cur.kind === "practice" ? cur.p.title : LESSONS[cur.id].title) : "";
  if (!el) return t || "Daily Drill";
  if (el.closest("#code")) return "My code · " + t;
  if (el.closest(".task")) return "Task · " + t;
  if (el.closest("#feed, #result")) return "Tutor feedback · " + t;
  if (el.closest("#paneBuild")) return "Python · " + t;
  if (el.closest("#paneText")) return (cur && cur.kind === "lesson" ? stepNames(cur.id) : STEPS)[cur ? cur.step : 0] + " · " + t;
  if (el.closest("#drawer")) return "Notebook";
  return t || "Daily Drill";
}
function hideSelbar() { $("selbar").hidden = true; pendingSel = null; }
function checkSelection() {
  const bar = $("selbar");
  let text = "", kind = "text", rect = null, node = null;
  if (document.activeElement === ed && ed.selectionEnd > ed.selectionStart) {
    text = ed.value.slice(ed.selectionStart, ed.selectionEnd); kind = "code"; node = ed;
    const r = ed.getBoundingClientRect();
    rect = lastPointer ? { left: lastPointer.x, bottom: lastPointer.y } : { left: r.left + 16, bottom: r.top + 24 };
  } else {
    const sel = window.getSelection();
    if (sel && sel.rangeCount && !sel.isCollapsed) {
      node = sel.anchorNode; const el = node && (node.nodeType === 1 ? node : node.parentElement);
      if (el && el.closest("main, #drawer") && !el.closest("#items, #selbar, input, textarea")) {
        text = sel.toString(); rect = sel.getRangeAt(0).getBoundingClientRect();
        if (el.closest("pre, code")) kind = "code";
      }
    }
  }
  text = text.trim();
  if (/^_+$/.test(text)) text = "";
  if (!text || text.length < 2 || !rect) { if (!bar.matches(":focus-within")) hideSelbar(); return; }
  pendingSel = { text, kind, source: sourceFor(node) };
  $("selExplain").hidden = !sample;
  $("selSave").textContent = "Save to study list";
  bar.hidden = false;
  const w = bar.offsetWidth, maxLeft = document.documentElement.clientWidth - w - 8;
  bar.style.left = Math.max(8, Math.min(maxLeft, rect.left + window.scrollX)) + "px";
  bar.style.top = (rect.bottom + window.scrollY + 8) + "px";
}
document.addEventListener("mouseup", e => { lastPointer = { x: e.clientX, y: e.clientY }; if (!e.target.closest("#selbar")) setTimeout(checkSelection, 0); });
document.addEventListener("keyup", e => { if (e.shiftKey || e.key === "Shift") { lastPointer = null; setTimeout(checkSelection, 0); } });
let selTimer = null;
document.addEventListener("selectionchange", () => {
  if (coarse.matches) { clearTimeout(selTimer); selTimer = setTimeout(checkSelection, 450); return; }
  if ($("selbar").hidden) return;
  const s = window.getSelection();
  if ((!s || s.isCollapsed) && !(document.activeElement === ed && ed.selectionEnd > ed.selectionStart)) setTimeout(() => { if (!$("selbar").matches(":focus-within")) hideSelbar(); }, 150);
});
$("selbar").addEventListener("mousedown", e => e.preventDefault());
$("selSave").onclick = async () => { if (!pendingSel) return; await addItem(pendingSel.text, pendingSel.source, pendingSel.kind); $("selSave").textContent = "Saved"; setTimeout(hideSelbar, 700); };
$("selExplain").onclick = async () => {
  if (!pendingSel) return;
  const it = await addItem(pendingSel.text, pendingSel.source, pendingSel.kind);
  hideSelbar(); openPocket(it.id); explainItem(it.id);
};
