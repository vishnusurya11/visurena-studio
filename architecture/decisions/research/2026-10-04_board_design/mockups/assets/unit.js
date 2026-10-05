/* Unit page mockup — running (ep17) and finished (ep12).  Hand SVG, no libraries.
   Reads window.UNIT (assets/data_<unit>.js, a read-only capture of the ledger + library).
   Exactly one <video> on the page; every other picture is a /thumb/ still. */
(() => {
'use strict';
const U = window.UNIT;
if (!U) return;
const CODEX = '20260827135508', EP = U.unit, RUNNING = U.row.state === 'running';
const BOARD = 'http://127.0.0.1:8700';
const TH = (w, rel) => `${BOARD}/thumb/${CODEX}/${w}/episodes/${EP}/${rel}`;
const LIB = rel => `${BOARD}/lib/${CODEX}/episodes/${EP}/${rel}`;
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const ic = (n, c = '') => `<svg class="i ${c}" aria-hidden="true"><use href="assets/icons.svg#${n}"/></svg>`;
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const pad = n => String(n).padStart(2, '0');
const OFF = -7 * 3600;                       // the studio's clock (PDT); the ledger is UTC
const D = t => new Date((t + OFF) * 1000);
const hm = t => { const d = D(t); return `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}`; };
const MON = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const day = t => { const d = D(t); return `${d.getUTCDate()} ${MON[d.getUTCMonth()]}`; };
const dhm = t => `${day(t)} ${hm(t)}`;
const iso = s => Date.parse(s.endsWith('Z') ? s : s + 'Z') / 1000;
const dur = s => { s = Math.max(0, s); if (s < 60) return `${Math.round(s)}s`; if (s < 3600) return `${Math.round(s / 60)}m`; const h = Math.floor(s / 3600); return `${h}h${pad(Math.round((s - h * 3600) / 60))}`; };
const tc = t => `${Math.floor(t / 60)}:${(t % 60).toFixed(2).padStart(5, '0')}`;
const S2 = i => pad(i);
const IDS = ['01','02','03','04','05','06','07','08','09','10','11','12'];
const NAME = Object.fromEntries(IDS.map((id, k) => [id, U.names[k]]));
const CLASS = { '01':3, '02':2, '03':1, '04':1, '05':3, '06':2, '07':1, '08':1, '09':1, '10':3, '11':3, '12':3 };
const CLASS_NAME = { 1: 'GPU', 2: 'judgement', 3: 'CPU' };
const NOW = RUNNING ? U.progress.now : U.runs[U.runs.length - 1].end;
const stat = id => U.stats[id] || { p50: 0, p90: 0, n: 0 };
function etaCalc() {
  // finish = now + what is left of the running step + the remaining steps, at p50 and at p90 of completed durations
  if (!RUNNING) return null;
  const run = U.runs[U.runs.length - 1], ids = ['01','02','03','04','05','06','07','08','09','10','11','12'];
  const cur = ids.find(id => run.steps[id] && run.steps[id].ev === 'running');
  const el = NOW - run.steps[cur].start, rest = ids.slice(ids.indexOf(cur) + 1);
  const left = q => Math.max(stat(cur)[q] - el, 0) + rest.reduce((a, id) => a + stat(id)[q], 0);
  const n = Math.min(...rest.concat(cur).map(id => stat(id).n));
  return { p50: NOW + left('p50'), p90: NOW + left('p90'), n, long: el > stat(cur).p90 };
}

function toast(msg) {
  if (window.board && window.board.toast) return window.board.toast(msg);
  const t = $('#toast'); if (!t) return; t.textContent = msg; t.hidden = false;
  clearTimeout(toast.k); toast.k = setTimeout(() => (t.hidden = true), 2600);
}

/* ------------------------------------------------------------ run model (events) */
const OUT = { completed: 'done', failed: 'failed', deferred: 'deferred', escalated: 'escalated', killed: 'held', running: 'running', skipped: 'skipped' };
const WORD = { completed: 'completed', failed: 'failed', deferred: 'deferred', escalated: 'refused', killed: 'killed', running: 'running', skipped: 'skipped' };
const RUNS = U.runs.map((r, k, all) => {
  const last = k === all.length - 1, next = all[k + 1];
  const st = {};
  for (const id of IDS) {
    const s = r.steps[id];
    if (!s) { st[id] = null; continue; }
    let ev = s.ev, end = s.end;
    if (ev === 'running' && !(last && RUNNING)) { ev = 'killed'; end = next ? next.start : s.start; }
    if (ev === 'running') end = NOW;
    st[id] = { ...s, ev, end: end ?? s.start };
  }
  const touched = IDS.filter(id => st[id] && st[id].ev !== 'skipped');
  const lastId = touched[touched.length - 1] || IDS.filter(id => st[id]).pop();
  const end = Math.max(r.end, ...IDS.filter(id => st[id]).map(id => st[id].end));
  return { id: r.id, n: k + 1, start: r.start, end, st, lastId, outcome: st[lastId].ev, log: r.log };
});
let SEL = RUNS.length - 1;

/* ------------------------------------------------------------ header + properties */
function verdictMap() {
  const m = {};
  for (const v of U.verdicts) m[v.gate] = v;
  return m;
}
const VER = verdictMap();
const GATES = ['PLAN', 'LAYOUT', 'EYE_PANELS', 'EYE_TAKES', 'MASTER', 'RENDER'];
const gateArrives = { LAYOUT: '07', EYE_PANELS: '08', EYE_TAKES: '09', MASTER: '11', RENDER: '12' };
const isFlag = v => v && v.by && (v.faults > 0 || /flag/i.test(v.word) || v.terminal === 'flag');

function curStep() { return RUNNING ? IDS.find(id => RUNS[RUNS.length - 1].st[id]?.ev === 'running') : '12'; }

function renderHead() {
  const p = U.plan, row = U.row, cs = curStep();
  const glyph = RUNNING ? ringGlyph(IDS.indexOf(cs) / 12) : ic('check', 'lg');
  const pills = RUNNING
    ? `<span class="pill running">${ic('loader')}running · ${cs} ${NAME[cs]}</span>`
    : `<span class="pill done">${ic('check')}done</span><span class="pill flagged">${ic('flag')}shipped with ${GATES.filter(g => isFlag(VER[g])).length} flagged gates</span>`;
  const acts = RUNNING
    ? `<button class="btn" data-mock="Notify me: done (silent), failed / refused / stalled (sticky)">${ic('bell')}Notify me</button>
       <button class="btn" data-mock="Hold ep17 after 08 panels (confirm dialog in the build)">${ic('pause')}Hold</button>
       <button class="btn icon" aria-label="More actions" data-mock="⋯ Redo a step · Bump · Retry · Open folder">${ic('ellipsis')}</button>`
    : `<button class="btn primary" data-mock="Acknowledge: clears ep12 from Needs you (new 'acknowledge' order kind)">${ic('check')}Acknowledge flags</button>
       <button class="btn" data-mock="Redo… pick a step or a shot (opens the confirm dialog)">${ic('rotate-ccw')}Redo…</button>
       <button class="btn icon" aria-label="More actions" data-mock="⋯ Hold · Bump · Open folder · Copy path">${ic('ellipsis')}</button>`;
  $('#u-head').innerHTML = `
    <div class="u-title"><span aria-hidden="true">${glyph}</span><span class="uid">${EP}</span><h1>${esc(p.title)}</h1>${pills}</div>
    <div class="u-actions">${acts}</div>
    <p class="u-q"><span class="label">Question</span>${esc(p.question)}</p>`;
}

function ringGlyph(frac) {
  const r = 7, c = 2 * Math.PI * r;
  return `<svg width="20" height="20" viewBox="0 0 20 20" style="vertical-align:-3px"><circle cx="10" cy="10" r="${r}" fill="none" style="stroke:var(--rule-2)" stroke-width="2.5"/><circle cx="10" cy="10" r="${r}" fill="none" style="stroke:var(--st-running)" stroke-width="2.5" stroke-dasharray="${c * frac} ${c}" transform="rotate(-90 10 10)"/></svg>`;
}

function renderProps() {
  const row = U.row, cs = curStep(), lastRun = RUNS[RUNS.length - 1];
  const gp = row.gpu_seconds, files = RUNNING
    ? [['plan.json', 'plan.json'], ['plan.verdict.json', 'plan.verdict.json'], [`learnings.jsonl`, 'learnings.jsonl', `${U.learnings.length} rows`], ['timing.jsonl', 'timing.jsonl'], ['storyboard/grids/', 'storyboard/grids/', `${U.grids.length} grids`]]
    : [['master_iter7.mp4', 'cut/master_iter7.mp4', '247 MB'], ['qc_r2v.json', 'qc_r2v.json'], ['review/eye_faf11c8f.json', 'review/eye_faf11c8f.json'], ['plan.json', 'plan.json'], ['learnings.jsonl', 'learnings.jsonl', `${U.learnings.length} rows`]];
  const nonpass = GATES.filter(g => isFlag(VER[g]));
  const passed = GATES.filter(g => VER[g]?.by && !isFlag(VER[g]));
  const unsigned = GATES.filter(g => !VER[g]?.by);
  const rows = RUNNING ? [
    ['State', `<span class="pill running">${ic('loader')}running</span>`],
    ['Step', `<span class="mono-v">${cs} ${NAME[cs]}</span><span class="sub">run #${lastRun.n} of ${RUNS.length} · since ${hm(lastRun.st[cs].start)}</span>`],
    ['Finish', `<span class="mono-v">~${hm(etaCalc().p50)}</span><span class="sub">p50 · p90 ${hm(etaCalc().p90)}</span>`],
    ['Attempt', `<span class="mono-v">${row.attempts}</span><span class="sub">unit attempts; this run's 02 plan took 4 rungs</span>`],
    ['GPU', `<span class="mono-v">${dur(gp)}</span><span class="sub">${Math.round(gp)} s on the lease</span>`],
    ['Cost', `<span class="mono-v">$${row.cost_usd.toFixed(2)}</span>`],
    ['Started', `<span class="mono-v">${dhm(iso(row.started_at))}</span>`],
    ['Elapsed', `<span class="mono-v">${dur(NOW - iso(row.started_at))}</span><span class="sub">run ${dur(NOW - lastRun.start)} · step ${dur(NOW - lastRun.st[cs].start)}</span>`],
    ['Lease', `<span class="mono-v"><span class="hb" aria-hidden="true"></span>→ ${hm(iso(U.lease[0]))}</span><span class="sub">heartbeat ${dur(U.progress.quiet_s)} ago · live</span>`],
  ] : [
    ['State', `<span class="pill done">${ic('check')}done</span>`],
    ['Step', `<span class="mono-v">12 deliver ✓</span><span class="sub">all 12 steps · 32 runs</span>`],
    ['Master', `<span class="mono-v">v7 · 2:40.25</span><span class="sub">= iter5 = master_r2v (80dc87dd)</span>`],
    ['Attempt', `<span class="mono-v">${row.attempts}</span>`],
    ['GPU', `<span class="mono-v">${dur(gp)}</span><span class="sub">${(gp / 3600).toFixed(1)} h on the lease</span>`],
    ['Cost', `<span class="mono-v">$${row.cost_usd.toFixed(2)}</span><span class="sub">local models only</span>`],
    ['Started', `<span class="mono-v">${dhm(RUNS[0].start)}</span>`],
    ['Finished', `<span class="mono-v">${dhm(iso(row.finished_at))}</span><span class="sub">wall ${dur(iso(row.finished_at) - RUNS[0].start)}</span>`],
    ['Lease', `<span class="mono-v">—</span><span class="sub">released</span>`],
  ];
  const gl = nonpass.map(g => `<li><span class="gate flag">${ic('flag')}${g}</span><span class="r">${VER[g].faults}${VER[g].terminal ? ' · ' + VER[g].terminal : ''}</span></li>`).join('')
    + passed.map(g => `<li><span class="gate ok">${ic('check')}${g}</span><span class="r">pass</span></li>`).join('')
    + (unsigned.length ? `<li><span class="gate">${ic('circle-dashed')}${unsigned.length} not signed</span><span class="r">${unsigned.map(g => g.replace('EYE_', '')).join(' · ').toLowerCase()}</span></li>` : '');
  const fl = files.map(([n, rel, r]) => `<li>${ic('external-link')}<a href="${LIB(rel)}" target="_blank" rel="noopener">${n}</a>${r ? `<span class="r">${r}</span>` : ''}</li>`).join('');
  const jumps = (RUNNING ? [['now', 'Now'], ['shots', 'Shots'], ['gates', 'Gates'], ['runs', 'Runs'], ['activity', 'Activity']]
    : [['screen', 'Screen'], ['shots', 'Shots'], ['gates', 'Gates'], ['runs', 'Runs'], ['activity', 'Activity']]).map(([h, t]) => `<a href="#${h}">${t}</a>`).join('');
  $('#props').innerHTML = `<nav class="jump" aria-label="Sections">${jumps}</nav>
    <dl>${rows.map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join('')}
    <h4>Gates · not passing</h4><ul class="list">${gl}</ul>
    <h4>Files</h4><ul class="list">${fl}</ul>
    <h4>Orders</h4><ul class="list"><li class="muted">— none for this unit</li></ul></dl>`;
}

/* ------------------------------------------------------------ NOW hero (running) */
function renderNow() {
  const P = U.progress, run = RUNS[RUNS.length - 1], cs = curStep(), s = run.st[cs];
  const el = NOW - s.start, st = stat(cs), long = el > st.p90;
  const scale = Math.max(st.p90 * 1.15, el * 1.05);
  const segs = IDS.map(id => {
    const x = run.st[id];
    const cls = !x ? '' : x.ev === 'skipped' ? 'skipped' : OUT[x.ev];
    return `<i class="${cls}${id === cs ? ' cur' : ''}" title="${id} ${NAME[id]} · ${x ? WORD[x.ev] : 'not reached'}"></i>`;
  }).join('');
  const labs = IDS.map(id => `<span class="${id === cs ? 'cur' : ''}">${id}<span class="hide-sm"> ${NAME[id]}</span></span>`).join('');
  const E = etaCalc();
  $('#now').innerHTML = `<div class="now">
    <div class="eyebrow"><span class="label">Now · ${cs} ${NAME[cs]}</span><span class="micro muted">run #${run.n} · captured ${hm(NOW)}</span></div>
    <div class="hero ${long ? 'long' : ''}"><small>done around</small>${hm(E.p50)}</div>
    <div class="range"><span class="k">p50</span> <b>${hm(E.p50)}</b> · <span class="k">p90</span> <b>${hm(E.p90)}${day(E.p90) !== day(NOW) ? ' +1d' : ''}</b> · <span class="k">measured: every step's completed runs, n ≥ ${E.n}</span></div>
    <div class="sbar" role="img" aria-label="12 steps, at ${cs} ${NAME[cs]}">${segs}</div>
    <div class="sbar-l" aria-hidden="true">${labs}</div>
    <div class="stepline"><span>${cs} ${NAME[cs]} · ${dur(el)}</span>
      <div class="ebar" role="img" aria-label="step elapsed ${dur(el)} against p50 ${dur(st.p50)} and p90 ${dur(st.p90)}">
        <div class="fill ${long ? 'long' : ''}" style="width:${Math.max(.6, 100 * el / scale)}%"></div>
        <div class="tick" style="left:${100 * st.p50 / scale}%"><span>p50 ${dur(st.p50)}</span></div>
        <div class="tick" style="left:${100 * st.p90 / scale}%"><span>p90 ${dur(st.p90)}</span></div>
      </div><span class="muted">${long ? 'longer than 9 of 10' : `${st.n} measured`}</span></div>
    <div class="secondary"><span>elapsed <b>${dur(NOW - run.start)}</b> this run</span><span><b>${dur(NOW - iso(U.row.started_at))}</b> since ${hm(iso(U.row.started_at))}</span><span>heartbeat <b>${dur(P.quiet_s)}</b> ago</span><span><b>${P.now_step.done}/${P.now_step.total}</b> panels cut${P.now_step.current ? ' · ' + esc(P.now_step.current) : ''}</span></div>
    <div class="lastw"><span class="label">Last words</span><code title="${esc(P.last_words)}">${esc(P.last_words)}</code></div>
  </div>`;
}

/* ------------------------------------------------------------ shots (running): the look so far */
function renderShotsRunning() {
  const g = U.grids, shots = U.plan.shots, covered = new Set(g.flatMap(x => x.shots));
  const st08 = stat('08'), run = RUNS[RUNS.length - 1], s08 = run.st['08'];
  const eta08 = s08 ? s08.start + st08.p50 : null;
  const figs = g.slice().reverse().map((x, k) => `<figure class="${k === 0 ? 'new' : ''}"><img src="${TH(320, x.rel)}" alt="grid ${esc(x.setup)}, shots ${x.shots.join(', ')}" loading="lazy" decoding="async"><figcaption><span>${esc(x.setup)} · ${x.cols}×${x.rows}</span><span>shots ${x.shots.map(S2).join(' ')} · ${hm(x.mtime)}</span></figcaption></figure>`).join('');
  $('#shots').innerHTML = `<header><h2>Shots</h2><span class="label">${shots.length} planned</span></header>
    <p class="empty">${ic('clock')}<span><b>Panels arrive during 08 panels</b> — cutting began ${s08 ? hm(s08.start) : '—'}, 0 of ${shots.length} so far, typical end ~${eta08 ? hm(eta08) : '—'} (p50 ${dur(st08.p50)}). Takes follow at 09 shoot.</span></p>
    <div class="label" style="margin:16px 0 8px">The look so far · ${g.length} storyboard grids from 07 board · ${covered.size} of ${shots.length} shots drawn</div>
    <div class="look">${figs}</div>
    <details class="planlist"><summary>${ic('chevron-right')} The shot list from plan.json (${shots.length})</summary>
      <ol>${shots.map(s => `<li><span class="mono">${S2(s.i)}</span><span class="mono">${esc(s.size)}</span><span>${esc(s.setup)}${s.faces.length ? ' · ' + esc(s.faces.join(', ').replace(/_/g, ' ')) : ''}</span></li>`).join('')}</ol></details>`;
}

/* ------------------------------------------------------------ gates: verdict threads */
function faultGroups(gate) {
  // -> [{kind, shots:[i], ev, chars}]
  if (gate === 'PLAN') {
    const m = {};
    for (const f of U.plan_verdict.faults) {
      const i = +f.where.split('_')[1]; (m[f.kind] ||= { kind: f.kind, shots: new Set(), notes: [] });
      m[f.kind].shots.add(i); m[f.kind].notes.push(f.note); m[f.kind].n = (m[f.kind].n || 0) + 1;
    }
    return Object.values(m).map(x => ({ kind: x.kind, n: x.n, shots: [...x.shots].sort((a, b) => a - b), ev: x.notes.slice(0, 2).join(' · ') }));
  }
  if (gate === 'EYE_PANELS' && U.panel_eye) {
    const m = {};
    for (const [i, kinds] of Object.entries(U.panel_eye.per_shot)) for (const [k, n] of Object.entries(kinds)) {
      (m[k] ||= { kind: k, n: 0, shots: [] }); m[k].n += n; m[k].shots.push(+i);
    }
    const ev = { landmark: 'a landmark drawn where the place names none (arch, barn, bridge …)', framing: 'subject off the planned framing', hat: 'hat differs from the sheet' };
    return Object.values(m).sort((a, b) => b.n - a.n).map(x => ({ ...x, shots: x.shots.sort((a, b) => a - b), ev: ev[x.kind] || '' }));
  }
  if (gate === 'MASTER' && U.master_eye) return U.master_eye.faults.map(f => {
    if (f.kind === 'faces') return { kind: 'faces', n: 1, shots: f.evidence.under, ev: f.evidence.closes.filter(c => f.evidence.under.includes(c.shot)).map(c => `shot ${S2(c.shot)} ${c.size} face h ${c.h} < wall ${c.wall}`).join(' · ') };
    const shots = U.plan.shots.filter(s => s.faces.includes(f.where)).map(s => s.i);
    return { kind: 'identity', n: 1, shots, ev: `${f.where.replace(/_/g, ' ')} · min cosine ${f.evidence.min_cosine} < ${f.evidence.wall} on ${f.evidence.below} of ${f.evidence.reads} reads · ${f.note}` };
  });
  return [];
}

function ladderSvg(rows) {
  const W = 150, H = 38, ladders = [], cur = [];
  for (const r of rows) { cur.push(r); if (r.terminal) { ladders.push(cur.splice(0)); } }
  if (cur.length) ladders.push(cur.splice(0));
  const ymax = 60, y = v => H - 6 - (H - 12) * Math.sqrt(Math.min(v, ymax) / ymax);
  const maxLen = Math.max(...ladders.map(l => l.length), 2), x = k => 4 + (W - 30) * k / (maxLen - 1);
  const lines = ladders.map((l, k) => `<polyline class="ln ${k === ladders.length - 1 ? 'last' : ''}" points="${l.map((r, j) => `${x(j)},${y(r.measured)}`).join(' ')}"/>`).join('');
  const last = ladders[ladders.length - 1] || [], e = last[last.length - 1];
  const lab = e ? `<text x="${x(last.length - 1) + 5}" y="${y(e.measured) + 3}">${Math.round(e.measured)}${e.terminal ? (e.action === 'keep_best' || e.action === 'flag' ? ' ⊘' : '') : ''}</text>` : '';
  return `<svg class="ladder" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="${ladders.length} ladders, last ends at ${e ? e.measured : '—'}">${lines}${lab}</svg>`;
}

function runOfTs(t) { let k = 0; RUNS.forEach((r, j) => { if (r.start <= t + 1) k = j; }); return RUNS[k]; }

function renderGates() {
  const out = [];
  const signed = GATES.filter(g => VER[g]?.by), unsigned = GATES.filter(g => !VER[g]?.by);
  const order = signed.sort((a, b) => (isFlag(VER[b]) - isFlag(VER[a])));
  for (const g of order) {
    const v = VER[g], flag = isFlag(v);
    const rows = U.learnings.filter(l => l.gate === g);
    let at = '';
    if (g === 'MASTER' && U.master_eye) at = dhm(U.master_eye.at);
    else if (g === 'EYE_PANELS' && U.panel_eye) at = dhm(U.panel_eye.at);
    else if (g === 'EYE_TAKES' && U.take_eye) at = dhm(U.take_eye.at);
    else if (rows.length) at = dhm(rows[rows.length - 1].ts);
    const groups = faultGroups(g);
    let lastRun = null;
    const rl = rows.map(r => {
      const run = runOfTs(r.ts), sep = run !== lastRun ? `<li class="sep">run #${run.n} · ${dhm(run.start)}</li>` : '';
      lastRun = run;
      return `${sep}<li class="${r.terminal ? 'term' : ''}"><span>${hm(r.ts)}</span><span><span class="k">rung</span> ${r.attempt}</span><span>${Math.round(r.measured)}</span><span>${esc(r.action)}${r.terminal ? ' ■' : ''}</span><span class="note" title="${esc(r.note)}">${r.seconds ? dur(r.seconds) + ' · ' : ''}${esc(r.note)}</span></li>`;
    }).join('');
    const chips = gs => gs.shots.map(i => EP === 'ep12' ? `<button class="chipnum" data-shot="${i}">${S2(i)}</button>` : `<span class="chipnum">${S2(i)}</span>`).join('');
    const fk = groups.length ? `<div class="fk">${groups.map(x => `<span class="kind">${ic('flag')}${esc(x.kind)} ×${x.n}</span><span class="sh">${x.shots.length >= 24 ? '<span class="chipnum">every shot 00–23</span>' : chips(x)}</span>${x.ev ? `<span class="ev">${esc(x.ev)}</span>` : ''}`).join('')}</div>` : '';
    const word = flag ? `${v.word || 'FLAGGED'} · ⚑ ${v.faults}` : 'PASSED';
    out.push(`<details class="thread ${flag ? 'flag' : 'pass'}" ${flag && !out.length ? 'open' : ''}>
      <summary><span class="gname">${ic(flag ? 'flag' : 'check')}${g}</span>
      <span class="gsum">${esc(word)}${v.terminal ? ` · ${esc(v.terminal)}` : ''} · ${rows.length} rung${rows.length === 1 ? '' : 's'} <span class="by">· ${esc(v.by)} · ${at}</span></span>
      ${rows.length > 1 ? ladderSvg(rows) : '<span></span>'}</summary>
      <div class="body">${fk}${rl ? `<ul class="rounds" aria-label="rounds">${rl}</ul>` : '<p class="gnotyet">signed in one read, no ladder</p>'}</div></details>`);
  }
  const ny = unsigned.length ? `<p class="gnotyet">${ic('circle-dashed')} ${unsigned.join(' · ')} — not signed yet${RUNNING ? '; they arrive at ' + unsigned.map(g => `${gateArrives[g] || '—'}`).join(', ') : ''}</p>` : '';
  $('#gates').innerHTML = `<header><h2>Gates</h2><span class="label">verdict threads · non-pass open</span></header><div class="threads">${out.join('')}</div>${ny}`;
}

/* ------------------------------------------------------------ run matrix (hand SVG) */
const FILL = { done: 'var(--st-done-bar)', failed: 'var(--st-failed-bar)', deferred: 'var(--st-deferred-bar)', escalated: 'var(--ink)', held: 'var(--st-held)', running: 'var(--st-running-bar)', skipped: 'var(--rule-2)' };
const DEFS = `<defs>
  <pattern id="pf" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="4" height="4" style="fill:var(--st-failed-bar)"/><rect x="3" width="1.2" height="4" style="fill:var(--paper)"/></pattern>
  <pattern id="ph" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="4" height="4" style="fill:var(--paper)"/><rect width="1.6" height="4" style="fill:var(--st-held)"/></pattern>
  <pattern id="pd" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="4" style="fill:var(--st-deferred-bar)"/><circle cx="2" cy="2" r=".8" style="fill:var(--paper)"/></pattern>
  <pattern id="pg" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="5" height="5" style="fill:var(--paper)"/><rect width="1.5" height="5" style="fill:var(--line)"/></pattern>
</defs>`;
function cell(ev, x, y, s) {
  switch (ev) {
    case 'skipped': return `<circle cx="${x + s / 2}" cy="${y + s / 2}" r="${s / 4.2}" fill="none" style="stroke:var(--line)" stroke-width="1.2"/>`;
    case 'completed': return `<rect x="${x + .5}" y="${y + .5}" width="${s - 1}" height="${s - 1}" rx="1.5" style="fill:var(--st-done-bg);stroke:var(--st-done-bar)" stroke-width="1"/>`;
    case 'failed': return `<rect x="${x}" y="${y}" width="${s}" height="${s}" rx="1.5" fill="url(#pf)"/>`;
    case 'deferred': return `<rect x="${x}" y="${y}" width="${s}" height="${s}" rx="1.5" fill="url(#pd)"/>`;
    case 'escalated': return `<rect x="${x}" y="${y}" width="${s}" height="${s}" rx="1.5" style="fill:var(--ink)"/><rect x="${x + s / 2 - 1}" y="${y + 2.5}" width="2" height="${s - 5}" style="fill:var(--paper)"/>`;
    case 'killed': return `<rect x="${x + .5}" y="${y + .5}" width="${s - 1}" height="${s - 1}" rx="1.5" fill="url(#ph)" style="stroke:var(--st-held)" stroke-width="1"/>`;
    case 'running': return `<rect x="${x}" y="${y}" width="${s}" height="${s}" rx="1.5" style="fill:var(--st-running-bar)"/>`;
  }
  return '';
}
function loops() {
  const out = []; let k = 0;
  while (k < RUNS.length) {
    const key = r => `${r.lastId}:${r.outcome}`;
    let j = k; while (j + 1 < RUNS.length && key(RUNS[j + 1]) === key(RUNS[k])) j++;
    if (j - k + 1 >= 3 && RUNS[k].outcome !== 'completed') {
      const fails = new Set(RUNS.slice(k, j + 1).map(r => (r.st[r.lastId].detail || '').slice(0, 40)));
      out.push({ a: k, b: j, n: j - k + 1, id: RUNS[k].lastId, ev: RUNS[k].outcome, span: RUNS[j].end - RUNS[k].start, kinds: fails.size });
    }
    k = j + 1;
  }
  return out;
}
function renderRuns() {
  const n = RUNS.length, colW = n <= 8 ? 60 : 18, cs = n <= 8 ? 16 : 12, lab = 104, stripH = 40, rowH = cs + 5;
  const xs = []; let x = lab + 6;
  RUNS.forEach((r, k) => { if (k && r.start - RUNS[k - 1].end > 2 * 3600) x += 14; xs.push(x); x += colW; });
  const W = x + 8, top = 8, gridY = top + stripH + 18, LP = loops();
  const bracketY = gridY + 12 * rowH + 8, H = bracketY + (LP.length ? 46 : 8) + 18;
  const maxWall = Math.max(...RUNS.map(r => r.end - r.start), 60);
  let s = `<svg class="mx" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="Run matrix: ${n} runs by 12 steps${LP.length ? ', loops at ' + LP.map(l => l.id).join(', ') : ''}">${DEFS}`;
  s += `<text x="0" y="${top + 10}" class="lab">RUN TIME</text><text x="0" y="${top + 22}">max ${dur(maxWall)}</text>`;
  IDS.forEach((id, i) => { s += `<text class="rl" x="0" y="${gridY + i * rowH + cs - 2}">${id} ${NAME[id]}</text>`; });
  let lastDay = '';
  RUNS.forEach((r, k) => {
    const cx = xs[k], cw = colW, h = 3 + (stripH - 3) * (r.end - r.start) / maxWall, oc = OUT[r.outcome];
    const sx = cx + (cw - cs) / 2;
    s += `<g class="col ${k === SEL ? 'sel' : ''}" data-run="${k}" tabindex="-1"><title>run #${r.n} · ${dhm(r.start)} · ${dur(r.end - r.start)} · ended ${WORD[r.outcome]} at ${r.lastId} ${NAME[r.lastId]}</title>`;
    s += `<rect class="hl" x="${cx}" y="${top - 4}" width="${cw}" height="${gridY + 12 * rowH - top + 4}" rx="2"/>`;
    const bf = r.outcome === 'failed' ? 'url(#pf)' : r.outcome === 'deferred' ? 'url(#pd)' : r.outcome === 'killed' ? 'url(#ph)' : '';
    s += `<rect x="${sx}" y="${top + stripH - h}" width="${cs}" height="${h}" ${bf ? `fill="${bf}"` : `style="fill:${FILL[oc]};opacity:${oc === 'done' ? .55 : 1}"`}/>`;
    IDS.forEach((id, i) => { const c = r.st[id]; if (c) s += cell(c.ev, sx, gridY + i * rowH, cs); });
    s += `</g>`;
    const dl = day(r.start);
    if (dl !== lastDay) { s += `<text x="${cx + 2}" y="${top + stripH + 14}" style="fill:var(--ink-2)">${dl}</text><line x1="${cx}" x2="${cx}" y1="${top + stripH + 2}" y2="${top + stripH + 6}" style="stroke:var(--ink-3)"/>`; lastDay = dl; }
    if (n <= 8 || k % 4 === 0 || k === n - 1) s += `<text x="${cx + cw / 2}" y="${H - 4}" text-anchor="middle">${n <= 8 ? `#${r.n} ${hm(r.start)}` : '#' + r.n}</text>`;
  });
  let lastEnd = -1e9, row2 = false;
  LP.forEach(l => {
    const x1 = xs[l.a] + 2, x2 = xs[l.b] + colW - 2;
    row2 = x1 < lastEnd + 8 ? !row2 : false;
    const y = bracketY + (row2 ? 20 : 0);
    s += `<path class="br" d="M${x1} ${y} v6 H${x2} v-6"/><text class="brt" x="${x1}" y="${y + 18}">↻ ×${l.n} at ${l.id} ${NAME[l.id]}</text><text class="brs" x="${x1}" y="${y + 18}" dx="${(`↻ ×${l.n} at ${l.id} ${NAME[l.id]}`.length) * 6.6 + 6}">${dur(l.span)} · ${WORD[l.ev]}${l.kinds > 1 ? ` · ${l.kinds} reasons` : ''}</text>`;
    lastEnd = x1 + 230;
  });
  s += `</svg>`;
  const legend = [['completed', 'completed'], ['skipped', 'skipped (cached)'], ['failed', 'failed'], ['deferred', 'deferred'], ['escalated', 'refused'], ['killed', 'killed'], ['running', 'running']]
    .map(([ev, w]) => `<span><svg viewBox="0 0 12 12">${DEFS}${cell(ev, 0, 0, 12)}</svg>${w}</span>`).join('');
  const totalWall = RUNS.reduce((a, r) => a + (r.end - r.start), 0);
  const burned = RUNS.filter(r => !['completed', 'running'].includes(r.outcome)).reduce((a, r) => a + (r.end - r.start), 0);
  $('#runs').innerHTML = `<header><h2>Runs</h2><span class="label">${n} runs · ${dur(totalWall)} run time · ${dur(burned)} in runs that did not finish</span><span class="r micro muted">click a run · ← → move</span></header>
    <div class="mx-scroll" id="mxs">${s}</div><div class="legend">${legend}</div>
    <div class="wfbox" id="wf"></div>`;
  const sc = $('#mxs'); sc.scrollLeft = sc.scrollWidth;
  $$('.mx .col').forEach(g => g.addEventListener('click', () => selectRun(+g.dataset.run)));
  renderWaterfall();
}
function selectRun(k) {
  SEL = Math.max(0, Math.min(RUNS.length - 1, k));
  $$('.mx .col').forEach(g => g.classList.toggle('sel', +g.dataset.run === SEL));
  renderWaterfall(); renderActivity();
}

/* ------------------------------------------------------------ waterfall (selected run) */
function niceStep(span) { const c = [60, 120, 300, 600, 900, 1800, 3600, 7200, 10800, 21600]; return c.find(v => span / v <= 7) || 21600; }
function renderWaterfall() {
  const r = RUNS[SEL], box = $('#wf');
  const W = Math.max(320, Math.min(980, box.clientWidth || 860)), phone = W < 560;
  const lab = phone ? 92 : 150, right = phone ? 44 : 70, pw = W - lab - right;
  const touched = IDS.filter(id => r.st[id] && r.st[id].ev !== 'skipped'), skipped = IDS.filter(id => r.st[id]?.ev === 'skipped');
  const ghost = (r === RUNS[RUNS.length - 1] && RUNNING) ? IDS.filter(id => !r.st[id]) : [];
  let t1 = r.end; let gt = NOW; const gh = ghost.map(id => { const a = gt; gt += stat(id).p50; return { id, a, b: gt }; });
  if (gh.length) t1 = Math.max(t1, gt);
  const t0 = r.start, span = Math.max(t1 - t0, 30), X = t => lab + pw * (t - t0) / span;
  const rows = [{ kind: 'run' }];
  if (skipped.length) rows.push({ kind: 'skip' });
  touched.forEach(id => rows.push({ kind: 'step', id }));
  gh.forEach(g => rows.push({ kind: 'ghost', ...g }));
  const rh = 22, top = 22, H = top + rows.length * rh + 8;
  let s = `<svg class="wf" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="Waterfall of run #${r.n}">${DEFS}`;
  const st = niceStep(span);
  for (let t = 0; t <= span + 1; t += st) { const x = X(t0 + t); s += `<line class="ax" x1="${x}" x2="${x}" y1="${top - 4}" y2="${H - 4}"/><text x="${x}" y="12" text-anchor="${t === 0 ? 'start' : 'middle'}">${t === 0 ? hm(t0) : '+' + dur(t)}</text>`; }
  if (RUNNING && r === RUNS[RUNS.length - 1]) { const x = X(NOW); s += `<line class="now" x1="${x}" x2="${x}" y1="${top - 6}" y2="${H}"/><text x="${x + 3}" y="${top - 8}" style="fill:var(--st-running)">now</text>`; }
  rows.forEach((row, i) => {
    const y = top + i * rh, by = y + 5, bh = rh - 10;
    s += `<g class="row"><rect class="rbg" x="0" y="${y}" width="${W}" height="${rh}"/>`;
    if (row.kind === 'run') {
      s += `<text class="lbl" x="0" y="${y + 15}" style="font-weight:600;fill:var(--ink)">run #${r.n}</text><rect x="${X(t0)}" y="${by + 2}" width="${Math.max(2, X(r.end) - X(t0))}" height="${bh - 4}" style="fill:var(--ink-3);opacity:.35"/><text class="dur" x="${W - 2}" y="${y + 15}" text-anchor="end">${dur(r.end - t0)}</text>`;
    } else if (row.kind === 'skip') {
      s += `<text class="lbl" x="0" y="${y + 15}" style="fill:var(--ink-3)">${phone ? `${skipped.length} cached` : `${skipped.join(' ')} cached`}</text>`;
      skipped.forEach(id => { const c = r.st[id]; s += `<circle cx="${X(c.start)}" cy="${y + rh / 2}" r="2.5" fill="none" style="stroke:var(--line)"><title>${id} ${NAME[id]} skipped · ${esc(c.detail || 'output exists')}</title></circle>`; });
      s += `<text class="dur" x="${W - 2}" y="${y + 15}" text-anchor="end">—</text>`;
    } else if (row.kind === 'step') {
      const c = r.st[row.id], x1 = X(c.start), x2 = Math.max(X(c.end), x1 + 2), sp = stat(row.id);
      const fill = `var(--viz-${CLASS[row.id]})`, capF = c.ev === 'failed' ? 'url(#pf)' : c.ev === 'deferred' ? 'url(#pd)' : c.ev === 'killed' ? 'url(#ph)' : '';
      const capS = capF ? '' : `style="fill:${c.ev === 'completed' ? 'var(--st-done-bar)' : c.ev === 'escalated' ? 'var(--ink)' : 'var(--st-running-bar)'}"`;
      s += `<text class="lbl" x="0" y="${y + 15}">${row.id} ${phone ? '' : NAME[row.id]}</text>`;
      s += `<rect x="${x1}" y="${by}" width="${x2 - x1}" height="${bh}" style="fill:${fill};opacity:.85"><title>${row.id} ${NAME[row.id]} (${CLASS_NAME[CLASS[row.id]]}) · ${hm(c.start)}–${hm(c.end)} · ${dur(c.end - c.start)} · ${WORD[c.ev]} · vs typical p50 ${dur(sp.p50)} · p90 ${dur(sp.p90)}${c.detail ? '\n' + esc(c.detail.slice(0, 160)) : ''}</title></rect>`;
      s += `<rect x="${x2 - 1}" y="${by - 2}" width="5" height="${bh + 4}" ${capF ? `fill="${capF}"` : capS}/>`;
      if (!phone && sp.p50 > 60) { const px = X(c.start + sp.p50), qx = X(c.start + sp.p90); if (px < lab + pw) s += `<line x1="${px}" x2="${px}" y1="${by - 3}" y2="${by + bh + 3}" style="stroke:var(--ink);opacity:.55" stroke-dasharray="2 2"><title>p50 ${dur(sp.p50)}</title></line>`; if (qx < lab + pw) s += `<line x1="${qx}" x2="${qx}" y1="${by - 3}" y2="${by + bh + 3}" style="stroke:var(--ink);opacity:.3" stroke-dasharray="2 2"><title>p90 ${dur(sp.p90)}</title></line>`; }
      U.learnings.filter(l => l.gate !== 'budget' && l.ts >= c.start - 2 && l.ts <= c.end + 2).forEach(l => {
        const lx = X(l.ts); s += `<line x1="${lx}" x2="${lx}" y1="${by - 2}" y2="${by + bh + 2}" style="stroke:var(--paper)" stroke-width="1.5"/><text class="tickt" x="${lx + 2}" y="${by - 1}">${l.attempt}</text><title>${l.gate} rung ${l.attempt} · measured ${l.measured} → ${l.action}</title>`;
      });
      s += `<text class="dur" x="${W - 2}" y="${y + 15}" text-anchor="end">${dur(c.end - c.start)}</text>`;
    } else {
      s += `<text class="lbl" x="0" y="${y + 15}" style="fill:var(--ink-3)">${row.id} ${phone ? '' : NAME[row.id]}</text><rect x="${X(row.a)}" y="${by}" width="${Math.max(2, X(row.b) - X(row.a))}" height="${bh}" fill="url(#pg)" style="stroke:var(--line)" stroke-width=".75"><title>${row.id} ${NAME[row.id]} · expected p50 ${dur(stat(row.id).p50)}</title></rect><text class="dur" x="${W - 2}" y="${y + 15}" text-anchor="end" style="fill:var(--ink-3)">~${dur(row.b - row.a)}</text>`;
    }
    s += `</g>`;
  });
  s += `</svg>`;
  const cls = [1, 2, 3].map(k => `<span><svg viewBox="0 0 12 12"><rect width="12" height="12" style="fill:var(--viz-${k})"/></svg>${CLASS_NAME[k]}</span>`).join('');
  box.innerHTML = `<header><h3>Run #${r.n}</h3><span class="mono muted">${dhm(r.start)} · ${dur(r.end - r.start)} · ended ${WORD[r.outcome]} at ${r.lastId} ${NAME[r.lastId]}</span><span class="micro muted" style="margin-left:auto">${r.id.split('__').pop()}</span></header>${s}
    <div class="legend">${cls}<span><svg viewBox="0 0 12 12"><rect width="12" height="12" fill="url(#pg)" style="stroke:var(--line)"/></svg>expected (p50)</span><span>┆ p50 / p90 of this step</span><span><b style="color:var(--ink)">2</b>&nbsp;gate rung</span></div>`;
}

/* ------------------------------------------------------------ activity: run log grouped by step */
let LV = { INFO: true, WARNING: true, ERROR: true, EVENT: true }, Q = '';
function activityEntries(r) {
  const e = [];
  for (const id of IDS) {
    const c = r.st[id]; if (!c) continue;
    if (c.ev === 'skipped') { e.push({ ts: c.start, step: id, level: 'EVENT', msg: `skipped · ${c.detail || 'output exists'}` }); continue; }
    e.push({ ts: c.start, step: id, level: 'EVENT', msg: 'started' });
    if (c.ev !== 'running') e.push({ ts: c.end, step: id, level: c.ev === 'failed' ? 'ERROR' : c.ev === 'completed' ? 'EVENT' : 'WARNING', msg: `${WORD[c.ev]}${c.detail ? ' · ' + c.detail : ''}` });
  }
  for (const l of r.log) e.push({ ts: l.ts, step: l.step === 'ladders' ? 'gates' : l.step, level: l.level, msg: l.msg });
  return e.sort((a, b) => a.ts - b.ts);
}
function renderActivity() {
  const r = RUNS[SEL], ents = activityEntries(r), groups = new Map();
  for (const x of ents) { if (!groups.has(x.step)) groups.set(x.step, []); groups.get(x.step).push(x); }
  const counts = { INFO: 0, WARNING: 0, ERROR: 0, EVENT: 0 }; ents.forEach(x => counts[x.level] = (counts[x.level] || 0) + 1);
  const skipped = IDS.filter(id => r.st[id]?.ev === 'skipped');
  const re = Q ? new RegExp(Q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi') : null;
  let html = '';
  if (skipped.length) html += `<details class="lg quiet"><summary>${ic('chevron-right', 'chev')}<span class="s">${skipped.length} skipped</span><span class="w">${skipped.join(' · ')} · output exists, cached</span><span class="r"></span></summary></details>`;
  for (const [step, xs] of groups) {
    if (skipped.includes(step)) continue;
    const c = r.st[step], ev = c ? c.ev : 'gates';
    const bad = ['failed', 'escalated', 'killed'].includes(ev), def = ev === 'deferred';
    const lines = xs.filter(x => LV[x.level] !== false).map(x => {
      const hit = re && re.test(x.msg); if (re) re.lastIndex = 0;
      const m = re ? esc(x.msg).replace(re, mm => `<mark>${mm}</mark>`) : esc(x.msg);
      return `<div class="ln ${x.level}" ${re && !hit ? 'hidden' : ''} id="L${Math.round(x.ts * 10)}"><span class="t">${hm(x.ts)}:${pad(D(x.ts).getUTCSeconds())}</span><span class="lv">${x.level === 'EVENT' ? 'EVENT' : x.level}</span><span class="m">${m}</span></div>`;
    }).join('');
    const anyHit = re ? xs.some(x => { const h = re.test(x.msg); re.lastIndex = 0; return h; }) : true;
    if (re && !anyHit) continue;
    const title = step === 'gates' ? 'gates' : NAME[step] ? `${step} ${NAME[step]}` : 'runner';
    const last = xs.filter(x => x.level !== 'EVENT' || /failed|deferred|refused/.test(x.msg)).pop() || xs[xs.length - 1];
    const span = c ? dur(c.end - c.start) : '';
    const open = bad || def || (re && anyHit) || (ev === 'running');
    html += `<details class="lg ${bad ? 'bad' : def ? 'def' : ''}" ${open ? 'open' : ''}><summary>${ic('chevron-right', 'chev')}<span class="s">${title}${c ? ` · ${WORD[ev]}` : ''}</span><span class="w">${esc(last.msg.split('\n')[0].slice(0, 140))}</span><span class="r">${xs.length} lines${span ? ' · ' + span : ''}</span></summary><div class="lines">${lines || '<div class="ln"><span></span><span></span><span class="m muted">no lines at the chosen levels</span></div>'}</div></details>`;
  }
  const nolog = r.log.length ? '' : `<p class="empty">${ic('minus')}No run log kept for run #${r.n}; the lines below are its ledger events.</p>`;
  const chips = ['ERROR', 'WARNING', 'INFO', 'EVENT'].map(l => `<button class="lvl ${l === 'ERROR' ? 'err' : l === 'WARNING' ? 'warn' : ''}" aria-pressed="${LV[l]}" data-lv="${l}">${l} ${counts[l] || 0}</button>`).join('');
  const on = Object.values(LV).filter(Boolean).length;
  const host = $('#activity');
  if (!host.dataset.built) {
    host.innerHTML = `<header><h2>Activity</h2><span class="label" id="act-l"></span></header>
      <div class="act-tools"><label class="search">${ic('search')}<input id="q" type="search" placeholder="Search this run's log" aria-label="Search the log"></label><span id="lvls" style="display:flex;gap:4px;flex-wrap:wrap"></span></div>
      <div id="act-b"></div>`;
    host.dataset.built = 1;
    $('#q').addEventListener('input', e => { Q = e.target.value.trim(); renderActivity(); });
    host.addEventListener('click', e => {
      const b = e.target.closest('.lvl'); if (b) { LV[b.dataset.lv] = !LV[b.dataset.lv]; renderActivity(); }
      const l = e.target.closest('.ln'); if (l) l.classList.toggle('open');
    });
  }
  $('#act-l').textContent = `run #${r.n} · ${dhm(r.start)} · ${on} of 4 levels`;
  $('#lvls').innerHTML = chips;
  $('#act-b').innerHTML = `${nolog}<div class="lgroups">${html || '<p class="empty">nothing matches</p>'}</div>`;
}

/* ============================================================ finished: screening room */
const FPS = 24;
let SH = [], VIDEO = null, curT = 0, VERS = 7;
function buildShots() {
  const segs = U.segments, pe = U.panel_eye.per_shot, mf = U.master_eye.faults;
  SH = U.plan.shots.map(p => {
    const seg = segs.find(s => s.shots.includes(p.i)) || segs[p.i];
    const take = U.takes[p.i], pk = pe[p.i] || {}, pn = Object.values(pk).reduce((a, b) => a + b, 0);
    const master = [];
    mf.forEach(f => {
      if (f.kind === 'faces' && f.evidence.under.includes(p.i)) { const c = f.evidence.closes.find(c => c.shot === p.i); master.push({ kind: 'faces', ev: `face h ${c.h} < wall ${c.wall}`, wide: false }); }
      if (f.kind === 'identity' && p.faces.includes(f.where)) master.push({ kind: 'identity', ev: `${f.where.replace(/_/g, ' ')} drifts (min cos ${f.evidence.min_cosine})`, wide: true });
    });
    const plan = U.plan_verdict.faults.filter(f => +f.where.split('_')[1] === p.i);
    return { ...p, t0: seg.start / FPS, t1: (seg.start + seg.n) / FPS, take, pn, pk, master, plan };
  });
}
const VERSIONS = [
  { v: 7, iter: 'iter7', also: 'iter5 · master_r2v', t: '25 Sep 18:49', md5: '80dc87dd', mb: 247.4, verdict: 'MASTER ⚑ 3 · faf11c8f' },
  { v: 6, iter: 'iter6', t: '25 Sep 18:22', md5: 'a78b0224', mb: 247.4, verdict: 'no verdict kept' },
  { v: 4, iter: 'iter4', t: '25 Sep 17:40', md5: '2e988fe7', mb: 245.0, verdict: 'no verdict kept' },
  { v: 3, iter: 'iter3', t: '25 Sep 17:14', md5: '90582070', mb: 245.0, verdict: 'no verdict kept' },
  { v: 2, iter: 'iter2', t: '25 Sep 08:47', md5: 'e61f8543', mb: 248.9, verdict: 'no verdict kept' },
  { v: 1, iter: 'iter1', t: '25 Sep 07:31', md5: '363e3b23', mb: 248.0, verdict: 'no verdict kept' },
];
function faultRows() {
  const rows = [];
  SH.forEach(s => s.master.filter(m => !m.wide).forEach(m => rows.push({ g: 'MASTER', t0: s.t0, t1: s.t1, k: m.kind, w: `shot ${S2(s.i)}`, e: m.ev, shot: s.i })));
  U.master_eye.faults.filter(f => f.kind === 'identity').forEach(f => {
    const ss = SH.filter(s => s.faces.includes(f.where));
    rows.push({ g: 'MASTER', t0: ss[0].t0, t1: ss[0].t1, k: 'identity', w: f.where.replace(/_/g, ' ').replace('unnamed first person ', ''), e: `shots ${ss.map(s => S2(s.i)).join(' ')} · min cos ${f.evidence.min_cosine} < ${f.evidence.wall} on ${f.evidence.below}/${f.evidence.reads} reads`, shot: ss[0].i, wide: ss.map(s => s.i) });
  });
  const q = U.qc, extra = q.seen_cuts.filter(c => !q.planned_cuts.some(p => Math.abs(p - c) < .05) && c < q.planned_seconds - .1);
  if (extra.length) { const s = SH.find(s => extra[0] >= s.t0 && extra[0] < s.t1); rows.push({ g: 'QC', t0: extra[0], t1: extra[extra.length - 1] + .05, k: 'cuts', w: `×${extra.length} in shot ${S2(s.i)}`, e: `unplanned cuts at ${extra.map(c => c.toFixed(2)).join(' · ')} s (seen − planned)`, shot: s.i, tick: extra }); }
  U.qc_lines.filter(l => l.error_rate > 0).forEach(l => { const pl = U.plan.lines[l.index], s = SH[pl.shot]; rows.push({ g: 'LINES', t0: s.t0, t1: s.t1, k: 'heard', w: `line ${S2(l.index)} · ${Math.round(l.error_rate * 100)}% off`, e: `“${l.heard}”`, shot: s.i, minor: true }); });
  const pg = {}; U.plan_verdict.faults.forEach(f => { const i = +f.where.split('_')[1]; (pg[f.kind] ||= []).push(i); });
  Object.entries(pg).forEach(([k, is]) => { const u = [...new Set(is)].sort((a, b) => a - b); rows.push({ g: 'PLAN', t0: SH[u[0]].t0, t1: SH[u[0]].t1, k, w: `shots ${u.map(S2).join(' ')}`, e: k === 'story' ? 'turn read on shot 11, marked on 16' : 'props / counts with no chapter span', shot: u[0], wide: u }); });
  return rows.sort((a, b) => a.t0 - b.t0);
}

function renderScreen() {
  const q = U.qc, me = U.master_eye, rows = faultRows();
  const stamp = (g, cls, word, glyph, by, at, extra) => `<div class="stamp ${cls}"><span class="g">${g}</span><span class="w">${ic(glyph)}${word}</span><span>${extra}</span><span class="by" title="${by}">${by} · ${at}</span></div>`;
  const lastPlan = U.learnings.filter(l => l.gate === 'PLAN').pop();
  const stamps = [
    stamp('MASTER', 'flag', 'flagged', 'flag', me.by, dhm(me.at), `faces n · identity ×2 · ${me.terminal}`),
    stamp('EYE_TAKES', 'pass', 'passed', 'check', U.take_eye.by, dhm(U.take_eye.at), `24 of 24 · 48 reads`),
    stamp('EYE_PANELS', 'flag', 'flagged', 'flag', U.panel_eye.by, dhm(U.panel_eye.at), `${U.panel_eye.n} faults · ${U.panel_eye.terminal}`),
    stamp('PLAN', 'flag', 'approve ⚑7', 'flag', U.plan_verdict.by, dhm(lastPlan.ts), `story ×2 · invented ×5 · kept best`),
  ].join('');
  const fl = rows.map((r, k) => `<li><button data-f="${k}" data-t="${r.t0}" data-shot="${r.shot}"><span class="gl ${r.minor ? 'tk' : ''}">${ic(r.minor ? 'minus' : 'flag')}</span><span><b>${r.k}</b> · ${esc(r.w)} <span class="micro" style="color:var(--stage-ink-3)">${r.g}</span></span><span class="t">${tc(r.t0)}</span><span class="e">${esc(r.e)}</span></button></li>`).join('');
  const v = VERSIONS.find(x => x.v === VERS);
  $('#screen').innerHTML = `<div class="wrap">
    <div class="pcol">
      <div class="qcline"><span><b>master_iter7.mp4</b> = iter5 = master_r2v</span><span>${q.sha8}</span><span>${tc(q.seconds)} <span style="color:var(--stage-ink-3)">(plan ${tc(q.planned_seconds)})</span></span><span>LUFS ${q.lufs} <span class="ok">✓</span></span><span>peak ${q.true_peak} <span class="ok">✓</span></span><span>cuts ${q.planned_cuts.length}/${q.planned_cuts.length} <span class="ok">✓</span></span><span>lines ${U.qc_lines.filter(l => l.passed).length}/${U.qc_lines.length} <span class="ok">✓</span></span></div>
      <div class="player" id="player">
        <img class="poster" id="poster" src="${LIB('takes/work/content/T19_1.png')}" alt="ep12 master, shot 19: the shell bursts in its face" decoding="async">
        <video id="vid" preload="none" playsinline hidden></video>
        <button class="bigplay" id="bigplay" aria-label="Play the master">${ic('play')}</button>
        <button class="vbadge" id="vbadge" aria-haspopup="true" aria-expanded="false">v${v.v} ${ic('chevron-down')}</button>
        <div class="stamp-on">${ic('flag')}master flagged · ${me.by.replace('judge:', '')}</div>
        <div class="vstack" id="vstack" hidden role="menu"></div>
      </div>
      <div class="pctrl"><button class="pbtn" id="pp" aria-label="Play or pause">${ic('play')}</button><span class="tc" id="tc">0:00.00 · f0 · shot 00</span><span class="sp"></span>
        <button class="pbtn" id="cmpb">${ic('layers')}Compare</button><span class="kbd dk">Space</span><span class="kbd dk">↑↓ faults</span><span class="kbd dk">C</span></div>
      <div style="position:relative"><svg class="lanes" id="lanes" role="img" aria-label="Shots, faults and lines lanes over the master"></svg><div class="lane-tip" id="ltip" hidden></div></div>
    </div>
    <div class="sside">
      <h3>Judges</h3><div class="stamps">${stamps}</div>
      <div class="fhd"><h3 style="margin:0">Faults on the master</h3><span class="micro">${rows.length} · by time · click to seek</span></div>
      <ul class="flist" id="flist">${fl}</ul>
      <p class="micro" style="color:var(--stage-ink-3);margin-top:10px">EYE_PANELS faults (531) stay on the panels in the shot strip; on this timeline they would be noise.</p>
    </div></div>`;
  VIDEO = $('#vid');
  renderVstack(); drawLanes(); wirePlayer(rows);
}
function renderVstack() {
  $('#vstack').innerHTML = `<div class="hd">Versions · 7 cuts, 6 distinct by hash</div>${VERSIONS.map(x => `<button role="menuitem" data-v="${x.v}" ${x.v === VERS ? 'aria-current="true"' : ''}><span class="v">v${x.v}</span><span>${x.iter}${x.also ? ` <span style="color:var(--stage-ink-3)">= ${x.also}</span>` : ''}</span><span>${x.md5}</span><span class="d">${x.t} · ${x.mb} MB · <span class="${x.v === 7 ? 'w' : ''}">${x.verdict}</span></span></button>`).join('')}<div class="ft">iter5 and iter7 are byte-identical (md5 80dc87dd); shown once. Shift-click picks B for compare.</div>`;
}
function laneGeom() { const W = $('#lanes').parentNode.clientWidth || 600; return { W, L: 54, R: 4, T: U.qc.seconds }; }
function drawLanes() {
  const { W, L, R, T } = laneGeom(), X = t => L + (W - L - R) * t / T, rows = faultRows();
  const yS = 14, hS = 22, yM = yS + hS + 6, yP = yM + 14, yC = yP + 14, yL = yC + 14, H = yL + 16;
  let s = `${DEFS}<defs><pattern id="tt" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="5" height="5" fill="#1b1b1b"/><rect width="1.4" height="5" fill="#3a3a3a"/></pattern></defs>`;
  for (let t = 0; t <= T; t += 30) s += `<text x="${X(t)}" y="9" text-anchor="${t ? 'middle' : 'start'}">${Math.floor(t / 60)}:${pad(t % 60)}</text>`;
  s += `<text class="lab" x="0" y="${yS + 15}">SHOTS</text><text class="lab" x="0" y="${yM + 9}">MASTER</text><text class="lab" x="0" y="${yP + 9}">PLAN</text><text class="lab" x="0" y="${yC + 9}">QC</text><text class="lab" x="0" y="${yL + 9}">LINES</text>`;
  SH.forEach(sh => {
    const x1 = X(sh.t0), x2 = X(sh.t1), fl = sh.master.some(m => !m.wide);
    s += `<g class="seg" data-shot="${sh.i}"><rect x="${x1 + .5}" y="${yS}" width="${Math.max(1, x2 - x1 - 1)}" height="${hS}" fill="${fl ? '#3a2c10' : '#262626'}" stroke="${fl ? '#c8952a' : '#3a3a3a'}" stroke-width="1"/>${x2 - x1 > 16 ? `<text x="${(x1 + x2) / 2}" y="${yS + 15}" text-anchor="middle" style="fill:${fl ? '#e9b44c' : '#bdbdbd'}">${S2(sh.i)}</text>` : ''}</g>`;
  });
  s += `<rect x="${X(U.qc.planned_seconds) + .5}" y="${yS}" width="${X(T) - X(U.qc.planned_seconds) - 1}" height="${hS}" fill="url(#tt)" stroke="#3a3a3a"><title>title card ${tc(U.qc.planned_seconds)}–${tc(T)}</title></rect>`;
  rows.forEach(r => {
    if (r.g === 'MASTER' && !r.wide) s += `<rect x="${X(r.t0)}" y="${yM}" width="${X(r.t1) - X(r.t0)}" height="10" fill="#e9b44c"><title>${r.k} · ${r.w} · ${r.e}</title></rect><path d="M${X(r.t0)} ${yM - 3} l4 0 l-4 4z" fill="#e9b44c"/>`;
    if (r.g === 'MASTER' && r.wide) r.wide.forEach(i => { s += `<rect x="${X(SH[i].t0) + 1}" y="${yM + 6}" width="${X(SH[i].t1) - X(SH[i].t0) - 2}" height="3" fill="#c8952a" opacity=".85"><title>${r.k} · ${r.w} (character-wide)</title></rect>`; });
    if (r.g === 'PLAN') r.wide.forEach(i => { s += `<rect x="${X(SH[i].t0) + 1}" y="${yP + 2}" width="${X(SH[i].t1) - X(SH[i].t0) - 2}" height="6" fill="none" stroke="#c8952a" stroke-dasharray="2 1.5"><title>PLAN ${r.k} · shot ${S2(i)}</title></rect>`; });
    if (r.g === 'QC') r.tick.forEach(c => { s += `<line x1="${X(c)}" x2="${X(c)}" y1="${yC}" y2="${yC + 10}" stroke="#e9b44c" stroke-width="1.5"><title>unplanned cut ${c.toFixed(2)} s</title></line>`; });
  });
  U.qc_lines.forEach(l => { const pl = U.plan.lines[l.index], x = X(SH[pl.shot].t0 + .3); s += `<path d="M${x} ${yL + 10} l3 -8 l3 8z" fill="${l.error_rate > 0 ? '#e9b44c' : '#5aa76a'}"><title>line ${S2(l.index)} · ${pl.speaker.replace(/_/g, ' ')} · ${l.passed ? 'passed' : 'failed'}${l.error_rate ? ' · ' + Math.round(l.error_rate * 100) + '% off' : ''}</title></path>`; });
  s += `<line id="ph" x1="${X(curT)}" x2="${X(curT)}" y1="${yS - 3}" y2="${H}" stroke="#fff" stroke-width="2"/>`;
  const svg = $('#lanes'); svg.setAttribute('viewBox', `0 0 ${W} ${H}`); svg.setAttribute('height', H); svg.innerHTML = s;
}
function shotAt(t) { return SH.find(s => t >= s.t0 && t < s.t1) || SH[SH.length - 1]; }
function setT(t, seek) {
  curT = Math.max(0, Math.min(U.qc.seconds, t));
  const { W, L, R, T } = laneGeom(), x = L + (W - L - R) * curT / T, ph = $('#ph');
  if (ph) { ph.setAttribute('x1', x); ph.setAttribute('x2', x); }
  const sh = shotAt(curT);
  $('#tc').textContent = `${tc(curT)} · f${Math.round(curT * FPS)} · shot ${S2(sh.i)}`;
  $$('#lanes .seg rect').forEach(r => r.setAttribute('stroke-width', +r.parentNode.dataset.shot === sh.i ? 2 : 1));
  if (seek && VIDEO && VIDEO.parentNode.id === 'player') { ensureMaster(); try { VIDEO.currentTime = curT; } catch (e) {} }
}
function masterSrc() { return LIB(`cut/master_iter${VERS}.mp4`); }
function ensureMaster() {
  if (VIDEO.dataset.src !== masterSrc()) { VIDEO.src = masterSrc(); VIDEO.dataset.src = masterSrc(); VIDEO.preload = 'metadata'; }
  VIDEO.hidden = false; $('#poster').hidden = true; $('#bigplay').hidden = true;
}
function playPause() {
  if (VIDEO.parentNode.id !== 'player') parkVideo();
  ensureMaster();
  if (VIDEO.paused) { if (Math.abs(VIDEO.currentTime - curT) > .2) VIDEO.currentTime = curT; VIDEO.play().catch(() => {}); } else VIDEO.pause();
}
function wirePlayer(rows) {
  VIDEO.addEventListener('timeupdate', () => { if (VIDEO.parentNode.id === 'player' && VIDEO.dataset.src === masterSrc()) setT(VIDEO.currentTime); });
  VIDEO.addEventListener('play', () => { $('#pp').innerHTML = ic('pause'); });
  VIDEO.addEventListener('pause', () => { $('#pp').innerHTML = ic('play'); });
  $('#bigplay').onclick = playPause; $('#pp').onclick = playPause;
  const vb = $('#vbadge'), vs = $('#vstack');
  vb.onclick = e => { e.stopPropagation(); vs.hidden = !vs.hidden; vb.setAttribute('aria-expanded', !vs.hidden); };
  vs.addEventListener('click', e => {
    const b = e.target.closest('button[data-v]'); if (!b) return;
    if (e.shiftKey) { openCompare(+b.dataset.v); vs.hidden = true; return; }
    VERS = +b.dataset.v; vb.innerHTML = `v${VERS} ${ic('chevron-down')}`; renderVstack(); vs.hidden = true;
    if (!VIDEO.hidden) { ensureMaster(); VIDEO.currentTime = curT; }
    toast(`v${VERS} loaded on the player (${VERSIONS.find(x => x.v === VERS).iter})`);
  });
  document.addEventListener('click', e => { if (!e.target.closest('#vstack,#vbadge')) { vs.hidden = true; vb.setAttribute('aria-expanded', 'false'); } });
  const svg = $('#lanes'), tip = $('#ltip');
  const tAt = e => { const { W, L, R, T } = laneGeom(), r = svg.getBoundingClientRect(); return (e.clientX - r.left - L) / (W - L - R) * T; };
  let drag = false;
  svg.addEventListener('pointerdown', e => { drag = true; svg.setPointerCapture(e.pointerId); setT(tAt(e), true); });
  svg.addEventListener('pointerup', () => { drag = false; });
  svg.addEventListener('pointermove', e => {
    const t = tAt(e); if (drag) setT(t, true);
    if (t < 0 || t > U.qc.seconds) { tip.hidden = true; return; }
    const sh = shotAt(t), r = svg.getBoundingClientRect(), x = Math.min(Math.max(e.clientX - r.left - 84, 0), r.width - 168);
    tip.innerHTML = `<img src="${TH(160, `takes/work/content/T${S2(sh.i)}_1.png`)}" alt=""><div>shot ${S2(sh.i)} · ${esc(sh.size)}</div><div style="color:var(--stage-ink-3)">${tc(sh.t0)}–${tc(sh.t1)}</div>${sh.master.length ? `<div style="color:#e9b44c">⚑ ${sh.master.map(m => m.kind).join(', ')}</div>` : ''}`;
    tip.style.left = x + 'px'; tip.style.bottom = (r.height + 8) + 'px'; tip.hidden = false;
  });
  svg.addEventListener('pointerleave', () => { tip.hidden = true; });
  $('#flist').addEventListener('click', e => { const b = e.target.closest('button[data-t]'); if (!b) return; $$('#flist button').forEach(x => x.classList.toggle('on', x === b)); setT(+b.dataset.t + .01, true); });
  $('#cmpb').onclick = () => openCompare(6);
  window.addEventListener('resize', () => { drawLanes(); setT(curT); });
  setT(0);
}

/* ------------------------------------------------------------ compare (mock: stills on one clock) */
function openCompare(b) {
  const d = $('#cmp'), sh = shotAt(curT), A = VERSIONS[0], B = VERSIONS.find(x => x.v === b) || VERSIONS[1];
  const img = TH(320, `takes/work/content/T${S2(sh.i)}_1.png`);
  let mode = 'side';
  const draw = () => {
    const side = (x, tag) => `<div class="cmp-side"><div class="hd"><span>${tag} · v${x.v} ${x.iter} · ${x.md5}</span><span>${x.verdict}</span></div><div class="frame"><img src="${img}" alt=""><span class="bl">${tc(curT)} · shot ${S2(sh.i)}</span></div></div>`;
    const area = mode === 'side' ? `<div class="cmp-area">${side(A, 'A')}${side(B, 'B')}</div>`
      : mode === 'wipe' ? `<div class="cmp-area wipe"><div class="wipe-stack" id="wst"><img src="${img}" alt=""><img class="top" src="${img}" alt="" style="filter:saturate(.75) contrast(1.05)"><div class="handle"></div><span class="tagA">A v${A.v}</span><span class="tagB">B v${B.v}</span></div></div>`
      : `<div class="cmp-area flip"><div class="cmp-side"><div class="hd"><span id="flipl">A · v${A.v} ${A.iter}</span><span>Tab flips</span></div><div class="frame"><img src="${img}" alt=""></div></div></div>`;
    d.innerHTML = `<div class="sv-h"><h2>Compare</h2><span class="meta">A v${A.v} (${A.iter}) vs B v${B.v} (${B.iter}) · one clock at ${tc(curT)}</span><span class="sp"></span>
      <div class="cmp-modes">${[['side', 'Side by side'], ['wipe', 'Wipe'], ['flip', 'Flip A/B']].map(([m, t]) => `<button data-m="${m}" aria-pressed="${m === mode}">${t}</button>`).join('')}</div>
      <button class="btn stg" data-close>${ic('x')}Close</button></div>
      <div class="sv-b">${area}<p class="cmp-note">Mock: the build plays both cuts as two linked &lt;video&gt; (B follows A within 1/48 s). Which shots changed between v${B.v} and v${A.v} needs cut/master_iterN.cut.json per iteration (SPEC, pipeline item 3); today only v7's qc_r2v survives.</p></div>`;
    d.querySelectorAll('[data-m]').forEach(bt => bt.onclick = () => { mode = bt.dataset.m; draw(); });
    d.querySelector('[data-close]').onclick = () => d.close();
    const w = d.querySelector('#wst'); if (w) { const mv = e => { const r = w.getBoundingClientRect(); w.style.setProperty('--x', Math.max(0, Math.min(100, 100 * (e.clientX - r.left) / r.width)) + '%'); }; w.addEventListener('pointermove', mv); w.addEventListener('pointerdown', mv); }
  };
  draw();
  d.onkeydown = e => { if (e.key === 'Tab' && mode === 'flip') { e.preventDefault(); const l = d.querySelector('#flipl'); l.textContent = l.textContent.startsWith('A') ? `B · v${B.v} ${B.iter}` : `A · v${A.v} ${A.iter}`; } };
  d.showModal();
}

/* ------------------------------------------------------------ shot strip (finished) */
let FILTER = 'all';
function stageGlyphs(s) {
  const take = s.take, tk = take.dq_bad.length ? 'ok' : 'ok';
  const m = s.master.length ? `<span class="fl" title="master: ${s.master.map(x => x.kind).join(', ')}">${ic('flag')}${s.master.some(x => !x.wide) ? s.master.find(x => !x.wide).kind : 'identity'}</span>` : `<span class="ok" title="master: clean">${ic('check')}master</span>`;
  return `<span class="fl" title="panel: ${Object.entries(s.pk).map(([k, n]) => `${k} ×${n}`).join(', ')}">${ic('flag')}panel ${s.pn}</span><span class="${tk}" title="take: EYE_TAKES pass${take.dq_bad.length ? '; soft misses ' + take.dq_bad.join(', ') : ''}">${ic('check')}take</span>${m}`;
}
function renderShotsFinished() {
  const cnt = { all: SH.length, master: SH.filter(s => s.master.length).length, retried: SH.filter(s => s.take.tries > 1).length, plan: SH.filter(s => s.plan.length).length };
  const cards = SH.map(s => `<button class="shot ${s.master.some(m => !m.wide) ? 'flag' : ''}" data-i="${s.i}" aria-label="shot ${s.i}, ${s.size}, try ${s.take.tries}${s.master.length ? ', master flagged' : ''}">
      <div class="pair"><div class="frame"><img src="${TH(160, `storyboard/shot_${S2(s.i)}.png`)}" alt="" loading="lazy" decoding="async" width="160" height="160"><span class="tl">P</span></div>
      <div class="frame tk"><img class="tki" src="${TH(160, `takes/work/content/T${S2(s.i)}_1.png`)}" alt="" loading="lazy" decoding="async" width="160" height="160"><span class="tl">T${S2(s.i)}</span><span class="br">${s.take.secs ? s.take.secs.toFixed(1) + 's' : ''}</span><span class="scrub"><i></i></span></div></div>
      <div class="m"><div class="m1">${S2(s.i)}<span class="sz">${esc(s.size.replace('_', ' '))}${s.faces.length ? ' · ' + esc(s.faces[0].replace('unnamed_first_person_', '').replace('_', ' ')) : ''}</span><span class="try ${s.take.tries > 1 ? 're' : ''}">${s.take.tries > 1 ? ic('rotate-ccw') + ' try ' + s.take.tries : 'try 1'}</span></div>
      <div class="stg">${stageGlyphs(s)}</div></div></button>`).join('');
  $('#shots').innerHTML = `<header><h2>Shots</h2><span class="label">24 · panel → take → master</span><span class="r"><span class="filters" role="group" aria-label="Filter shots">
    ${[['all', 'All'], ['master', '⚑ Master'], ['retried', '↻ Retried'], ['plan', '⚑ Plan']].map(([f, t]) => `<button class="fchip" data-filter="${f}" aria-pressed="${f === FILTER}">${t} ${cnt[f]}</button>`).join('')}</span></span></header>
    <div class="shots" id="shotgrid">${cards}</div>
    <p class="micro muted" style="margin-top:10px">Hover a take to scrub its three content frames; rest on it to play (the page's one video moves here). Click for the shot view.</p>`;
  $$('.fchip').forEach(b => b.onclick = () => { FILTER = b.dataset.filter; $$('.fchip').forEach(x => x.setAttribute('aria-pressed', x === b)); $$('.shot').forEach(c => { const s = SH[+c.dataset.i]; c.hidden = !(FILTER === 'all' || (FILTER === 'master' && s.master.length) || (FILTER === 'retried' && s.take.tries > 1) || (FILTER === 'plan' && s.plan.length)); }); });
  const grid = $('#shotgrid');
  grid.addEventListener('click', e => { const c = e.target.closest('.shot'); if (c) openShot(+c.dataset.i, 1); });
  let dwell = null;
  grid.addEventListener('pointermove', e => {
    const f = e.target.closest('.frame.tk'); if (!f) return;
    const i = +f.closest('.shot').dataset.i, r = f.getBoundingClientRect(), k = Math.max(0, Math.min(2, Math.floor(3 * (e.clientX - r.left) / r.width)));
    const img = f.querySelector('.tki'), want = TH(160, `takes/work/content/T${S2(i)}_${k}.png`);
    if (img.src !== want) img.src = want;
    f.style.setProperty('--k', k);
    clearTimeout(dwell);
    if (!matchMedia('(prefers-reduced-motion: reduce)').matches) dwell = setTimeout(() => hoverPlay(f, i), 700);
  });
  grid.addEventListener('pointerout', e => { const f = e.target.closest('.frame.tk'); if (f && !f.contains(e.relatedTarget)) { clearTimeout(dwell); if (VIDEO.parentNode === f) parkVideo(); } });
}
function hoverPlay(f, i) {
  if (VIDEO.parentNode === f) return;
  VIDEO.pause(); f.appendChild(VIDEO); VIDEO.hidden = false; VIDEO.muted = true; VIDEO.loop = true;
  VIDEO.src = LIB(`takes/r2v/T${S2(i)}.mp4`); VIDEO.dataset.src = VIDEO.src; VIDEO.play().catch(() => {});
}
function parkVideo() {
  VIDEO.pause(); VIDEO.loop = false; VIDEO.muted = false;
  const p = $('#player'); p.insertBefore(VIDEO, $('#bigplay'));
  VIDEO.removeAttribute('src'); VIDEO.dataset.src = ''; VIDEO.load();
  VIDEO.hidden = true; $('#poster').hidden = false; $('#bigplay').hidden = false;
}

/* ------------------------------------------------------------ shot view (lightbox) */
let SV = { i: 0, st: 1, redo: false, ghost: {} };
const STAGES = ['panel', 'take', 'master'];
function openShot(i, st) {
  SV.i = i; SV.st = st ?? 1; SV.redo = false;
  const d = $('#sv'); drawShot(); if (!d.open) d.showModal();
  history.replaceState(null, '', `#shot-${S2(i)}`);
}
function drawShot() {
  const s = SH[SV.i], d = $('#sv'), take = s.take;
  if (VIDEO.parentNode && VIDEO.parentNode.closest && VIDEO.parentNode.closest('#sv')) parkVideo();
  const learn = U.learnings.filter(l => l.gate === 'EYE_TAKES' && new RegExp(`T${S2(s.i)}\\b`).test(l.note));
  const pk = Object.entries(s.pk).sort((a, b) => b[1] - a[1]);
  const col = (k, title, v, body, ft) => `<div class="stg3" data-st="${k}" aria-current="${SV.st === k}"><div class="hd"><span>${title}</span><span class="v">${v}</span></div>${body}<div class="ft">${ft}</div></div>`;
  const panel = col(0, 'Panel · 08', `shot_${S2(s.i)}.png`, `<div class="frame"><img src="${TH(320, `storyboard/shot_${S2(s.i)}.png`)}" alt="panel ${s.i}"></div>`,
    `<span class="fl">⚑ EYE_PANELS ${s.pn}</span> · ${pk.map(([k, n]) => `${k} ×${n}`).join(' · ')}`);
  const tframe = SV.st === 1 ? `<div class="frame" id="svtake"><img src="${TH(320, `takes/work/content/T${S2(s.i)}_1.png`)}" alt="take ${s.i}"><span class="bl">T${S2(s.i)} · ${take.secs}s</span><span class="br">Space plays</span></div>` : `<div class="frame"><img src="${TH(320, `takes/work/content/T${S2(s.i)}_1.png`)}" alt="take ${s.i}"></div>`;
  const ghost = SV.ghost[s.i] ? `<div class="ghost">${ic('rotate-ccw')}try ${take.tries + 1} · queued · “${esc(SV.ghost[s.i].slice(0, 60))}”</div>` : '';
  const takeC = col(1, 'Take · 09', `try ${take.tries}${take.tries > 1 ? ` · ${take.tries - 1} failed` : ''}`, tframe + ghost,
    `<span class="ok">✓ EYE_TAKES pass</span>${take.dq_bad.length ? ` · soft misses: ${take.dq_bad.join(', ')}` : ' · dq clean'} · content ${take.content_ok ? 'ok' : 'fault'}`);
  const masterC = col(2, 'In the master · v7', `${tc(s.t0)}–${tc(s.t1)}`, `<div class="frame" id="svmaster"><img src="${TH(320, `takes/work/content/T${S2(s.i)}_2.png`)}" alt="master segment ${s.i}"><span class="bl">f${Math.round(s.t0 * FPS)}–f${Math.round(s.t1 * FPS)}</span><span class="br">Space plays the segment</span></div>`,
    s.master.length ? s.master.map(m => `<span class="fl">⚑ ${m.kind}</span> ${esc(m.ev)}`).join('<br>') : '<span class="ok">✓ MASTER: nothing named here</span>');
  const faults = [
    ...s.plan.map(f => `<li><span class="g fl">PLAN ⚑</span>${esc(f.kind)} · ${esc(f.note)}</li>`),
    ...pk.map(([k, n]) => `<li><span class="g fl">EYE_PANELS ⚑</span>${k} ×${n}</li>`),
    ...take.dq_bad.map(g => `<li><span class="g">take dq</span>${g} (soft; passed)</li>`),
    ...s.master.map(m => `<li><span class="g fl">MASTER ⚑</span>${m.kind} · ${esc(m.ev)}${m.wide ? ' · character-wide' : ''}</li>`),
  ].join('') || '<li><span class="g ok">✓</span>no fault names this shot</li>';
  const tries = learn.length ? learn.map(l => `<li><span class="g">${dhm(l.ts)}</span>rung ${l.attempt} · ${esc(l.action)} · ${esc((l.note.match(new RegExp(`[^;]*T${S2(s.i)}[^;]*`)) || [''])[0].trim())}</li>`).join('') : `<li>${take.tries > 1 ? `${take.tries - 1} failed attempt(s) in takes/r2v/attempts/` : 'first take kept'}</li>`;
  const note = [...s.master.filter(m => !m.wide).map(m => `MASTER ${m.kind}: ${m.ev}`), ...s.plan.map(f => `PLAN ${f.kind}: ${f.note}`)].join('; ') || `shot ${S2(s.i)}: `;
  d.innerHTML = `<div class="sv-h"><h2>Shot ${S2(s.i)}</h2><span class="meta">${esc(s.size.replace('_', ' '))} · ${esc(s.setup)} · ${esc(s.section)}${s.faces.length ? ' · ' + esc(s.faces.join(', ').replace(/_/g, ' ')) : ''}</span><span class="sp"></span>
    <span class="stabs">${STAGES.map((n, k) => `<button class="fchip" data-goto="${k}" aria-pressed="${SV.st === k}">${n}</button>`).join('')}</span>
    <button class="btn stg icon" data-nav="-1" aria-label="Previous shot">←</button><span class="meta">${SV.i + 1}/24</span><button class="btn stg icon" data-nav="1" aria-label="Next shot">→</button>
    <button class="btn stg" data-close>${ic('x')}Esc</button></div>
    <div class="sv-b"><div class="stages3">${panel}${takeC}${masterC}</div>
    <div class="sv-txt"><div><h4>Frame</h4><p>${esc(s.frame)}</p><h4>Motion</h4><p>${esc(s.motion)}</p><h4>Camera</h4><p>${esc(s.camera)}</p></div>
      <div><h4>Faults naming shot ${S2(s.i)}</h4><ul>${faults}</ul><h4>Take history</h4><ul>${tries}</ul></div></div>
    <div class="redo"><button class="btn st" id="redob">${ic('rotate-ccw')}Redo this shot <span class="kbd" style="margin-left:4px">R</span></button>
      <div class="keys"><span><span class="kbd">←</span><span class="kbd">→</span> shots</span><span><span class="kbd">↑</span><span class="kbd">↓</span> stages</span><span><span class="kbd">Space</span> play</span><span><span class="kbd">Esc</span> close</span></div>
      <div class="box" id="redobox" ${SV.redo ? '' : 'hidden'}><label><input type="radio" name="rs" value="08" ${SV.st === 0 ? 'checked' : ''}> redraw the panel · 08</label><label><input type="radio" name="rs" value="09" ${SV.st !== 0 ? 'checked' : ''}> reshoot the take · 09</label>
        <textarea id="redonote" aria-label="Note for the redo">${esc(note)}</textarea>
        <div style="display:flex;gap:8px;margin-top:8px"><button class="btn st" id="redogo">Queue redo ↵</button><button class="btn stg" id="redocancel">Cancel</button><span class="micro" style="color:var(--stage-ink-3);align-self:center">posts /act/redo (mock) · confirm dialog in the build</span></div></div></div></div>`;
  d.querySelector('[data-close]').onclick = () => d.close();
  d.querySelectorAll('[data-nav]').forEach(b => b.onclick = () => nav(+b.dataset.nav));
  d.querySelectorAll('[data-goto]').forEach(b => b.onclick = () => { SV.st = +b.dataset.goto; drawShot(); });
  d.querySelectorAll('.stg3').forEach(c => c.onclick = e => { if (+c.dataset.st !== SV.st) { SV.st = +c.dataset.st; drawShot(); } else if (SV.st) svPlay(); });
  $('#redob').onclick = () => { SV.redo = true; $('#redobox').hidden = false; $('#redonote').focus(); };
  $('#redocancel').onclick = () => { SV.redo = false; $('#redobox').hidden = true; };
  $('#redogo').onclick = () => { SV.ghost[s.i] = $('#redonote').value; SV.redo = false; toast(`Mock: redo of shot ${S2(s.i)} queued — order would read “${d.querySelector('input[name=rs]:checked').value}”`); drawShot(); };
}
function svPlay() {
  const s = SH[SV.i], slot = SV.st === 1 ? $('#svtake') : SV.st === 2 ? $('#svmaster') : null;
  if (!slot) return;
  if (VIDEO.parentNode === slot) { VIDEO.paused ? VIDEO.play().catch(() => {}) : VIDEO.pause(); return; }
  VIDEO.pause(); slot.appendChild(VIDEO); VIDEO.hidden = false; VIDEO.muted = false; VIDEO.loop = SV.st === 1;
  VIDEO.src = SV.st === 1 ? LIB(`takes/r2v/T${S2(s.i)}.mp4`) : `${masterSrc()}#t=${s.t0.toFixed(2)},${s.t1.toFixed(2)}`;
  VIDEO.dataset.src = VIDEO.src; VIDEO.play().catch(() => {});
}
function nav(k) { SV.i = (SV.i + k + SH.length) % SH.length; SV.redo = false; drawShot(); history.replaceState(null, '', `#shot-${S2(SV.i)}`); }

/* ------------------------------------------------------------ keys */
function wireKeys() {
  document.addEventListener('keydown', e => {
    if (e.target.closest('input,textarea,select')) return;
    const sv = $('#sv');
    if (sv && sv.open) {
      if (e.key === 'ArrowRight') { e.preventDefault(); nav(1); }
      else if (e.key === 'ArrowLeft') { e.preventDefault(); nav(-1); }
      else if (e.key === 'ArrowDown') { e.preventDefault(); SV.st = Math.min(2, SV.st + 1); drawShot(); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); SV.st = Math.max(0, SV.st - 1); drawShot(); }
      else if (e.key === ' ') { e.preventDefault(); svPlay(); }
      else if (e.key === 'r' || e.key === 'R') { e.preventDefault(); $('#redob').click(); }
      return;
    }
    if ($('#cmp')?.open) return;
    if (e.target.closest('.mx-scroll') || document.activeElement === document.body) {
      if (e.key === 'ArrowRight' && e.target.closest('.mx-scroll')) { e.preventDefault(); selectRun(SEL + 1); }
      if (e.key === 'ArrowLeft' && e.target.closest('.mx-scroll')) { e.preventDefault(); selectRun(SEL - 1); }
    }
    if (EP !== 'ep12') return;
    if (e.key === ' ' && !e.target.closest('button,a,summary')) { e.preventDefault(); playPause(); }
    if (e.key === 'c' || e.key === 'C') openCompare(6);
    if ((e.key === 'ArrowDown' || e.key === 'ArrowUp') && e.target.closest('#screen')) {
      e.preventDefault(); const bs = $$('#flist button'), cur = bs.findIndex(b => b.classList.contains('on'));
      const nx = bs[Math.max(0, Math.min(bs.length - 1, cur + (e.key === 'ArrowDown' ? 1 : -1)))]; nx.click(); nx.focus();
    }
  });
  const sv = $('#sv'); if (sv) sv.addEventListener('close', () => { if (VIDEO && VIDEO.parentNode !== $('#player')) parkVideo(); history.replaceState(null, '', location.pathname); });
  $$('.mx-scroll').forEach(m => m.tabIndex = 0);
  document.addEventListener('click', e => {
    const m = e.target.closest('[data-mock]'); if (m) toast(`Mock — ${m.dataset.mock}`);
    const c = e.target.closest('.chipnum[data-shot]'); if (c && EP === 'ep12') openShot(+c.dataset.shot, 1);
  });
}

/* ------------------------------------------------------------ boot */
renderHead(); renderProps();
if (RUNNING) { const gp = $('.gpu-pill'), E = etaCalc(), cs = curStep(); if (gp) { gp.lastChild.textContent = ` ${cs} ${NAME[cs]} · ~${hm(E.p50)}`; gp.title = `GPU: ep17 The Thunder Child, ${cs} ${NAME[cs]}, done around ${hm(E.p50)} (p90 ${hm(E.p90)}) · captured ${hm(NOW)}`; } }
if (RUNNING) { renderNow(); renderShotsRunning(); }
else { buildShots(); renderScreen(); renderShotsFinished(); }
renderGates(); renderRuns(); renderActivity(); wireKeys();
let rz; window.addEventListener('resize', () => { clearTimeout(rz); rz = setTimeout(renderWaterfall, 120); });
if (!RUNNING && /^#shot-\d\d$/.test(location.hash)) openShot(+location.hash.slice(6), 1);
document.title = RUNNING ? `● ${curStep()} ${NAME[curStep()]} · ~${hm(etaCalc().p50)} · ${EP}` : `✓ ${EP} · done · ⚑ flagged`;
})();
