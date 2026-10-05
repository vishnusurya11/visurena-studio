/* Visurena Studio board -- the shell's behaviour (plan G1, panel ruling PKG-2; vendored, no build, no dependency).
   The sidebar, tabs and dialogs are rendered by the server (templates/_shell.html); this file wires them:
   theme (Studio black <-> Graphite, localStorage `cc-theme`), the ⌘K palette over #pal-data (every unit,
   Recent, hold / lift / acknowledge), the key map from #keys-data (= shell.KEYS, C4) with its single-key
   switch (`cc-keys`), the phone sheet, board.announce() over #sr-status / #sr-alert (C5), the receipt
   toast for the owner's own orders, the held bar's Lift, the org chart's theme and htmx's 4xx receipts.
   Nothing here polls: pulse.js is the one clock. */
(function () {
  'use strict';
  var root = document.documentElement;
  function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } return null; }
  function $(id) { return document.getElementById(id); }
  function readJSON(id, empty) { try { return JSON.parse(($(id) || {}).textContent || '') || empty; } catch (e) { return empty; } }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function sprite() { var u = document.querySelector('svg.i use'); return u ? u.getAttribute('href').split('#')[0] : '/static/icons.svg'; }
  function icon(id) { return '<svg class="i" aria-hidden="true"><use href="' + sprite() + '#' + esc(id) + '"/></svg>'; }
  function textOf(htmlText) { return new DOMParser().parseFromString(String(htmlText || ''), 'text/html').body.textContent.trim(); }

  /* ---------------------------------------------------------- C5: the one voice */
  var queue = { polite: [], urgent: [] }, said = {}, flushTimer = 0;
  function announce(text, o) {
    o = o || {}; text = String(text || '').trim(); if (!text) return;
    var key = o.key || text, now = Date.now(), q = o.urgent ? queue.urgent : queue.polite;
    if (said[key] && said[key].text === text && now - said[key].at < 10000) return;      /* dedupe */
    said[key] = { text: text, at: now };
    for (var i = q.length - 1; i >= 0; i--) if (q[i].key === key) q.splice(i, 1);          /* coalesce */
    q.push({ key: key, text: text });
    clearTimeout(flushTimer); flushTimer = setTimeout(flush, 250);
  }
  function speak(id, q) {
    if (!q.length) return;
    var el = $(id), msg = q.map(function (x) { return x.text; }).join('. '); q.length = 0;
    if (!el) return;
    el.textContent = ''; requestAnimationFrame(function () { el.textContent = msg; });
  }
  function flush() { speak('sr-status', queue.polite); speak('sr-alert', queue.urgent); }
  window.board = window.board || {}; window.board.announce = announce;

  /* ---------------------------------------------------------- receipts: own actions only, >= 6 s */
  var receiptTimer = 0;
  function hideReceipt() { var r = $('receipts'); if (r && !r.matches(':hover') && !r.contains(document.activeElement)) r.hidden = true; }
  function receipt(htmlText, refused) {
    var r = $('receipts'), t = textOf(htmlText); if (!r || !t) return;
    r.textContent = t; r.dataset.refused = refused ? '1' : ''; r.hidden = false;
    clearTimeout(receiptTimer); receiptTimer = setTimeout(hideReceipt, 6000);
    announce(t, { key: 'receipt', urgent: !!refused });
  }
  function wireReceipts() {
    var r = $('receipts'); if (!r) return;
    r.addEventListener('mouseleave', function () { clearTimeout(receiptTimer); receiptTimer = setTimeout(hideReceipt, 6000); });
    r.addEventListener('focusout', function () { clearTimeout(receiptTimer); receiptTimer = setTimeout(hideReceipt, 6000); });
  }
  function post(path, fields) {
    return fetch(path, { method: 'POST', body: new URLSearchParams(fields || {}), headers: { 'HX-Request': 'true' } })
      .then(function (res) { return res.text().then(function (t) { receipt(t, !res.ok); if (res.ok) document.body.dispatchEvent(new Event('orders-changed')); }); })
      .catch(function () { receipt('The board did not answer; nothing was ordered.', true); });
  }

  /* ---------------------------------------------------------- theme */
  function theme() { return root.dataset.theme === 'light' ? 'light' : 'dark'; }
  function orgTheme() {               /* the org chart in /architecture follows the board */
    var f = document.querySelector('iframe[data-org]');
    if (f && f.getAttribute('src') !== '/org?theme=' + theme()) f.setAttribute('src', '/org?theme=' + theme());
  }
  function toggleTheme() { root.dataset.theme = theme() === 'light' ? 'dark' : 'light'; store('cc-theme', root.dataset.theme); orgTheme(); }

  /* ---------------------------------------------------------- the palette */
  var entries = [], loadedAt = Date.now(), shown = [], sel = 0, mode = null;
  function score(q, text) {          /* subsequence match; lower is better, -1 none */
    if (!q) return 0;
    var t = text.toLowerCase(), i = 0, gaps = 0, last = -1;
    for (var j = 0; j < t.length && i < q.length; j++) {
      if (t[j] === q[i]) { gaps += last < 0 ? j : j - last - 1; last = j; i++; }
    }
    return i === q.length ? gaps : -1;
  }
  function recent() {
    var list = []; try { list = JSON.parse(store('cc-recent') || '[]'); } catch (e) { list = []; }
    return list.filter(function (r) { return r && r.h && r.h !== location.pathname; })
      .map(function (r) { return { g: 'Recent', ic: 'history', l: r.l, s: r.h, h: r.h }; });
  }
  function remember() {
    var here = { h: location.pathname, l: document.title.replace(/ · Visurena Studio$/, '') }, list = [];
    try { list = JSON.parse(store('cc-recent') || '[]'); } catch (e) { list = []; }
    list = [here].concat(list.filter(function (r) { return r && r.h !== here.h; })).slice(0, 6);
    store('cc-recent', JSON.stringify(list));
  }
  function pool() {
    if (mode) return mode.reasons.map(function (r) { return { g: 'Why hold the studio?', ic: 'pause', l: r, s: 'Enter holds the studio', reason: r }; });
    return recent().concat(entries);
  }
  function item(x, n) {
    var e = x.e, st = e.st ? ' data-state="' + esc(e.st) + '"' : '';
    return '<li class="pal-item" role="option" id="pal-' + n + '" data-n="' + n + '" aria-selected="' + (n === sel) + '"' + st + '>' +
      icon(e.ic || 'circle') + '<span class="lbl">' + esc(e.l) + '<small>' + esc(e.s || '') + '</small></span>' +
      '<span class="meta">' + (e.k ? '<span class="kbd">' + esc(e.k) + '</span>' : '') + '</span></li>';
  }
  function render() {
    var q = $('pal-q').value.trim().toLowerCase(), out = '', group = null;
    shown = pool().map(function (e) { return { e: e, s: score(q, e.l + ' ' + (e.s || '') + ' ' + e.g) }; })
      .filter(function (x) { return x.s >= 0; });
    if (q) shown.sort(function (a, b) { return a.s - b.s; });
    shown.forEach(function (x, n) {
      if (!q && x.e.g !== group) { group = x.e.g; out += '<li class="pal-group" role="presentation">' + esc(group) + '</li>'; }
      out += item(x, n);
    });
    $('pal-list').innerHTML = out || (mode ? '<li class="pal-empty">Type a reason and press Enter.</li>' : '<li class="pal-empty">Nothing matches. Try a unit, a book or a department.</li>');
    var cur = $('pal-' + sel);
    if (cur) { cur.scrollIntoView({ block: 'nearest' }); $('pal-q').setAttribute('aria-activedescendant', cur.id); }
  }
  function refetch() {               /* the embedded index goes stale; re-read it when it is older than 10 s */
    if (Date.now() - loadedAt < 10000) return;
    loadedAt = Date.now();
    fetch('/api/palette.json', { cache: 'no-store' }).then(function (r) { return r.ok ? r.json() : null; })
      .then(function (list) { if (Array.isArray(list)) { entries = list; if ($('palette').open) render(); } }).catch(function () {});
  }
  function openPalette() {
    var dlg = $('palette'); if (!dlg || dlg.open) return;
    mode = null; sel = 0; $('pal-q').value = ''; $('pal-q').placeholder = 'Jump to a page, unit, book or department…';
    render(); dlg.showModal(); $('pal-q').focus(); refetch();
  }
  function act(e) {
    if (e.a === 'hold') { mode = e; sel = 0; $('pal-q').value = ''; $('pal-q').placeholder = 'Why hold the studio? Pick one or type it'; render(); return; }
    $('palette').close();
    if (e.a === 'lift') post('/act/lift/' + e.id);
    else if (e.a === 'ack') post('/act/acknowledge', { codex: e.codex, stage: e.stage, unit: e.unit });
  }
  function go(n) {
    var x = shown[n], typed = $('pal-q').value.trim();
    if (mode) { var why = x ? x.e.reason : typed; if (!why) return; $('palette').close(); mode = null; post('/act/hold', { scope: 'studio', reason: why }); return; }
    if (!x) return;
    if (x.e.a) { act(x.e); return; }
    $('palette').close(); location.href = x.e.h;
  }

  /* ---------------------------------------------------------- C4: the key map from shell.KEYS */
  var KEYS = {}, PREFIX = {}, pending = '';
  function keysOn() { return store('cc-keys') !== 'off'; }
  function rowStep(d) {             /* j/k walk [data-row] rows */
    var rows = Array.prototype.slice.call(document.querySelectorAll('[data-row]')); if (!rows.length) return;
    var i = rows.indexOf(document.activeElement && document.activeElement.closest('[data-row]'));
    rows[d > 0 ? Math.min(i + 1, rows.length - 1) : Math.max(i - 1, 0)].focus();
  }
  var ACTS = {
    palette: openPalette, keys: function () { $('keysheet').showModal(); }, theme: toggleTheme,
    gpu: function () { var g = document.querySelector('aside [data-gpu]:not(.idle)'); if (g) location.href = g.getAttribute('href'); },
    'row-next': function () { rowStep(1); }, 'row-prev': function () { rowStep(-1); }
  };
  function run(row) {
    if (row.go) location.href = row.go;
    else if (row.act && ACTS[row.act]) ACTS[row.act]();
    else if (row.click) { var c = document.querySelector('[data-key="' + CSS.escape(row.click) + '"]'); if (c) c.click(); }
  }
  function loadKeys() {
    readJSON('keys-data', []).forEach(function (row) {
      KEYS[row.keys] = row;
      if (row.keys.indexOf(' ') > 0) PREFIX[row.keys.split(' ')[0]] = 1;
    });
  }
  function typing(t) { var tag = (t.tagName || '').toLowerCase(); return tag === 'input' || tag === 'textarea' || tag === 'select' || t.isContentEditable; }
  function onKey(ev) {
    if ((ev.metaKey || ev.ctrlKey) && !ev.altKey && ev.key.toLowerCase() === 'k' && KEYS['ctrl+k']) { ev.preventDefault(); run(KEYS['ctrl+k']); return; }
    if (typing(ev.target) || document.querySelector('dialog[open]') || ev.metaKey || ev.ctrlKey || ev.altKey || !keysOn()) return;
    var k = ev.key, row;
    if (pending) { row = KEYS[pending + ' ' + k.toLowerCase()]; pending = ''; if (row) { ev.preventDefault(); run(row); } return; }
    if (PREFIX[k]) { pending = k; setTimeout(function () { pending = ''; }, 1200); return; }
    row = KEYS[k]; if (row) { ev.preventDefault(); run(row); }
  }

  /* ---------------------------------------------------------- wiring */
  function wirePalette() {
    var q = $('pal-q'); if (!q) return;
    q.addEventListener('input', function () { sel = 0; render(); });
    q.addEventListener('keydown', function (ev) {
      if (ev.key === 'ArrowDown') { sel = Math.min(sel + 1, shown.length - 1); render(); ev.preventDefault(); }
      else if (ev.key === 'ArrowUp') { sel = Math.max(sel - 1, 0); render(); ev.preventDefault(); }
      else if (ev.key === 'Enter') { go(mode && q.value.trim() && !shown.length ? -1 : sel); ev.preventDefault(); }
    });
    $('pal-list').addEventListener('click', function (ev) { var li = ev.target.closest('.pal-item'); if (li) go(+li.dataset.n); });
  }
  function wireDialogs() {
    ['palette', 'keysheet', 'sheet'].forEach(function (id) {   /* a click on the backdrop closes */
      var dlg = $(id); if (!dlg) return;
      dlg.addEventListener('click', function (ev) { if (ev.target === dlg || ev.target.closest('[data-close]') || (id === 'sheet' && ev.target.closest('a'))) dlg.close(); });
    });
    var sw = document.querySelector('[data-keys-switch]');
    if (sw) { sw.checked = keysOn(); sw.addEventListener('change', function () { store('cc-keys', sw.checked ? 'on' : 'off'); }); }
  }
  document.addEventListener('DOMContentLoaded', function () {
    entries = readJSON('pal-data', []); loadKeys();
    orgTheme(); wirePalette(); wireDialogs(); wireReceipts(); remember();
  });
  document.body.addEventListener('htmx:beforeSwap', function (e) {   /* a refused order shows its reason */
    var x = e.detail.xhr, path = (e.detail.requestConfig || {}).path || '';
    if (x && x.status >= 400 && x.status < 500 && path.indexOf('/act/') === 0) { e.detail.shouldSwap = true; e.detail.isError = false; }
  });
  document.body.addEventListener('htmx:afterRequest', function (e) {   /* the owner's own order: the toast says what it did */
    var x = e.detail.xhr, path = (e.detail.requestConfig || {}).path || '';
    if (e.detail.target && e.detail.target.id === 'receipts') return;   /* orders.js draws its live chip there */
    if (x && path.indexOf('/act/') === 0 && (e.detail.requestConfig || {}).verb === 'post') receipt(x.responseText, x.status >= 400);
  });
  /* [data-copy]: copy the value, say so (a refused clipboard selects nothing and says that) */
  function copyValue(b) {
    var say = function (t) { if (window.board && board.announce) board.announce(t, { key: 'copy' }); };
    try { navigator.clipboard.writeText(b.dataset.copy).then(function () { say('Copied ' + b.dataset.copy); }, function () { say('Copy refused by the browser'); }); }
    catch (e) { say('Copy refused by the browser'); }
  }
  /* [data-ack-all]: every acknowledge form on the page, each through its own Undo (orders.js) */
  function ackAll() {
    document.querySelectorAll('form.ack').forEach(function (f) { if (f.requestSubmit) f.requestSubmit(); });
  }
  document.addEventListener('click', function (ev) {
    var cp = ev.target.closest('[data-copy]'); if (cp) { ev.preventDefault(); copyValue(cp); return; }
    var all = ev.target.closest('[data-ack-all]'); if (all) { ev.preventDefault(); ackAll(); return; }
    var lift = ev.target.closest('[data-lift]');
    if (lift && lift.dataset.lift) { ev.preventDefault(); post('/act/lift/' + lift.dataset.lift); return; }
    var t = ev.target.closest('[data-palette],[data-theme-toggle],[data-keys],[data-sheet]'); if (!t) return;
    ev.preventDefault();
    var sh = $('sheet'); if (sh && sh.open && !t.hasAttribute('data-sheet')) sh.close();
    if (t.hasAttribute('data-palette')) openPalette();
    else if (t.hasAttribute('data-theme-toggle')) toggleTheme();
    else if (t.hasAttribute('data-keys')) $('keysheet').showModal();
    else if (sh) sh.showModal();
  });
  document.addEventListener('keydown', onKey);
})();
