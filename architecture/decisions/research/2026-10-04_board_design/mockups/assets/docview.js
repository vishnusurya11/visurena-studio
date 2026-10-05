/* docview.js — a prompt-aware JSON / JSONL / log / text viewer. No dependency, MIT.
   Four views: Read (prose lifted, verdict header, <Picture n> chips), Table (arrays of like objects,
   JSONL, logs with level facets), Tree (lazy children, previews), Raw (the bytes, tokenised).
   RULE: every value reaches the page through textContent, never innerHTML — prompts carry
   <Subject 1>, <Picture 1>, <image1>, which an HTML parser would silently eat.
   API: DocView.render(host, {text, rel, view, focus, refs, onRef, thumb, toast}) -> controller
        DocView.prose(text, opts) -> element (prose with token chips; used by the info panel)
        DocView.kindOf(rel, text) -> 'json' | 'jsonl' | 'log' | 'textlog' | 'text' */
(function () {
'use strict';

/* ------------------------------------------------------------------ tiny DOM (textContent only) */
function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text !== undefined && text !== null) n.textContent = String(text);
  return n;
}
function add(parent, ...kids) { kids.forEach(k => k && parent.appendChild(k)); return parent; }
function btn(cls, text, title) { const b = el('button', cls, text); b.type = 'button'; if (title) b.title = title; return b; }

/* ------------------------------------------------------------------ pure helpers */
const PROSE_KEYS = new Set(['prompt', 'note', 'notes', 'msg', 'how', 'at_rest', 'motion', 'described', 'frame', 'camera', 'why', 'question', 'text', 'detail']);
const LEAD_KEYS = ['verdict', 'terminal', 'passed', 'score', 'action', 'ok', 'outcome', 'signed_by', 'signed_at', 'reviewed_by', 'reviewed_at', 'lufs_ok', 'tp_ok', 'sha8', 'plan_sha8'];
const GROUP_KEYS = ['kind', 'level', 'gate', 'name', 'step', 'stage', 'action', 'step_id', 'severity', 'section', 'setup', 'where'];
const TOKEN_RE = /<(?:Subject|Picture|Audio|Video) \d+>|<image\d+>/g;

function isProse(key, v) { return typeof v === 'string' && (v.includes('\n') || v.length >= 120 || PROSE_KEYS.has(key)); }
function typeOf(v) { return v === null ? 'null' : Array.isArray(v) ? 'array' : typeof v; }
function isIdent(k) { return /^[A-Za-z_][A-Za-z0-9_]*$/.test(k); }
function jqPath(parts) { return parts.map(p => typeof p === 'number' ? `[${p}]` : isIdent(p) ? `.${p}` : `[${JSON.stringify(p)}]`).join('') || '.'; }
function parsePath(s) {
  const out = []; if (!s || s === '.') return out;
  s.replace(/\.([A-Za-z_][A-Za-z0-9_]*)|\[(\d+)\]|\["((?:[^"\\]|\\.)*)"\]/g, (m, a, b, c) => { out.push(a !== undefined ? a : b !== undefined ? +b : JSON.parse(`"${c}"`)); return m; });
  return out;
}
function getAt(data, parts) { return parts.reduce((o, p) => (o == null ? undefined : o[p]), data); }
function preview(v, n = 80) {
  const t = typeOf(v);
  if (t === 'array') return `[${v.length}]`;
  if (t === 'object') {
    const ks = Object.keys(v), lab = ['name', 'class_type', 'kind', 'step', 'setup', 'index'].find(k => k in v);
    const body = ks.slice(0, 4).map(k => `${k}: ${scalarText(v[k], 24)}`).join(', ');
    return (lab ? `${v[lab]} · ` : '') + `{${body}${ks.length > 4 ? ', …' : ''}}`.slice(0, n);
  }
  return scalarText(v, n);
}
function scalarText(v, n = 80) {
  const t = typeOf(v);
  if (t === 'array') return `[${v.length}]`;
  if (t === 'object') return `{${Object.keys(v).length}}`;
  const s = t === 'string' ? v.replace(/\n/g, ' ⏎ ') : String(v);
  return s.length > n ? s.slice(0, n - 1) + '…' : s;
}
function countNodes(v, cap = 5000) {
  let n = 0; const walk = x => { if (n > cap) return; n++; if (x && typeof x === 'object') for (const k in x) walk(x[k]); };
  walk(v); return n;
}
function likeObjects(a) {
  if (!Array.isArray(a) || a.length < 3) return false;
  const objs = a.filter(x => x && typeof x === 'object' && !Array.isArray(x));
  if (objs.length < a.length * 0.9) return false;
  const k0 = Object.keys(objs[0]); return objs.every(o => k0.filter(k => k in o).length >= Math.min(2, k0.length));
}
function tableCandidates(data) {
  const out = [];
  const walk = (v, parts, depth) => {
    if (depth > 2 || !v || typeof v !== 'object') return;
    if (likeObjects(v)) out.push({ parts, n: v.length });
    if (!Array.isArray(v)) for (const k of Object.keys(v)) walk(v[k], parts.concat(k), depth + 1);
  };
  walk(data, [], 0);
  return out.sort((a, b) => b.n - a.n);
}
function groupKey(rows) {
  for (const k of GROUP_KEYS) {
    const vals = rows.map(r => r && r[k]).filter(v => typeof v === 'string');
    if (vals.length < rows.length * 0.8) continue;
    const distinct = new Set(vals).size;
    if (distinct >= 1 && distinct <= Math.max(8, rows.length / 8) && distinct < rows.length) return k;
  }
  return null;
}
function counts(rows, k) { const m = new Map(); rows.forEach(r => m.set(r[k], (m.get(r[k]) || 0) + 1)); return [...m.entries()].sort((a, b) => b[1] - a[1]); }

