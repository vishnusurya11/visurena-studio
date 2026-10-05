/* Visurena Studio board -- the shell's behaviour (plan G1; vendored, no build, no dependency).
   The sidebar, tabs and dialogs are rendered by the server (templates/_shell.html); this file
   only wires them: theme (Studio black <-> Graphite, localStorage `cc-theme`), the ⌘K palette
   over #pal-data, the `?` keyboard sheet, g-chords, j/k rows, the phone sheet, the inbox badge,
   the GPU card's finish time, the org chart's theme, and htmx's 4xx receipts for /act/. */
(function () {
  'use strict';
  var root = document.documentElement;
  function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } }
  function $(id) { return document.getElementById(id); }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function sprite() { var u = document.querySelector('svg.i use'); return u ? u.getAttribute('href').split('#')[0] : '/static/icons.svg'; }
  function icon(id) { return '<svg class="i" aria-hidden="true"><use href="' + sprite() + '#' + id + '"/></svg>'; }

  /* ---------------------------------------------------------- theme */
  function theme() { return root.dataset.theme === 'light' ? 'light' : 'dark'; }
  function orgTheme() {               /* the org chart in /architecture follows the board */
    var f = document.querySelector('iframe[data-org]');
    if (f && f.getAttribute('src') !== '/org?theme=' + theme()) f.setAttribute('src', '/org?theme=' + theme());
  }
  function toggleTheme() {
    root.dataset.theme = theme() === 'light' ? 'dark' : 'light';
    store('cc-theme', root.dataset.theme);
    orgTheme();
  }

  /* ---------------------------------------------------------- the palette */
  var entries = [], shown = [], sel = 0;
  function score(q, text) {          /* subsequence match; lower is better, -1 none */
    if (!q) return 0;
    var t = text.toLowerCase(), i = 0, gaps = 0, last = -1;
    for (var j = 0; j < t.length && i < q.length; j++) {
      if (t[j] === q[i]) { gaps += last < 0 ? j : j - last - 1; last = j; i++; }
    }
    return i === q.length ? gaps : -1;
  }
  function render() {
    var q = $('pal-q').value.trim().toLowerCase(), html = '', group = null;
    shown = entries.map(function (e) { return { e: e, s: score(q, e.l + ' ' + e.s + ' ' + e.g) }; })
      .filter(function (x) { return x.s >= 0; });
    if (q) shown.sort(function (a, b) { return a.s - b.s; });
    shown.forEach(function (x, n) {
      if (!q && x.e.g !== group) { group = x.e.g; html += '<li class="pal-group" role="presentation">' + esc(group) + '</li>'; }
      html += '<li class="pal-item" role="option" id="pal-' + n + '" data-n="' + n + '" aria-selected="' + (n === sel) + '">' +
        icon(x.e.ic) + '<span class="lbl">' + esc(x.e.l) + '<small>' + esc(x.e.s) + '</small></span>' +
        '<span class="meta">' + (x.e.k ? '<span class="kbd">' + esc(x.e.k) + '</span>' : '') + '</span></li>';
    });
    $('pal-list').innerHTML = html || '<li class="pal-empty">Nothing matches. Try a unit, a book or a department.</li>';
    var cur = $('pal-' + sel);
    if (cur) { cur.scrollIntoView({ block: 'nearest' }); $('pal-q').setAttribute('aria-activedescendant', cur.id); }
  }
  function openPalette() {
    var dlg = $('palette'); if (!dlg || dlg.open) return;
    sel = 0; $('pal-q').value = ''; render(); dlg.showModal(); $('pal-q').focus();
  }
  function go(n) { var x = shown[n]; if (!x) return; $('palette').close(); location.href = x.e.h; }

  /* ---------------------------------------------------------- live bits */
  function needs() {                 /* the inbox badge, every 10 s and after an order */
    fetch('/partials/needs-you-count', { cache: 'no-store' }).then(function (r) { return r.ok ? r.text() : null; }).then(function (t) {
      if (t === null) return;
      document.querySelectorAll('[data-needs]').forEach(function (b) { b.textContent = t.trim(); b.dataset.n = t.trim(); });
    }).catch(function () {});
  }
  function eta() {                   /* the GPU card's finish time, from the progress JSON */
    var card = document.querySelector('.gpu-card[data-progress]'); if (!card) return;
    fetch(card.dataset.progress, { cache: 'no-store' }).then(function (r) { return r.ok ? r.json() : null; }).then(function (p) {
      var e = p && p.eta || {}; if (!e.finish) return;
      document.querySelectorAll('[data-eta]').forEach(function (s) { s.textContent = ' · ~' + e.finish; });
      var span = e.finish_at && p.run_started ? (e.finish_at - p.run_started) : 0;
      document.querySelectorAll('.gpu-card[data-progress]').forEach(function (c) {   /* the sidebar's and the sheet's */
        var head = c.querySelector('.eta'), bar = c.querySelector('[data-prog]');
        if (head) head.textContent = '~' + e.finish;
        if (bar && span > 0) bar.style.width = Math.max(2, Math.min(100, 100 * (p.now - p.run_started) / span)) + '%';
      });
    }).catch(function () {});
  }

  /* ---------------------------------------------------------- wiring */
  document.addEventListener('DOMContentLoaded', function () {
    try { entries = JSON.parse(($('pal-data') || {}).textContent || '[]'); } catch (e) { entries = []; }
    orgTheme(); needs(); eta();
    setInterval(needs, 10000); setInterval(eta, 30000);
    var q = $('pal-q');
    if (q) {
      q.addEventListener('input', function () { sel = 0; render(); });
      q.addEventListener('keydown', function (ev) {
        if (ev.key === 'ArrowDown') { sel = Math.min(sel + 1, shown.length - 1); render(); ev.preventDefault(); }
        else if (ev.key === 'ArrowUp') { sel = Math.max(sel - 1, 0); render(); ev.preventDefault(); }
        else if (ev.key === 'Enter') { go(sel); ev.preventDefault(); }
      });
      $('pal-list').addEventListener('click', function (ev) { var li = ev.target.closest('.pal-item'); if (li) go(+li.dataset.n); });
    }
    ['palette', 'keysheet', 'sheet'].forEach(function (id) {   /* a click on the backdrop closes */
      var dlg = $(id); if (!dlg) return;
      dlg.addEventListener('click', function (ev) { if (ev.target === dlg || ev.target.closest('[data-close]') || (id === 'sheet' && ev.target.closest('a'))) dlg.close(); });
    });
  });
  document.body.addEventListener('orders-changed', needs);
  document.body.addEventListener('htmx:beforeSwap', function (e) {   /* a refused order shows its reason */
    var x = e.detail.xhr, path = (e.detail.requestConfig || {}).path || '';
    if (x && x.status >= 400 && x.status < 500 && path.indexOf('/act/') === 0) { e.detail.shouldSwap = true; e.detail.isError = false; }
  });
  document.addEventListener('click', function (ev) {
    var t = ev.target.closest('[data-palette],[data-theme-toggle],[data-keys],[data-sheet]'); if (!t) return;
    ev.preventDefault();
    var sh = $('sheet'); if (sh && sh.open && !t.hasAttribute('data-sheet')) sh.close();
    if (t.hasAttribute('data-palette')) openPalette();
    else if (t.hasAttribute('data-theme-toggle')) toggleTheme();
    else if (t.hasAttribute('data-keys')) $('keysheet').showModal();
    else if (sh) sh.showModal();
  });

  var CHORDS = { h: '/', i: '/#attention', q: '/queue', b: '/books', a: '/architecture' }, gPending = 0;
  document.addEventListener('keydown', function (ev) {
    var tag = (ev.target.tagName || '').toLowerCase();
    if ((ev.metaKey || ev.ctrlKey) && ev.key.toLowerCase() === 'k') { ev.preventDefault(); openPalette(); return; }
    if (tag === 'input' || tag === 'textarea' || tag === 'select' || ev.target.isContentEditable) return;
    if (document.querySelector('dialog[open]') || ev.metaKey || ev.ctrlKey || ev.altKey) return;
    var k = ev.key.toLowerCase();
    if (gPending) {
      gPending = 0;
      var gpu = document.querySelector('aside .gpu-card[data-progress], aside .gpu-card:not(.idle)');
      if (k === 'r' && gpu) { location.href = gpu.getAttribute('href'); return; }
      if (CHORDS[k]) { location.href = CHORDS[k]; return; }
    }
    if (k === 'g') { gPending = 1; setTimeout(function () { gPending = 0; }, 1200); return; }
    if (ev.key === '/') { ev.preventDefault(); openPalette(); }
    else if (ev.key === '?') { ev.preventDefault(); $('keysheet').showModal(); }
    else if (k === 't') toggleTheme();
    else if (k === 'j' || k === 'k') {                     /* j/k walk [data-row] rows */
      var rows = Array.prototype.slice.call(document.querySelectorAll('[data-row]')); if (!rows.length) return;
      var i = rows.indexOf(document.activeElement.closest('[data-row]'));
      rows[k === 'j' ? Math.min(i + 1, rows.length - 1) : Math.max(i - 1, 0)].focus();
    }
  });
})();
