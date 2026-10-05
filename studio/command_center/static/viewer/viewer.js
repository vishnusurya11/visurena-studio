/* viewer.js — the universal in-page Viewer (SPEC_v3). No dependency, MIT.
   One <dialog id="viewer"> per page = a cursor (sequence, index, depth) + a renderer per kind
   (image · video · JSON/doc · log/text) + an info panel that says why the item looks the way it does.
   Public API:
     Viewer.open({seq, items, index, seqs, depth, focus, opener, unit, panel, tab})
     Viewer.openUnit(unit, {seq, id, rel, shot, depth, focus, opener})   (needs a provider: Viewer.use)
     Viewer.use({unit(ep), info(ctx), related(ctx), pivot(ctx, seqId)})
     Viewer.action(name, {key, label, applies, choices, note, submit})    (e.g. R = redo this shot)
     [data-view] elements anywhere: data-view = rel path, data-set = sequence, data-kind, data-unit,
     data-depth, data-path (focus inside a doc), data-src / data-thumb for non-unit pictures,
     data-codex (else <body data-codex>) for the book.
   Board port: pictures from /thumb/{codex}/{160|320}/{path} then the 1024 WebP (the original behind a link); video and
   originals from /lib; JSON from /json; logs from /log; a unit's sequences from /viewer (prov.js). */
(function () {
'use strict';
if (window.Viewer) return;
const FPS = 24;
const PLACE = {};          /* unit -> {codex, home}: set by the provider from /viewer/<codex>/<stage>/<unit>.json */
const VER = new Map();     /* '<codex>/<book rel>' -> mtime: /thumb answers are immutable, so a redraw is a new URL */
let CUR_CODEX = null;      /* the book of the page or of the element that opened the Viewer */
function codexOf(unit) { return (unit && PLACE[unit] && PLACE[unit].codex) || CUR_CODEX || (document.body && document.body.dataset.codex) || ''; }
const IC = {
  x: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
  left: '<path d="m15 18-6-6 6-6"/>', right: '<path d="m9 18 6-6-6-6"/>',
  back: '<path d="m12 19-7-7 7-7"/><path d="M19 12H5"/>',
  info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
  braces: '<path d="M8 3H7a2 2 0 0 0-2 2v5a2 2 0 0 1-2 2 2 2 0 0 1 2 2v5c0 1.1.9 2 2 2h1"/><path d="M16 21h1a2 2 0 0 0 2-2v-5c0-1.1.9-2 2-2a2 2 0 0 1-2-2V5a2 2 0 0 0-2-2h-1"/>',
  copy: '<rect width="14" height="14" x="8" y="8" rx="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>',
  ext: '<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
  image: '<rect width="18" height="18" x="3" y="3" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/>',
  film: '<rect width="18" height="18" x="3" y="3" rx="2"/><path d="M7 3v18"/><path d="M3 7.5h4"/><path d="M3 12h18"/><path d="M3 16.5h4"/><path d="M17 3v18"/><path d="M17 7.5h4"/><path d="M17 16.5h4"/>',
  log: '<path d="M15 12h-5"/><path d="M15 8h-5"/><path d="M19 17V5a2 2 0 0 0-2-2H4"/><path d="M8 21h12a2 2 0 0 0 2-2v-1a1 1 0 0 0-1-1H11a1 1 0 0 0-1 1v1a2 2 0 1 1-4 0V5a2 2 0 1 0-4 0v2a1 1 0 0 0 1 1h3"/>',
  text: '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>',
  audio: '<path d="M2 10v3"/><path d="M6 6v11"/><path d="M10 3v18"/><path d="M14 8v7"/><path d="M18 5v13"/><path d="M22 10v3"/>',
  play: '<polygon points="6 3 20 12 6 21 6 3"/>', pause: '<rect x="14" y="4" width="4" height="16" rx="1"/><rect x="6" y="4" width="4" height="16" rx="1"/>',
  vol: '<path d="M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"/><path d="M16 9a5 5 0 0 1 0 6"/>',
  mute: '<path d="M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"/><line x1="22" x2="16" y1="9" y2="15"/><line x1="16" x2="22" y1="9" y2="15"/>',
  loop: '<path d="m17 2 4 4-4 4"/><path d="M3 11v-1a4 4 0 0 1 4-4h14"/><path d="m7 22-4-4 4-4"/><path d="M21 13v1a4 4 0 0 1-4 4H3"/>',
  zoom: '<circle cx="11" cy="11" r="8"/><line x1="21" x2="16.65" y1="21" y2="16.65"/><line x1="11" x2="11" y1="8" y2="14"/><line x1="8" x2="14" y1="11" y2="11"/>',
  redo: '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>',
  keys: '<path d="M10 8h.01"/><path d="M12 12h.01"/><path d="M14 8h.01"/><path d="M16 12h.01"/><path d="M18 8h.01"/><path d="M6 8h.01"/><path d="M7 16h10"/><path d="M8 12h.01"/><rect width="20" height="16" x="2" y="4" rx="2"/>',
  panel: '<rect width="18" height="18" x="3" y="3" rx="2"/><path d="M15 3v18"/>',
  more: '<circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/>',
  flag: '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" x2="4" y1="22" y2="15"/>',
  check: '<path d="M20 6 9 17l-5-5"/>',
};
const icoHTML = (n, c = '') => `<svg class="vi ${c}" viewBox="0 0 24 24" aria-hidden="true">${IC[n] || ''}</svg>`;   /* static strings only */
const KIND_IC = { image: 'image', video: 'film', audio: 'audio', doc: 'braces', log: 'log', text: 'text' };
const $ = (s, r) => (r || document).querySelector(s);
const $$ = (s, r) => [...(r || document).querySelectorAll(s)];
function el(tag, cls, text) { const n = document.createElement(tag); if (cls) n.className = cls; if (text !== undefined && text !== null) n.textContent = String(text); return n; }
function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } return null; }
const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
const phone = () => matchMedia('(max-width: 640px)').matches;