/* ------------------------------------------------------------------ kinds and parsing */
function kindOf(rel, text) {
  const r = (rel || '').toLowerCase();
  if (r.endsWith('.jsonl')) return 'jsonl';
  if (r.endsWith('.json')) return 'json';
  if (r.endsWith('.log')) { const first = (text || '').split('\n').find(l => l.trim()); try { const o = JSON.parse(first); if (o && o.level) return 'log'; } catch (e) { /* plain */ } return 'textlog'; }
  return 'text';
}
function parseJsonl(text) { return text.split('\n').filter(l => l.trim()).map((l, i) => { try { return JSON.parse(l); } catch (e) { return { _line: i + 1, _raw: l }; } }); }
function classifyLine(line) {
  if (/^\[drive\]/.test(line)) return /WARNING/.test(line) ? 'WARNING' : 'INFO';
  if (/^warning:/i.test(line)) return 'WARNING';
  if (/^\w*(Error|Exception):/.test(line) || /^error:/i.test(line)) return 'ERROR';
  return 'INFO';
}
function parseTextLog(text) {
  const rows = []; let tb = null;
  text.split('\n').forEach((line, i) => {
    if (/^Traceback /.test(line)) { tb = { level: 'ERROR', msg: line, _n: i + 1, tb: 1 }; rows.push(tb); return; }
    if (tb && (/^\s+/.test(line) || /^\w*(Error|Exception)/.test(line))) { tb.msg += '\n' + line; tb.tb++; if (!/^\s/.test(line)) tb = null; return; }
    tb = null;
    if (line.trim()) rows.push({ level: classifyLine(line), msg: line, _n: i + 1 });
  });
  rows.forEach(r => { if (r.tb) r.msg = `traceback (${r.tb} lines)\n` + r.msg; });
  return rows;
}
function parse(kind, text) {
  if (kind === 'json') return JSON.parse(text);
  if (kind === 'jsonl' || kind === 'log') return parseJsonl(text);
  if (kind === 'textlog') return parseTextLog(text);
  return text;
}
function viewsFor(kind, rel, data) {
  if (kind === 'text') return ['read', 'raw'];
  if (kind === 'log' || kind === 'textlog') return ['table', 'raw'];
  if (kind === 'jsonl') return ['table', 'tree', 'raw'];
  const v = ['read'];
  if (tableCandidates(data).length) v.push('table');
  return v.concat('tree', 'raw');
}
function defaultView(kind, rel, data) {
  if (kind === 'text') return 'read';
  if (kind === 'log' || kind === 'textlog' || kind === 'jsonl') return 'table';
  const r = rel || '';
  if (/prompts\.json$|shots\.json$|verdict\.json$|eye_[0-9a-f]+\.json$|speaker_check\.json$|lines\.json$|stills\.json$|content\.json$/.test(r)) return 'read';
  if (/layout\.json$|panel_dq\.json$|panel_content\.json$/.test(r)) return 'table';
  return 'tree';
}

