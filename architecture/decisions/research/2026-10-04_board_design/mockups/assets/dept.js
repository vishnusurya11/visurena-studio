/* Department · Book · Books shelf mockups. Renders window.BOARD (assets/dept_data.js,
   captured read-only from the ledger + library + :8700 on 2026-10-04). Nothing here writes. */
(function () {
  "use strict";
  const B = window.BOARD;
  const API = "http://127.0.0.1:8700";
  const NOW = Date.parse(B.captured);
  const WOTW = "20260827135508", SIS = "20260822113400";
  const STEP = B.steps;
  const GATE_SHORT = { PLAN: "plan", LAYOUT: "layout", EYE_PANELS: "panels", EYE_TAKES: "takes", MASTER: "master", RENDER: "render" };
  const GROUPS = [
    ["running", "Running", "loader"], ["needs", "Needs you", "flag"], ["progress", "In progress", "circle"],
    ["queued", "Queued", "circle"], ["done", "Done", "check"], ["blocked", "Blocked", "circle-dashed"]];
  const COLLAPSED = { done: true, blocked: true };
  const PUB = { [WOTW]: new Set(B.wotw.published), [SIS]: new Set(B.sis.published) };

  /* ---------- small helpers */
  const $ = (s, el = document) => el.querySelector(s);
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const icon = (id, cls = "") => `<svg class="i ${cls}" aria-hidden="true"><use href="assets/icons.svg#${id}"/></svg>`;
  const thumb = (codex, rel, w = 160) => `${API}/thumb/${codex}/${w}/${rel}`;
  const pad = (n) => String(n).padStart(2, "0");
  function ago(ts) {
    const m = Math.max(0, (NOW - Date.parse(ts)) / 60000);
    return m < 60 ? `${Math.round(m)}m` : m < 1440 ? `${Math.round(m / 60)}h` : `${Math.round(m / 1440)}d`;
  }
  function gpuh(s) {
    if (!s) return "–";
    return s < 3600 ? `${Math.round(s / 60)}m` : `${(s / 3600).toFixed(1)}h`;
  }
  function store(key, val) {
    try { if (val === undefined) return JSON.parse(localStorage.getItem(key)); localStorage.setItem(key, JSON.stringify(val)); }
    catch (e) { return null; }
  }
  function toast(msg) { if (window.board && window.board.toast) window.board.toast(msg); }

  /* ---------- the state vocabulary */
  function shown(r) { return r.shown || r.state; }
  function groupOf(r) {
    const s = shown(r);
    if (s === "running") return "running";
    if (["flagged", "failed", "deferred", "escalated", "stale"].includes(s)) return "needs";
    if (s === "queued") return (r.steps && Object.keys(r.steps).length) ? "progress" : "queued";
    return s === "blocked" ? "blocked" : "done";
  }
  const PILL = { running: ["loader", "running"], flagged: ["flag", "flagged"], failed: ["x", "failed"],
    deferred: ["undo-2", "deferred"], escalated: ["hand", "escalated"], queued: ["circle", "queued"],
    blocked: ["circle-dashed", "blocked"], done: ["check", "done"], held: ["pause", "held"] };
  function pill(r) {
    const s = shown(r), [ic, word] = PILL[s] || ["circle", s];
    return `<span class="pill ${s}">${icon(ic)}${word}</span>`;
  }
  function stepState(r, i) {
    const id = pad(i + 1), st = r.steps && r.steps[id];
    if (!st) return r.state === "done" ? "inferred" : "";
    const [state, attempt, terminal] = st;
    if (["keep_best", "still", "flag"].includes(terminal)) return "flagged";
    return state === "running" ? "running" : state;
  }
  function stepTitle(r, i) {
    const id = pad(i + 1), st = r.steps && r.steps[id], s = stepState(r, i);
    if (!st) return `${id} ${STEP[i]} · ${s === "inferred" ? "done, inferred (pre-ledger)" : "not started"}`;
    return `${id} ${STEP[i]} · ${st[0]}${st[2] ? " · " + st[2] : ""} · ${st[1]} attempt${st[1] === 1 ? "" : "s"}`;
  }
  function sbar(r, quiet) {
    const cur = r.state === "running" ? Number(r.step_id) - 1 : -1;
    const segs = STEP.map((_, i) => `<i class="${stepState(r, i)}${i === cur ? " cur" : ""}" title="${esc(stepTitle(r, i))}"></i>`);
    return `<span class="sbar${quiet ? " quiet" : ""}" role="img" aria-label="${esc(steplabel(r))}">${segs.join("")}</span>`;
  }
  function steplabel(r) {
    const n = STEP.filter((_, i) => ["done", "skipped", "flagged", "inferred"].includes(stepState(r, i))).length;
    return `${n} of 12 steps done`;
  }
  function nonPass(r) {
    return Object.entries(r.gates || {}).filter(([, g]) => g[3] && g[3] !== "✓" && g[3] !== "○");
  }
  function gatesCell(r) {
    const bad = nonPass(r);
    if (!bad.length) return Object.keys(r.gates || {}).length ? `<span class="chip2 ok gate">${icon("check")}gates pass</span>` : "";
    return bad.map(([g, v]) => `<span class="chip2 flag gate" title="${esc(`${g} flagged ${v[0]}${v[2] ? " · kept: " + v[2] : ""} · ${v[4]}`)}"><span>${GATE_SHORT[g]}</span>${icon("flag")}<b>${v[0]}</b></span>`)
      .join("");
  }
  function face(r, size = 160) {
    if (!r.face) return `<span class="face"></span>`;
    return `<span class="face"><img decoding="async" class="${r.face_src === "take frame" ? "strip3" : ""}" src="${thumb(r.codex_id, r.face, size)}" alt="" title="face today: ${esc(r.face_src)} · pipeline poster.jpg (proposed)"></span>`;
  }
  function nowLine(r) {
    const s = shown(r), pub = PUB[r.codex_id] && PUB[r.codex_id].has(r.unit);
    if (s === "running") return `<span class="now live" title="p50 finish">${r.step_id} ${r.step_name} · done ~${r.eta}</span>`;
    if (s === "flagged") return `<span class="now">${pub ? "published ▲ · not acked" : "12 deliver · not acked"}</span>`;
    if (s === "queued") return `<span class="now">${pub ? "re-run · published ▲" : "waiting for the GPU"}</span>`;
    if (s === "blocked") return "";
    return `<span class="now">${pub ? "published ▲" : ""}</span>`;
  }
  const UNIT_HREF = (r) => r.codex_id === WOTW && r.unit === "ep17" ? "unit-running.html" : r.codex_id === WOTW && r.unit === "ep12" ? "unit-finished.html" : "#";

  /* ================================================================ department */
  function row(r) {
    const g = groupOf(r), quiet = g === "done";
    const [ic] = PILL[shown(r)] || ["circle"];
    return `<div class="urow" role="row" tabindex="0" data-row data-g="${g}" data-unit="${r.unit}">
      ${face(r)}
      ${pill(r)}
      <span class="who"><span class="gl ${shown(r)}">${icon(ic)}</span><a class="uid" href="${UNIT_HREF(r)}">${r.unit}</a><span class="ttl" title="${esc(r.title)}">${esc(r.title || "")}</span></span>
      <span class="stp">${sbar(r, quiet)}${nowLine(r)}</span>
      <span class="gc gates">${gatesCell(r)}</span>
      <span class="num moved dim" title="${esc(r.updated_at)}">${ago(r.updated_at)}</span>
      <span class="num gpu" title="cost $${(r.cost_usd || 0).toFixed(2)}">${gpuh(r.gpu_seconds)}</span>
      <span class="acts">
        <a class="ib hov" href="${UNIT_HREF(r)}" title="Open (↵)" aria-label="Open ${r.unit}">${icon("chevron-right")}</a>
        ${g === "needs" ? `<button class="ib hov" data-act="acknowledge" title="Acknowledge flags (a)" aria-label="Acknowledge">${icon("check")}</button>` : ""}
        ${g === "running" || g === "needs" ? `<button class="ib hov" data-act="redo" title="Redo last step (r)" aria-label="Redo">${icon("rotate-ccw")}</button>` : ""}
        ${g === "queued" || g === "progress" ? `<button class="ib hov" data-act="bump" title="Bump to the front (b)" aria-label="Bump">${icon("arrow-up")}</button>` : ""}
        <button class="ib more" data-act="menu" title="More (⋯)" aria-haspopup="menu" aria-label="More actions">${icon("ellipsis")}</button>
      </span>
    </div>`;
  }
  function sharedReason(rows) {
    const c = {};
    rows.forEach((r) => { if (r.blocked_on) c[r.blocked_on] = (c[r.blocked_on] || 0) + 1; });
    const top = Object.entries(c).sort((a, b) => b[1] - a[1])[0];
    if (!top) return "";
    const rest = rows.length - top[1];
    return `${top[1] === rows.length ? "all" : top[1]} waiting on <a href="#" title="refs unit, step 04">${top[0]}</a>${rest ? ` +${rest} other` : ""}`;
  }
  const WHY = { needs: () => "shipped with flags · not acknowledged", running: () => "", done: () => "", queued: () => "next on the GPU after ep17" };
  function group(book, key, label, ic, rows) {
    const open = store(`dept.open.${book}.${key}`) ?? !COLLAPSED[key];
    const why = key === "blocked" ? sharedReason(rows) : (WHY[key] || (() => ""))();
    return `<section class="grp" data-g="${key}" data-open="${open}">
      <button class="ghead ${key}" aria-expanded="${open}" data-book="${book}" data-key="${key}">
        ${icon("chevron-down", "chev")}<span class="gl">${icon(ic)}</span><span class="gt">${label}</span><span class="count">${rows.length}</span>
        ${why ? `<span class="why">${why}</span>` : ""}
      </button>
      <div class="rows" role="rowgroup">${rows.map(row).join("")}</div>
    </section>`;
  }
  function mix(rows) {
    return `<span class="mix" title="unit states">${GROUPS.map(([k]) => {
      const n = rows.filter((r) => groupOf(r) === k).length;
      return n ? `<i class="${k}" style="flex:${n}" title="${k} ${n}"></i>` : "";
    }).join("")}</span>`;
  }
  function bookBlock(codex, name, rows) {
    const shelf = B.shelf.find((b) => b.id === codex);
    const nDone = rows.filter((r) => r.state === "done").length, nNeed = rows.filter((r) => groupOf(r) === "needs").length;
    const groups = GROUPS.map(([k, l, ic]) => {
      const rs = rows.filter((r) => groupOf(r) === k).sort((a, b) => a.unit.localeCompare(b.unit));
      return rs.length ? group(codex, k, l, ic, rs) : "";
    }).join("");
    return `<section class="bookblk panel" data-book="${codex}">
      <header class="bookhead">
        <div class="bh-t"><h2><a href="${codex === WOTW ? "book.html" : "#"}">${esc(name)}</a></h2>
        <span class="meta"><b>${rows.length}</b> units · <b>${nDone}</b> done${nNeed ? ` · <b class="need">${nNeed}</b> need you` : ""} · <b>${PUB[codex].size}</b> published · <b>${shelf ? shelf.gpu_h : "–"}</b> GPU h</span></div>
        ${mix(rows)}
      </header>
      <div class="dg" role="table" aria-label="${esc(name)} units">
      <div class="colhead" aria-hidden="true"><span></span><span>State</span><span>Unit</span><span>Steps</span><span class="c-g">Gates (non-pass)</span><span class="r c-m">Moved</span><span class="r">GPU</span><span></span></div>
      ${groups}
      </div>
    </section>`;
  }
  function filterPills(rows) {
    const n = (k) => rows.filter((r) => groupOf(r) === k).length;
    const ps = [["all", "All", "layers", rows.length], ["running", "Running", "loader", n("running")],
      ["needs", "Needs you", "flag", n("needs")], ["queued", "Queued", "circle", n("queued") + n("progress")],
      ["blocked", "Blocked", "circle-dashed", n("blocked")], ["done", "Done", "check", n("done")]];
    return ps.filter((p) => p[3] || p[0] === "all").map(([k, l, ic, c]) =>
      `<button class="fpill ${k}" data-f="${k}" aria-pressed="${k === "all"}">${k === "all" ? "" : `<i class="dot ${k}"></i>`}${l}<span class="n">${c}</span></button>`).join("");
  }
  function applyFilter(f) {
    document.querySelectorAll(".fpill").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.f === f)));
    document.querySelectorAll(".grp").forEach((g) => {
      const k = g.dataset.g, match = f === "all" || k === f || (f === "queued" && k === "progress");
      g.hidden = !match;
      if (match && f !== "all") setOpen(g, true, false);
    });
    document.querySelectorAll(".bookblk").forEach((b) => { b.hidden = ![...b.querySelectorAll(".grp")].some((g) => !g.hidden); });
    try { history.replaceState(null, "", f === "all" ? location.pathname : `?state=${f}`); } catch (e) { /* file:// */ }
  }
  function setOpen(g, open, remember = true) {
    g.dataset.open = String(open);
    const h = $(".ghead", g); h.setAttribute("aria-expanded", String(open));
    if (remember) store(`dept.open.${h.dataset.book}.${h.dataset.key}`, open);
  }

  /* fault matrix: gate x unit */
  function binOf(n) { return n === 0 ? "f0" : n <= 5 ? "f1" : n <= 20 ? "f2" : "f3"; }
  function faultMatrix(rows) {
    const units = rows.filter((r) => Object.keys(r.gates || {}).length).sort((a, b) => a.unit.localeCompare(b.unit));
    const taste = ["EYE_PANELS", "EYE_TAKES", "MASTER"];
    let signed = 0, clean = 0;
    units.forEach((r) => taste.forEach((g) => { const v = r.gates[g]; if (v) { signed++; if (v[3] === "✓") clean++; } }));
    const head = B.gates.map((g) => `<th title="${g}">${GATE_SHORT[g]}</th>`).join("");
    const body = units.map((r) => `<tr><td class="u">${face(r)}<b>${r.unit}</b><span class="ft">${esc(r.title)}</span></td>${B.gates.map((g) => {
      const v = r.gates[g];
      if (!v) return `<td><span class="fc f0" title="${g}: not signed">·</span></td>`;
      if (v[3] === "✓") return `<td><span class="fc ok" title="${g} pass · ${esc(v[4])}">${icon("check")}pass</span></td>`;
      const kept = v[2] ? `<span class="k">${v[2] === "keep_best" ? "kept" : v[2]}</span>` : "";
      return `<td><span class="fc ${binOf(v[0])}" title="${esc(`${g} ${v[0]} faults · ${v[2] || v[1]} · ${v[4]}`)}">${icon("flag")}${v[0]}${kept}</span></td>`;
    }).join("")}<td class="num">${r.flags}</td></tr>`).join("");
    return `<div class="panel-h"><h2>Gate × unit faults</h2><span class="sub">signed verdicts, every episode with a gate</span></div>
      <div class="panel-b"><div class="stat"><b>${clean} of ${signed}</b><span class="soft">taste gates clean (panels · takes · master) across ${units.length - units.filter((r) => r.state === "running").length} finished episodes — a terminal is not a pass.</span></div>
      <div class="fm-wrap"><table class="fm"><thead><tr><th>Unit</th>${head}<th class="r">Flags</th></tr></thead><tbody>${body}</tbody></table></div>
      <p class="note">Cell = signed fault count from <code>work_orders.verdicts.*.faults</code>; tint bins 0 · 1–5 · 6–20 · 21+, the number is always printed. “kept” = the ladder ended on keep_best / still, not a pass.</p></div>`;
  }

  function department() {
    const rows = B.dept.rows;
    $("#pills").innerHTML = filterPills(rows);
    const books = [WOTW, SIS];
    $("#list").innerHTML = books.map((c) => bookBlock(c, B.dept.books[c], rows.filter((r) => r.codex_id === c))).join("");
    $("#faults").innerHTML = faultMatrix(rows);
    $("#sub").innerHTML = `<b>${rows.length}</b> units · <b>2</b> books · 12 steps · 6 gates · <b style="color:var(--st-flagged)">${rows.filter((r) => groupOf(r) === "needs").length}</b> need you`;
    document.addEventListener("click", onDeptClick);
    document.addEventListener("keydown", onDeptKey);
    const f = new URLSearchParams(location.search).get("state");
    if (f) applyFilter(f);
  }
  function onDeptClick(e) {
    const fp = e.target.closest(".fpill"); if (fp) return applyFilter(fp.dataset.f);
    const gh = e.target.closest(".ghead"); if (gh && !e.target.closest("a")) { const g = gh.closest(".grp"); return setOpen(g, g.dataset.open !== "true"); }
    const view = e.target.closest("[data-view]"); if (view) return setView(view.dataset.view);
    const act = e.target.closest("[data-act]");
    if (act) { e.preventDefault(); return act.dataset.act === "menu" ? openMenu(act) : confirmAct(act.dataset.act, act.closest(".urow")); }
    if (!e.target.closest(".rmenu")) closeMenus();
  }
  function setView(v) {
    document.querySelectorAll("[data-view]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.view === v)));
    $("#list").hidden = v !== "list"; $("#pills").hidden = v !== "list"; $("#faults").hidden = v !== "faults";
  }
  function openMenu(btn) {
    closeMenus();
    const rowEl = btn.closest(".urow");
    const m = document.createElement("div"); m.className = "rmenu"; m.setAttribute("role", "menu");
    m.innerHTML = [["chevron-right", "Open", "↵"], ["check", "Acknowledge flags", "a"], ["rotate-ccw", "Redo a step…", "r"],
      ["pause", "Hold…", "h"], ["arrow-up", "Bump", "b"], ["history", "Retry", "t"], null, ["external-link", "Open folder", ""]]
      .map((x) => x ? `<button role="menuitem" data-act="${x[1].split(" ")[0].toLowerCase()}">${icon(x[0])}${x[1]}<kbd>${x[2]}</kbd></button>` : "<hr>").join("");
    rowEl.append(m); $("button", m).focus();
  }
  function closeMenus() { document.querySelectorAll(".rmenu").forEach((m) => m.remove()); }
  function confirmAct(act, rowEl) {
    closeMenus();
    toast(`Mockup: the confirm dialog would open, then order “${act} ${rowEl ? rowEl.dataset.unit : ""}” is placed · pending.`);
  }
  function onDeptKey(e) {
    if (e.key === "Escape") return closeMenus();
    const rowsEl = [...document.querySelectorAll(".urow")].filter((r) => r.offsetParent);
    const i = rowsEl.indexOf(document.activeElement);
    if (e.key === "Enter" && i >= 0) { const a = $(".uid", rowsEl[i]); if (a.getAttribute("href") !== "#") location.href = a.href; }
  }

  /* ================================================================ book */
  const CH2 = ["Under Foot", "What We Saw from the Ruined House", "The Days of Imprisonment", "The Death of the Curate",
    "The Stillness", "The Work of Fifteen Days", "The Man on Putney Hill", "Dead London", "Wreckage", "The Epilogue"];
  function gdots(r) {
    const dots = B.gates.map((g) => {
      const v = r.gates && r.gates[g];
      const cls = !v ? "" : v[3] === "✓" ? "pass" : "flag";
      return `<i class="${cls}" title="${g}${v ? (v[3] === "✓" ? " pass" : ` flagged ${v[0]}`) : " not signed"}"></i>`;
    }).join("");
    const bad = nonPass(r).reduce((s, [, v]) => s + v[0], 0);
    const t = Object.keys(r.gates || {}).length ? (bad ? `<span class="t">!${bad}</span>` : `<span class="t ok">✓</span>`) : "";
    return `<span class="gdots" aria-label="gates">${dots}${t}</span>`;
  }
  function poster(r) {
    const pub = PUB[WOTW].has(r.unit), s = shown(r);
    const src = r.face ? thumb(WOTW, r.face, 320) : "";
    const kind = r.contact ? "contact" : r.frames && r.frames.length > 1 ? "frames" : "";
    const label = { "storyboard panel": "PANEL", "take frame": "TAKE", "storyboard grid": "GRID" }[r.face_src] || "";
    return `<a class="poster" href="${UNIT_HREF(r)}" data-unit="${r.unit}" data-scrub="${kind}" aria-label="${r.unit} ${esc(r.title)}">
      <span class="frame ${s === "flagged" ? "flagged" : ""}">
        ${src ? `<img loading="lazy" src="${src}" alt="">` : r.contact ? `<span class="sprite still" style="background-image:url(${API}/lib/${WOTW}/${r.contact});background-position:25% 20%"></span>` : `<span class="frame waiting" style="position:absolute;inset:0">no picture today<br>poster.jpg (proposed)</span>`}
        <span class="sprite"></span><span class="scrubbar"></span>
        <span class="tl">${r.unit}</span>
        ${pub ? `<span class="tr pub" title="published">▲</span>` : s === "running" ? `<span class="tr" style="background:var(--st-running-bar);color:#fff">● ${r.step_id} ${r.step_name}</span>` : ""}
        ${label || r.contact ? `<span class="bl" title="face today; pipeline poster.jpg proposed">${label || "CONTACT"} · today</span>` : ""}
        ${r.iters ? `<span class="br">iter${r.iters}</span>` : ""}
      </span>
      <span class="cap"><span class="t">${esc(r.title)}</span></span>
      <span class="cap">${gdots(r)}<span class="pill ${s}" style="padding:2px 7px;font-size:10px">${(PILL[s] || [])[1] || s}</span></span>
    </a>`;
  }
  function futurePoster(n) {
    return `<a class="poster future" href="#" aria-label="ep${pad(n)} not planned"><span class="frame">ep${pad(n)}<br>not planned</span>
      <span class="cap"><span class="t">${CH2[n - 18]}</span></span><span class="meta">Book II · ch ${n - 17}</span></a>`;
  }
  function wall(rows) {
    const byU = Object.fromEntries(rows.map((r) => [r.unit, r]));
    const one = Array.from({ length: 17 }, (_, i) => byU[`ep${pad(i + 1)}`]).filter(Boolean).map(poster).join("");
    const two = Array.from({ length: 10 }, (_, i) => futurePoster(18 + i)).join("");
    return `<div class="part"><h3>Book I · The Coming of the Martians</h3><span class="note">17 chapters · 17 units</span></div>${one}
      <div class="part"><h3>Book II · The Earth under the Martians</h3><span class="note">10 chapters · none planned yet</span></div><div class="fwall">${two}</div>`;
  }
  function bindScrub(root) {
    root.querySelectorAll(".poster[data-scrub]").forEach((p) => {
      const r = B.dept.rows.find((x) => x.codex_id === WOTW && x.unit === p.dataset.unit);
      if (!r || !p.dataset.scrub) return;
      const fr = $(".frame", p), sp = $(".sprite", p), bar = $(".scrubbar", p), img = $("img", fr);
      fr.addEventListener("pointerenter", () => {
        p.classList.add("scrub");
        if (p.dataset.scrub === "contact" && !sp.style.backgroundImage) sp.style.backgroundImage = `url(${API}/lib/${WOTW}/${r.contact})`;
      });
      fr.addEventListener("pointerleave", () => { p.classList.remove("scrub"); if (img && r.face) img.src = thumb(WOTW, r.face, 320); });
      fr.addEventListener("pointermove", (e) => {
        const x = Math.min(0.999, Math.max(0, (e.clientX - fr.getBoundingClientRect().left) / fr.clientWidth));
        bar.style.width = `${x * 100}%`;
        if (p.dataset.scrub === "contact") {
          const k = Math.floor(x * 30), c = k % 5, rr = Math.floor(k / 5);
          sp.style.backgroundPosition = `${c * 25}% ${rr * 20}%`;
        } else if (img) {
          img.src = thumb(WOTW, r.frames[Math.floor(x * r.frames.length)], 320);
        }
      });
    });
  }
  const MCLS = { done: "done", skipped: "skipped", flagged: "flagged", running: "running", failed: "failed", inferred: "inferred", "": "queued" };
  const MICON = { done: "check", skipped: "check", flagged: "flag", running: "loader", failed: "x", inferred: "check", "": "" };
  function mrow(r) {
    const pub = PUB[WOTW].has(r.unit), s = shown(r);
    const cells = STEP.map((_, i) => { const st = stepState(r, i); return `<a class="c ${MCLS[st]}" href="${UNIT_HREF(r)}" title="${esc(r.unit + " · " + stepTitle(r, i))}">${MICON[st] ? icon(MICON[st]) : ""}</a>`; }).join("");
    const n = STEP.filter((_, i) => ["done", "skipped", "flagged", "inferred"].includes(stepState(r, i))).length;
    const bad = nonPass(r).reduce((a, [, v]) => a + v[0], 0);
    return `<div class="row"><a class="lab" href="${UNIT_HREF(r)}"><b>${r.unit}</b><span>${esc(r.title)}</span></a><span class="cells">${cells}</span>
      <span class="end"><span>${n}/12</span>${r.iters ? `<span class="x">iter${r.iters}</span>` : ""}${bad ? `<span class="warn">!${bad}</span>` : ""}${pub ? `<span class="pub" title="published">▲</span>` : ""}${s === "running" ? `<span style="color:var(--st-running)">~${r.eta}</span>` : ""}${s === "queued" ? `<span class="x">queued (re-run)</span>` : ""}</span></div>`;
  }
  function frow(n) {
    return `<div class="row"><span class="lab future"><b>ep${pad(n)}</b><span>${CH2[n - 18]}</span></span><span class="cells">${STEP.map(() => `<span class="c future"></span>`).join("")}</span><span class="end"><span class="x">not planned</span></span></div>`;
  }
  function matrix(rows) {
    const byU = Object.fromEntries(rows.map((r) => [r.unit, r]));
    const fam = `<span class="fam"><span style="grid-column:1/4">prep</span><span style="grid-column:4/6" title="sound">snd</span><span style="grid-column:6/10">picture</span><span style="grid-column:10/13">finish</span></span>`;
    const names = `<span class="cells">${STEP.map((s, i) => `<span class="sn" title="${pad(i + 1)} ${s}">${pad(i + 1)} ${s}</span>`).join("")}</span>`;
    const body = Array.from({ length: 17 }, (_, i) => byU[`ep${pad(i + 1)}`]).filter(Boolean).map(mrow).join("")
      + Array.from({ length: 10 }, (_, i) => frow(18 + i)).join("");
    return `<div class="smx"><span></span>${fam}<span></span><span class="h">unit</span>${names}<span class="h">steps · iter · flags · ▲</span>${body}</div>`;
  }
  function cast() {
    return B.wotw.cast.map((c) => `<figure><span class="frame"><img loading="lazy" src="${thumb(WOTW, c.sheet, 320)}" alt="${esc(c.name)} character sheet"></span><figcaption>${esc(c.name.replace(/_/g, " "))}</figcaption></figure>`).join("");
  }
  function book() {
    const rows = B.dept.rows.filter((r) => r.codex_id === WOTW);
    const shelf = B.shelf.find((b) => b.id === WOTW);
    const cost = rows.reduce((s, r) => s + (r.cost_usd || 0), 0);
    const need = rows.filter((r) => groupOf(r) === "needs").length;
    $("#kv").innerHTML = [["Units", `${rows.length}<small>of 27 chapters</small>`], ["Published", `${PUB[WOTW].size}<small>of 27</small>`],
      ["Needs you", `<span style="color:var(--st-flagged)">${need}</span><small>flagged</small>`], ["Running", `1<small>ep17 · ~${rows.find((r) => r.state === "running").eta}</small>`],
      ["GPU", `${shelf.gpu_h}<small>h</small>`], ["LLM spend", `$${cost.toFixed(2)}<small>episodes</small>`]].map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join("");
    $("#wall").innerHTML = wall(rows);
    $("#matrix").innerHTML = matrix(rows);
    $("#cast").innerHTML = cast();
    $("#castn").textContent = `${B.wotw.cast.length} character sheets`;
    bindScrub(document);
  }

  /* ================================================================ books shelf */
  const DEPTS = [["analysis", "A"], ["screenplay", "S"], ["trailer", "T"], ["refs", "R"], ["episode", "E"]];
  function dmark(b, d, letter) {
    const o = b.orders[d], st = o ? o[0] : "", flags = o ? o[1] : 0;
    const disk = b.disk[d === "episode" ? "episodes" : d];
    let cls = "", word = "not started";
    if (st === "done" && flags) { cls = "flagged"; word = `done, ${flags} flag`; }
    else if (st === "done") { cls = "done"; word = "done"; }
    else if (st === "running") { cls = "running"; word = "running"; }
    else if (st === "blocked") { cls = "blocked"; word = "blocked"; }
    else if (disk) { cls = "disk"; word = "files on disk, not in the ledger (pre-ledger)"; }
    else if (st === "queued") { word = "queued"; }
    return `<span class="dm ${cls}" title="${d}: ${word}">${letter}</span>`;
  }
  function seasonStrip(b) {
    const rows = B.dept.rows.filter((r) => r.codex_id === b.id), byU = Object.fromEntries(rows.map((r) => [r.unit, r]));
    const n = b.id === WOTW ? 27 : rows.length;
    return `<span class="season" style="--n:${n}" title="one cell per chapter">${Array.from({ length: n }, (_, i) => {
      const r = byU[`ep${pad(i + 1)}`];
      if (!r) return "<i></i>";
      const s = shown(r);
      const cls = s === "running" ? "run" : s === "flagged" ? "flag" : s === "blocked" ? "blk" : PUB[b.id] && PUB[b.id].has(r.unit) ? "pub" : "";
      return `<i class="${cls}" title="${r.unit} ${s}"></i>`;
    }).join("")}</span>`;
  }
  /* v2 shelf: a department's state as a word + a class, and its progress as a mini bar */
  function dstate(b, d) {
    const o = b.orders[d], st = o ? o[0] : "", flags = o ? o[1] : 0;
    const disk = b.disk[d === "episode" ? "episodes" : d];
    if (st === "done" && flags) return ["flagged", `done · ${flags} flag`];
    if (st === "done") return ["done", "done"];
    if (st === "running") return ["running", "running"];
    if (st === "blocked") return ["blocked", "blocked"];
    if (disk) return ["disk", "on disk"];
    return ["", st === "queued" ? "queued" : "not started"];
  }
  function epBar(b) {
    const rows = B.dept.rows.filter((r) => r.codex_id === b.id), n = b.id === WOTW ? 27 : Math.max(rows.length, b.chapters);
    const k = { pub: 0, flag: 0, run: 0, blk: 0 };
    rows.forEach((r) => { const s = shown(r), c = s === "running" ? "run" : s === "flagged" ? "flag" : s === "blocked" ? "blk" : PUB[b.id].has(r.unit) ? "pub" : ""; if (c) k[c]++; });
    const seg = (c, v) => v ? `<i class="${c}" style="width:${(v / n) * 100}%"></i>` : "";
    return [`${seg("done", k.pub)}${seg("flagged", k.flag)}${seg("running", k.run)}${seg("blocked", k.blk)}`, `${b.published} of ${n}`];
  }
  function deptBars(b) {
    return `<span class="dbars">${DEPTS.map(([d]) => {
      const [cls, word] = dstate(b, d);
      const [fill, frac] = d === "episode" && b.eps.units ? epBar(b) : [`<i class="${cls}" style="width:${cls ? 100 : 0}%"></i>`, word];
      return `<span class="db" title="${d}: ${word}"><span class="dl">${d}</span><span class="mb">${fill}</span><span class="dw ${cls}">${frac}</span></span>`;
    }).join("")}</span>`;
  }
  function dticks(b) {
    return `<span class="dticks" aria-label="departments">${DEPTS.map(([d, l]) => { const [cls, word] = dstate(b, d); return `<i class="${cls}" title="${d}: ${word}">${l}</i>`; }).join("")}</span>`;
  }
  function monogram(name) {
    const words = name.replace(/;.*$/, "").replace(/^(The|A|An)\s+/i, "").split(/[\s.-]+/).filter((w) => /^[A-Z]/.test(w));
    const init = (words[0] || name)[0] + (words[1] ? words[1][0] : "");
    let h = 0; for (const c of name) h = (h * 31 + c.charCodeAt(0)) % 360;
    return `<span class="cover" style="--h:${h}" aria-hidden="true"><span class="ci">${esc(init)}</span><span class="cb"></span></span>`;
  }
  function liveCard(b) {
    const rows = B.dept.rows.filter((r) => r.codex_id === b.id && r.face).sort((x, y) => y.unit.localeCompare(x.unit)).slice(0, 6);
    const run = B.dept.rows.find((r) => r.codex_id === b.id && r.state === "running");
    const need = B.dept.rows.filter((r) => r.codex_id === b.id && groupOf(r) === "needs").length;
    const blk = B.dept.rows.filter((r) => r.codex_id === b.id && groupOf(r) === "blocked").length;
    const tag = (r) => r.state === "running" ? `<span class="tag r live">● ${r.step_id} ${r.step_name}</span>` : shown(r) === "flagged" ? `<span class="tag r flag">⚑</span>` : "";
    return `<a class="bcard live panel" href="${b.id === WOTW ? "book.html" : "#"}">
      <span class="mosaic">${rows.map((r) => `<span class="pic"><img loading="lazy" src="${thumb(b.id, r.face, 320)}" alt=""><span class="tag">${r.unit}</span>${tag(r)}</span>`).join("")}</span>
      <span class="body">
        <span class="hd"><span><h3>${esc(b.name)}</h3><span class="au">${esc(b.author)}</span></span><span class="last">${ago(b.last)} ago</span></span>
        <span class="figs"><span><b>${b.eps.units}</b><small>of ${b.id === WOTW ? 27 : b.eps.units} planned</small></span><span><b>${b.published}</b><small>published</small></span>
          <span><b>${b.gpu_h}</b><small>GPU h</small></span>${need ? `<span class="need"><b>${need}</b><small>need you</small></span>` : ""}</span>
        ${deptBars(b)}
        <span class="status">${run ? `<span class="run"><i></i>${run.unit} ${run.step_id} ${run.step_name} · done ~${run.eta}</span>` : ""}${blk ? `<span>${blk} waiting on <span class="mono">refs/04</span></span>` : ""}</span>
      </span></a>`;
  }
  function smallCard(b) {
    return `<a class="bcard small" href="#" data-name="${esc((b.name + " " + b.author).toLowerCase())}">${monogram(b.name)}<span class="body">
      <h3>${esc(b.name.replace(/;.*$/, ""))}</h3><span class="au">${esc(b.author)}</span>
      <span class="meta">${dticks(b)}<span class="ch"><b>${b.chapters}</b> ch · ${ago(b.last)}</span></span></span></a>`;
  }
  function books() {
    const all = [...B.shelf].sort((a, b) => Date.parse(b.last) - Date.parse(a.last));
    const live = all.filter((b) => b.eps.units), rest = all.filter((b) => !b.eps.units);
    $("#live").innerHTML = live.map(liveCard).join("");
    $("#shelf").innerHTML = rest.map(smallCard).join("");
    $("#sub").innerHTML = `<b>${all.length}</b> books · <b>${live.length}</b> making episodes · <b>${all.reduce((s, b) => s + b.published, 0)}</b> episodes published · sorted by last activity`;
    $("#restn").textContent = `${rest.length} books · analysis done, screenplay on disk`;
    $("#q").addEventListener("input", (e) => {
      const q = e.target.value.trim().toLowerCase();
      document.querySelectorAll("#shelf .bcard").forEach((c) => { c.hidden = q && !c.dataset.name.includes(q); });
    });
  }

  const page = document.body.dataset.page;
  ({ department, book, books }[page] || (() => {}))();
})();
