/* media.js — the media contract of the board (panel ruling PKG-5, 5.1/5.3/5.8; P05).
   No dependency, MIT.  Every page's audio and video obey four rules:
     1. one play owner: a player that starts pauses every other (hover previews, muted
        and without controls, never count);
     2. never play unseen: a playing element that stops being visible (checkVisibility)
        pauses, and every <dialog>'s close pauses and empties the media inside it;
     3. say what happens: a waiting ring after 300 ms, an error card naming the file,
        a replay button at the end;
     4. sound first: a programmatic start is unmuted, and when the browser blocks sound
        it plays muted with a "sound blocked · M" chip (M unmutes).
   The unit page's wiring rides along: the Viewer is loaded when the shell has not loaded
   it, the body names the unit, the shot filter, the redo picks, the Viewer's R = redo,
   file names in the Activity window open the Viewer, and a new master iteration shows a
   badge without ever reloading the playing player. */
(function () {
'use strict';
if (window.BoardMedia) return;
const WAIT_MS = 300;
const $ = (s, r) => (r || document).querySelector(s);
const $$ = (s, r) => [...(r || document).querySelectorAll(s)];
const isMedia = n => n instanceof HTMLMediaElement;
const isPreview = v => v.muted && !v.controls && !v.closest('dialog');
const inViewer = v => !!v.closest('#viewer');

/* ------------------------------------------------------------------ 1. one play owner */
document.addEventListener('play', e => {
  const t = e.target; if (!isMedia(t) || isPreview(t)) return;
  $$('video, audio').forEach(v => { if (v !== t && !v.paused && !isPreview(v)) v.pause(); });
}, true);

/* ------------------------------------------------------------------ 2. never play unseen */
function unseen(v) { return typeof v.checkVisibility === 'function' ? !v.checkVisibility({ checkOpacity: false, checkVisibilityCSS: true }) : !v.offsetParent; }
document.addEventListener('timeupdate', e => {
  const v = e.target; if (isMedia(v) && !v.paused && v.tagName === 'VIDEO' && unseen(v)) v.pause();
}, true);
function emptyMedia(root) {
  $$('video, audio', root).forEach(v => {
    v.pause();
    if (v.getAttribute('src')) { v.removeAttribute('src'); v.load(); }
    if (v.dataset.src) v.dataset.src = '';   /* the Viewer's own "src already set" mark */
  });
}
document.addEventListener('close', e => { if (e.target instanceof HTMLDialogElement) emptyMedia(e.target); }, true);

/* ------------------------------------------------------------------ 3. say what happens */
const waits = new WeakMap();
function box(v) { return v.closest('.player') || v.parentElement; }
document.addEventListener('waiting', e => {
  const v = e.target; if (!isMedia(v) || inViewer(v)) return;
  clearTimeout(waits.get(v)); waits.set(v, setTimeout(() => { if (!v.paused) box(v).classList.add('is-waiting'); }, WAIT_MS));
}, true);
['playing', 'canplay', 'pause', 'emptied', 'seeked', 'loadeddata'].forEach(k => document.addEventListener(k, e => {
  const v = e.target; if (!isMedia(v)) return;
  clearTimeout(waits.get(v)); const b = box(v); if (b) b.classList.remove('is-waiting');
  if (k === 'playing' && b) { b.classList.remove('is-ended'); const r = $('.m-replay', b); if (r) r.hidden = true; }
}, true));
document.addEventListener('error', e => {
  const v = e.target; if (!isMedia(v) || inViewer(v) || !v.getAttribute('src')) return;
  const b = box(v); if (!b || $('.m-err', b)) return;
  const card = document.createElement('div'); card.className = 'm-err'; card.setAttribute('role', 'alert');
  const code = document.createElement('code'); code.textContent = v.dataset.rel || v.getAttribute('src');
  card.append('Could not play ', code, '. The file may be missing or still being written.');
  b.appendChild(card);
}, true);
document.addEventListener('ended', e => {
  const v = e.target; if (!isMedia(v) || inViewer(v) || v.loop) return;
  const b = box(v); if (!b) return;
  b.classList.add('is-ended');
  let r = $('.m-replay', b);
  if (!r) {
    r = document.createElement('button'); r.type = 'button'; r.className = 'btn sm m-replay'; r.textContent = 'Replay';
    r.addEventListener('click', () => { v.currentTime = 0; playWithSound(v); });
    b.appendChild(r);
  }
  r.hidden = false;
}, true);

/* ------------------------------------------------------------------ 4. sound first */
function soundChip(v, on) {
  const b = box(v); if (!b) return;
  let c = $('.m-sound', b);
  if (on && !c) { c = document.createElement('button'); c.type = 'button'; c.className = 'chip2 m-sound'; c.textContent = 'sound blocked · M'; c.addEventListener('click', () => unmute(v)); b.appendChild(c); }
  if (c) c.hidden = !on;
}
function unmute(v) { v.muted = false; soundChip(v, false); }
function playWithSound(v) {
  v.muted = false;
  return v.play().catch(err => {
    if (!err || err.name !== 'NotAllowedError') return;
    v.muted = true; soundChip(v, true);
    return v.play().catch(() => {});
  });
}
document.addEventListener('keydown', e => {
  if ((e.key !== 'm' && e.key !== 'M') || e.ctrlKey || e.metaKey || e.altKey) return;
  if (e.target.closest && e.target.closest('input, textarea, select, [contenteditable], dialog')) return;
  const v = $$('video.m-video').find(x => !x.paused) || $$('video.m-video').find(x => x.muted);
  if (!v) return;
  e.preventDefault(); if (v.muted) unmute(v); else v.muted = true;
});

/* ------------------------------------------------------------------ the Viewer, when the shell has not loaded it */
function loadScript(src) { return new Promise((ok, no) => { const s = document.createElement('script'); s.src = src; s.onload = ok; s.onerror = no; document.head.appendChild(s); }); }
function ensureViewer() {
  if (window.Viewer || !$('[data-view]')) return Promise.resolve();
  if (!$('link[href*="viewer/viewer.css"]')) { const l = document.createElement('link'); l.rel = 'stylesheet'; l.href = '/static/viewer/viewer.css'; document.head.appendChild(l); }
  return loadScript('/static/viewer/docview.js').then(() => loadScript('/static/viewer/viewer.js')).then(() => loadScript('/static/viewer/prov.js')).catch(() => {});
}
function nameTheBody() {
  const u = $('#unit'); if (!u) return;
  ['codex', 'stage', 'unit'].forEach(k => { if (!document.body.dataset[k] && u.dataset[k]) document.body.dataset[k] = u.dataset[k]; });
}

/* ------------------------------------------------------------------ the unit page */
function onFilter(b) {
  const sec = b.closest('.u-sec'), grid = sec && $('.shots', sec); if (!grid) return;
  $$('[data-filter]', sec).forEach(x => x.setAttribute('aria-pressed', String(x === b)));
  grid.classList.toggle('only-flagged', b.dataset.filter === 'flagged');
}
function onPick(input) {
  const f = input.closest('form'), shots = $$('.picks input:checked', f).map(x => x.dataset.shot);
  f.note.value = f.note.value.replace(/; shots [0-9, ]*$/, '') + (shots.length ? '; shots ' + shots.join(', ') : '');
}
document.addEventListener('click', e => { const b = e.target.closest('[data-filter]'); if (b) onFilter(b); });
document.addEventListener('change', e => { if (e.target.matches && e.target.matches('.picks input')) onPick(e.target); });
document.addEventListener('keydown', e => {
  if ((e.key !== 'Enter' && e.key !== ' ') || !e.target.matches || !e.target.matches('[data-view][role="button"]')) return;
  e.preventDefault(); e.target.click();
});

/* R in the Viewer: the redo form, filled for this picture and sent through /act/redo */
const REDOABLE = /^(panel|staged|take|kept)$/;
function redoStep(L) { const u = $('#unit'); return /^(panel|staged)$/.test(L.name) ? u.dataset.panelStep : u.dataset.takeStep; }
function redoSubmit(it, L, choice, note) {
  const u = $('#unit'), d = $('#redo'), f = d && $('form', d); if (!f) return 'No redo form on this page';
  f.step_id.value = redoStep(L) || f.step_id.value;
  f.artefact.value = `${u.dataset.home}/${L.rel}`;
  f.note.value = note || `${it.label}: redo`;
  d.open = true;
  if (f.requestSubmit) f.requestSubmit(); else f.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
  return `Redo of ${it.label} sent: see its receipt`;
}
function registerRedo() {
  if (!window.Viewer || !$('#redo')) return;
  window.Viewer.action('redo', { key: 'R', label: 'Redo this shot', applies: (it, L) => !!(L && REDOABLE.test(L.name || '')),
    note: (it, L) => `${it.label} (${L.name}): `, submit: redoSubmit });
}

/* file names in the Activity window open the Viewer */
const FILE_RE = /(?:[\w.-]+\/)*[\w.-]+\.(?:png|mp4|jsonl?|log|txt|wav)\b/g;
function linkText(node, home) {
  const text = node.nodeValue; FILE_RE.lastIndex = 0;
  if (!FILE_RE.test(text)) return;
  const frag = document.createDocumentFragment(); let at = 0; FILE_RE.lastIndex = 0;
  for (const m of text.matchAll(FILE_RE)) {
    frag.append(text.slice(at, m.index));
    const b = document.createElement('button'); b.type = 'button'; b.className = 'vlink';
    b.dataset.view = m[0].startsWith(home + '/') ? m[0].slice(home.length + 1) : m[0]; b.dataset.set = 'files'; b.textContent = m[0];
    frag.append(b); at = m.index + m[0].length;
  }
  frag.append(text.slice(at)); node.replaceWith(frag);
}
function linkActivity() {
  const u = $('#unit'), root = $('#tails'); if (!u || !root) return;
  const walk = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, { acceptNode: n => (n.parentElement.closest('td.note, li, pre') && !n.parentElement.closest('button, a') ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT) });
  const nodes = []; while (walk.nextNode()) nodes.push(walk.currentNode);
  nodes.forEach(n => linkText(n, u.dataset.home || ''));
}

/* 5.8: a new master iteration lands -> a badge and a toast; the playing player is never reloaded */
function checkNewMaster() {
  const screen = $('#master[data-latest]'), mark = $('#head [data-latest-master]'); if (!screen || !mark) return;
  const latest = mark.dataset.latestMaster; if (!latest || latest === screen.dataset.latest) return;
  const badge = $('[data-k="vnew"]', screen); if (!badge || badge.dataset.rel === latest) return;
  badge.dataset.rel = latest; badge.textContent = `${mark.dataset.latestShort} •`; badge.title = `${latest} landed; open it in the Viewer`;
  badge.hidden = false; badge.setAttribute('data-view', latest); badge.setAttribute('data-set', 'masters'); badge.setAttribute('role', 'button'); badge.tabIndex = 0;
  const msg = `A new master landed: ${mark.dataset.latestShort}. The player keeps playing.`;
  if (window.Viewer && window.Viewer.toast) window.Viewer.toast(msg); else if (window.board && window.board.toast) window.board.toast(msg);
}

/* the Watch link (unit#master?play): the master plays at once, with sound when allowed */
function playFromHash() {
  if (!/[#&?]play\b/.test(location.hash) && !/^#master\?play/.test(location.hash)) return;
  const v = $('#master-video'); if (!v) return;
  v.scrollIntoView({ block: 'center' }); playWithSound(v);
}

/* a pulse morphs the running unit's Activity: the folds the owner opened stay open */
let keptFolds = new Set();
function openFolds(root) { return new Set([...root.querySelectorAll('details[open] > summary')].map(s => s.textContent.trim())); }
function reopenFolds(root, kept) {
  root.querySelectorAll('details > summary').forEach(s => { if (kept.has(s.textContent.trim())) s.parentElement.open = true; });
}
document.addEventListener('htmx:beforeSwap', e => {
  const t = e.detail && e.detail.target; if (t && t.id === 'tails') keptFolds = openFolds(t);
});
document.addEventListener('htmx:afterSettle', e => {
  const t = e.detail && e.detail.target; if (!t) return;
  if (t.id === 'head') checkNewMaster();
  if (t.id === 'tails') { reopenFolds(t, keptFolds); linkActivity(); }
});
function boot() {
  nameTheBody(); linkActivity(); checkNewMaster(); playFromHash();
  ensureViewer().then(registerRedo);
  document.addEventListener('viewer:ready', registerRedo);
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();

window.BoardMedia = { playWithSound, unmute, emptyMedia };
})();