/* ------------------------------------------------------------------ URLs + item normalisation */
function libRel(unit, rel) { return !unit || /^(episodes|refs)\//.test(rel) ? rel : `${(PLACE[unit] && PLACE[unit].home) || 'episodes/' + unit}/${rel}`; }
function thumbUrl(unit, rel, w) {
  const c = codexOf(unit), b = libRel(unit, rel), v = VER.get(`${c}/${b}`);
  return `/thumb/${c}/${(w || 320) >= 1024 ? 1024 : (w || 320) <= 160 ? 160 : 320}/${b}${v ? '?v=' + v : ''}`;
}
function docUrl(unit, rel) {
  /* a run log (_logs/<name>) or a .log of the book -> /log; JSON/JSONL -> /json (2 MB cap, slices); text -> /lib */
  const c = codexOf(unit);
  if (/^_logs\//.test(rel)) return `/log/${c}/${rel.slice(6)}`;
  const b = libRel(unit, rel);
  if (/\.log$/i.test(b)) return `/log/${c}/${b}`;
  return /\.jsonl?$/i.test(b) ? `/json/${c}/${b}` : `/lib/${c}/${b}`;
}
const URLS = {
  lib: (unit, rel) => `/lib/${codexOf(unit)}/${libRel(unit, rel)}`,
  thumb: thumbUrl,
  data: docUrl,
};
function kindOfRel(rel) {
  const r = (rel || '').toLowerCase().split('#')[0];
  if (/\.(png|jpe?g|webp|gif)$/.test(r)) return 'image';
  if (/\.(mp4|webm|mov)$/.test(r)) return 'video';
  if (/\.(wav|mp3|m4a|ogg)$/.test(r)) return 'audio';
  if (/\.log$/.test(r)) return 'log';
  if (/\.txt$/.test(r)) return 'text';
  return 'doc';
}
function normLayer(L, item) {
  const unit = L.unit || item.unit, kind = L.kind || kindOfRel(L.rel);
  const out = Object.assign({ unit, kind, name: L.name || '' }, L);
  const book = !!codexOf(unit);
  if (!out.src && out.rel) out.src = !book ? out.rel : kind === 'doc' || kind === 'log' || kind === 'text' ? URLS.data(unit, out.rel) : kind === 'image' && book ? URLS.thumb(unit, out.rel, 1024) : URLS.lib(unit, out.rel);
  if (!out.thumb && kind === 'image' && out.rel && book) out.thumb = URLS.thumb(unit, out.rel, 320);
  out.kind = kind;
  return out;
}
function normItem(it, unit) {
  const item = Object.assign({ unit: it.unit || unit }, it);
  item.layers = (it.layers || [it]).map(L => normLayer(L, item)); item._norm = true;
  item.id = item.id || item.layers[0].rel || item.label;
  item.label = item.label || (item.layers[0].rel || '').split('/').pop();
  return item;
}

/* ------------------------------------------------------------------ state */
const S = { seqs: [], si: 0, ii: 0, depth: 0, unit: null, opener: null, pushed: false, ignorePop: false, stack: [], zoom: false,
  panel: ['0', '360', '50', 'full'].includes(store('vw.panel')) ? store('vw.panel') : '0', lastPanel: '360', tab: 'about', sheet: 0, keys: false, dir: 1, loadTok: 0, doc: null, focus: null, note: null, noteDirty: false, escArm: false };
let D = null, V = null, provider = null;
const ACTIONS = {};
const cache = new Map();
const pageVideos = new Map();
const seq = () => S.seqs[S.si] || { items: [] };
const item = () => seq().items[S.ii];
const layer = () => { const it = item(); return it ? it.layers[Math.min(S.depth, it.layers.length - 1)] : null; };

/* ------------------------------------------------------------------ build the dialog once */
function mount() {
  if (D) return D;
  D = document.getElementById('viewer');
  if (!D) { D = document.createElement('dialog'); D.id = 'viewer'; document.body.appendChild(D); }
  D.className = 'vw';
  D.setAttribute('aria-labelledby', 'vw-title');
  D.innerHTML = TEMPLATE;
  V = D.querySelector('video.vw-video');
  wireDialog();
  return D;
}
const TEMPLATE = `
<div class="vw-shell">
 <header class="vw-top">
  <button class="vw-ib vw-back" type="button" data-act="back" aria-label="Back to the item you came from" aria-keyshortcuts="Backspace" hidden>${icoHTML('back')}</button>
  <div class="vw-ttl"><span class="vw-kind" aria-hidden="true"></span><h2 id="vw-title"></h2><span class="vw-path"></span></div>
  <div class="vw-tabs" role="tablist" aria-label="Sequences"></div>
  <div class="vw-pos"><button class="vw-ib" type="button" data-act="prev" aria-label="Previous item" aria-keyshortcuts="ArrowLeft">${icoHTML('left')}</button><span class="vw-count" aria-hidden="true"></span><button class="vw-ib" type="button" data-act="next" aria-label="Next item" aria-keyshortcuts="ArrowRight">${icoHTML('right')}</button></div>
  <div class="vw-switch" role="group" aria-label="Beside the picture"><button type="button" data-sw="pic" aria-pressed="true">Picture</button><button type="button" data-sw="prompt" aria-keyshortcuts="P" aria-pressed="false">Prompt</button><button type="button" data-sw="json" aria-pressed="false">JSON</button></div>
  <div class="vw-acts">
   <button class="vw-ib vw-redo" type="button" data-act="redo" aria-keyshortcuts="R" hidden>${icoHTML('redo')}<span>Redo</span></button>
   <button class="vw-ib" type="button" data-act="info" aria-label="Info panel" aria-keyshortcuts="I" aria-pressed="false">${icoHTML('panel')}</button>
   <button class="vw-ib" type="button" data-act="copy" aria-label="Copy the relative path" aria-keyshortcuts="C">${icoHTML('copy')}</button>
   <a class="vw-ib" data-act="orig" target="_blank" rel="noopener" aria-label="Open the original in a new tab" aria-keyshortcuts="O">${icoHTML('ext')}</a>
   <button class="vw-ib" type="button" data-act="keys" aria-label="Keys" aria-keyshortcuts="?">${icoHTML('keys')}</button>
   <button class="vw-close" type="button" data-act="close" aria-label="Close" aria-keyshortcuts="Escape">${icoHTML('x')}<span class="kbd2">Esc</span></button>
  </div>
 </header>
 <div class="vw-body">
  <section class="vw-stage" tabindex="-1" aria-roledescription="viewer stage">
   <div class="vw-cap"><span class="vw-subj"></span><span class="vw-dots" role="group" aria-label="Depth"></span></div>
   <div class="vw-media">
    <div class="vw-pic" hidden><img class="vw-lo" alt="" decoding="async"><img class="vw-hi" alt="" decoding="async"></div>
    <div class="vw-vid" hidden><div class="vw-vbox"><img class="vw-poster" alt=""><video class="vw-video" playsinline preload="metadata"></video><button class="vw-bigplay" type="button" aria-label="Play">${icoHTML('play')}</button></div>
     <div class="vw-vbar">
      <button class="vw-ib" type="button" data-v="play" aria-label="Play or pause" aria-keyshortcuts="Space K">${icoHTML('play')}</button>
      <span class="vw-tc" aria-live="off">0:00.00</span>
      <input class="vw-scrub" type="range" min="0" max="1000" value="0" step="1" aria-label="Seek">
      <button class="vw-tb" type="button" data-v="speed" aria-label="Speed" aria-keyshortcuts="&lt; &gt;">1×</button>
      <button class="vw-ib" type="button" data-v="loop" aria-label="Loop" aria-keyshortcuts="O" aria-pressed="false">${icoHTML('loop')}</button>
      <button class="vw-ib" type="button" data-v="mute" aria-label="Sound" aria-keyshortcuts="M" aria-pressed="false">${icoHTML('vol')}</button>
      <span class="vw-src" role="group" aria-label="Source"><button type="button" data-v="take" aria-keyshortcuts="T">Take</button><button type="button" data-v="master" aria-keyshortcuts="T">In master</button></span>
     </div></div>
    <div class="vw-doc" hidden></div>
    <div class="vw-empty" hidden></div>
   </div>
   <button class="vw-edge prev" type="button" data-act="prev" aria-label="Previous item" tabindex="-1">${icoHTML('left')}</button>
   <button class="vw-edge next" type="button" data-act="next" aria-label="Next item" tabindex="-1">${icoHTML('right')}</button>
   <form class="vw-note" hidden><div class="vw-note-h"><b class="vw-note-t"></b><span class="vw-note-c"></span></div><textarea aria-label="Note"></textarea><div class="vw-note-f"><button class="vw-tb pri" type="submit">Queue ↵</button><button class="vw-tb" type="button" data-note="cancel">Cancel</button><span class="vw-note-w" role="status"></span></div></form>
   <div class="vw-keys" hidden></div>
  </section>
  <div class="vw-seam" role="separator" tabindex="0" aria-orientation="vertical" aria-label="Resize the info panel" aria-valuemin="0" aria-valuemax="100"></div>
  <aside class="vw-panel" role="complementary" aria-label="About this item">
   <div class="vw-grab" aria-hidden="true"></div>
   <div class="vw-ptabs" role="tablist" aria-label="Info"><button type="button" role="tab" data-tab="about">About</button><button type="button" role="tab" data-tab="prompt">Prompt</button><button type="button" role="tab" data-tab="verdict">Verdict</button><button type="button" role="tab" data-tab="raw">Raw</button><span class="vw-psp"></span><button class="vw-ib" type="button" data-act="pfull" aria-label="Panel full width">${icoHTML('panel')}</button><button class="vw-ib" type="button" data-act="info" aria-label="Close the panel">${icoHTML('x')}</button></div>
   <div class="vw-pbody" tabindex="0"></div>
  </aside>
 </div>
 <footer class="vw-strip" role="listbox" aria-label="Items"></footer>
 <div class="vw-live" aria-live="polite"></div>
 <div class="vw-toast" role="status" hidden></div>
</div>`;

/* ------------------------------------------------------------------ open / close */
function open(o) {
  mount();
  const unit = o.unit || null;
  if (o.codex) CUR_CODEX = o.codex;
  if (o.seqs) { S.seqs = o.seqs; S.si = Math.max(0, o.seqs.findIndex(s => s.id === o.seq)); }
  else S.seqs = [{ id: o.seq || 'items', name: o.name || cap(o.seq || 'Items'), items: (o.items || []).map(x => normItem(x, unit)) }];
  S.seqs.forEach(s => { s.items = s.items.map(x => (x._norm ? x : normItem(x, unit))); });
  S.unit = unit; S.ii = clampIndex(o.index || 0); S.depth = o.depth || 0; S.focus = o.focus || null; S.stack = []; S.zoom = false;
  if (o.panel !== undefined) S.panel = String(o.panel);
  if (o.tab) S.tab = o.tab;
  if (!D.open) {
    S.opener = o.opener || document.activeElement;
    pausePage();
    D.showModal();
    document.documentElement.classList.add('vw-lock');
    if (o.cold) { S.pushed = false; history.replaceState({ vw: 1 }, '', hashFor()); }
    else { history.pushState({ vw: 1 }, '', hashFor()); S.pushed = true; }
  }
  draw(true);
  $('.vw-stage', D).focus({ preventScroll: true });
}
function clampIndex(i) { return Math.max(0, Math.min(seq().items.length - 1, i)); }
function cap(s) { return s.charAt(0).toUpperCase() + s.slice(1); }
function close() { if (D && D.open) D.close(); }
function onClosed() {
  document.documentElement.classList.remove('vw-lock');
  stopVideo(); hideNote(true); S.keys = false;
  const back = S.pushed; S.pushed = false;
  if (back && history.state && history.state.vw) { S.ignorePop = true; history.back(); }
  else if (/[#&]v=|#shot-/.test(location.hash)) history.replaceState(null, '', location.pathname + location.search);
  restorePage();
  returnFocus();
}
function returnFocus() {
  const L = layer(), it = item();
  const cand = it && ($$(`[data-view]`).find(n => n.dataset.view === (L && L.rel) || n.dataset.view === it.id) || null);
  const target = cand && cand.offsetParent ? cand : S.opener;
  if (target && target.focus) { target.focus({ preventScroll: true }); if (target.scrollIntoView) target.scrollIntoView({ block: 'nearest' }); }
}
function pausePage() { $$('video').filter(v => v !== V && !v.paused).forEach(v => { pageVideos.set(v, v.currentTime); v.pause(); }); }
function restorePage() { pageVideos.forEach((t, v) => { try { v.currentTime = t; } catch (e) { /* gone */ } }); pageVideos.clear(); }

/* ------------------------------------------------------------------ history */
function hashFor() {
  const s = seq(), it = item(), L = layer(); if (!it) return location.hash;
  const rt = V && L && L.kind === 'video' ? V.currentTime - (L.seg ? L.seg.t0 : 0) : 0, t = rt > 0.05 ? `&t=${rt.toFixed(1)}` : '';
  return `#v=${s.id}:${it.id}${S.depth && L.name ? '@' + L.name : ''}${t}`;
}
function syncHash() { if (D && D.open) history.replaceState({ vw: 1 }, '', hashFor()); }
window.addEventListener('popstate', () => {
  if (S.ignorePop) { S.ignorePop = false; return; }
  if (D && D.open && !(history.state && history.state.vw)) { S.pushed = false; D.close(); }
});
function parseHash(h) {
  const m = (h || '').match(/[#&]v=([^:&]+):([^@&]+)(?:@([^&]+))?(?:&t=([\d.]+))?/);
  if (m) return { seq: m[1], id: decodeURIComponent(m[2]), depthName: m[3] || '', t: m[4] ? +m[4] : null };
  const s = (h || '').match(/^#shot-(\d\d)$/);
  return s ? { seq: 'shots', shot: +s[1], depthName: 'take' } : null;
}

/* ------------------------------------------------------------------ draw */
function draw(full) {
  const it = item(), L = layer(); if (!it) return;
  hideNote(true); S.zoom = false; S.escArm = false;
  drawTop(it, L); drawCap(it, L); drawStage(it, L);
  if (full) drawTabs();
  drawStrip(); drawPanelState(); drawPanel(it, L); prefetch();
  announce(it, L);
  syncHash();
}
function drawTop(it, L) {
  const s = seq(), file = (L.rel || it.label || '').split('/').pop();
  $('.vw-kind', D).innerHTML = icoHTML(KIND_IC[L.kind] || 'text');
  $('#vw-title', D).textContent = L.title || file || it.label;
  const dir = (L.rel || '').split('/').slice(0, -1).join('/');
  $('.vw-path', D).textContent = L.unit ? `${L.unit} / ${dir}${dir ? '/' : ''}` : dir;
  $('.vw-path', D).title = libRel(L.unit, L.rel || '');
  $('.vw-count', D).textContent = `${S.ii + 1} / ${s.items.length}`;
  $('.vw-count', D).title = `${s.name}: ${S.ii + 1} of ${s.items.length}`;
  $('[data-act="prev"]', D).disabled = S.ii === 0; $('[data-act="next"]', D).disabled = S.ii >= s.items.length - 1;
  $$('.vw-edge', D).forEach(b => { b.hidden = b.classList.contains('prev') ? S.ii === 0 : S.ii >= s.items.length - 1; });
  const orig = $('[data-act="orig"]', D);
  const o = L.orig || (L.kind === 'log' ? L.src : L.rel && codexOf(L.unit) ? URLS.lib(L.unit, L.rel) : L.src);
  if (o) { orig.href = o; orig.removeAttribute('aria-disabled'); } else { orig.removeAttribute('href'); orig.setAttribute('aria-disabled', 'true'); }
  const media = L.kind === 'image' || L.kind === 'video';
  $('.vw-switch', D).hidden = !media || !provider || !it.unit;
  $('.vw-back', D).hidden = !S.stack.length;
  const a = activeAction(it, L);
  const rb = $('.vw-redo', D); rb.hidden = !a; if (a) { rb.querySelector('span').textContent = a.label; rb.setAttribute('aria-label', a.label); }
}
function drawTabs() {
  const box = $('.vw-tabs', D); box.textContent = '';
  box.hidden = S.seqs.length < 2;
  S.seqs.forEach((s, k) => {
    const b = el('button', 'vw-tab'); b.type = 'button'; b.setAttribute('role', 'tab'); b.dataset.si = k;
    b.append(el('span', 'n', s.name), el('span', 'c', s.items.length));
    if (s.extra) b.append(el('span', 'x', s.extra));
    b.disabled = !s.items.length; b.setAttribute('aria-keyshortcuts', String(k + 1));
    b.title = `${s.name} · ${s.items.length}${s.items.length ? '' : ' (none yet)'} · key ${k + 1}`;
    box.appendChild(b);
  });
  markTab();
}
function markTab() { $$('.vw-tab', D).forEach(b => b.setAttribute('aria-selected', String(+b.dataset.si === S.si))); }
function drawCap(it, L) {
  const subj = $('.vw-subj', D); subj.textContent = '';
  subj.append(el('b', '', it.label));
  [L.name && it.layers.length > 1 ? L.name : '', L.sub || it.sub || ''].filter(Boolean).forEach(t => subj.append(el('span', 'sep', '·'), el('span', '', t)));
  (L.chips || it.chips || []).forEach(c => subj.append(el('span', 'vw-chip ' + (c.cls || ''), c.t)));
  const dots = $('.vw-dots', D); dots.textContent = '';
  if (it.layers.length > 1) it.layers.forEach((x, k) => {
    const b = el('button', 'vw-dot', x.name); b.type = 'button'; b.dataset.depth = k;
    b.setAttribute('aria-pressed', String(k === S.depth)); b.disabled = !!x.missing; if (x.missing) b.title = x.missing;
    dots.appendChild(b);
  });
  dots.hidden = it.layers.length < 2;
  if (it.layers.length > 1) dots.setAttribute('aria-label', `${it.axis || 'depth'}: ↑ ↓`);
}

/* ------------------------------------------------------------------ stage renderers */
function show(part) { ['.vw-pic', '.vw-vid', '.vw-doc', '.vw-empty'].forEach(s => { $(s, D).hidden = s !== part; }); }
function drawStage(it, L) {
  const st = $('.vw-stage', D);
  st.dataset.kind = L.kind;
  st.setAttribute('aria-label', `${it.label}${L.name ? ', ' + L.name : ''}, ${S.ii + 1} of ${seq().items.length}`);
  if (L.kind !== 'video' && L.kind !== 'audio') stopVideo();
  if (L.missing) return empty(L.missing, L);
  if (L.kind === 'image') return drawImage(L);
  if (L.kind === 'video' || L.kind === 'audio') return drawVideo(L);
  return drawDoc(L);
}
function empty(msg, L) {
  show('.vw-empty');
  const e = $('.vw-empty', D); e.textContent = '';
  e.append(el('div', 'vw-e-ic'), el('p', 'vw-e-t', msg));
  e.firstChild.innerHTML = icoHTML(KIND_IC[L.kind] || 'text');
  if (L.rel && codexOf(L.unit) && L.kind !== 'log') { const a = el('a', 'vw-tb', 'Open the original ↗'); a.href = URLS.lib(L.unit, L.rel); a.target = '_blank'; a.rel = 'noopener'; e.append(a); }
}
function drawImage(L) {
  show('.vw-pic');
  const box = $('.vw-pic', D), lo = $('.vw-lo', box), hi = $('.vw-hi', box), tok = ++S.loadTok;
  box.classList.remove('zoom', 'ready'); box.scrollTop = box.scrollLeft = 0;
  lo.src = L.thumb || L.src; lo.alt = L.alt || ''; hi.alt = L.alt || ''; hi.removeAttribute('src');
  const img = new Image(); img.decoding = 'async'; img.src = L.src;
  (img.decode ? img.decode() : Promise.resolve()).then(() => {
    if (tok !== S.loadTok) return;                     /* a late load never replaces a newer item */
    hi.src = L.src; box.classList.add('ready');
  }).catch(() => {
    if (tok !== S.loadTok) return;
    /* a running unit rewrites files while the Viewer is open: say so instead of a broken picture */
    if (!lo.complete || !lo.naturalWidth) empty(`${(L.rel || '').split('/').pop()} is not on the board any more (HTTP 404): the running unit moved or redrew it since this list was read.`, L);
    else box.classList.add('ready', 'lo-only');
  });
}
function toggleZoom(e) {
  const L = layer(); if (!L || L.kind !== 'image') return false;
  const box = $('.vw-pic', D); S.zoom = !box.classList.contains('zoom');
  box.classList.toggle('zoom', S.zoom);
  if (S.zoom && e && e.clientX) { const r = box.getBoundingClientRect(), hi = $('.vw-hi', box); requestAnimationFrame(() => { box.scrollLeft = (hi.naturalWidth - r.width) * ((e.clientX - r.left) / r.width); box.scrollTop = (hi.naturalHeight - r.height) * ((e.clientY - r.top) / r.height); }); }
  return true;
}

/* video: the Viewer owns its own <video>; one plays at a time (capture-phase listener below) */
function drawVideo(L) {
  show('.vw-vid');
  const box = $('.vw-vid', D), poster = $('.vw-poster', box);
  box.dataset.audio = L.kind === 'audio' ? '1' : '';
  poster.src = L.poster || L.thumb || ''; poster.hidden = !poster.src; poster.alt = L.alt || '';
  box.classList.remove('playing', 'started');
  const src = L.seg ? L.seg.src : L.src;
  V.dataset.seg = L.seg ? `${L.seg.t0},${L.seg.t1}` : '';
  V.playbackRate = 1; $('[data-v="speed"]', D).textContent = '1×';
  if (V.dataset.src !== src) { V.pause(); V.src = src; V.dataset.src = src; V.preload = 'metadata'; }
  const t0 = L.seg ? L.seg.t0 : 0;
  const start = () => { try { V.currentTime = t0 + (S.startT || 0) + (L.seg ? 0.001 : 0); } catch (e) { /* not ready */ } S.startT = 0; };
  if (V.readyState >= 1) start(); else V.addEventListener('loadedmetadata', start, { once: true });
  const src2 = $('.vw-src', D), it = item();
  const hasPair = it.layers.some(x => x.name === 'take' && !x.missing) && it.layers.some(x => x.name === 'master' && !x.missing);
  src2.hidden = !hasPair && !L.toMaster;
  $('[data-v="take"]', D).setAttribute('aria-pressed', String(!L.seg)); $('[data-v="master"]', D).setAttribute('aria-pressed', String(!!L.seg));
  updateTC();
  if (!reduced()) play(true);
}
function play(auto) {
  const L = layer(); if (!L) return;
  const p = V.play();
  if (p && p.catch) p.catch(err => {
    if (err && err.name === 'NotAllowedError') { V.muted = true; markMute(); V.play().catch(() => {}); if (!auto) toast('Sound blocked by the browser — press M'); }
  });
}
function togglePlay() { if (V.paused) play(false); else V.pause(); }
function stopVideo() { if (!V) return; V.pause(); if (V.getAttribute('src')) { V.removeAttribute('src'); V.dataset.src = ''; V.load(); } }
function segBounds() { const s = (V.dataset.seg || '').split(',').map(Number); return s.length === 2 && !isNaN(s[0]) ? { t0: s[0], t1: s[1] } : null; }
function updateTC() {
  const b = segBounds(), d = V.duration || 0, t0 = b ? b.t0 : 0, t1 = b ? b.t1 : d, t = Math.max(0, V.currentTime - t0), len = Math.max(0.001, t1 - t0);
  const fr = Math.round(V.currentTime * FPS);
  $('.vw-tc', D).textContent = `${tc(t)} / ${tc(len)} · f${fr}${b ? ` · master ${tc(V.currentTime)}` : ''}`;
  if (!S.scrubbing) $('.vw-scrub', D).value = String(Math.round(1000 * t / len));
  $('[data-v="play"]', D).innerHTML = icoHTML(V.paused ? 'play' : 'pause');
  $('.vw-vid', D).classList.toggle('playing', !V.paused);
}
function tc(t) { t = Math.max(0, t || 0); return `${Math.floor(t / 60)}:${(t % 60).toFixed(2).padStart(5, '0')}`; }
function frameStep(k) { V.pause(); const f = Math.round(V.currentTime * FPS) + k, b = segBounds(); let t = (f + 0.5) / FPS; if (b) t = Math.max(b.t0, Math.min(b.t1 - 1 / 48, t)); V.currentTime = Math.max(0, t); }
function seekBy(s) { const b = segBounds(); V.currentTime = Math.max(b ? b.t0 : 0, Math.min(b ? b.t1 - 1 / 48 : V.duration || 0, V.currentTime + s)); }
function speed(d) { const R = [0.25, 0.5, 1, 1.5, 2, 4]; let i = R.indexOf(V.playbackRate); i = Math.max(0, Math.min(R.length - 1, (i < 0 ? 2 : i) + d)); V.playbackRate = R[i]; $('[data-v="speed"]', D).textContent = `${R[i]}×`; toast(`Speed ${R[i]}×`); }
function markMute() { const b = $('[data-v="mute"]', D); b.innerHTML = icoHTML(V.muted ? 'mute' : 'vol'); b.setAttribute('aria-pressed', String(V.muted)); }
function watchSegment() {
  /* the master segment stops exactly on its last frame: rVFC reads the frame being shown */
  const tick = (now, meta) => {
    const b = segBounds();
    if (b && !V.paused && (meta ? meta.mediaTime : V.currentTime) >= b.t1 - 1 / 48) {
      if (V.loop || $('[data-v="loop"]', D).getAttribute('aria-pressed') === 'true') V.currentTime = b.t0 + 0.001; else { V.pause(); V.currentTime = b.t1 - 1 / 48; }
    }
    if (D.open && V.getAttribute('src')) schedule();
  };
  const schedule = () => { if (V.requestVideoFrameCallback) V.requestVideoFrameCallback(tick); else setTimeout(() => tick(0, null), 20); };
  schedule();
}
function sourceToggle() {
  const it = item(), L = layer();
  if (L.toMaster) { L.toMaster(); return; }
  const want = L.seg ? 'take' : 'master', k = it.layers.findIndex(x => x.name === want && !x.missing);
  if (k >= 0) { S.startT = V.currentTime - (L.seg ? L.seg.t0 : 0); setDepth(k); }
}

/* doc / log / text: DocView on the stage */
function drawDoc(L) {
  show('.vw-doc');
  const host = $('.vw-doc', D), tok = ++S.loadTok;
  host.textContent = ''; host.append(el('div', 'vw-skel'));
  fetchText(L.src).then(text => {
    if (tok !== S.loadTok) return;
    S.doc = window.DocView.render(host, { text, rel: L.rel, view: L.view, focus: S.focus || L.focus, refs: L.refs, thumb: r => URLS.thumb(L.unit, r, 160), onRef: r => openRef(r), toast });
    S.focus = null;
  }).catch(err => {
    if (tok !== S.loadTok) return;
    empty(`${(L.rel || '').split('/').pop()} could not be read: ${err.message}`, L);
  });
}
function fetchText(src) {
  if (cache.has(src)) { const v = cache.get(src); cache.delete(src); cache.set(src, v); return v; }
  const p = fetch(src).then(r => (r.ok ? r.text() : r.text().then(t => {
    let d = ''; try { d = JSON.parse(t).detail || ''; } catch (e) { /* an HTML refusal page */ }
    throw new Error(`HTTP ${r.status}${d ? ' · ' + d : ''}`);
  })));
  cache.set(src, p); p.catch(() => cache.delete(src));
  while (cache.size > 24) cache.delete(cache.keys().next().value);
  return p;
}
function openRef(rel) {
  /* a <Picture n> chip: open that picture in the same Viewer, back-stack the current position */
  const unit = item().unit;
  pushStack();
  S.seqs = [{ id: 'refs', name: 'Refs', items: [normItem({ rel, label: rel.split('/').slice(-2).join('/'), unit }, unit)] }];
  S.si = 0; S.ii = 0; S.depth = 0; draw(true);
}

/* ------------------------------------------------------------------ the back stack (promote + refs) */
function openWithin(seqId, pred, depth) {
  /* jump to an item of another sequence of this unit (Attempts → Takes@fail2), keeping one back step */
  const k = S.seqs.findIndex(s => s.id === seqId); if (k < 0) return false;
  const i = S.seqs[k].items.findIndex(pred); if (i < 0) return false;
  pushStack(); S.si = k; S.ii = i; S.depth = depth || 0; markTab(); draw(true); return true;
}
function pushStack() { S.stack.push({ seqs: S.seqs, si: S.si, ii: S.ii, depth: S.depth, panel: S.panel, tab: S.tab }); if (S.stack.length > 8) S.stack.shift(); }
function popStack() {
  const b = S.stack.pop(); if (!b) return false;
  Object.assign(S, { seqs: b.seqs, si: b.si, ii: b.ii, depth: b.depth, panel: b.panel, tab: b.tab });
  draw(true); return true;
}
function promote(rel, focus, label) {
  /* move a file onto the stage (the prompt beside the picture → "open full") */
  const it = item(), unit = it.unit;
  const rels = provider && provider.related ? provider.related(ctx()) : [];
  pushStack();
  const items = (rels.length ? rels : [{ rel, label }]).map(r => normItem({ rel: r.rel, label: r.label || r.rel.split('/').pop(), unit, focus: r.focus }, unit));
  let k = items.findIndex(x => x.layers[0].rel === rel);
  if (k < 0) { items.unshift(normItem({ rel, label: label || rel.split('/').pop(), unit }, unit)); k = 0; }
  S.seqs = [{ id: 'related', name: `Files of ${it.label}`, items }];
  S.si = 0; S.ii = k; S.depth = 0; S.focus = focus || null; S.panel = '0';
  draw(true);
}

/* ------------------------------------------------------------------ filmstrip */
function drawStrip() {
  const s = seq(), box = $('.vw-strip', D);
  const docs = s.items.every(x => ['doc', 'log', 'text'].includes(x.layers[0].kind));
  if (box.dataset.seq !== `${S.si}:${s.id}:${s.items.length}`) {
    box.textContent = ''; box.dataset.seq = `${S.si}:${s.id}:${s.items.length}`;
    box.classList.toggle('docs', docs);
    s.items.forEach((x, k) => box.appendChild(stripItem(x, k, docs)));
  }
  box.hidden = s.items.length < 2;
  $$('.vw-th', box).forEach(b => b.setAttribute('aria-selected', String(+b.dataset.k === S.ii)));
  const cur = box.children[S.ii];
  if (cur) { box.setAttribute('aria-activedescendant', cur.id); cur.scrollIntoView({ inline: 'center', block: 'nearest', behavior: reduced() ? 'auto' : 'smooth' }); }
}
function stripItem(x, k, docs) {
  const L0 = x.layers[0], b = el('button', 'vw-th'); b.type = 'button'; b.dataset.k = k; b.id = `vw-th-${k}`; b.setAttribute('role', 'option');
  b.title = `${x.label}${x.sub ? ' · ' + x.sub : ''}`;
  if (x.layers.every(l => l.missing)) b.classList.add('missing');
  const pic = x.strip || L0.thumb160 || (L0.kind === 'image' && L0.unit ? URLS.thumb(L0.unit, L0.rel, 160) : L0.poster160 || L0.poster);
  if (!docs && pic) { const im = el('img'); im.loading = 'lazy'; im.alt = ''; im.src = pic; im.onerror = () => { im.remove(); b.classList.add('gone'); const t = el('span', 'vw-thi'); t.innerHTML = icoHTML(KIND_IC[L0.kind] || 'image'); b.prepend(t); b.title += ' · not on the board now'; }; b.appendChild(im); }
  else { const t = el('span', 'vw-thi'); t.innerHTML = icoHTML(KIND_IC[L0.kind] || 'text'); b.appendChild(t); }
  b.appendChild(el('span', 'vw-thl', x.short || x.label));
  if (L0.kind === 'video') { const g = el('span', 'vw-thv'); g.innerHTML = icoHTML('play'); if (x.dur) g.append(el('span', '', x.dur)); b.appendChild(g); }
  if (x.badge) b.appendChild(el('span', 'vw-thb', x.badge));
  if (x.flag) b.appendChild(el('span', 'vw-thf'));
  return b;
}

/* ------------------------------------------------------------------ panel (About · Prompt · Verdict · Raw) */
const SNAPS = ['0', '360', '50', 'full'];
function drawPanelState() {
  const ph = phone(), body = $('.vw-body', D);
  let p = S.panel;
  if (!ph && p !== '0' && innerWidth < 1100 && p === '360') p = '360';
  body.dataset.panel = ph ? (S.sheet ? 'sheet' : '0') : p;
  body.style.setProperty('--vw-pw', ph ? '0px' : p === '0' ? '0px' : p === '360' ? 'min(360px, 44vw)' : p === '50' ? '50%' : '100%');
  if (ph) $('.vw-panel', D).style.setProperty('--sheet', `${S.sheet || 0}%`);
  const openNow = ph ? S.sheet > 0 : p !== '0';
  $$('[data-act="info"]', D).forEach(b => b.setAttribute('aria-pressed', String(openNow)));
  $('.vw-panel', D).inert = !openNow;
  $('.vw-seam', D).setAttribute('aria-valuenow', String(p === '0' ? 0 : p === '360' ? 25 : p === '50' ? 50 : 100));
  $('.vw-seam', D).hidden = ph;
  $$('.vw-ptabs [data-tab]', D).forEach(b => b.setAttribute('aria-selected', String(b.dataset.tab === S.tab)));
  const sw = S.tab === 'prompt' && openNow ? 'prompt' : S.tab === 'raw' && openNow ? 'json' : 'pic';
  $$('.vw-switch [data-sw]', D).forEach(b => b.setAttribute('aria-pressed', String(b.dataset.sw === sw)));
  store('vw.panel', S.panel);
}
function setPanel(p, tab) {
  if (phone()) { S.sheet = p === '0' ? 0 : p === 'full' ? 100 : 60; if (tab) S.tab = tab; drawPanelState(); if (S.sheet) drawPanel(item(), layer()); return; }
  if (p !== '0') S.lastPanel = p === 'full' ? S.lastPanel : p;
  S.panel = p; if (tab) S.tab = tab;
  drawPanelState(); if (tab || p !== '0') drawPanel(item(), layer());
}
function toggleInfo() { const openNow = phone() ? S.sheet > 0 : S.panel !== '0'; setPanel(openNow ? '0' : (phone() ? '50' : S.lastPanel || '360')); }
function togglePrompt() {
  const openNow = phone() ? S.sheet > 0 : S.panel !== '0';
  if (openNow && S.tab === 'prompt' && (S.panel === '50' || phone())) setPanel(S.lastPanel === '50' ? '360' : S.lastPanel || '360', 'about');
  else setPanel('50', 'prompt');
}
function ctx() {
  return { seqs: S.seqs, item: item(), layer: layer(), seq: seq(), unit: item() && item().unit, urls: URLS, el, toast, icon: icoHTML,
    promote, open: (rel, focus) => promote(rel, focus), openRef, jumpLog: jumpToActivity, docview: window.DocView,
    setPromptRel: v => { S.promptRel = v; }, openSeq: (seqId, pred, depth) => openWithin(seqId, pred, depth) };
}
function drawPanel(it, L) {
  const body = $('.vw-pbody', D), openNow = phone() ? S.sheet > 0 : S.panel !== '0';
  if (!openNow || !it) return;
  const tok = ++S.panelTok || (S.panelTok = 1);
  const tabs = $$('.vw-ptabs [data-tab]', D);
  const gen = provider && provider.info ? provider.info(ctx()) : null;
  Promise.resolve(gen).then(res => {
    if (tok !== S.panelTok) return;
    res = res || genericInfo(it, L);
    tabs.forEach(b => { b.hidden = !res[b.dataset.tab]; });
    if (!res[S.tab]) S.tab = ['about', 'prompt', 'verdict', 'raw'].find(t => res[t]) || 'about';
    tabs.forEach(b => b.setAttribute('aria-selected', String(b.dataset.tab === S.tab)));
    const node = res[S.tab];
    body.textContent = '';
    body.appendChild(typeof node === 'function' ? node() : node);
    $('.vw-panel', D).setAttribute('aria-label', `${cap(S.tab)} · ${it.label}`);
  }).catch(err => { body.textContent = ''; body.append(el('p', 'vw-perr', `Could not build the panel: ${err.message}`)); });
}
function genericInfo(it, L) {
  const box = el('div', 'pv');
  const dl = el('dl', 'pv-kv');
  [['File', (L.rel || L.src || '').split('/').pop()], ['Path', libRel(L.unit, L.rel || '') || L.src], ['Kind', L.kind], ['Unit', L.unit || '—']].forEach(([k, v]) => dl.append(el('dt', '', k), el('dd', '', v)));
  box.append(dl);
  return { about: box };
}

/* ------------------------------------------------------------------ moving */
function go(k) {
  const s = seq(); let i = S.ii + k;
  while (i >= 0 && i < s.items.length && s.items[i].skip) i += k > 0 ? 1 : -1;
  if (i < 0 || i >= s.items.length) { bump(k); return; }
  S.dir = k > 0 ? 1 : -1; S.ii = i;
  const it = item(); if (S.depth >= it.layers.length || it.layers[S.depth].missing) S.depth = firstDepth(it, S.depth);
  draw(false);
}
function goTo(i) { if (i === S.ii || i < 0 || i >= seq().items.length) return; S.dir = i > S.ii ? 1 : -1; S.ii = i; const it = item(); if (S.depth >= it.layers.length || it.layers[S.depth].missing) S.depth = firstDepth(it, S.depth); draw(false); }
function firstDepth(it, want) { for (let k = Math.min(want, it.layers.length - 1); k >= 0; k--) if (!it.layers[k].missing) return k; return Math.max(0, it.layers.findIndex(x => !x.missing)); }
function bump(k) { const st = $('.vw-stage', D); st.classList.remove('bump-l', 'bump-r'); void st.offsetWidth; st.classList.add(k < 0 ? 'bump-l' : 'bump-r'); toast(k < 0 ? 'First item' : 'Last item'); }
function stepDepth(k) {
  const it = item(); let d = S.depth + k;
  while (d >= 0 && d < it.layers.length && it.layers[d].missing) d += k;
  if (d < 0 || d >= it.layers.length) { if (it.layers.length > 1) toast(k < 0 ? `Top of ${it.axis || 'depth'}` : `Nothing deeper${it.layers[it.layers.length - 1].missing ? ' yet: ' + it.layers[it.layers.length - 1].missing : ''}`); return; }
  setDepth(d);
}
function setDepth(d) { S.depth = d; const it = item(), L = layer(); drawTop(it, L); drawCap(it, L); drawStage(it, L); drawPanel(it, L); announce(it, L); syncHash(); }
function switchSeq(k) {
  if (k < 0 || k >= S.seqs.length || !S.seqs[k].items.length) return;
  if (k === S.si) return;
  const from = ctx();
  const piv = provider && provider.pivot ? provider.pivot(from, S.seqs[k].id) : null;
  S.si = k; S.ii = piv && piv.index >= 0 ? piv.index : 0; S.depth = piv && piv.depth ? piv.depth : 0; S.focus = piv && piv.focus || null; S.startT = piv && piv.t || 0;
  if (piv && piv.miss) toast(piv.miss);
  markTab(); draw(false);
}

/* ------------------------------------------------------------------ prefetch (images only, never video) */
function prefetch() {
  const s = seq(), it = item(); if (!it) return;
  const want = [S.ii - 1, S.ii + 1, S.ii + 2 * S.dir];
  setTimeout(() => want.forEach(i => {
    const x = s.items[i]; if (!x) return;
    const L = x.layers[Math.min(S.depth, x.layers.length - 1)];
    if (L.kind === 'image' && !L.missing) { const im = new Image(); im.fetchPriority = 'low'; im.src = Math.abs(i - S.ii) === 1 ? L.src : (L.thumb || L.src); }
    else if (L.kind === 'video' && L.poster) { const im = new Image(); im.src = L.poster; }
  }), 150);
}

/* ------------------------------------------------------------------ announcements + toast */
let annT;
function announce(it, L) {
  clearTimeout(annT);
  annT = setTimeout(() => {
    const s = seq(), parts = [`${it.label} of ${s.items.length}`, it.layers.length > 1 ? L.name : '', L.sub || it.sub || '', (L.chips || it.chips || []).map(c => c.t).join(', ')];
    $('.vw-live', D).textContent = parts.filter(Boolean).join(', ').replace(`${it.label} of`, `${it.label}, ${S.ii + 1} of`);
  }, 250);
}
let toastT;
function toast(msg) {
  if (!D || !D.open) { if (window.board && window.board.toast) window.board.toast(msg); return; }
  const t = $('.vw-toast', D); t.textContent = msg; t.hidden = false;
  clearTimeout(toastT); toastT = setTimeout(() => { t.hidden = true; }, 2400);
}

/* ------------------------------------------------------------------ actions (R = redo) with a two-step Esc on a dirty note */
function activeAction(it, L) { return Object.values(ACTIONS).find(a => a.applies && a.applies(it, L)) || null; }
function showNote() {
  const it = item(), L = layer(), a = activeAction(it, L); if (!a) return;
  const f = $('.vw-note', D); f.hidden = false; S.note = a; S.noteDirty = false;
  $('.vw-note-t', f).textContent = `${a.label} · ${it.label}`;
  const c = $('.vw-note-c', f); c.textContent = '';
  (a.choices ? a.choices(it, L) : []).forEach(([v, lab, on], k) => { const l = el('label'), r = el('input'); r.type = 'radio'; r.name = 'vw-ch'; r.value = v; r.checked = !!on || (!k && !a.choices(it, L).some(x => x[2])); l.append(r, document.createTextNode(' ' + lab)); c.appendChild(l); });
  const ta = $('textarea', f); ta.value = a.note ? a.note(it, L) : ''; $('.vw-note-w', f).textContent = '';
  ta.focus(); ta.setSelectionRange(ta.value.length, ta.value.length);
}
function hideNote(force) {
  const f = D && $('.vw-note', D); if (!f || f.hidden) return true;
  if (!force && S.noteDirty) {
    if (!S.escArm) { S.escArm = true; $('.vw-note-w', f).textContent = 'Discard this note? Esc again discards, Enter queues.'; return false; }
  }
  f.hidden = true; S.note = null; S.noteDirty = false; S.escArm = false;
  if (!force) $('.vw-stage', D).focus({ preventScroll: true });
  return true;
}
function submitNote(e) {
  e.preventDefault();
  const f = $('.vw-note', D), a = S.note; if (!a) return;
  const ch = f.querySelector('input[name="vw-ch"]:checked');
  const msg = a.submit(item(), layer(), ch ? ch.value : '', $('textarea', f).value);
  S.noteDirty = false; hideNote(true); $('.vw-stage', D).focus({ preventScroll: true });
  if (msg) toast(msg);
  drawCap(item(), layer());
}

/* ------------------------------------------------------------------ Activity link (info panel "In the log" → back to the line) */
function jumpToActivity(fn) { close(); setTimeout(fn, 60); }

/* ------------------------------------------------------------------ keys */
function escStep() {
  if (S.keys) { S.keys = false; $('.vw-keys', D).hidden = true; return; }
  if (!$('.vw-note', D).hidden) { hideNote(false); return; }
  if (S.zoom) { toggleZoom(); return; }
  if (S.doc && S.doc.q) { S.doc.findInput.value = ''; S.doc.search(''); return; }
  if (!phone() && S.panel === 'full') { setPanel('50'); return; }
  if (phone() && S.sheet === 100) { S.sheet = 60; drawPanelState(); return; }
  close();
}
function onKey(e) {
  const t = e.target, typing = t.closest && t.closest('input,textarea,select');
  if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); if (typing && typing.type === 'search' && typing.value) { typing.value = ''; typing.dispatchEvent(new Event('input')); return; } escStep(); return; }
  if (typing) { if (t.tagName === 'TEXTAREA') { S.noteDirty = true; S.escArm = false; if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) $('.vw-note', D).requestSubmit(); } return; }
  if (e.ctrlKey || e.metaKey || e.altKey) { if (e.altKey && e.key === 'ArrowLeft' && S.stack.length) { e.preventDefault(); popStack(); } return; }
  const inDoc = t.closest && t.closest('.vw-doc .dv-body, .vw-pbody, .dv-tree');
  const L = layer(), vid = L && (L.kind === 'video' || L.kind === 'audio') && !L.missing;
  const k = e.key, handled = () => { e.preventDefault(); e.stopPropagation(); };
  if (t.closest && t.closest('.vw-seam') && (k === 'ArrowLeft' || k === 'ArrowRight')) { handled(); const i = SNAPS.indexOf(S.panel); setPanel(SNAPS[Math.max(0, Math.min(3, i + (k === 'ArrowLeft' ? 1 : -1)))]); return; }
  if (!inDoc && (k === 'ArrowRight' || k === ']')) { handled(); go(1); return; }
  if (!inDoc && (k === 'ArrowLeft' || k === '[')) { handled(); go(-1); return; }
  if (!inDoc && k === 'ArrowDown') { handled(); stepDepth(1); return; }
  if (!inDoc && k === 'ArrowUp') { handled(); stepDepth(-1); return; }
  if (vid && !inDoc) {
    if (k === ' ' || k === 'k' || k === 'K') { if (t.tagName === 'BUTTON' && k === ' ' && !t.closest('.vw-vbar')) return; handled(); togglePlay(); return; }
    if (k === 'l' || k === 'L') { handled(); if (!V.paused) speed(1); else play(false); return; }
    if (k === 'j' || k === 'J') { handled(); seekBy(-1); return; }
    if (k === ',' ) { handled(); frameStep(-1); return; }
    if (k === '.') { handled(); frameStep(1); return; }
    if (k === '<') { handled(); speed(-1); return; }
    if (k === '>') { handled(); speed(1); return; }
    if (k === 'o' || k === 'O') { if (!e.shiftKey) { handled(); const b = $('[data-v="loop"]', D), on = b.getAttribute('aria-pressed') !== 'true'; b.setAttribute('aria-pressed', String(on)); V.loop = on && !segBounds(); toast(on ? 'Loop on' : 'Loop off'); return; } }
    if (k === 'm' || k === 'M') { handled(); V.muted = !V.muted; markMute(); return; }
    if (k === 't' || k === 'T') { handled(); sourceToggle(); return; }
  } else {
    if (k === 'j' || k === 'J') { handled(); go(1); return; }
    if (k === 'k' || k === 'K') { handled(); go(-1); return; }
  }
  if (k === 'Home' && !inDoc) { handled(); goTo(firstReal(1)); return; }
  if (k === 'End' && !inDoc) { handled(); goTo(firstReal(-1)); return; }
  if (/^[1-9]$/.test(k) && !inDoc) { handled(); switchSeq(+k - 1); return; }
  if (k === 'i' || k === 'I') { handled(); toggleInfo(); return; }
  if (k === 'p' || k === 'P') { handled(); if ($('.vw-switch', D).hidden) toast('No prompt beside a file'); else togglePrompt(); return; }
  if (k === 'z' || k === 'Z') { handled(); toggleZoom(); return; }
  if (k === 'r' || k === 'R') { if (activeAction(item(), layer())) { handled(); showNote(); } return; }
  if (k === 'c' && !inDoc) { handled(); copyPath(); return; }
  if (k === 'o' || k === 'O') { handled(); const a = $('[data-act="orig"]', D); if (a.href) window.open(a.href, '_blank', 'noopener'); return; }
  if (k === 'Backspace') { if (S.stack.length) { handled(); popStack(); } return; }
  if (k === '?') { handled(); keySheet(); return; }
  if (k === '/' && S.doc && !$('.vw-doc', D).hidden) { handled(); S.doc.findInput.focus(); return; }
  if (k === 'Enter' && !inDoc && t.classList && t.classList.contains('vw-stage') && S.tab === 'prompt' && S.promptRel) { handled(); promote(S.promptRel.rel, S.promptRel.focus); return; }
  if (k === ' ' && !vid && t === $('.vw-stage', D)) { handled(); toggleZoom(); }
}
function firstReal(dir) { const xs = seq().items; if (dir > 0) { const i = xs.findIndex(x => !x.skip); return i < 0 ? 0 : i; } for (let i = xs.length - 1; i >= 0; i--) if (!xs[i].skip) return i; return xs.length - 1; }
function copyPath() { const L = layer(); const p = libRel(L.unit, L.rel || '') || L.src; window.DocView.copyText(p, `Copied ${p}`, toast); }
const KEYS = [['← →  or  J K', 'previous / next item (J K are transport on a video)'], ['↑ ↓', 'depth: stage · attempt · revision'], ['Home End', 'first / last'], ['1 – 5', 'Shots · Takes · Grids · Masters · Files'], ['I', 'info panel'], ['P', 'the prompt beside the picture (50 %)'], ['Enter', 'open the prompt full on the stage'], ['Backspace', 'back to the item you came from'], ['Z  or  double-click', 'fit ↔ 1:1, drag to pan'], ['Space  K', 'play / pause'], ['J  L', '−1 s / play, faster'], [',  .', 'one frame back / forward (24 fps)'], ['<  >', 'speed'], ['O  M  T', 'loop · sound · take ↔ in master'], ['R', 'redo this shot'], ['C', 'copy the relative path'], ['/', 'find inside a file'], ['Esc', 'zoom → panel → search → close']];
function keySheet() {
  const k = $('.vw-keys', D); S.keys = !S.keys; k.hidden = !S.keys; if (!S.keys) return;
  k.textContent = ''; const h = el('h3', '', 'Viewer keys'); k.append(h);
  const dl = el('dl'); KEYS.forEach(([a, b]) => dl.append(el('dt', '', a), el('dd', '', b))); k.append(dl);
}

/* ------------------------------------------------------------------ pointer: seam drag, swipe, pan, backdrop */
function wireDialog() {
  D.addEventListener('keydown', onKey);
  D.addEventListener('cancel', e => { e.preventDefault(); escStep(); });
  D.addEventListener('close', onClosed);
  D.addEventListener('click', onClick);
  D.addEventListener('dblclick', e => { if (e.target.closest('.vw-pic')) toggleZoom(e); if (e.target.closest('.vw-seam')) { const i = SNAPS.indexOf(S.panel); setPanel(SNAPS[(i + 1) % 4]); } });
  let down = null;
  D.addEventListener('pointerdown', e => { down = e.target === D ? { x: e.clientX, y: e.clientY } : null; });
  D.addEventListener('pointerup', e => {
    if (!down || e.target !== D) return;
    const r = D.querySelector('.vw-shell').getBoundingClientRect(), out = e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom;
    if (out && !String(getSelection())) close();
    down = null;
  });
  $('.vw-note', D).addEventListener('submit', submitNote);
  $('.vw-note', D).addEventListener('input', () => { S.noteDirty = true; S.escArm = false; });
  wireSeam(); wireSwipe(); wirePan(); wireVideo(); wireSheet();
  $('.vw-strip', D).addEventListener('click', e => { const b = e.target.closest('.vw-th'); if (b) goTo(+b.dataset.k); });
}
function onClick(e) {
  const a = e.target.closest('[data-act],[data-sw],[data-tab],.vw-tab,.vw-dot,[data-v],[data-note]'); if (!a) return;
  if (a.dataset.note === 'cancel') { S.noteDirty = false; hideNote(true); return; }
  if (a.classList.contains('vw-tab')) return switchSeq(+a.dataset.si);
  if (a.classList.contains('vw-dot')) return setDepth(+a.dataset.depth);
  if (a.dataset.tab) { S.tab = a.dataset.tab; if (S.panel === '0' && !phone()) S.panel = S.lastPanel || '360'; drawPanelState(); drawPanel(item(), layer()); return; }
  if (a.dataset.sw) { const w = a.dataset.sw; if (w === 'pic') setPanel(phone() ? '0' : (S.panel === '50' || S.panel === 'full' ? '360' : S.panel), 'about'); else setPanel('50', w === 'prompt' ? 'prompt' : 'raw'); return; }
  if (a.dataset.v) return videoButton(a.dataset.v);
  const act = a.dataset.act;
  if (act === 'orig') { if (!a.href) e.preventDefault(); return; }
  e.preventDefault();
  if (act === 'close') close(); else if (act === 'prev') go(-1); else if (act === 'next') go(1);
  else if (act === 'info') toggleInfo(); else if (act === 'copy') copyPath(); else if (act === 'keys') keySheet();
  else if (act === 'back') popStack(); else if (act === 'redo') showNote();
  else if (act === 'pfull') setPanel(S.panel === 'full' ? '50' : 'full');
}
function videoButton(v) {
  if (v === 'play') togglePlay(); else if (v === 'speed') speed(1); else if (v === 'mute') { V.muted = !V.muted; markMute(); }
  else if (v === 'loop') { const b = $('[data-v="loop"]', D), on = b.getAttribute('aria-pressed') !== 'true'; b.setAttribute('aria-pressed', String(on)); V.loop = on && !segBounds(); }
  else if (v === 'take' || v === 'master') { const L = layer(); if ((v === 'master') !== !!L.seg) sourceToggle(); }
}
function wireVideo() {
  V.addEventListener('timeupdate', updateTC); V.addEventListener('play', () => { updateTC(); $('.vw-vid', D).classList.add('started'); watchSegment(); });
  V.addEventListener('pause', updateTC); V.addEventListener('loadeddata', () => $('.vw-vid', D).classList.add('started'));
  V.addEventListener('ended', updateTC);
  $('.vw-bigplay', D).addEventListener('click', () => togglePlay());
  $('.vw-vbox', D).addEventListener('click', e => { if (e.target === V) togglePlay(); });
  const sc = $('.vw-scrub', D);
  sc.addEventListener('input', () => { S.scrubbing = true; const b = segBounds(), t0 = b ? b.t0 : 0, t1 = b ? b.t1 : V.duration || 0; V.currentTime = t0 + (t1 - t0) * sc.value / 1000; });
  sc.addEventListener('change', () => { S.scrubbing = false; });
}
function wireSeam() {
  const seam = $('.vw-seam', D), body = $('.vw-body', D);
  seam.addEventListener('pointerdown', e => {
    e.preventDefault(); seam.setPointerCapture(e.pointerId); body.classList.add('dragging');
    const r = body.getBoundingClientRect();
    const move = ev => { const w = Math.max(0, Math.min(r.width, r.right - ev.clientX)); body.style.setProperty('--vw-pw', `${w}px`); };
    const up = ev => {
      seam.removeEventListener('pointermove', move); seam.removeEventListener('pointerup', up); body.classList.remove('dragging');
      const w = r.right - ev.clientX, f = w / r.width;
      const snap = w < 160 ? '0' : f > 0.82 ? 'full' : f > 0.36 ? '50' : '360';
      setPanel(snap, snap !== '0' && S.panel === '0' ? 'about' : undefined);
    };
    seam.addEventListener('pointermove', move); seam.addEventListener('pointerup', up);
  });
}
function wireSheet() {
  /* phone: the panel is a bottom sheet at 25 / 60 / 100 %; drag the grab bar */
  const g = $('.vw-grab', D);
  g.addEventListener('pointerdown', e => {
    g.setPointerCapture(e.pointerId); const y0 = e.clientY, h = D.clientHeight, s0 = S.sheet;
    const up = ev => { g.removeEventListener('pointerup', up); const s = s0 - 100 * (ev.clientY - y0) / h; S.sheet = s < 12 ? 0 : s < 42 ? 25 : s < 80 ? 60 : 100; drawPanelState(); };
    g.addEventListener('pointerup', up);
  });
}
function wireSwipe() {
  const st = $('.vw-stage', D); let p = null;
  st.addEventListener('pointerdown', e => { if (e.pointerType === 'mouse' || S.zoom || e.target.closest('.vw-vbar,.vw-doc,.vw-note,button,input')) { p = null; return; } p = { x: e.clientX, y: e.clientY, t: Date.now() }; });
  st.addEventListener('pointerup', e => {
    if (!p) return; const dx = e.clientX - p.x, dy = e.clientY - p.y; p = null;
    if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy) * 1.3) go(dx < 0 ? 1 : -1);
    else if (dy > 120 && Math.abs(dy) > Math.abs(dx) * 1.3) close();
  });
}
function wirePan() {
  const box = $('.vw-pic', D); let p = null;
  box.addEventListener('pointerdown', e => { if (!S.zoom || e.pointerType !== 'mouse') return; p = { x: e.clientX, y: e.clientY, l: box.scrollLeft, t: box.scrollTop }; box.setPointerCapture(e.pointerId); box.classList.add('panning'); });
  box.addEventListener('pointermove', e => { if (!p) return; box.scrollLeft = p.l - (e.clientX - p.x); box.scrollTop = p.t - (e.clientY - p.y); });
  box.addEventListener('pointerup', () => { p = null; box.classList.remove('panning'); });
}

/* one playing at a time, page-wide (capture phase: play events do not bubble) */
document.addEventListener('play', e => {
  const t = e.target;
  if (!t.isConnected || (t.parentElement && t.parentElement.closest('[hidden]'))) { t.pause(); return; }   /* never play unseen */
  if (t.hidden) t.hidden = false;
  $$('video, audio').forEach(v => { if (v !== t && !v.paused) v.pause(); });
}, true);

/* ------------------------------------------------------------------ [data-view] delegation */
document.addEventListener('click', e => {
  if (e.defaultPrevented || e.button !== 0 || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;
  const n = e.target.closest('[data-view]'); if (!n || (D && D.contains(n))) return;
  e.preventDefault(); e.stopPropagation();
  openFrom(n);
}, true);
document.addEventListener('keydown', e => {
  if (e.key !== ' ' || !e.target.closest) return;
  const n = e.target.closest('[data-view-peek]'); if (!n || e.target.closest('input,textarea')) return;
  e.preventDefault(); openFrom(n, n.dataset.viewPeek);
});
function openFrom(n, rel) {
  const unit = n.dataset.unit || document.body.dataset.unit || null, set = n.dataset.set || 'items';
  CUR_CODEX = n.dataset.codex || document.body.dataset.codex || CUR_CODEX;
  const spec = { seq: set, rel: rel || n.dataset.view, depth: n.dataset.depth, focus: n.dataset.path || (n.dataset.match ? { match: n.dataset.match } : n.dataset.line ? { line: +n.dataset.line } : null), opener: n, shot: n.dataset.shot !== undefined ? +n.dataset.shot : undefined, id: n.dataset.id };
  if (unit && provider && provider.unit && n.dataset.unit !== '') return openUnit(unit, spec);
  const els = $$(`[data-view][data-set="${CSS.escape(set)}"]`);
  const items = (els.length ? els : [n]).map(x => {
    const im = x.querySelector('img');
    return { rel: x.dataset.view, kind: x.dataset.kind, src: x.dataset.src || undefined, thumb: x.dataset.thumb || (im && im.src) || undefined, label: x.dataset.label || x.getAttribute('aria-label') || x.dataset.view.split('/').pop(), unit: x.dataset.unit || unit || undefined };
  });
  open({ seq: set, items, index: Math.max(0, els.indexOf(n)), opener: n, unit, focus: spec.focus });
}
function openUnit(unit, spec) {
  return provider.unit(unit).then(U => {
    const seqs = U.seqs.map(x => Object.assign({}, x, { items: x.items.slice() })), si = Math.max(0, seqs.findIndex(s => s.id === spec.seq));
    const s = seqs[si] || seqs[0];
    let ii = s.items.findIndex(x => (spec.id && x.id === spec.id) || (spec.shot !== undefined && x.shot === spec.shot) || (spec.rel && x.layers.some(l => l.rel === spec.rel)));
    if (ii < 0 && spec.rel) {   /* a file that is in no sequence: open it alone, Files-like */
      const one = normItem({ rel: spec.rel, label: spec.rel.split('/').pop(), unit }, unit);
      ii = s.items.length; s.items.push(one);
    }
    const it = s.items[Math.max(0, ii)];
    let depth = 0;
    if (spec.depth !== undefined && spec.depth !== null && spec.depth !== '') { const d = isNaN(+spec.depth) ? it.layers.findIndex(l => l.name === spec.depth) : +spec.depth; depth = d >= 0 ? d : 0; }
    else if (spec.rel) { const d = it.layers.findIndex(l => l.rel === spec.rel); depth = d >= 0 ? d : 0; }
    if (it.layers[depth] && it.layers[depth].missing) depth = firstDepth(it, depth);
    S.startT = spec.t || 0;
    open({ seqs, seq: s.id, index: Math.max(0, ii), depth, unit, focus: spec.focus, opener: spec.opener, cold: spec.cold, panel: spec.panel, tab: spec.tab });
  }).catch(err => toast(`Viewer: ${err.message}`));
}
function fromHash(cold) {
  const h = parseHash(location.hash); if (!h) return false;
  const unit = document.body.dataset.unit; if (!unit || !provider) return false;
  const spec = { seq: h.seq, depth: h.depthName || undefined, cold, t: h.t };
  if (h.shot !== undefined) spec.shot = h.shot; else { spec.id = h.id; spec.rel = h.id; }
  openUnit(unit, spec); return true;
}

/* ------------------------------------------------------------------ public */
window.Viewer = {
  mount, open, openUnit: (u, s) => openUnit(u, s || {}), close, toast, urls: URLS, icon: icoHTML, normItem,
  codex: codexOf,
  place(unit, p) { PLACE[unit] = p; },
  version(bookRel, v, codex) { VER.set(`${codex || codexOf(null)}/${bookRel}`, String(v)); },
  use(p) { provider = p; if (document.readyState !== 'loading') setTimeout(() => fromHash(true), 0); else document.addEventListener('DOMContentLoaded', () => fromHash(true)); },
  action(name, a) { ACTIONS[name] = a; },
  isOpen: () => !!(D && D.open),
  state: () => ({ seq: seq().id, index: S.ii, depth: S.depth, item: item(), layer: layer(), panel: S.panel, tab: S.tab }),
  setPanel, fromHash,
};
window.addEventListener('hashchange', () => { if (!(D && D.open)) fromHash(false); });
document.dispatchEvent(new Event('viewer:ready'));
})();
