/* prov.js — the unit model and the provenance panel for the Viewer (SPEC_v3, V03, V06).
   A take is graph(prompt(plan_row, refs), seed) judged by gates: every field in the panel has one
   source file and one key, carried as a source chip that opens the raw file at that key; a field
   with no source says "not recorded". Reads the read-only snapshot under data/<unit>/ (JSON + logs);
   pictures and video come from :8700. Registers itself with Viewer.use(). */
(function () {
'use strict';
const OFF = -7 * 3600, FPS = 24, MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const pad = n => String(n).padStart(2, '0');
const hm = t => { const d = new Date((t + OFF) * 1000); return `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}`; };
const dhm = t => { const d = new Date((t + OFF) * 1000); return `${d.getUTCDate()} ${MON[d.getUTCMonth()]} ${hm(t)}`; };
const isoT = s => Date.parse(/Z$|[+-]\d\d:?\d\d$/.test(s) ? s : s + 'Z') / 1000;
const tc = t => `${Math.floor(t / 60)}:${(t % 60).toFixed(2).padStart(5, '0')}`;
const sz = n => n < 1024 ? `${n} B` : n < 1048576 ? `${(n / 1024).toFixed(n < 10240 ? 1 : 0)} KB` : `${(n / 1048576).toFixed(1)} MB`;
function el(tag, cls, text) { const n = document.createElement(tag); if (cls) n.className = cls; if (text !== undefined && text !== null) n.textContent = String(text); return n; }
function add(p, ...k) { k.forEach(x => x && p.appendChild(x)); return p; }

/* ------------------------------------------------------------------ fetch the snapshot */
const UNITS = {}, LOADED = {}, FILES = new Map();
function getText(unit, rel) {
  const k = `${unit}/${rel}`;
  if (!FILES.has(k)) FILES.set(k, fetch(`data/${unit}/${rel}`).then(r => (r.ok ? r.text() : null)).catch(() => null));
  return FILES.get(k);
}
function getJSON(unit, rel) {
  return getText(unit, rel).then(t => {
    if (t == null) return null;
    if (rel.endsWith('.jsonl')) return t.split('\n').filter(l => l.trim()).map(l => { try { return JSON.parse(l); } catch (e) { return null; } }).filter(Boolean);
    try { return JSON.parse(t); } catch (e) { return null; }
  });
}
const WANT = { plan: 'plan.json', pv: 'plan.verdict.json', layout: 'storyboard/layout.json', cards: 'takes/r2v/prompts.json', ran: 'takes/r2v/shots.json', stills: 'takes/r2v/stills.json', qc: 'qc_r2v.json', learn: 'learnings.jsonl', pdq: 'storyboard/panel_dq.json', pcont: 'storyboard/panel_content.json', lines: 'audio/lines/lines.json', placed: 'placed.json' };
function load(unit) {
  if (UNITS[unit]) return UNITS[unit];
  UNITS[unit] = (async () => {
    const idx = await getJSON(unit, '_index.json');
    if (!idx) throw new Error(`no snapshot for ${unit}`);
    const U = { unit, idx, F: new Map(idx.files.map(f => [f.rel, f])) };
    const keys = Object.keys(WANT);
    const got = await Promise.all(keys.map(k => (U.F.get(WANT[k]) || {}).snap ? getJSON(unit, WANT[k]) : null));
    keys.forEach((k, i) => { U[k] = got[i]; });
    const eyeRels = idx.files.filter(f => f.snap && /^(storyboard|takes\/r2v|review)\/eye_[0-9a-f]+\.json$/.test(f.rel)).map(f => f.rel);
    const eyes = await Promise.all(eyeRels.map(r => getJSON(unit, r).then(j => j && Object.assign({ _rel: r }, j))));
    const by = d => eyes.filter(e => e && e._rel.startsWith(d)).sort((a, b) => eyeTime(b) - eyeTime(a));
    U.eyes = { panel: by('storyboard/'), take: by('takes/'), master: by('review/') };
    U.seqs = buildSeqs(U);
    LOADED[unit] = U;
    return U;
  })();
  return UNITS[unit];
}
const eyeTime = e => isoT(e.signed_at || e.reviewed_at || '1970-01-01T00:00:00');
const has = (U, rel) => U.F.has(rel);
const NN = i => pad(i);

/* ------------------------------------------------------------------ joins (one key per shot) */
const planShot = (U, i) => ((U.plan && U.plan.shots) || []).find(s => s.index === i) || (U.plan && U.plan.shots[i]);
const cardOfShot = (U, i) => (U.cards || []).find(c => (c.shots || []).includes(i));
const cardByIndex = (U, k) => (U.cards || []).find(c => c.index === k);
const ranByIndex = (U, k) => (U.ran || []).find(c => c.index === k);
const segOf = (U, i) => U.qc && U.qc.edit ? U.qc.edit.segments.find(s => s.shots.includes(i)) : null;
function gridOfShot(U, i) {
  const row = (U.layout || []).find(r => r.shots.includes(i)); if (!row) return null;
  const name = `${U.unit}_grid_${row.setup}_${row.cols}x${row.rows}${row.tag ? '_' + row.tag : ''}`;
  return { row, name, slot: row.shots.indexOf(i), rel: `storyboard/grids/${name}.png` };
}
function masterRel(U) {
  const r2v = U.F.get('cut/master_r2v.mp4'); if (!r2v) return null;
  const iters = U.idx.files.filter(f => /^cut\/master_iter\d+\.mp4$/.test(f.rel) && f.size === r2v.size).sort((a, b) => b.mtime - a.mtime);
  return iters.length ? iters[0].rel : 'cut/master_r2v.mp4';
}
function shotFaults(U, i) {
  const w = `shot_${NN(i)}`, out = { plan: [], panel: [], master: [] };
  if (U.pv) out.plan = (U.pv.faults || []).filter(f => f.where === w);
  const pe = U.eyes.panel[0]; if (pe) out.panel = (pe.faults || []).filter(f => f.where === w);
  const me = U.eyes.master[0];
  if (me && me.rubric) Object.entries(me.rubric).forEach(([k, r]) => {
    const ev = r.evidence || {};
    (ev.closes || []).filter(c => c.shot === i && (ev.under || []).includes(i)).forEach(c => out.master.push({ kind: k, note: `face h ${c.h} < wall ${c.wall} (${c.size})`, rel: me._rel, path: `.rubric.${k}.evidence` }));
  });
  if (me) (me.faults || []).forEach(f => { const p = planShot(U, i); if (p && (p.faces || []).includes(f.where)) out.master.push({ kind: f.kind, note: `${f.where.replace(/_/g, ' ')}: ${f.note || ''}`, rel: me._rel, path: '.faults' }); });
  return out;
}
const T = k => `T${NN(k)}`;

/* ------------------------------------------------------------------ sequences */
function buildSeqs(U) {
  const V = window.Viewer.urls;
  return [
    { id: 'shots', name: 'Shots', items: shotItems(U, V) },
    { id: 'takes', name: 'Takes', items: takeItems(U, V), extra: failCount(U) },
    { id: 'grids', name: 'Grids', items: gridItems(U, V) },
    { id: 'masters', name: 'Masters', items: masterItems(U, V) },
    { id: 'files', name: 'Files', items: fileItems(U) },
  ];
}
function failCount(U) { const n = U.idx.files.filter(f => /^takes\/r2v\/attempts\/T\d\d_fail\d+\.mp4$/.test(f.rel)).length; return n ? `+${n}` : ''; }
function shotItems(U, V) {
  const mrel = masterRel(U), shots = (U.plan && U.plan.shots) || [];
  return shots.map((p, k) => {
    const i = p.index ?? k, n = NN(i), card = cardOfShot(U, i), seg = segOf(U, i), still = U.stills && U.stills[String(i)];
    const tk = card ? T(card.index) : null, f = shotFaults(U, i), ran = card ? ranByIndex(U, card.index) : null;
    const nf = tk ? U.idx.files.filter(x => new RegExp(`^takes/r2v/attempts/${tk}_fail\\d+\\.mp4$`).test(x.rel)).length : 0;
    const poster = tk && has(U, `takes/work/content/${tk}_1.png`) ? V.thumb(U.unit, `takes/work/content/${tk}_1.png`, 320) : V.thumb(U.unit, `storyboard/shot_${n}.png`, 320);
    const chips = [];
    if (f.master.length) chips.push({ t: `⚑ master ${f.master[0].kind}`, cls: 'flag' });
    if (f.panel.length) chips.push({ t: `⚑ panel ${f.panel.length}`, cls: 'flag' });
    if (f.plan.length) chips.push({ t: `⚑ plan ${f.plan[0].kind}`, cls: 'flag' });
    if (still) chips.push({ t: 'held as a still', cls: 'warn' });
    const t0 = seg ? seg.start / FPS : 0, t1 = seg ? (seg.start + seg.n) / FPS : 0;
    return {
      id: `storyboard/shot_${n}.png`, label: `Shot ${n}`, short: n, shot: i, axis: 'stage', unit: U.unit,
      sub: `${(p.size || '').replace(/_/g, ' ')} · ${p.setup}`, chips, flag: f.master.length > 0,
      layers: [
        { name: 'panel', rel: `storyboard/shot_${n}.png`, alt: p.frame, missing: has(U, `storyboard/shot_${n}.png`) ? null : 'not drawn yet (08 panels)' },
        { name: 'staged', rel: `storyboard/h3/shot_${n}.png`, alt: `staged 768² copy for H3: ${p.frame}`, missing: has(U, `storyboard/h3/shot_${n}.png`) ? null : 'not staged yet' },
        { name: 'take', rel: tk ? `takes/r2v/${tk}.mp4` : `takes/r2v/T${n}.mp4`, poster, alt: p.motion, sub: ran && ran.measured_seconds ? `${ran.measured_seconds} s · try ${nf + 1} of ${nf + 1}` : '', missing: tk && has(U, `takes/r2v/${tk}.mp4`) ? null : card ? `not rendered yet — card ${tk} waits for 09 shoot` : 'no take card' },
        { name: 'master', rel: mrel || 'cut/master_r2v.mp4', poster, seg: seg && mrel ? { src: V.lib(U.unit, mrel), t0, t1 } : null, sub: seg ? `${tc(t0)}–${tc(t1)}${still ? ' · the panel is held, not the take' : ''}` : '', missing: seg && mrel ? null : 'no master yet (11 assemble)' },
      ],
    };
  });
}
function takeItems(U, V) {
  return (U.cards || []).filter(c => has(U, `takes/r2v/${T(c.index)}.mp4`)).map(c => {
    const tk = T(c.index), ran = ranByIndex(U, c.index) || {};
    const fails = U.idx.files.map(f => f.rel.match(new RegExp(`^takes/r2v/attempts/${tk}_fail(\\d+)\\.mp4$`))).filter(Boolean).map(m => +m[1]).sort((a, b) => b - a);
    const poster = has(U, `takes/work/content/${tk}_1.png`) ? V.thumb(U.unit, `takes/work/content/${tk}_1.png`, 320) : null;
    const tries = fails.length + 1, still = U.stills && U.stills[String(c.index)];
    const layers = [{ name: 'kept', rel: `takes/r2v/${tk}.mp4`, poster, sub: `try ${tries} of ${tries}${ran.measured_seconds ? ' · ' + ran.measured_seconds + ' s' : ''}`, alt: (planShot(U, c.shots[0]) || {}).motion }];
    fails.forEach(k => layers.push({ name: `fail${k}`, rel: `takes/r2v/attempts/${tk}_fail${k}.mp4`, sub: `try ${k} of ${tries} · retired · recipe not recorded` }));
    if (has(U, `takes/work/dq/${tk}_head.mp4`)) layers.push({ name: 'head', rel: `takes/work/dq/${tk}_head.mp4`, sub: 'head trim (take_dq)' });
    const teye = U.eyes.take[0], tf = teye ? (teye.faults || []).filter(f => f.where === tk) : [];
    const chips = []; if (tf.length) chips.push({ t: `⚑ ${tf.map(f => f.kind).join(', ')}`, cls: 'flag' }); else if (teye) chips.push({ t: 'EYE_TAKES ✓', cls: 'ok' });
    if (still) chips.push({ t: 'not in the master: still', cls: 'warn' });
    return { id: `takes/r2v/${tk}.mp4`, label: tk, short: tk, shots: c.shots, shot: c.shots[0], axis: 'attempt', unit: U.unit, sub: `shots ${c.shots.map(NN).join(' ')} · ${c.setup}`, chips, badge: fails.length ? `+${fails.length}` : '', flag: tf.length > 0, dur: ran.measured_seconds ? `${ran.measured_seconds}s` : '', layers, strip: poster ? poster.replace('/320/', '/160/') : null };
  });
}
function gridItems(U) {
  const live = U.idx.files.filter(f => /^storyboard\/grids\/[^/]+\.png$/.test(f.rel)).map(f => f.rel);
  const order = (U.layout || []).map(r => `storyboard/grids/${U.unit}_grid_${r.setup}_${r.cols}x${r.rows}${r.tag ? '_' + r.tag : ''}.png`);
  const rels = order.filter(r => live.includes(r)).concat(live.filter(r => !order.includes(r)).sort());
  const old = U.idx.files.filter(f => /^storyboard\/(superseded\/[^/]+|grids\/[^/]+)\/[^/]+\.png$/.test(f.rel));
  return rels.map(rel => {
    const name = rel.split('/').pop().replace('.png', ''), m = name.match(/_grid_(.+?)_(\d+)x(\d+)(?:_(.+))?$/) || [];
    const setup = m[1] || '', row = (U.layout || []).find(r => `${U.unit}_grid_${r.setup}_${r.cols}x${r.rows}${r.tag ? '_' + r.tag : ''}` === name);
    const same = old.filter(f => f.rel.endsWith('/' + name + '.png'));
    const bySetup = old.filter(f => /superseded\//.test(f.rel) && f.rel.split('/').pop().startsWith(`${U.unit}_grid_${setup}_`) && !same.includes(f));
    const revs = same.concat(bySetup).sort((a, b) => b.mtime - a.mtime);
    const f = U.F.get(rel);
    return {
      id: rel, label: `${setup.replace(/_/g, ' ')} ${m[2]}×${m[3]}${m[4] ? ' ' + m[4] : ''}`, short: `${setup.split('_')[0]} ${m[2]}×${m[3]}`, axis: 'revision', unit: U.unit,
      shots: row ? row.shots : [], shot: row ? row.shots[0] : undefined, sub: row ? `shots ${row.shots.map(NN).join(' ')} · ${hm(f.mtime)}` : `not in layout.json · ${hm(f.mtime)}`,
      chips: row ? [] : [{ t: 'not in layout.json', cls: 'warn' }], badge: revs.length ? `+${revs.length}` : '',
      layers: [{ name: 'current', rel, sub: `drawn ${dhm(f.mtime)}` }].concat(revs.map(r => ({ name: r.rel.split('/').slice(-2, -1)[0] + (r.rel.endsWith('/' + name + '.png') ? '' : ' ' + r.rel.split('/').pop().replace(`${U.unit}_grid_${setup}_`, '').replace('.png', '')), rel: r.rel, sub: `superseded · ${dhm(r.mtime)}` }))),
    };
  });
}
function masterItems(U, V) {
  const files = U.idx.files.filter(f => /^cut\/master_(iter\d+|r2v)\.mp4$/.test(f.rel));
  const iters = files.filter(f => /iter/.test(f.rel)).sort((a, b) => +b.rel.match(/iter(\d+)/)[1] - +a.rel.match(/iter(\d+)/)[1]);
  const seen = new Map(), out = [];
  iters.forEach(f => { if (seen.has(f.size)) { seen.get(f.size).also.push(f.rel.match(/iter\d+/)[0]); return; } const x = { f, also: [] }; seen.set(f.size, x); out.push(x); });
  const r2v = files.find(f => /r2v/.test(f.rel)); if (r2v && seen.has(r2v.size)) seen.get(r2v.size).also.push('master_r2v');
  const poster = has(U, 'takes/work/content/T19_1.png') ? V.thumb(U.unit, 'takes/work/content/T19_1.png', 320) : null;
  return out.map(({ f, also }) => {
    const it = f.rel.match(/iter(\d+)/)[1], judged = r2v && f.size === r2v.size;
    return { id: f.rel, label: `v${it}`, short: `v${it}`, unit: U.unit, sub: `iter${it}${also.length ? ' = ' + also.join(' = ') : ''} · ${sz(f.size)} · ${dhm(f.mtime)}`,
      chips: judged ? [{ t: `MASTER ⚑ ${(U.eyes.master[0] && U.eyes.master[0].faults || []).length} · ${U.qc ? U.qc.sha8 : ''}`, cls: 'flag' }] : [{ t: 'no verdict kept', cls: '' }],
      layers: [{ name: 'master', rel: f.rel, poster, sub: judged && U.qc ? `${tc(U.qc.seconds)} · LUFS ${U.qc.lufs}` : 'no QC kept for this iteration' }], strip: poster && poster.replace('/320/', '/160/') };
  });
}
const FILE_ORDER = ['plan.json', 'plan.verdict.json', 'storyboard/layout.json', 'storyboard/panel_dq.json', 'storyboard/panel_content.json', /^storyboard\/eye_/, 'takes/r2v/prompts.json', 'takes/r2v/shots.json', 'takes/r2v/stills.json', /^takes\/r2v\/eye_/, 'qc_r2v.json', /^review\/eye_/, 'review/speaker_check.json', 'audio/lines/lines.json', 'placed.json', 'moves.json', 'heads.json', 'manifest.json', 'youtube.json', 'learnings.jsonl', 'timing.jsonl', 'drive.jsonl', /^drive_run\d+\.log$/];
function fileItems(U) {
  const snap = U.idx.files.filter(f => f.snap), out = [];
  FILE_ORDER.forEach(p => snap.filter(f => (typeof p === 'string' ? f.rel === p : p.test(f.rel))).forEach(f => out.push(f)));
  const items = out.map(f => ({ id: f.rel, label: f.rel.split('/').pop(), short: f.rel.split('/').pop(), unit: U.unit, sub: `${f.rel} · ${sz(f.size)} · ${dhm(f.mtime)}`, layers: [{ rel: f.rel }] }));
  (U.idx.logs || []).forEach(l => items.push({ id: l.rel, label: `run log ${l.run.split('__').pop()}`, short: l.run.split('__').pop(), unit: U.unit, sub: `logs/…/episode/${l.rel.split('/').pop()} · ${sz(l.size)}`, run: l.run, layers: [{ rel: l.rel, kind: 'log', title: l.rel.split('/').pop() }] }));
  return items;
}

/* ------------------------------------------------------------------ pivot (1–5 keep the subject) */
function pivotIn(c, to, s) {
  const all = c.seqs, T2 = all.find(x => x.id === to); if (!T2) return null;
  if (s === undefined) return { index: 0 };
  if (to === 'shots') { const i = T2.items.findIndex(x => x.shot === s); const d = c.seq.id === 'takes' ? 2 : c.seq.id === 'masters' ? 3 : 0; return { index: i, depth: T2.items[i] && !T2.items[i].layers[d].missing ? d : 0 }; }
  if (to === 'takes' || to === 'grids') { const i = T2.items.findIndex(x => (x.shots || []).includes(s)); return i < 0 ? { index: 0, miss: `no ${to === 'takes' ? 'take' : 'grid'} holds shot ${NN(s)}` } : { index: i }; }
  if (to === 'masters') { const sh = all.find(x => x.id === 'shots').items.find(x => x.shot === s), m = sh && sh.layers[3].seg; return { index: 0, t: m ? m.t0 : 0 }; }
  if (to === 'files') { const i = T2.items.findIndex(x => x.id === 'takes/r2v/prompts.json'); const k = c.cards ? c.cards.findIndex(x => x.shots.includes(s)) : -1; return { index: i < 0 ? 0 : i, focus: k >= 0 ? `[${k}]` : null }; }
  return { index: 0 };
}

/* ------------------------------------------------------------------ panel building blocks */
function sec(title, opts = {}) {
  const s = el(opts.fold ? 'details' : 'section', 'pv-sec');
  if (opts.fold) { s.open = !!opts.open; add(s, add(el('summary'), el('h3', '', title), opts.note ? el('span', 'pv-note', opts.note) : null)); }
  else add(s, add(el('div', 'pv-h'), el('h3', '', title), opts.note ? el('span', 'pv-note', opts.note) : null));
  return s;
}
function srcChip(c, rel, path, label) {
  const b = el('button', 'pv-src', label || `${rel.split('/').pop()}${path ? ' ' + path : ''}`); b.type = 'button';
  b.setAttribute('aria-label', `open ${rel}${path ? ' at ' + path : ''}`);
  b.title = `${rel}${path ? ' › ' + path : ''}`;
  b.onclick = () => c.promote(rel, path || null);
  return b;
}
function kv(rows) {
  const dl = el('dl', 'pv-kv');
  rows.filter(Boolean).forEach(([k, v, chip]) => { const dd = el('dd'); if (v instanceof Node) dd.appendChild(v); else if (v !== undefined && v !== null && v !== '') dd.textContent = v; if (v === undefined || v === null || v === '') dd.classList.add('nr'); if (chip) dd.appendChild(chip); dl.append(el('dt', '', k), dd); });
  return dl;
}
function fate(text, cls, chip) { return add(el('p', 'pv-fate ' + (cls || '')), el('span', '', text), chip); }
function faultCard(c, f, judge, rel, path) {
  const a = el('article', 'pv-fault sev-' + (f.severity || 'normal'));
  add(a, add(el('header'), el('b', '', f.kind), el('span', 'pv-sev', f.severity || ''), el('span', 'pv-j', judge), rel ? srcChip(c, rel, path, '↗') : null));
  if (f.note) a.appendChild(el('p', '', f.note));
  if (f.evidence && typeof f.evidence === 'object') {
    const ev = el('dl', 'pv-ev'); Object.entries(f.evidence).slice(0, 6).forEach(([k, v]) => ev.append(el('dt', '', k), el('dd', '', typeof v === 'object' ? JSON.stringify(v).slice(0, 80) : String(v))));
    a.appendChild(ev);
  }
  return a;
}
function groupedFaults(c, faults, judge, rel) {
  /* 531 landmark faults read as "landmark ×19" with each distinct note once and its count */
  const box = el('div', 'pv-groups'), g = new Map();
  faults.forEach((f, k) => { const x = g.get(f.kind) || { n: 0, notes: new Map(), first: k, sev: f.severity }; x.n++; x.notes.set(f.note, (x.notes.get(f.note) || 0) + 1); g.set(f.kind, x); });
  [...g.entries()].sort((a, b) => b[1].n - a[1].n).forEach(([kind, x]) => {
    const a = el('article', 'pv-fault sev-' + (x.sev || 'normal'));
    add(a, add(el('header'), el('b', '', `${kind} ×${x.n}`), el('span', 'pv-j', judge), srcChip(c, rel, null, '↗')));
    const ul = el('ul', 'pv-notes');
    [...x.notes.entries()].sort((p, q) => q[1] - p[1]).slice(0, 8).forEach(([n, k]) => ul.appendChild(add(el('li'), el('span', '', n), k > 1 ? el('b', '', ` ×${k}`) : null)));
    if (x.notes.size > 8) ul.appendChild(el('li', 'more', `+ ${x.notes.size - 8} more distinct notes`));
    a.appendChild(ul); box.appendChild(a);
  });
  return box;
}
function empty(text) { return el('p', 'pv-empty', text); }
function thumbRow(c, refs) {
  const row = el('div', 'pv-refs');
  refs.forEach((r, k) => {
    const b = el('button', 'pv-ref'); b.type = 'button'; b.title = r;
    const im = el('img'); im.alt = ''; im.loading = 'lazy'; im.src = c.urls.thumb(c.unit, r, 160);
    add(b, im, el('span', '', `<Picture ${k + 1}>`), el('small', '', r.split('/').slice(-2).join('/')));
    b.onclick = () => c.openRef(r);
    row.appendChild(b);
  });
  return row;
}
function rawList(c, rows) {
  const box = el('div', 'pv-raw');
  rows.filter(Boolean).forEach(([rel, path, note, U]) => {
    const f = U && U.F.get(rel), b = el('button', 'pv-file'); b.type = 'button';
    add(b, el('span', 'n', rel), el('span', 'm', `${f ? sz(f.size) : 'not on disk'}${path ? ' · ' + path : ''}${note ? ' · ' + note : ''}`));
    if (f) b.onclick = () => c.promote(rel, path || null); else b.disabled = true;
    box.appendChild(b);
  });
  return box;
}

/* ------------------------------------------------------------------ prompt lineage: plan words in / missing from a prompt */
const FIELDS = ['frame', 'motion', 'camera', 'at_rest'];
function toks(s) { const out = []; String(s).replace(/[A-Za-z0-9][A-Za-z0-9'’-]*/g, (w, i) => { out.push({ w: w.toLowerCase(), s: i, e: i + w.length }); return w; }); return out; }
function lcs(a, b) {
  const n = a.length, m = b.length, W = m + 1, dp = new Uint16Array((n + 1) * W);
  for (let i = n - 1; i >= 0; i--) for (let j = m - 1; j >= 0; j--) dp[i * W + j] = a[i].w === b[j].w ? dp[(i + 1) * W + j + 1] + 1 : Math.max(dp[(i + 1) * W + j], dp[i * W + j + 1]);
  const pairs = []; let i = 0, j = 0;
  while (i < n && j < m) { if (a[i].w === b[j].w) { pairs.push([i, j]); i++; j++; } else if (dp[(i + 1) * W + j] >= dp[i * W + j + 1]) i++; else j++; }
  return pairs;
}
function lineage(promptText, plan) {
  const P = toks(promptText), spans = [], missing = {};
  FIELDS.forEach(f => {
    const src = plan && plan[f]; if (!src) return;
    const F = toks(src); if (!F.length) return;
    const pairs = lcs(F, P), runs = []; let cur = null;
    pairs.forEach(([fi, pi]) => { if (cur && fi === cur.f1 + 1 && pi === cur.p1 + 1) { cur.f1 = fi; cur.p1 = pi; cur.n++; } else { cur = { f0: fi, f1: fi, p0: pi, p1: pi, n: 1 }; runs.push(cur); } });
    const kept = runs.filter(r => r.n >= 3), hit = new Set();
    kept.forEach(r => { spans.push({ f, s: P[r.p0].s, e: P[r.p1].e }); for (let k = r.f0; k <= r.f1; k++) hit.add(k); });
    const miss = []; let run = [];
    F.forEach((t, k) => { if (hit.has(k)) { if (run.length) miss.push(run); run = []; } else run.push(t); });
    if (run.length) miss.push(run);
    missing[f] = { arrived: hit.size, of: F.length, phrases: miss.filter(r => r.length >= 2).map(r => src.slice(r[0].s, r[r.length - 1].e)) };
  });
  spans.sort((a, b) => a.s - b.s || b.e - a.e);
  const clean = []; let end = -1; spans.forEach(s => { if (s.s >= end) { clean.push(s); end = s.e; } });
  return { spans: clean, missing };
}
function markedProse(c, text, spans, offset, opts) {
  /* text with lineage marks; inside each run, token chips (<Picture n>) via DocView.chipText — textContent only */
  const box = el('div', 'dv-prose pv-prompt'), DV = window.DocView;
  let at = 0; const local = spans.filter(s => s.e > offset && s.s < offset + text.length).map(s => ({ f: s.f, s: Math.max(0, s.s - offset), e: Math.min(text.length, s.e - offset) }));
  local.forEach(s => {
    if (s.s > at) DV.chipText(box, text.slice(at, s.s), opts);
    const m = el('mark', 'pl pl-' + s.f); m.dataset.field = s.f; m.title = `from plan shot ${s.f}`; DV.chipText(m, text.slice(s.s, s.e), opts); box.appendChild(m); at = s.e;
  });
  if (at < text.length) DV.chipText(box, text.slice(at), opts);
  return box;
}
function promptBlocks(text) {
  /* split "name:\n…" blocks; keeps each block's char offset so lineage spans land */
  const re = /^([a-z_]{4,}):[ \t]*(\n)?/gm, out = []; let m, last = null;
  while ((m = re.exec(text))) { if (last) last.body = text.slice(last.bs, m.index); last = { name: m[1], bs: m.index + m[0].length }; out.push(last); }
  if (last) last.body = text.slice(last.bs); else out.push({ name: 'prompt', bs: 0, body: text });
  return out;
}
function legend() {
  const l = el('div', 'pv-legend');
  FIELDS.forEach(f => l.appendChild(el('span', 'pl pl-' + f, f.replace('_', ' '))));
  l.appendChild(el('span', 'pv-lg-n', 'underline = words that came from the plan shot (runs of ≥ 3)'));
  return l;
}
function missingList(miss, plan, c, U, i) {
  const box = el('div', 'pv-miss');
  FIELDS.filter(f => miss[f]).forEach(f => {
    const m = miss[f], row = el('div', 'pv-mrow');
    add(row, el('span', 'pl pl-' + f, f.replace('_', ' ')), el('span', 'pv-mn', `${m.arrived}/${m.of} words arrived`), srcChip(c, 'plan.json', `.shots[${i}].${f}`, '↗'));
    box.appendChild(row);
    if (m.phrases.length) { const ul = el('ul'); m.phrases.slice(0, 6).forEach(p => ul.appendChild(el('li', '', `“${p}”`))); box.appendChild(ul); }
  });
  return box;
}
function promptView(c, U, text, shotIdx, opts) {
  const plan = planShot(U, shotIdx), L = lineage(text, plan), wrap = el('div');
  wrap.appendChild(legend());
  promptBlocks(text).forEach(b => {
    const open = opts.openBlocks ? opts.openBlocks.includes(b.name) : true;
    const d = el('details', 'pv-pb'); d.open = open;
    add(d, add(el('summary'), el('span', '', b.name.replace(/_/g, ' ')), el('span', 'pv-note', `${b.body.length} chars`)));
    d.appendChild(markedProse(c, b.body, L.spans, b.bs, { refs: opts.refs, thumb: r => c.urls.thumb(c.unit, r, 160), onRef: r => c.openRef(r) }));
    wrap.appendChild(d);
  });
  const ms = sec('Plan words that never reached the prompt', { note: `plan.json shots[${shotIdx}]` });
  ms.appendChild(missingList(L.missing, plan, c, U, shotIdx));
  wrap.appendChild(ms);
  return wrap;
}
function planSection(c, U, i, fold) {
  const p = planShot(U, i), s = sec(`Plan shot ${NN(i)}`, { fold: !!fold, open: !fold, note: p ? `${(p.size || '').replace(/_/g, ' ')} · ${p.setup}` : '' });
  if (!p) { s.appendChild(empty('not in plan.json')); return s; }
  s.appendChild(kv([['size', p.size], ['setup', p.setup], ['faces', (p.faces || []).join(', ') || 'none'], p.extras !== undefined ? ['extras', String(p.extras)] : null, ['path', p.path !== undefined ? String(p.path) : null]]));
  FIELDS.concat('why').forEach(f => { if (!p[f]) return; const b = el('div', 'pv-pf'); add(b, add(el('div', 'pv-pfl'), el('span', 'pl pl-' + f, f.replace('_', ' ')), srcChip(c, 'plan.json', `.shots[${i}].${f}`, '↗')), el('p', '', p[f])); s.appendChild(b); });
  return s;
}

/* ------------------------------------------------------------------ info: panel (storyboard picture) */
async function panelInfo(c, U, i, staged) {
  const n = NN(i), g = gridOfShot(U, i), rel = `storyboard/${staged ? 'h3/' : ''}shot_${n}.png`, pf = U.F.get(`storyboard/shot_${n}.png`);
  const gf = g && U.F.get(g.rel), gjson = g ? await getJSON(U.unit, `storyboard/grids/${g.name}.json`) : null, gtxt = g ? await getText(U.unit, `storyboard/grids/${g.name}.txt`) : null;
  const claims = (await Promise.all(U.idx.files.filter(f => /^storyboard\/grids\/[^/]+\.json$/.test(f.rel)).map(f => getJSON(U.unit, f.rel).then(j => j && (j.shots || []).includes(i) ? f.rel : null)))).filter(Boolean);
  const older = pf && gf && pf.mtime < gf.mtime - 60, twice = claims.length > 1;
  const superseded = g ? U.idx.files.filter(f => f.rel.endsWith('/' + g.name + '.png') && f.rel !== g.rel) : [];
  const f = shotFaults(U, i), card = cardOfShot(U, i);
  const about = el('div', 'pv');
  if (!pf) about.appendChild(fate('Not drawn yet: panels arrive at 08 panels', 'run'));
  else if (older || twice) about.appendChild(fate(`Source uncertain: ${older ? `panel ${hm(pf.mtime)} is older than its grid ${hm(gf.mtime)} (redrawn after the cut)` : ''}${older && twice ? '; ' : ''}${twice ? `${claims.length} live grids claim shot ${n}` : ''}`, 'warn'));
  else about.appendChild(fate(`Cut from ${g ? g.name : 'an unknown grid'}${g ? `, panel ${g.slot + 1}` : ''}${staged ? '; this is the 768² copy staged into H3' : ''}`, 'ok', g ? srcChip(c, `storyboard/grids/${g.name}.txt`, null, 'prompt ↗') : null));
  if (staged && card) about.appendChild(el('p', 'pv-sub', `Staged as <Picture ${(card.refs || []).indexOf(`episodes/${U.unit}/storyboard/h3/shot_${n}.png`) + 1 || '?'}> into ${T(card.index)}`));
  const fs = sec('Faults on this panel', { note: f.panel.length || f.plan.length ? `${f.panel.length + f.plan.length}` : 'none' });
  if (f.plan.length) f.plan.forEach(x => fs.appendChild(faultCard(c, x, 'plan@1', 'plan.verdict.json', '.faults')));
  if (f.panel.length) fs.appendChild(groupedFaults(c, f.panel, (U.eyes.panel[0].signed_by || 'panel_eye').replace('judge:', ''), U.eyes.panel[0]._rel));
  if (!f.plan.length && !f.panel.length) fs.appendChild(empty(U.eyes.panel[0] ? `No judge named a fault on shot ${n} (${U.eyes.panel[0].signed_by}, ${dhm(eyeTime(U.eyes.panel[0]))}).` : `Not judged yet: no storyboard/eye_*.json for ${U.unit}.`));
  about.appendChild(fs);
  const pd = U.pdq && U.pdq.find(x => x.shot === i), pc = U.pcont && U.pcont.find(x => x.shot === i);
  const gs = sec('Panel gates', { note: pd ? (pd.passed ? 'passed' : 'failed') : 'not recorded' });
  gs.appendChild(kv([pd ? ['panel_dq', `faces ${pd.faces} · cast ${pd.cast_faces} · sharp ${pd.sharp} · ink ${pd.ink}${(pd.flags || []).length ? ' · ' + pd.flags.join(', ') : ''}`, srcChip(c, 'storyboard/panel_dq.json', `[${U.pdq.indexOf(pd)}]`, '↗')] : ['panel_dq', null],
    pc ? ['content', `${(pc.subjects || []).join(', ')} · people ${pc.people} · ${pc.hour}${pc.landform ? ' · ' + pc.landform : ''}`, srcChip(c, 'storyboard/panel_content.json', `[${U.pcont.indexOf(pc)}]`, '↗')] : ['content', null]]));
  about.appendChild(gs);
  about.appendChild(planSection(c, U, i, true));
  if (superseded.length) { const ss = sec('Earlier draws of this grid', { fold: true, note: String(superseded.length) }); superseded.forEach(x => ss.appendChild(add(el('p', 'pv-sub'), el('span', '', `${x.rel} · ${dhm(x.mtime)}`)))); about.appendChild(ss); }
  /* prompt: the PANEL k block of the grid .txt, lineage against the plan shot */
  const prompt = el('div', 'pv');
  if (!g || !gtxt) prompt.appendChild(empty(`No grid prompt: shot ${n} is in no layout.json row${g ? '' : ''}.`));
  else {
    const blk = gtxt.split(/\n\s*\n/).find(p => p.startsWith(`PANEL ${g.slot + 1} (`)) || '';
    c.setPromptRel({ rel: `storyboard/grids/${g.name}.txt`, focus: { panel: g.slot + 1 } });
    add(prompt, add(el('div', 'pv-srcline'), el('span', '', `storyboard/grids/${g.name}.txt › PANEL ${g.slot + 1}`), openFull(c, `storyboard/grids/${g.name}.txt`, { panel: g.slot + 1 })));
    if (older) prompt.appendChild(fate('This grid text may not be the draw the panel was cut from (panel older than grid).', 'warn'));
    prompt.appendChild(promptView(c, U, blk, i, { refs: null }));
    const meta = sec('Grid recipe', { fold: true, open: true });
    meta.appendChild(kv([['seed', gjson && String(gjson.seed), srcChip(c, `storyboard/grids/${g.name}.json`, '.seed', '↗')], ['template', gjson && gjson.prompt], ['plan', gjson && (gjson.plan || '').slice(0, 8)], ['drawn_from', gjson && (gjson.drawn_from || '').slice(0, 8)], ['inputs', gjson && (gjson.inputs || '').slice(0, 8)], ['model', null], ['images', '<image1…n> = cast sheets then the place plate (rule; not recorded per grid)']]));
    prompt.appendChild(meta);
    const pre = sec('Grid preamble and image bindings', { fold: true });
    pre.appendChild(window.DocView.prose(gtxt.split(/\n\s*\n/).filter(p => !/^PANEL \d+ \(/.test(p)).join('\n\n')));
    prompt.appendChild(pre);
  }
  const verdict = el('div', 'pv');
  verdict.appendChild(f.panel.length ? groupedFaults(c, f.panel, 'panel_eye@1', U.eyes.panel[0]._rel) : empty('No panel-eye fault on this shot.'));
  if (U.eyes.panel.length) verdict.appendChild(kv([['judge', U.eyes.panel[0].signed_by], ['signed', dhm(eyeTime(U.eyes.panel[0]))], ['verdict', U.eyes.panel[0].verdict], ['terminal', U.eyes.panel[0].terminal]]));
  const raw = rawList(c, [[`storyboard/grids/${g ? g.name : '?'}.txt`, null, 'grid prompt', U], [`storyboard/grids/${g ? g.name : '?'}.json`, null, 'grid manifest', U], ['plan.json', `.shots[${i}]`, '', U], U.eyes.panel[0] ? [U.eyes.panel[0]._rel, '.faults', 'panel eye', U] : null, ['plan.verdict.json', '.faults', '', U], ['storyboard/panel_dq.json', pd ? `[${U.pdq.indexOf(pd)}]` : null, '', U], ['storyboard/panel_content.json', pc ? `[${U.pcont.indexOf(pc)}]` : null, '', U], ['storyboard/layout.json', null, '', U]]);
  return { about, prompt, verdict, raw };
}
function openFull(c, rel, focus) { const b = el('button', 'pv-open', 'Open full ↵'); b.type = 'button'; b.title = 'Move this file onto the stage (Enter); Backspace returns'; b.onclick = () => c.promote(rel, focus); return b; }

/* ------------------------------------------------------------------ info: take */
async function takeInfo(c, U, card, L) {
  const tk = T(card.index), i = card.shots[0], ran = ranByIndex(U, card.index) || {};
  const exists = has(U, `takes/r2v/${tk}.mp4`);
  const [graph, dq, content] = await Promise.all([getJSON(U.unit, `takes/r2v/${tk}.graph.json`), getJSON(U.unit, `takes/r2v/${tk}.dq.json`), getJSON(U.unit, `takes/r2v/${tk}.content.json`)]);
  const node = cls => graph ? Object.entries(graph).filter(([, v]) => v.class_type === cls) : [];
  const runPrompt = node('MiniMaxH3ReferenceToVideo')[0], ranText = runPrompt ? runPrompt[1].inputs.prompt : null;
  const seedRan = node('RandomNoise')[0], still = U.stills && U.stills[String(card.index)], seg = segOf(U, i);
  const fail = L && /^fail/.test(L.name) ? L.name : null;
  const about = el('div', 'pv');
  if (fail) about.appendChild(fate(`Retired render ${fail}: not in the master. No prompt or graph was kept for it (TNN.graph.json is overwritten on retake).`, 'bad'));
  else if (!exists) about.appendChild(fate(`Not rendered yet: card ${tk} waits for 09 shoot`, 'run'));
  else if (still) about.appendChild(fate(`Not in the master: replaced by the still ${still.panel.replace(`episodes/${U.unit}/`, '')} (${still.why})`, 'bad', srcChip(c, 'takes/r2v/stills.json', `["${card.index}"]`, '↗')));
  else if (seg) about.appendChild(fate(`In the master at ${tc(seg.start / FPS)}–${tc((seg.start + seg.n) / FPS)} (frames ${seg.start}–${seg.start + seg.n - 1})`, 'ok', srcChip(c, 'qc_r2v.json', `.edit.segments[${U.qc.edit.segments.indexOf(seg)}]`, '↗')));
  else about.appendChild(fate('Rendered; no master yet', 'run'));
  const pmt = U.F.get('takes/r2v/prompts.json'), plt = U.F.get('plan.json');
  if (!exists && pmt && plt && pmt.mtime < plt.mtime) about.appendChild(fate(`Stale card: prompts.json ${dhm(pmt.mtime)} is older than plan.json ${dhm(plt.mtime)}; the next shoot rewrites it.`, 'warn'));
  const fs = sec(`Faults on ${tk}`);
  const eyes = U.eyes.take, cur = eyes[0];
  const mine = cur ? (cur.faults || []).filter(f => f.where === tk) : [];
  mine.forEach(f => fs.appendChild(faultCard(c, f, `${(cur.signed_by || '').replace('judge:', '')} · ${dhm(eyeTime(cur))}`, cur._rel, `.faults[${cur.faults.indexOf(f)}]`)));
  eyes.slice(1).forEach(e => (e.faults || []).filter(f => f.where === tk).forEach(f => { const a = faultCard(c, f, `superseded · ${dhm(eyeTime(e))}`, e._rel, `.faults[${e.faults.indexOf(f)}]`); a.classList.add('old'); fs.appendChild(a); }));
  card.shots.forEach(s => { const sf = shotFaults(U, s); sf.plan.forEach(f => fs.appendChild(faultCard(c, f, `plan@1 · shot ${NN(s)}`, 'plan.verdict.json', `.faults[${U.pv.faults.indexOf(f)}]`))); sf.master.forEach(f => fs.appendChild(faultCard(c, { kind: f.kind, note: f.note, severity: 'high' }, `master_eye · shot ${NN(s)}`, f.rel, f.path))); });
  if (!fs.querySelector('article')) fs.appendChild(empty(cur ? `No judge named a fault on ${tk} (${cur.signed_by}, ${(cur.files || []).length} files read, signed ${dhm(eyeTime(cur))}).` : `Not judged yet: no takes/r2v/eye_*.json for ${U.unit}.`));
  about.appendChild(fs);
  const inp = sec('Inputs', { note: `${(card.refs || []).length} pictures · ${card.audio}` });
  inp.appendChild(thumbRow(c, card.refs || []));
  const la = node('LoadAudio')[0];
  inp.appendChild(kv([['audio', `${card.audio}${la ? ' → ' + la[1].inputs.audio : ''}`, srcChip(c, `takes/r2v/${tk}.graph.json`, la ? `["${la[0]}"]` : null, '↗')], ['staged as', node('LoadImage').map(([, v]) => v.inputs.image).join(', ') || null]]));
  about.appendChild(inp);
  about.appendChild(modelSection(c, U, tk, card, graph, node, seedRan));
  about.appendChild(planSection(c, U, i, true));
  about.appendChild(attemptsSection(c, U, tk, dq));
  /* prompt: as run (graph) vs as it would run now (prompts.json) */
  const prompt = el('div', 'pv'), k = (U.cards || []).indexOf(card);
  c.setPromptRel({ rel: 'takes/r2v/prompts.json', focus: `[${k}]` });
  const same = ranText && ranText === card.prompt;
  add(prompt, add(el('div', 'pv-srcline'), el('span', '', ranText ? `${tk}.graph.json › node ${runPrompt[0]} .inputs.prompt` : `prompts.json › [${k}].prompt`), openFull(c, ranText ? `takes/r2v/${tk}.graph.json` : 'takes/r2v/prompts.json', ranText ? `["${runPrompt[0]}"].inputs.prompt` : `[${k}]`)));
  prompt.appendChild(fate(ranText ? (same ? 'As run = as it would run now (graph prompt equals prompts.json)' : 'As run differs from prompts.json: the card was rewritten after this render') : exists ? 'As run: not recorded (no graph kept)' : 'Would run now: not rendered yet, so there is no "as run"', ranText ? (same ? 'ok' : 'warn') : 'run'));
  prompt.appendChild(promptView(c, U, ranText || card.prompt, i, { refs: card.refs, openBlocks: ['detailed_description', 'subject_definitions'] }));
  if (ranText && !same) { const w = sec('As it would run now (prompts.json)', { fold: true }); w.appendChild(window.DocView.prose(card.prompt, { refs: card.refs, thumb: r => c.urls.thumb(U.unit, r, 160), onRef: r => c.openRef(r) })); prompt.appendChild(w); }
  const verdict = el('div', 'pv');
  if (dq) {
    verdict.appendChild(fate(`take_dq ${dq.passed ? 'PASS' : 'FAIL'} ${dq.score}/100`, dq.passed ? 'ok' : 'bad', srcChip(c, `takes/r2v/${tk}.dq.json`, '.gates', '↗')));
    const bad = dq.gates.filter(g => g.penalty > 0 || !g.ok || g.hard), clean = dq.gates.length - bad.length;
    const tb = el('table', 'pv-gates'); add(tb, add(el('tr'), el('th', '', 'gate'), el('th', '', 'value'), el('th', '', 'note'), el('th', '', 'pen')));
    bad.forEach(g => add(tb, add(el('tr', g.ok ? (g.penalty ? 'soft' : '') : 'bad'), el('td', '', `${g.name}${g.hard ? ' ·hard' : ''}`), el('td', '', g.value === null ? '—' : String(g.value)), el('td', '', g.note), el('td', '', String(g.penalty)))));
    verdict.appendChild(tb); verdict.appendChild(el('p', 'pv-sub', `${clean} clean gates folded`));
  } else verdict.appendChild(empty(exists ? 'take_dq: not recorded' : 'take_dq: not rendered yet'));
  if (content) verdict.appendChild(kv([['content', `${content.passed ? 'passed' : 'FAILED'} · people ${content.people} · ${content.hour}${content.text ? ' · text!' : ''}${(content.faults || []).length ? ' · ' + content.faults.join(', ') : ''}`, srcChip(c, `takes/r2v/${tk}.content.json`, null, '↗')]]));
  eyes.forEach((e, n) => verdict.appendChild(kv([[n ? 'superseded eye' : 'take eye', `${e.verdict} · ${e.note}`.slice(0, 220), srcChip(c, e._rel, null, e._rel.split('/').pop())]])));
  const raw = rawList(c, [['takes/r2v/prompts.json', `[${k}]`, 'would run now', U], [`takes/r2v/${tk}.graph.json`, null, 'as run', U], ['takes/r2v/shots.json', ran.index !== undefined ? `[${(U.ran || []).indexOf(ran)}]` : null, 'run record', U], [`takes/r2v/${tk}.dq.json`, null, 'take dq', U], [`takes/r2v/${tk}.content.json`, null, 'content read', U], ...eyes.map(e => [e._rel, null, 'take eye', U]), ['plan.json', `.shots[${i}]`, '', U], ['learnings.jsonl', null, 'ladder reasons', U]]);
  return { about, prompt, verdict, raw };
}
function modelSection(c, U, tk, card, graph, node, seedRan) {
  const s = sec('Model and params', { note: graph ? 'from the graph that ran' : 'not rendered: planned values' });
  const chips = el('div', 'pv-chips');
  if (graph) {
    node('UNETLoader').forEach(([, v]) => chips.appendChild(el('span', 'pv-mchip', v.inputs.unet_name.replace(/\.safetensors$/, ''))));
    node('LoraLoaderModelOnly').forEach(([id, v]) => chips.appendChild(el('span', 'pv-mchip lora', `${v.inputs.lora_name.split(/[\\/]/).pop().replace(/\.safetensors$/, '')} × ${v.inputs.strength_model}${id === 'lora_second' ? ' (2nd)' : ''}`)));
    node('CLIPLoader').forEach(([, v]) => chips.appendChild(el('span', 'pv-mchip', v.inputs.clip_name.replace(/\.safetensors$/, ''))));
  } else chips.appendChild(el('span', 'pv-mchip nr', card.model || 'model not recorded'));
  s.appendChild(chips);
  const ran = seedRan ? seedRan[1].inputs.noise_seed : null, d = ran !== null && ran !== card.seed ? ` (planned ${card.seed}, ${ran - card.seed > 0 ? '+' : ''}${ran - card.seed} reseed)` : '';
  const sch = node('BasicScheduler')[0], smp = node('KSamplerSelect')[0], sh = node('MiniMaxH3SigmaShift')[0];
  s.appendChild(kv([['seed', ran !== null ? `${ran}${d}` : `${card.seed} (planned)`, srcChip(c, graph ? `takes/r2v/${tk}.graph.json` : 'takes/r2v/prompts.json', graph && seedRan ? `["${seedRan[0]}"].inputs.noise_seed` : null, '↗')],
    ['steps', sch ? `${sch[1].inputs.steps} · ${sch[1].inputs.scheduler}` : String(card.steps)], ['sampler', smp ? smp[1].inputs.sampler_name : null], ['shift', sh ? `${sh[1].inputs.shift_video} / ${sh[1].inputs.shift_audio}` : null],
    ['size', `${card.width}×${card.height} · ${card.frames} f @ ${card.fps} fps · ${card.seconds} s`]]));
  const cp = el('button', 'pv-open', 'Copy recipe'); cp.type = 'button';
  cp.onclick = () => window.DocView.copyText([`take ${tk} (${U.unit})`, `model ${chips.textContent}`, `seed ${ran ?? card.seed}`, `size ${card.width}x${card.height} ${card.frames}f@${card.fps}`, `refs ${(card.refs || []).join(', ')}`, '', card.prompt].join('\n'), `Copied the ${tk} recipe`, c.toast);
  s.appendChild(cp);
  return s;
}
function attemptsSection(c, U, tk, dq) {
  const fails = U.idx.files.filter(f => new RegExp(`^takes/r2v/attempts/${tk}_fail\\d+\\.mp4$`).test(f.rel)).sort((a, b) => a.rel.localeCompare(b.rel, undefined, { numeric: true }));
  const why = (U.learn || []).filter(l => l.gate === 'EYE_TAKES' && new RegExp(`\\b${tk}\\b`).test(l.note || ''));
  const s = sec('Attempts', { fold: true, open: fails.length > 0, note: fails.length ? `${fails.length} retired` : 'first take kept' });
  if (!fails.length && !why.length) { s.appendChild(empty('First render kept; no ladder row names this take.')); return s; }
  s.appendChild(el('p', 'pv-sub', 'Two honest lists: the files carry no reason and the reasons name no file, so they are not paired.'));
  const a = el('ol', 'pv-list'); fails.forEach(f => { const li = el('li'); const b = el('button', 'pv-link', `${f.rel.split('/').pop()} · rendered ${dhm(f.mtime)}`); b.type = 'button'; b.onclick = () => c.openSeq('takes', x => x.id === `takes/r2v/${tk}.mp4`, 1 + fails.length - +f.rel.match(/fail(\d+)/)[1]); li.appendChild(b); a.appendChild(li); });
  s.appendChild(add(el('div', 'pv-lh'), el('b', '', 'Renders, in order'))); s.appendChild(a);
  const r = el('ol', 'pv-list'); why.forEach(l => { const frag = ((l.note || '').match(new RegExp(`[^;]*\\b${tk}\\b[^;]*`)) || [''])[0].trim(); r.appendChild(add(el('li'), el('span', 'pv-t', dhm(l.ts)), el('span', '', ` rung ${l.attempt} · ${l.action} · ${frag}`))); });
  s.appendChild(add(el('div', 'pv-lh'), el('b', '', 'The ladder said, in order'), srcChip(c, 'learnings.jsonl', null, '↗'))); s.appendChild(why.length ? r : empty('no learnings.jsonl row names this take'));
  if (dq && dq.attempts) s.appendChild(el('p', 'pv-sub', `take_dq scored: ${dq.attempts.map(x => `${x.file} ${x.score}`).join(' · ')}`));
  return s;
}

/* ------------------------------------------------------------------ info: master segment, grid, master, file */
async function segInfo(c, U, i) {
  const seg = segOf(U, i), still = U.stills && U.stills[String(i)], f = shotFaults(U, i), me = U.eyes.master[0];
  const about = el('div', 'pv');
  if (!seg) about.appendChild(fate('No master yet', 'run'));
  else about.appendChild(fate(`${still ? 'Holds the still panel' : `Take T${NN(seg.take)}`} in ${c.layer.rel.split('/').pop()} at ${tc(seg.start / FPS)}–${tc((seg.start + seg.n) / FPS)} · frames ${seg.start}–${seg.start + seg.n - 1}`, still ? 'warn' : 'ok', srcChip(c, 'qc_r2v.json', `.edit.segments[${U.qc.edit.segments.indexOf(seg)}]`, '↗')));
  const fs = sec('Master faults on this shot', { note: me ? `${me.reviewed_by || me.signed_by || 'master_eye'}` : '' });
  f.master.forEach(x => fs.appendChild(faultCard(c, { kind: x.kind, note: x.note, severity: 'high' }, 'master_eye', x.rel, x.path)));
  if (!f.master.length) fs.appendChild(empty(`The master judge named nothing on shot ${NN(i)}.`));
  about.appendChild(fs);
  const ln = (U.lines || []).filter(l => l.shot === i);
  if (ln.length) { const ls = sec('Lines over this shot'); ln.forEach(l => ls.appendChild(kv([[`line ${NN(l.index)}`, `${l.speaker.replace(/_/g, ' ')}: “${l.text}” · heard “${l.heard}” · ${l.passed ? 'passed' : 'FAILED'}`, srcChip(c, 'audio/lines/lines.json', `[${U.lines.indexOf(l)}]`, '↗')]]))); about.appendChild(ls); }
  about.appendChild(planSection(c, U, i, false));
  const card = cardOfShot(U, i);
  const t = card ? await takeInfo(c, U, card, null) : null;
  return { about, prompt: t ? t.prompt : null, verdict: masterVerdict(c, U), raw: rawList(c, [['qc_r2v.json', seg ? `.edit.segments[${U.qc.edit.segments.indexOf(seg)}]` : null, '', U], me ? [me._rel, null, 'master eye', U] : null, ['placed.json', null, 'timeline', U], ['audio/lines/lines.json', null, '', U]]) };
}
function masterVerdict(c, U) {
  const v = el('div', 'pv'), me = U.eyes.master[0], q = U.qc;
  if (q) v.appendChild(kv([['duration', `${tc(q.seconds)} · plan ${tc(q.planned_seconds)}`], ['loudness', `LUFS ${q.lufs} ${q.lufs_ok ? '✓' : '✗'} · peak ${q.true_peak} ${q.tp_ok ? '✓' : '✗'}`], ['cuts', `${(q.planned_cuts || []).length} planned · ${(q.seen_cuts || []).length} seen · missing ${(q.missing_cuts || []).length}`, srcChip(c, 'qc_r2v.json', '.seen_cuts', '↗')], ['QC', q.passed ? 'passed' : 'not passed']]));
  if (!me) { v.appendChild(empty('No master judge file.')); return v; }
  v.appendChild(fate(`${me.reviewed_by || ''} · ${me.terminal || ''} · ${(me.faults || []).length} faults`, (me.faults || []).length ? 'warn' : 'ok', srcChip(c, me._rel, null, '↗')));
  (me.faults || []).forEach((f, k) => v.appendChild(faultCard(c, f, 'master_eye', me._rel, `.faults[${k}]`)));
  const rs = sec('Rubric', { fold: true, open: true });
  Object.entries(me.rubric || {}).forEach(([k, r]) => { const row = add(el('div', 'pv-rub ' + (r.answer === 'y' ? 'y' : 'n')), el('b', '', r.answer === 'y' ? '✓' : '✗'), el('span', '', `${k}: ${r.question || ''}`), srcChip(c, me._rel, `.rubric.${k}`, '↗')); rs.appendChild(row); });
  v.appendChild(rs);
  return v;
}
async function gridInfo(c, U) {
  const it = c.item, L = c.layer, base = L.rel.replace(/\.png$/, ''), name = base.split('/').pop();
  const [gj, gt] = await Promise.all([getJSON(U.unit, base + '.json'), getText(U.unit, base + '.txt')]);
  const f = U.F.get(L.rel), shots = gj ? gj.shots : it.shots || [];
  const about = el('div', 'pv');
  const cur = L.name === 'current';
  const panels = shots.map(i => U.F.get(`storyboard/shot_${NN(i)}.png`)).filter(Boolean), older = panels.filter(p => p.mtime < f.mtime - 60);
  if (!cur) about.appendChild(fate(`Superseded draw (${L.name}) · ${dhm(f.mtime)}`, 'warn'));
  else if (older.length) about.appendChild(fate(`Redrawn after its panels were cut: ${older.length} of ${panels.length} panels are older than this grid; their source is uncertain.`, 'warn'));
  else if (panels.length) about.appendChild(fate(`Live grid: ${panels.length} panels cut from it`, 'ok'));
  else about.appendChild(fate('Live grid: no panels cut yet', 'run'));
  about.appendChild(kv([['setup', gj && gj.setup], ['layout', gj && `${gj.cols} × ${gj.rows}`], ['shots', shots.map(NN).join(' ')], ['seed', gj && String(gj.seed), srcChip(c, base + '.json', '.seed', '↗')], ['template', gj && gj.prompt], ['plan', gj && (gj.plan || '').slice(0, 8)], ['drawn_from', gj && (gj.drawn_from || '').slice(0, 8)], ['inputs', gj && (gj.inputs || '').slice(0, 8)], ['room', gj && gj.room ? JSON.stringify(gj.room).slice(0, 80) : null], ['model', null], ['drawn', dhm(f.mtime)], ['size', sz(f.size)]]));
  if (it.layers.length > 1) { const rv = sec('Revisions (↑ ↓)', { note: String(it.layers.length - 1) }); it.layers.forEach((x, k) => rv.appendChild(add(el('p', 'pv-sub' + (k === c.item.layers.indexOf(L) ? ' cur' : '')), el('span', '', `${x.name} · ${x.rel}`)))); about.appendChild(rv); }
  const ps = sec('Its panels'); const row = el('div', 'pv-refs');
  shots.forEach((i, k) => { const b = el('button', 'pv-ref'); b.type = 'button'; const im = el('img'); im.alt = ''; im.loading = 'lazy'; im.src = c.urls.thumb(U.unit, `storyboard/shot_${NN(i)}.png`, 160); add(b, im, el('span', '', `PANEL ${k + 1}`), el('small', '', `shot ${NN(i)}`)); b.onclick = () => c.openSeq('shots', x => x.shot === i, 0); row.appendChild(b); });
  ps.appendChild(row); about.appendChild(ps);
  const prompt = el('div', 'pv');
  if (gt) { c.setPromptRel({ rel: base + '.txt', focus: null }); add(prompt, add(el('div', 'pv-srcline'), el('span', '', `${base}.txt`), openFull(c, base + '.txt', null))); prompt.appendChild(window.DocView.prose(gt)); }
  else prompt.appendChild(empty(`${name}.txt: not in the snapshot`));
  const verdict = el('div', 'pv'), pe = U.eyes.panel[0];
  if (pe) { const fl = (pe.faults || []).filter(x => shots.some(i => x.where === `shot_${NN(i)}`)); verdict.appendChild(fl.length ? groupedFaults(c, fl, 'panel_eye@1', pe._rel) : empty('No panel-eye fault on these shots.')); }
  else verdict.appendChild(empty('Not judged yet.'));
  return { about, prompt, verdict, raw: rawList(c, [[base + '.txt', null, 'grid prompt', U], [base + '.json', null, 'grid manifest', U], ['storyboard/layout.json', null, '', U], ['timing.jsonl', null, 'grids rows carry the args', U]]) };
}
async function masterInfo(c, U) {
  const it = c.item, about = el('div', 'pv'), judged = /=.*master_r2v/.test(it.sub || '');
  about.appendChild(fate(judged ? 'The delivered master: QC and the master judge describe these bytes' : 'An earlier iteration: no QC or verdict was kept for it', judged ? 'ok' : 'run'));
  about.appendChild(kv([['file', it.layers[0].rel], ['iteration', it.sub]]));
  if (judged && U.F.get('review/contact_' + (U.qc && U.qc.sha8) + '.png')) { const b = el('button', 'pv-open', 'Open the master contact sheet'); b.type = 'button'; b.onclick = () => c.openRef(`episodes/${U.unit}/review/contact_${U.qc.sha8}.png`); about.appendChild(b); }
  return { about, verdict: judged ? masterVerdict(c, U) : null, raw: rawList(c, [['qc_r2v.json', null, judged ? '' : 'describes master_r2v only', U], U.eyes.master[0] ? [U.eyes.master[0]._rel, null, 'master eye', U] : null, ['timing.jsonl', null, '', U], ['manifest.json', null, '', U]]) };
}
function fileInfo(c, U) {
  const L = c.layer, f = U.F.get(L.rel), about = el('div', 'pv'), name = (L.rel || '').split('/').pop();
  const log = (U.idx.logs || []).find(l => l.rel === L.rel);
  about.appendChild(kv([['file', name], ['path', log ? `logs/${U.idx.codex}/episode/${name}` : `episodes/${U.unit}/${L.rel}`], ['size', f ? sz(f.size) : log ? sz(log.size) : null], ['modified', f ? dhm(f.mtime) : null], log ? ['run', log.run] : null, ['source', f && f.snap || log ? 'mockup snapshot (read-only copy)' : 'not snapshotted']]));
  const lines = logLinesNaming(name), s = sec('In the log', { note: lines.length ? `${lines.length} lines name this file` : 'no run log line names it' });
  if (log && window.UnitPage) { const b = el('button', 'pv-open', 'Show this run in Activity'); b.type = 'button'; b.onclick = () => c.jumpLog(() => window.UnitPage.jumpToRun(log.run)); s.appendChild(b); }
  lines.slice(0, 30).forEach(x => { const b = el('button', 'pv-logline lv-' + x.level.toLowerCase()); b.type = 'button'; add(b, el('span', 't', `run #${x.n} · ${hm(x.ts)}`), el('span', 'l', x.level), el('span', 'm', x.msg.split('\n')[0].slice(0, 160))); b.onclick = () => c.jumpLog(() => window.UnitPage && window.UnitPage.jumpToLine(x.k, x.ts)); s.appendChild(b); });
  about.appendChild(s);
  return { about };
}
function logLinesNaming(name) {
  const U = window.UNIT; if (!U || !name) return [];
  const out = [];
  U.runs.forEach((r, k) => (r.log || []).forEach(l => { if ((l.msg || '').includes(name)) out.push({ n: k + 1, k, ts: l.ts, level: l.level, msg: l.msg }); }));
  return out.reverse();
}

/* ------------------------------------------------------------------ related files (promote: "open full") */
function related(c) {
  const it = c.item, L = c.layer, U = c.U;
  if (!U) return [];
  const i = it.shot, card = i !== undefined ? cardOfShot(U, i) : null, tk = card ? T(card.index) : null, g = i !== undefined ? gridOfShot(U, i) : null;
  const out = [];
  const push = (rel, label, focus) => { if (U.F.has(rel) && U.F.get(rel).snap && !out.some(x => x.rel === rel)) out.push({ rel, label, focus }); };
  if (c.seq.id === 'grids') { const b = L.rel.replace(/\.png$/, ''); push(b + '.txt', b.split('/').pop() + '.txt'); push(b + '.json', b.split('/').pop() + '.json'); push('storyboard/layout.json'); }
  if (g) { push(`storyboard/grids/${g.name}.txt`, `${g.name}.txt`, { panel: g.slot + 1 }); push(`storyboard/grids/${g.name}.json`, `${g.name}.json`); }
  if (tk) { push('takes/r2v/prompts.json', 'prompts.json', `[${U.cards.indexOf(card)}]`); push(`takes/r2v/${tk}.graph.json`); push(`takes/r2v/${tk}.dq.json`); push(`takes/r2v/${tk}.content.json`); U.eyes.take.forEach(e => push(e._rel)); }
  if (i !== undefined) { push('plan.json', 'plan.json', `.shots[${i}]`); push('plan.verdict.json'); if (U.eyes.panel[0]) push(U.eyes.panel[0]._rel); push('storyboard/panel_dq.json'); push('storyboard/panel_content.json'); }
  if (c.seq.id === 'masters' || L.name === 'master') { push('qc_r2v.json'); U.eyes.master.forEach(e => push(e._rel)); push('timing.jsonl'); }
  return out.map(x => Object.assign({ label: x.rel.split('/').pop() }, x));
}

/* ------------------------------------------------------------------ register */
function info(c) {
  return load(c.unit).then(U => {
    c.U = U; c.setPromptRel(null);
    const it = c.item, L = c.layer, id = c.seq.id;
    if (id === 'shots') {
      if (L.name === 'take') { const card = cardOfShot(U, it.shot); return card ? takeInfo(c, U, card, L) : { about: empty('No take card names this shot.') }; }
      if (L.name === 'master') return segInfo(c, U, it.shot);
      return panelInfo(c, U, it.shot, L.name === 'staged');
    }
    if (id === 'takes') return takeInfo(c, U, cardByIndex(U, it.shot) || cardOfShot(U, it.shot), L);
    if (id === 'grids') return gridInfo(c, U);
    if (id === 'masters') return masterInfo(c, U);
    return fileInfo(c, U);
  });
}
function boot() {
  window.Viewer.use({
    unit: load,
    info,
    related: c => related(Object.assign({ U: LOADED[c.unit] }, c)),
    pivot: (c, to) => { const U = LOADED[c.unit]; return pivotIn(Object.assign({ cards: U && U.cards }, c), to, c.item.shot !== undefined ? c.item.shot : (c.item.shots || [])[0]); },
  });
  document.dispatchEvent(new Event('prov:ready'));
}
window.Prov = { load, lineage, getJSON, getText, ready: true };
if (window.Viewer) boot(); else document.addEventListener('viewer:ready', boot, { once: true });
})();