/* ------------------------------------------------------------------ prose with token chips */
function prose(text, opts = {}) {
  const box = el('div', 'dv-prose');
  String(text).split('\n').forEach((line, i, all) => {
    const head = /^[a-z_]+:$/.test(line.trim()) || /^PANEL \d+ \(/.test(line);
    const ln = el(head ? 'div' : 'span', head ? 'dv-ph' : 'dv-pl');
    if (head && /^PANEL \d+ \(/.test(line)) { const m = line.match(/^(PANEL \d+ \([^)]*\)[^:]*:)(.*)$/); if (m) { add(ln, el('b', '', m[1])); chipText(ln, m[2], opts); } else chipText(ln, line, opts); }
    else chipText(ln, line, opts);
    box.appendChild(ln);
    if (!head && i < all.length - 1) box.appendChild(document.createTextNode('\n'));
  });
  return box;
}
function chipText(parent, text, opts) {
  let last = 0; TOKEN_RE.lastIndex = 0; let m;
  while ((m = TOKEN_RE.exec(text))) {
    if (m.index > last) parent.appendChild(document.createTextNode(text.slice(last, m.index)));
    parent.appendChild(tokenChip(m[0], opts));
    last = m.index + m[0].length;
  }
  if (last < text.length) parent.appendChild(document.createTextNode(text.slice(last)));
}
function tokenChip(tok, opts) {
  const m = tok.match(/<Picture (\d+)>|<image(\d+)>/), n = m ? +(m[1] || m[2]) : 0;
  const ref = n && opts.refs ? opts.refs[n - 1] : null;
  const c = el(ref ? 'button' : 'span', 'dv-tok' + (ref ? ' ref' : ''), tok);
  if (ref) {
    c.type = 'button'; c.title = `${tok} = ${ref}`; c.setAttribute('aria-label', `${tok}, opens ${ref}`);
    if (opts.thumb) { const im = el('img', 'dv-tokthumb'); im.alt = ''; im.loading = 'lazy'; im.src = opts.thumb(ref); c.appendChild(im); }
    c.addEventListener('click', e => { e.stopPropagation(); opts.onRef && opts.onRef(ref, tok); });
  }
  return c;
}

/* ------------------------------------------------------------------ value spans (Tree / Read) */
function valueSpan(v) {
  const t = typeOf(v);
  const cls = t === 'string' ? 'dv-s' : t === 'number' ? 'dv-n' : t === 'boolean' || t === 'null' ? 'dv-l' : 'dv-p';
  return el('span', cls, t === 'string' ? JSON.stringify(v).length > 400 ? `"${v.slice(0, 400)}…"` : JSON.stringify(v) : t === 'array' || t === 'object' ? preview(v) : String(v));
}
function leadCard(data) {
  const keys = LEAD_KEYS.filter(k => data && typeof data === 'object' && !Array.isArray(data) && k in data && typeof data[k] !== 'object');
  if (!keys.length) return null;
  const card = el('div', 'dv-lead');
  keys.forEach(k => {
    const v = data[k], s = String(v), cls = /^(APPROVE|pass|passed|true)$/i.test(s) ? 'ok' : /flag|keep_best|improve|recut/i.test(s) ? 'flag' : /REFUSE|fail|false/i.test(s) ? 'bad' : '';
    add(card, add(el('span', 'dv-chip ' + cls), el('span', 'k', k), el('span', 'v', s)));
  });
  return card;
}

/* ------------------------------------------------------------------ the controller */
function render(host, opts) {
  host.textContent = '';
  const rel = opts.rel || '', text = opts.text ?? '', kind = opts.kind || kindOf(rel, text);
  let data, err = null;
  try { data = parse(kind, text); } catch (e) { err = e; data = text; }
  const views = err ? ['raw'] : viewsFor(kind, rel, data);
  const C = { host, rel, kind, data, text, views, view: null, opts, q: '', hits: [], hi: -1, tableAt: null, filter: null, newest: kind === 'log' || kind === 'textlog', wrap: true };
  const root = host.appendChild(el('div', 'dv'));
  C.root = root;
  C.bar = buildBar(C);
  root.appendChild(C.bar);
  if (err) root.appendChild(el('p', 'dv-err', `Not valid ${kind.toUpperCase()}: ${err.message}. Showing the bytes.`));
  C.body = root.appendChild(el('div', 'dv-body'));
  C.body.tabIndex = 0;
  C.body.setAttribute('role', 'region');
  C.body.setAttribute('aria-label', `${rel.split('/').pop()} contents`);
  C.setView = v => setView(C, v);
  C.search = q => runSearch(C, q);
  C.step = d => stepHit(C, d);
  C.focusPath = p => focusPath(C, p);
  C.copyAll = () => copy(C, text, 'Copied all ' + fmtSize(text.length));
  C.destroy = () => { host.textContent = ''; };
  setView(C, opts.view && views.includes(opts.view) ? opts.view : (err ? 'raw' : defaultView(kind, rel, data)));
  if (opts.focus) focusPath(C, opts.focus);
  return C;
}
function fmtSize(n) { return n < 1024 ? `${n} B` : n < 1048576 ? `${(n / 1024).toFixed(n < 10240 ? 1 : 0)} KB` : `${(n / 1048576).toFixed(1)} MB`; }

function buildBar(C) {
  const bar = el('div', 'dv-bar');
  const seg = el('div', 'dv-views'); seg.setAttribute('role', 'tablist'); seg.setAttribute('aria-label', 'View');
  const NAMES = { read: 'Read', table: 'Table', tree: 'Tree', raw: 'Raw' };
  C.views.forEach(v => { const b = btn('dv-vbtn', NAMES[v]); b.dataset.v = v; b.setAttribute('role', 'tab'); b.onclick = () => setView(C, v); seg.appendChild(b); });
  const find = el('label', 'dv-find');
  const inp = el('input'); inp.type = 'search'; inp.placeholder = 'Find'; inp.setAttribute('aria-label', 'Find in this file');
  const cnt = el('span', 'dv-cnt'); cnt.setAttribute('aria-live', 'polite');
  const up = btn('dv-ib', '↑', 'Previous hit (Shift+Enter)'), dn = btn('dv-ib', '↓', 'Next hit (Enter)');
  let t; inp.addEventListener('input', () => { clearTimeout(t); t = setTimeout(() => runSearch(C, inp.value), 120); });
  inp.addEventListener('keydown', e => {
    if (e.key === 'Enter') { e.preventDefault(); stepHit(C, e.shiftKey ? -1 : 1); }
    else if (e.key === 'Escape' && inp.value) { e.preventDefault(); e.stopPropagation(); inp.value = ''; runSearch(C, ''); }
  });
  up.onclick = () => stepHit(C, -1); dn.onclick = () => stepHit(C, 1);
  add(find, el('span', 'dv-fi', '⌕'), inp, cnt, up, dn);
  C.findInput = inp; C.countEl = cnt;
  const tools = el('div', 'dv-tools');
  const wrap = btn('dv-tb', 'Wrap', 'Soft wrap (raw)'); wrap.setAttribute('aria-pressed', 'true');
  wrap.onclick = () => { C.wrap = !C.wrap; wrap.setAttribute('aria-pressed', String(C.wrap)); C.root.classList.toggle('nowrap', !C.wrap); };
  const all = btn('dv-tb', 'Copy all', 'Copy the file as fetched'); all.onclick = () => C.copyAll();
  const size = el('span', 'dv-size', `${fmtSize(C.text.length)}${Array.isArray(C.data) ? ` · ${C.data.length} rows` : ''}`);
  add(tools, size, wrap, all);
  return add(bar, seg, find, tools);
}

function setView(C, v) {
  C.view = v;
  C.bar.querySelectorAll('.dv-vbtn').forEach(b => b.setAttribute('aria-selected', String(b.dataset.v === v)));
  C.root.dataset.view = v;
  C.body.textContent = '';
  const fn = { read: renderRead, table: renderTable, tree: renderTree, raw: renderRaw }[v];
  fn(C);
  if (C.q) runSearch(C, C.q);
}

/* ------------------------------------------------------------------ Read view */
function renderRead(C) {
  const b = C.body, d = C.data;
  if (C.kind === 'text') return readText(C);
  const lead = leadCard(d); if (lead) b.appendChild(lead);
  if (Array.isArray(d)) { d.forEach((x, i) => b.appendChild(readCard(C, x, [i]))); return; }
  readObject(C, b, d, [], 0, true);
}
function readText(C) {
  const paras = C.text.split(/\n\s*\n/);
  paras.forEach((p, i) => {
    const m = p.match(/^PANEL (\d+) \(/);
    const sec = el('section', 'dv-para' + (m ? ' panel' : i === 0 ? ' pre' : ''));
    if (m) sec.dataset.panel = m[1];
    sec.dataset.path = `para${i}`;
    sec.appendChild(prose(p, C.opts));
    C.body.appendChild(sec);
  });
}
function readCard(C, x, parts) {
  const card = el('section', 'dv-card'); card.dataset.path = jqPath(parts);
  const lab = x && typeof x === 'object' ? ['index', 'name', 'kind', 'shot', 'take'].filter(k => k in x).map(k => `${k} ${scalarText(x[k], 30)}`).join(' · ') : '';
  const h = add(el('header', 'dv-cardh'), el('span', 'dv-cpath', jqPath(parts)), el('span', 'dv-clab', lab));
  card.appendChild(h);
  if (x && typeof x === 'object') readObject(C, card, x, parts, 1, false); else card.appendChild(valueSpan(x));
  return card;
}
function readObject(C, host, obj, parts, depth, top) {
  const grid = el('dl', 'dv-kv'), keys = Object.keys(obj);
  const prosey = keys.filter(k => isProse(k, obj[k])), nested = keys.filter(k => obj[k] && typeof obj[k] === 'object');
  keys.filter(k => !prosey.includes(k) && !nested.includes(k) && !(top && LEAD_KEYS.includes(k))).forEach(k => {
    const row = el('div'); row.dataset.path = jqPath(parts.concat(k));
    add(row, el('dt', '', k), add(el('dd'), valueSpan(obj[k])));
    grid.appendChild(row);
  });
  if (grid.children.length) host.appendChild(grid);
  prosey.forEach(k => host.appendChild(proseBlock(C, k, obj[k], parts.concat(k))));
  nested.forEach(k => host.appendChild(readNested(C, k, obj[k], parts.concat(k), depth)));
}
function proseBlock(C, k, v, parts) {
  const blk = el('div', 'dv-pblock'); blk.dataset.path = jqPath(parts);
  const lab = add(el('div', 'dv-plab'), el('span', '', k), el('span', 'dv-pn', `${v.length.toLocaleString()} chars`));
  const body = prose(v, C.opts);
  blk.appendChild(lab); blk.appendChild(body);
  if (v.length > 1200) {
    body.classList.add('dv-clamp');
    const more = btn('dv-more', `Show all ${v.length.toLocaleString()} characters`); more.setAttribute('aria-expanded', 'false');
    more.onclick = () => { const open = body.classList.toggle('dv-clamp'); more.setAttribute('aria-expanded', String(!open)); more.textContent = open ? `Show all ${v.length.toLocaleString()} characters` : 'Show less'; };
    blk.appendChild(more);
  }
  return blk;
}
function readNested(C, k, v, parts, depth) {
  const sec = el('details', 'dv-sec'); sec.dataset.path = jqPath(parts);
  const sum = add(el('summary'), el('span', 'dv-sk', k), el('span', 'dv-sp', preview(v, 60)));
  sec.appendChild(sum);
  const fill = () => {
    if (sec.dataset.built) return; sec.dataset.built = 1;
    if (likeObjects(v) && v.length > 20) sec.appendChild(groupSummary(C, v, parts));
    else if (Array.isArray(v) && v.every(x => x === null || typeof x !== 'object')) sec.appendChild(el('p', 'dv-inline', v.map(x => scalarText(x, 40)).join(', ')));
    else if (Array.isArray(v)) v.forEach((x, i) => sec.appendChild(readCard(C, x, parts.concat(i))));
    else if (depth < 3) readObject(C, sec, v, parts, depth + 1, false);
    else sec.appendChild(treeRoot(C, v, parts));
  };
  const small = !(Array.isArray(v) && v.length > 20) && depth < 2;
  sec.open = small; if (small) fill();
  sec.addEventListener('toggle', () => sec.open && fill());
  return sec;
}
function groupSummary(C, rows, parts) {
  const k = groupKey(rows), box = el('div', 'dv-groups');
  box.appendChild(el('span', 'dv-glab', `${rows.length} rows${k ? ' by ' + k : ''}`));
  (k ? counts(rows, k) : []).forEach(([v, n]) => {
    const b = btn('dv-gchip', ''); add(b, el('span', '', v), el('b', '', n));
    b.title = `Open Table filtered to ${k} = ${v}`;
    b.onclick = () => { C.tableAt = parts; C.filter = { k, v }; setView(C, 'table'); };
    box.appendChild(b);
  });
  const all = btn('dv-gchip all', 'Table of all'); all.onclick = () => { C.tableAt = parts; C.filter = null; setView(C, 'table'); };
  box.appendChild(all);
  return box;
}

/* ------------------------------------------------------------------ Table view */
function tableRows(C) {
  if (Array.isArray(C.data)) return { rows: C.data, parts: [] };
  const cands = tableCandidates(C.data);
  const at = C.tableAt || (cands[0] && cands[0].parts) || [];
  return { rows: getAt(C.data, at) || [], parts: at, cands };
}
function renderTable(C) {
  const { rows, parts, cands } = tableRows(C), log = C.kind === 'log' || C.kind === 'textlog';
  const head = el('div', 'dv-thead');
  if (cands && cands.length > 1) {
    const sel = el('select', 'dv-tsel'); sel.setAttribute('aria-label', 'Table of');
    cands.forEach(c => { const o = el('option', '', `${jqPath(c.parts)} [${c.n}]`); o.value = JSON.stringify(c.parts); o.selected = jqPath(c.parts) === jqPath(parts); sel.appendChild(o); });
    sel.onchange = () => { C.tableAt = JSON.parse(sel.value); C.filter = null; setView(C, 'table'); };
    head.appendChild(sel);
  } else if (!Array.isArray(C.data)) head.appendChild(el('span', 'dv-tpath', `${jqPath(parts)} [${rows.length}]`));
  const gk = log ? 'level' : groupKey(rows);
  if (gk) counts(rows, gk).forEach(([v, n]) => {
    const on = !C.filter || C.filter.v === v;
    const b = btn('dv-gchip' + (log ? ' lv-' + String(v).toLowerCase() : ''), ''); add(b, el('span', '', v), el('b', '', n));
    b.setAttribute('aria-pressed', String(C.filter ? C.filter.v === v : false)); if (!on) b.classList.add('off');
    b.onclick = () => { C.filter = C.filter && C.filter.v === v ? null : { k: gk, v }; setView(C, 'table'); };
    head.appendChild(b);
  });
  const refused = rows.filter(r => /refused/i.test(String(r.msg || r.note || ''))).length;
  if (refused) head.appendChild(add(el('span', 'dv-gchip refused static'), el('span', '', 'refused'), el('b', '', refused)));
  if (log) { const nf = btn('dv-tb', C.newest ? 'Newest first' : 'Oldest first'); nf.onclick = () => { C.newest = !C.newest; setView(C, 'table'); }; head.appendChild(nf); }
  C.body.appendChild(head);
  let shown = rows.map((r, i) => ({ r, i })).filter(x => !C.filter || x.r[C.filter.k] === C.filter.v);
  if (log && C.newest) shown = shown.reverse();
  const cols = columns(rows, log);
  const tbl = el('table', 'dv-table' + (log ? ' log' : ''));
  const thr = el('tr'); add(tbl, add(el('thead'), thr));
  thr.appendChild(el('th', 'dv-rn', '#'));
  cols.forEach(c => { const th = el('th', '', c); th.scope = 'col'; thr.appendChild(th); });
  const tb = el('tbody'); tbl.appendChild(tb);
  const page = n => shown.slice(n, n + 200).forEach(x => tb.appendChild(tableRow(C, x, cols, parts, log)));
  page(0);
  C.body.appendChild(tbl);
  if (shown.length > 200) {
    let at = 200; const more = btn('dv-more', `Show 200 more of ${shown.length - at}`);
    more.onclick = () => { page(at); at += 200; if (at >= shown.length) more.remove(); else more.textContent = `Show 200 more of ${shown.length - at}`; };
    C.body.appendChild(more);
    C.pageAll = () => { while (at < shown.length) { page(at); at += 200; } more.remove(); };
  } else C.pageAll = null;
}
function columns(rows, log) {
  if (log) return rows[0] && 'ts' in rows[0] ? ['ts', 'level', 'step_id', 'msg'] : ['level', 'msg'];
  const seen = []; rows.slice(0, 400).forEach(r => r && typeof r === 'object' && Object.keys(r).forEach(k => { if (!seen.includes(k)) seen.push(k); }));
  return seen.filter(k => rows.some(r => r && r[k] !== null && r[k] !== undefined && r[k] !== '')).slice(0, 12);
}
const OFF = -7 * 3600;   /* the studio clock, PDT */
function hms(iso) { const t = Date.parse(/Z$|[+-]\d\d:?\d\d$/.test(iso) ? iso : iso + 'Z'); if (isNaN(t)) return String(iso); const d = new Date(t + OFF * 1000); return d.toISOString().slice(11, 19); }
function tableRow(C, x, cols, parts, log) {
  const r = x.r, tr = el('tr', 'dv-row'); tr.dataset.path = jqPath(parts.concat(x.i)); tr.tabIndex = -1;
  if (log) tr.classList.add('lv-' + String(r.level || 'INFO').toLowerCase());
  tr.appendChild(el('td', 'dv-rn', r._n || x.i + (Array.isArray(C.data) && C.kind !== 'json' ? 1 : 0)));
  cols.forEach(c => {
    const v = r ? r[c] : undefined, td = el('td', 'c-' + c.replace(/\W/g, ''));
    if (c === 'ts' && typeof v === 'string') { td.textContent = hms(v); td.title = v; }
    else if (c === 'level') { add(td, el('span', 'dv-lv lv-' + String(v).toLowerCase(), v)); }
    else if (typeof v === 'string' && (isProse(c, v) || v.length > 60)) { td.className += ' dv-tprose'; td.textContent = v.replace(/\s*\n\s*/g, ' ⏎ ').slice(0, 260); td.title = v.slice(0, 600); if (/refused/i.test(v)) td.prepend(el('span', 'dv-out', 'refused')); }
    else if (typeof v === 'string') td.appendChild(el('span', 'dv-s', v));
    else if (v !== undefined) td.appendChild(typeof v === 'object' && v !== null ? el('span', 'dv-p', preview(v, 60)) : valueSpan(v));
    tr.appendChild(td);
  });
  tr.addEventListener('click', e => { if (!e.target.closest('button')) toggleDetail(C, tr, r, cols.length + 1, parts.concat(x.i)); });
  tr.addEventListener('keydown', e => { if (e.key === 'Enter') toggleDetail(C, tr, r, cols.length + 1, parts.concat(x.i)); });
  return tr;
}
function toggleDetail(C, tr, r, span, parts) {
  const nx = tr.nextElementSibling;
  if (nx && nx.classList.contains('dv-detail')) { nx.remove(); tr.classList.remove('open'); return; }
  const d = el('tr', 'dv-detail'), td = el('td'); td.colSpan = span;
  const tools = el('div', 'dv-dtools');
  const cp = btn('dv-tb', 'Copy row as JSON'); cp.onclick = () => copy(C, JSON.stringify(r, null, 2), 'Copied ' + jqPath(parts));
  const cpp = btn('dv-tb', 'Copy path'); cpp.onclick = () => copy(C, jqPath(parts), 'Copied path ' + jqPath(parts));
  add(tools, el('span', 'dv-cpath', jqPath(parts)), cp, cpp);
  td.appendChild(tools);
  if (r && typeof r === 'object') readObject(C, td, r, parts, 1, false); else td.appendChild(valueSpan(r));
  d.appendChild(td); tr.after(d); tr.classList.add('open');
}

/* ------------------------------------------------------------------ Tree view (lazy) */
function renderTree(C) {
  const tree = treeRoot(C, C.data, []);
  C.body.appendChild(tree);
}
function treeRoot(C, v, parts) {
  const ul = el('ul', 'dv-tree'); ul.setAttribute('role', 'tree');
  const big = countNodes(v) > 300;
  if (v && typeof v === 'object') Object.keys(v).forEach((k, i) => ul.appendChild(treeNode(C, Array.isArray(v) ? i : k, v[k], parts.concat(Array.isArray(v) ? i : k), 1, big)));
  else ul.appendChild(treeNode(C, '', v, parts, 1, big));
  ul.addEventListener('keydown', e => treeKeys(C, ul, e));
  const first = ul.querySelector('.dv-tr'); if (first) first.tabIndex = 0;
  return ul;
}
function treeNode(C, k, v, parts, depth, big) {
  const li = el('li'); li.setAttribute('role', 'treeitem'); li.setAttribute('aria-level', depth);
  const row = el('div', 'dv-tr'); row.dataset.path = jqPath(parts); row.tabIndex = -1;
  row.style.setProperty('--d', Math.min(depth - 1, 8));
  const obj = v && typeof v === 'object', n = obj ? Object.keys(v).length : 0;
  const tog = el('span', 'dv-tog', obj && n ? '▸' : ''); tog.setAttribute('aria-hidden', 'true');
  add(row, tog, el('span', 'dv-k', k === '' ? '' : typeof k === 'number' ? String(k) : k), el('span', 'dv-colon', k === '' ? '' : ': '));
  if (obj && Array.isArray(v) && v.length && v.every(x => typeof x === 'number') ) row.appendChild(el('span', 'dv-n', `[${v.length}] ` + v.slice(0, 24).join(', ') + (v.length > 24 ? ', …' : '')));
  else if (obj) row.appendChild(el('span', 'dv-pv', Array.isArray(v) ? `[${v.length}]  ${v.length ? preview(v[0], 70) : ''}` : preview(v, 90)));
  else row.appendChild(isProse(String(k), v) ? el('span', 'dv-s dv-ps', v) : valueSpan(v));
  row.appendChild(copyBtns(C, v, parts));
  li.appendChild(row);
  if (obj && n) {
    li.setAttribute('aria-expanded', 'false');
    const open = !(Array.isArray(v) && v.length > 20) && depth <= (big ? 1 : 2);
    row.addEventListener('click', e => { if (!e.target.closest('.dv-cp')) toggleNode(C, li, v, parts, depth, big); });
    if (open) toggleNode(C, li, v, parts, depth, big);
  }
  return li;
}
function toggleNode(C, li, v, parts, depth, big, force) {
  const open = force !== undefined ? force : li.getAttribute('aria-expanded') !== 'true';
  li.setAttribute('aria-expanded', String(open));
  li.querySelector(':scope > .dv-tr > .dv-tog').textContent = open ? '▾' : '▸';
  let kids = li.querySelector(':scope > ul');
  if (open && !kids) {
    kids = el('ul'); kids.setAttribute('role', 'group');
    Object.keys(v).forEach((k, i) => { const kk = Array.isArray(v) ? i : k; kids.appendChild(treeNode(C, kk, v[k], parts.concat(kk), depth + 1, big)); });
    li.appendChild(kids);
  }
  if (kids) kids.hidden = !open;
}
function treeKeys(C, ul, e) {
  const rows = [...ul.querySelectorAll('.dv-tr')].filter(r => !r.closest('ul[hidden]'));
  const i = rows.indexOf(document.activeElement); if (i < 0) return;
  const li = rows[i].parentNode, mv = j => { const r = rows[Math.max(0, Math.min(rows.length - 1, j))]; rows.forEach(x => x.tabIndex = -1); r.tabIndex = 0; r.focus(); };
  if (e.key === 'ArrowDown') mv(i + 1);
  else if (e.key === 'ArrowUp') mv(i - 1);
  else if (e.key === 'ArrowRight') { if (li.getAttribute('aria-expanded') === 'false') rows[i].click(); else mv(i + 1); }
  else if (e.key === 'ArrowLeft') { if (li.getAttribute('aria-expanded') === 'true') rows[i].click(); else { const up = li.parentNode.closest('li'); if (up) mv(rows.indexOf(up.querySelector('.dv-tr'))); } }
  else if (e.key === 'c' || e.key === 'C') { const p = rows[i].dataset.path, v = getAt(C.data, parsePath(p)); if (e.shiftKey) copy(C, p, 'Copied path ' + p); else copy(C, typeof v === 'string' ? v : JSON.stringify(v, null, 2), 'Copied ' + p); }
  else return;
  e.preventDefault(); e.stopPropagation();
}
function copyBtns(C, v, parts) {
  const box = el('span', 'dv-cp');
  const cv = btn('dv-cpb', 'value', 'Copy value'), cp = btn('dv-cpb', 'path', 'Copy jq path');
  cv.onclick = e => { e.stopPropagation(); copy(C, typeof v === 'string' ? v : JSON.stringify(v, null, 2), 'Copied ' + jqPath(parts)); };
  cp.onclick = e => { e.stopPropagation(); copy(C, jqPath(parts), 'Copied path ' + jqPath(parts)); };
  return add(box, cv, cp);
}

/* ------------------------------------------------------------------ Raw view */
const RAW_RE = /"(?:\\.|[^"\\])*"(?=\s*:)|"(?:\\.|[^"\\])*"|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|\btrue\b|\bfalse\b|\bnull\b|[{}[\],:]/g;
function renderRaw(C) {
  const pre = el('div', 'dv-raw'), json = C.kind === 'json' || C.kind === 'jsonl' || C.kind === 'log';
  const lines = C.text.split('\n');
  const cap = Math.min(lines.length, 20000);
  for (let i = 0; i < cap; i++) {
    const ln = el('div', 'dv-ln'); ln.dataset.line = i + 1;
    ln.appendChild(el('span', 'dv-g', i + 1));
    const code = el('span', 'dv-c');
    if (json) tokenise(code, lines[i].length > 4000 ? lines[i].slice(0, 4000) + ' …' : lines[i]); else code.textContent = lines[i];
    ln.appendChild(code); pre.appendChild(ln);
  }
  C.body.appendChild(pre);
}
function tokenise(code, line) {
  let last = 0, m; RAW_RE.lastIndex = 0;
  while ((m = RAW_RE.exec(line))) {
    if (m.index > last) code.appendChild(document.createTextNode(line.slice(last, m.index)));
    const t = m[0], after = line.slice(m.index + t.length);
    const cls = t[0] === '"' ? (/^\s*:/.test(after) ? 'dv-k' : 'dv-s') : /^[{}[\],:]$/.test(t) ? 'dv-p' : /^(true|false|null)$/.test(t) ? 'dv-l' : 'dv-n';
    code.appendChild(el('span', cls, t)); last = m.index + t.length;
  }
  if (last < line.length) code.appendChild(document.createTextNode(line.slice(last)));
}

/* ------------------------------------------------------------------ focus a path / line / panel */
function focusPath(C, f) {
  const p = typeof f === 'string' ? f : f && f.path;
  if (f && f.panel) return flash(C, C.body.querySelector(`[data-panel="${f.panel}"]`));
  if (f && f.line) { if (C.view !== 'raw') setView(C, 'raw'); return flash(C, C.body.querySelector(`[data-line="${f.line}"]`)); }
  if (f && f.match) return focusMatch(C, f.match);
  if (!p) return;
  if (C.view === 'tree') { expandTo(C, parsePath(p)); return flash(C, C.body.querySelector(`.dv-tr[data-path="${cssq(p)}"]`)); }
  if (C.view === 'table') { const r = C.body.querySelector(`tr[data-path="${cssq(p)}"]`); if (r) { flash(C, r); return; } }
  let node = C.body.querySelector(`[data-path="${cssq(p)}"]`);
  if (!node) { const parts = parsePath(p); while (parts.length && !node) { parts.pop(); node = C.body.querySelector(`[data-path="${cssq(jqPath(parts))}"]`); } }
  if (node && node.tagName === 'DETAILS') node.open = true;
  flash(C, node);
}
function focusMatch(C, needle) {
  const rows = [...C.body.querySelectorAll('tr.dv-row, .dv-ln')];
  const r = rows.find(x => x.textContent.includes(needle));
  if (r) flash(C, r);
}
function cssq(s) { return s.replace(/["\\]/g, '\\$&'); }
function expandTo(C, parts) {
  for (let i = 1; i <= parts.length; i++) {
    const row = C.body.querySelector(`.dv-tr[data-path="${cssq(jqPath(parts.slice(0, i)))}"]`);
    if (!row) return;
    const li = row.parentNode;
    if (i < parts.length && li.getAttribute('aria-expanded') === 'false') row.click();
  }
}
function flash(C, node) {
  if (!node) return;
  C.body.querySelectorAll('.dv-focus').forEach(n => n.classList.remove('dv-focus'));
  node.classList.add('dv-focus');
  requestAnimationFrame(() => node.scrollIntoView({ block: 'center' }));
}

/* ------------------------------------------------------------------ search (n of m) */
function clearMarks(C) {
  C.body.querySelectorAll('mark.dv-hit').forEach(m => { const t = document.createTextNode(m.textContent); m.replaceWith(t); });
  C.body.normalize();
  C.hits = []; C.hi = -1;
}
function runSearch(C, q) {
  C.q = q = (q || '').trim();
  clearMarks(C);
  C.root.classList.toggle('searching', q.length >= 2);
  if (q.length < 2) { C.countEl.textContent = ''; return; }
  if (C.pageAll) C.pageAll();
  if (C.view === 'tree') expandForSearch(C, q);
  C.body.querySelectorAll('details.dv-sec:not([open])').forEach(d => { if (d.textContent.toLowerCase().includes(q.toLowerCase())) d.open = true; });
  const walker = document.createTreeWalker(C.body, NodeFilter.SHOW_TEXT, { acceptNode: n => n.parentNode.closest('.dv-cp,.dv-g,button,select') ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT });
  const nodes = []; while (walker.nextNode()) nodes.push(walker.currentNode);
  const lq = q.toLowerCase();
  nodes.forEach(n => {
    const t = n.nodeValue, lt = t.toLowerCase(); let i = lt.indexOf(lq); if (i < 0) return;
    const frag = document.createDocumentFragment(); let last = 0;
    while (i >= 0) { frag.appendChild(document.createTextNode(t.slice(last, i))); const m = el('mark', 'dv-hit', t.slice(i, i + q.length)); frag.appendChild(m); C.hits.push(m); last = i + q.length; i = lt.indexOf(lq, last); }
    frag.appendChild(document.createTextNode(t.slice(last))); n.replaceWith(frag);
  });
  C.countEl.textContent = C.hits.length ? `1 of ${C.hits.length}` : '0 of 0';
  if (C.hits.length) stepHit(C, 1, 0);
}
function expandForSearch(C, q) {
  const lq = q.toLowerCase(), paths = [];
  const walk = (v, parts) => {
    if (paths.length > 400) return;
    if (v && typeof v === 'object') { for (const k of Object.keys(v)) { const kk = Array.isArray(v) ? +k : k; if (String(k).toLowerCase().includes(lq)) paths.push(parts.concat(kk)); walk(v[k], parts.concat(kk)); } }
    else if (String(v).toLowerCase().includes(lq)) paths.push(parts);
  };
  walk(C.data, []);
  paths.forEach(p => expandTo(C, p));
}
function stepHit(C, d, abs) {
  if (!C.hits.length) return;
  if (C.hi >= 0) C.hits[C.hi].classList.remove('cur');
  C.hi = abs !== undefined ? abs : (C.hi + d + C.hits.length) % C.hits.length;
  const m = C.hits[C.hi]; m.classList.add('cur');
  const clamp = m.closest('.dv-clamp'); if (clamp) clamp.classList.remove('dv-clamp');
  m.scrollIntoView({ block: 'center' });
  C.countEl.textContent = `${C.hi + 1} of ${C.hits.length}`;
}

/* ------------------------------------------------------------------ copy */
function copy(C, text, msg) {
  const done = () => C.opts.toast && C.opts.toast(msg);
  if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(text).then(done, () => fallbackCopy(text, done));
  else fallbackCopy(text, done);
}
function fallbackCopy(text, done) {
  const ta = el('textarea'); ta.value = text; ta.style.cssText = 'position:fixed;opacity:0';
  (document.querySelector('dialog[open]') || document.body).appendChild(ta); ta.select();
  try { document.execCommand('copy'); } catch (e) { /* nothing */ }
  ta.remove(); done();
}

window.DocView = { render, prose, kindOf, parse, jqPath, parsePath, getAt, preview, fmtSize, hms, chipText, copyText: (text, msg, toast) => copy({ opts: { toast } }, text, msg) };
})();
