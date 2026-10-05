/* Visurena Studio board — shell behaviour for the mockups: theme toggle, ⌘K palette,
   `?` keyboard sheet, g-chords, row ⋯ menus, receipt toast. No dependency.
   The build replaces PALETTE with GET /api/index.json (report 07 §4). */
(function () {
  'use strict';
  var SPRITE = 'assets/icons.svg#';
  function icon(id) { return '<svg class="i" aria-hidden="true"><use href="' + SPRITE + id + '"/></svg>'; }
  function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } }

  /* ---------------------------------------------------------- palette index
     Real units/books captured read-only 2026-10-04 19:21 PDT. */
  var PALETTE = [
    { g: 'Units', ic: 'loader', l: 'ep17 The Thunder Child', s: 'The War of the Worlds · running 07 board', h: 'unit-running.html', k: 'G R' },
    { g: 'Units', ic: 'flag', l: 'ep16 The Exodus Northward', s: 'War of the Worlds · shipped ⚑37', h: 'unit-finished.html?u=ep16' },
    { g: 'Units', ic: 'flag', l: 'ep15 What Had Happened in Surrey', s: 'War of the Worlds · shipped ⚑27', h: 'unit-finished.html?u=ep15' },
    { g: 'Units', ic: 'flag', l: 'ep14 The Great Panic', s: 'War of the Worlds · shipped ⚑26', h: 'unit-finished.html?u=ep14' },
    { g: 'Units', ic: 'flag', l: 'ep13 How I Fell in with the Curate', s: 'War of the Worlds · shipped ⚑20 · 52 runs', h: 'unit-finished.html?u=ep13' },
    { g: 'Units', ic: 'flag', l: 'ep12 Weybridge and Shepperton', s: 'War of the Worlds · shipped ⚑4', h: 'unit-finished.html?u=ep12' },
    { g: 'Units', ic: 'circle', l: 'ep01 The Eve of the War', s: 'War of the Worlds · queued, next', h: 'queue.html#q-episode' },
    { g: 'Units', ic: 'circle', l: 'ep02 The Falling Star', s: 'War of the Worlds · queued', h: 'queue.html#q-episode' },
    { g: 'Units', ic: 'circle', l: 'ep05 The Heat-Ray', s: 'War of the Worlds · queued', h: 'queue.html#q-episode' },
    { g: 'Units', ic: 'circle', l: 'refs · A Study in Scarlet', s: 'queued at 03 voices 2/4', h: 'queue.html#q-refs' },
    { g: 'Books', ic: 'book-open', l: 'The War of the Worlds', s: '17 episodes · 1 running · 16 cut', h: 'book.html' },
    { g: 'Books', ic: 'book-open', l: 'A Study in Scarlet', s: '7 episodes wait on refs/04', h: 'book.html?b=scarlet' },
    { g: 'Books', ic: 'layers', l: 'All 30 books', s: 'the shelf', h: 'books.html', k: 'G B' },
    { g: 'Departments', ic: 'clapperboard', l: 'episode', s: '31 units · 1 running · 3 queued', h: 'department.html?stage=episode', k: 'G E' },
    { g: 'Departments', ic: 'image', l: 'refs', s: '30 units · 29 queued', h: 'department.html?stage=refs' },
    { g: 'Departments', ic: 'film', l: 'trailer', s: '30 units · 30 queued', h: 'department.html?stage=trailer' },
    { g: 'Departments', ic: 'book-open', l: 'screenplay', s: '30 units · 30 queued', h: 'department.html?stage=screenplay' },
    { g: 'Departments', ic: 'search', l: 'analysis', s: '30 units · all done', h: 'department.html?stage=analysis' },
    { g: 'Pages', ic: 'gauge', l: 'Now', s: 'the GPU, needs you, up next', h: 'index.html', k: 'G N' },
    { g: 'Pages', ic: 'inbox', l: 'Needs you', s: '5 shipped with flags, not acknowledged', h: 'index.html#needs', k: 'G I' },
    { g: 'Pages', ic: 'clock', l: 'Queue', s: 'GPU lane · 92 queued', h: 'queue.html', k: 'G Q' },
    { g: 'Pages', ic: 'external-link', l: 'Org chart', s: 'architecture page', h: 'http://127.0.0.1:8700/org', k: 'G O' },
    { g: 'Actions', ic: 'sun-moon', l: 'Toggle theme', s: 'paper / screening room', act: 'theme', k: 'T' },
    { g: 'Actions', ic: 'circle-dashed', l: 'Keyboard shortcuts', s: '', act: 'keys', k: '?' },
    { g: 'Actions', ic: 'check', l: 'Acknowledge ep16 flags…', s: 'opens the confirm, places an ack order', act: 'ack' },
    { g: 'Actions', ic: 'pause', l: 'Hold studio…', s: 'stops every run before its next GPU step', act: 'hold' }
  ];
  var CHORDS = { n: 'index.html', i: 'index.html#needs', q: 'queue.html', b: 'books.html', r: 'unit-running.html', e: 'department.html?stage=episode', o: 'http://127.0.0.1:8700/org' };

  /* ---------------------------------------------------------- dialogs (injected once) */
  function inject() {
    if (document.getElementById('palette')) return;
    var d = document.createElement('div');
    d.innerHTML =
      '<dialog id="palette" class="palette" aria-label="Search and jump">' +
        '<div class="pal-head">' + icon('search') +
          '<input id="pal-q" type="text" placeholder="Jump to a unit, book, department or action…" autocomplete="off" spellcheck="false" role="combobox" aria-controls="pal-list" aria-expanded="true">' +
          '<span class="kbd">Esc</span></div>' +
        '<ul id="pal-list" class="pal-list" role="listbox"></ul>' +
        '<div class="pal-foot"><span><span class="kbd">↑</span><span class="kbd">↓</span>move</span><span><span class="kbd">↵</span>open</span><span><span class="kbd">G</span> then a letter goes anywhere</span></div>' +
      '</dialog>' +
      '<dialog id="keysheet" class="keysheet" aria-label="Keyboard shortcuts">' +
        '<header><h2>Keyboard</h2><button class="iconbtn" data-close aria-label="Close">' + icon('x') + '</button></header>' +
        '<div class="cols"><div><h3>Everywhere</h3><dl>' +
          '<dt><span class="kbd">Ctrl</span><span class="kbd">K</span></dt><dd>search &amp; jump (⌘K on a Mac)</dd>' +
          '<dt><span class="kbd">/</span></dt><dd>search</dd>' +
          '<dt><span class="kbd">?</span></dt><dd>this sheet</dd>' +
          '<dt><span class="kbd">G</span><span class="kbd">N</span></dt><dd>Now</dd>' +
          '<dt><span class="kbd">G</span><span class="kbd">I</span></dt><dd>Needs you</dd>' +
          '<dt><span class="kbd">G</span><span class="kbd">Q</span></dt><dd>Queue</dd>' +
          '<dt><span class="kbd">G</span><span class="kbd">B</span></dt><dd>Books</dd>' +
          '<dt><span class="kbd">G</span><span class="kbd">R</span></dt><dd>the running unit</dd>' +
          '<dt><span class="kbd">G</span><span class="kbd">E</span></dt><dd>episode department</dd>' +
          '<dt><span class="kbd">T</span></dt><dd>toggle theme</dd>' +
          '<dt><span class="kbd">Esc</span></dt><dd>close, clear</dd>' +
        '</dl></div><div><h3>Lists</h3><dl>' +
          '<dt><span class="kbd">J</span><span class="kbd">K</span></dt><dd>next / previous row</dd>' +
          '<dt><span class="kbd">↵</span></dt><dd>open the row</dd>' +
          '<dt><span class="kbd">Space</span></dt><dd>peek</dd>' +
          '<dt><span class="kbd">.</span></dt><dd>row actions (⋯)</dd>' +
          '<dt><span class="kbd">A</span></dt><dd>acknowledge (Now, Needs you)</dd>' +
          '</dl><h3>Unit</h3><dl>' +
          '<dt><span class="kbd">[</span><span class="kbd">]</span></dt><dd>previous / next unit in the book</dd>' +
          '<dt><span class="kbd">T</span><span class="kbd">M</span><span class="kbd">L</span></dt><dd>takes · master · log</dd>' +
        '</dl></div>' +
        '<div class="legend">' +
          '<span class="pill">' + icon('circle') + 'queued</span><span class="pill blocked">' + icon('circle-dashed') + 'blocked</span>' +
          '<span class="pill running">' + icon('loader') + 'running</span><span class="pill done">' + icon('check') + 'done</span>' +
          '<span class="pill flagged">' + icon('flag') + 'flagged</span><span class="pill deferred">' + icon('corner-up-left') + 'deferred</span>' +
          '<span class="pill failed">' + icon('x') + 'failed</span><span class="pill escalated">' + icon('hand') + 'escalated</span>' +
          '<span class="pill held">' + icon('pause') + 'held</span><span class="pill stale">' + icon('history') + 'stale</span>' +
        '</div></div>' +
      '</dialog>' +
      '<div id="toast" class="toast" role="status" hidden></div>';
    while (d.firstChild) document.body.appendChild(d.firstChild);
  }

  /* ---------------------------------------------------------- palette */
  var sel = 0, shown = [];
  function score(q, text) {           /* subsequence match; lower = better, -1 = none */
    if (!q) return 0;
    var t = text.toLowerCase(), i = 0, gaps = 0, last = -1;
    for (var j = 0; j < t.length && i < q.length; j++) {
      if (t[j] === q[i]) { gaps += last < 0 ? j : j - last - 1; last = j; i++; }
    }
    return i === q.length ? gaps : -1;
  }
  function mark(text, q) {
    if (!q) return esc(text);
    var out = '', i = 0, lt = text.toLowerCase();
    for (var j = 0; j < text.length; j++) {
      if (i < q.length && lt[j] === q[i]) { out += '<mark>' + esc(text[j]) + '</mark>'; i++; } else out += esc(text[j]);
    }
    return out;
  }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function render() {
    var q = document.getElementById('pal-q').value.trim().toLowerCase();
    shown = PALETTE.map(function (e) { return { e: e, s: score(q, e.l + ' ' + e.s + ' ' + e.g) }; })
      .filter(function (x) { return x.s >= 0; });
    if (q) shown.sort(function (a, b) { return a.s - b.s; });
    var html = '', group = null;
    shown.forEach(function (x, n) {
      if (!q && x.e.g !== group) { group = x.e.g; html += '<li class="pal-group" role="presentation">' + group + '</li>'; }
      html += '<li class="pal-item" role="option" id="pal-' + n + '" data-n="' + n + '" aria-selected="' + (n === sel) + '">' +
        icon(x.e.ic) + '<span class="lbl">' + mark(x.e.l, q) + '<small>' + esc(x.e.s) + '</small></span>' +
        '<span class="meta">' + (q ? '<span>' + x.e.g + '</span>' : '') + (x.e.k ? '<span class="kbd">' + x.e.k + '</span>' : '') + '</span></li>';
    });
    var list = document.getElementById('pal-list');
    list.innerHTML = html || '<li class="pal-empty">Nothing matches. Try a unit (ep16), a book or a department.</li>';
    var cur = document.getElementById('pal-' + sel);
    if (cur) { cur.scrollIntoView({ block: 'nearest' }); document.getElementById('pal-q').setAttribute('aria-activedescendant', cur.id); }
  }
  function openPalette() {
    var dlg = document.getElementById('palette');
    if (dlg.open) return;
    sel = 0; document.getElementById('pal-q').value = '';
    render(); dlg.showModal(); document.getElementById('pal-q').focus();
  }
  function run(n) {
    var x = shown[n]; if (!x) return;
    var e = x.e; document.getElementById('palette').close();
    if (e.h) { location.href = e.h; return; }
    if (e.act === 'theme') toggleTheme();
    else if (e.act === 'keys') document.getElementById('keysheet').showModal();
    else if (e.act === 'ack') toast('Mockup: the confirm dialog would open, then order “ack ep16” is placed · pending.');
    else if (e.act === 'hold') toast('Mockup: the hold dialog would ask “why hold?” — nothing is sent.');
  }

  /* ---------------------------------------------------------- theme, toast */
  function toggleTheme() {
    var root = document.documentElement;
    var dark = root.dataset.theme ? root.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
    root.dataset.theme = dark ? 'light' : 'dark';
    store('cc-theme', root.dataset.theme);
  }
  var tt;
  function toast(msg) {
    var t = document.getElementById('toast');
    t.innerHTML = icon('check') + '<span>' + esc(msg) + '</span>'; t.hidden = false;
    clearTimeout(tt); tt = setTimeout(function () { t.hidden = true; }, 3600);
  }
  window.board = { toast: toast, icon: icon, openPalette: openPalette };

  /* ---------------------------------------------------------- wiring */
  var saved = store('cc-theme'); if (saved) document.documentElement.dataset.theme = saved;
  document.addEventListener('DOMContentLoaded', function () {
    inject();
    var q = document.getElementById('pal-q');
    q.addEventListener('input', function () { sel = 0; render(); });
    q.addEventListener('keydown', function (ev) {
      if (ev.key === 'ArrowDown' || (ev.ctrlKey && ev.key === 'n')) { sel = Math.min(sel + 1, shown.length - 1); render(); ev.preventDefault(); }
      else if (ev.key === 'ArrowUp' || (ev.ctrlKey && ev.key === 'p')) { sel = Math.max(sel - 1, 0); render(); ev.preventDefault(); }
      else if (ev.key === 'Enter') { run(sel); ev.preventDefault(); }
    });
    document.getElementById('pal-list').addEventListener('click', function (ev) {
      var li = ev.target.closest('.pal-item'); if (li) run(+li.dataset.n);
    });
    document.getElementById('pal-list').addEventListener('mousemove', function (ev) {
      var li = ev.target.closest('.pal-item'); if (li && +li.dataset.n !== sel) { sel = +li.dataset.n; render(); }
    });
    ['palette', 'keysheet'].forEach(function (id) {   /* click on the backdrop closes */
      var dlg = document.getElementById(id);
      dlg.addEventListener('click', function (ev) { if (ev.target === dlg || ev.target.closest('[data-close]')) dlg.close(); });
    });
    document.querySelectorAll('[data-palette]').forEach(function (b) { b.addEventListener('click', function (ev) { ev.preventDefault(); openPalette(); }); });
    document.querySelectorAll('[data-theme-toggle]').forEach(function (b) { b.addEventListener('click', toggleTheme); });
    document.querySelectorAll('[data-keys]').forEach(function (b) { b.addEventListener('click', function (ev) { ev.preventDefault(); document.getElementById('keysheet').showModal(); }); });
    document.querySelectorAll('[data-order]').forEach(function (b) {   /* any order button: receipt only */
      b.addEventListener('click', function (ev) { ev.preventDefault(); var m = b.closest('details'); if (m) m.open = false; toast('Mockup: order “' + b.dataset.order + '” would be placed · pending until a run takes it.'); });
    });
  });
  document.addEventListener('click', function (ev) {   /* close open ⋯ / ▾ menus on outside click */
    document.querySelectorAll('details.rowmenu[open], details.menu[open]').forEach(function (d) { if (!d.contains(ev.target)) d.open = false; });
  });

  var gPending = 0;
  document.addEventListener('keydown', function (ev) {
    var tag = (ev.target.tagName || '').toLowerCase();
    if ((ev.metaKey || ev.ctrlKey) && ev.key.toLowerCase() === 'k') { ev.preventDefault(); openPalette(); return; }
    if (tag === 'input' || tag === 'textarea' || tag === 'select' || ev.target.isContentEditable) return;
    if (document.querySelector('dialog[open]') || ev.metaKey || ev.ctrlKey || ev.altKey) return;
    if (gPending && CHORDS[ev.key.toLowerCase()]) { location.href = CHORDS[ev.key.toLowerCase()]; return; }
    if (ev.key === 'g' || ev.key === 'G') { gPending = 1; setTimeout(function () { gPending = 0; }, 1200); return; }
    if (ev.key === '/') { ev.preventDefault(); openPalette(); }
    else if (ev.key === '?') { ev.preventDefault(); document.getElementById('keysheet').showModal(); }
    else if (ev.key === 't' || ev.key === 'T') toggleTheme();
    else if (ev.key === 'j' || ev.key === 'k') {        /* j/k walk [data-row] rows */
      var rows = Array.prototype.slice.call(document.querySelectorAll('[data-row]'));
      if (!rows.length) return;
      var i = rows.indexOf(document.activeElement.closest('[data-row]'));
      i = ev.key === 'j' ? Math.min(i + 1, rows.length - 1) : Math.max(i - 1, 0);
      rows[i].focus();
    }
  });
})();
