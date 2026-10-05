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
    { g: 'Pages', ic: 'house', l: 'Home', s: 'now on the GPU, needs you, up next', h: 'index.html', k: 'G H' },
    { g: 'Pages', ic: 'inbox', l: 'Needs you', s: '5 shipped with flags, not acknowledged', h: 'index.html#needs', k: 'G I' },
    { g: 'Pages', ic: 'clock', l: 'Queue', s: 'GPU lane · 92 queued', h: 'queue.html', k: 'G Q' },
    { g: 'Pages', ic: 'network', l: 'Architecture', s: 'the org chart · current, future, command center', h: 'architecture.html', k: 'G A' },
    { g: 'Pages', ic: 'external-link', l: 'Org chart', s: 'architecture page, standalone', h: 'http://127.0.0.1:8700/org', k: 'G O' },
    { g: 'Actions', ic: 'sun-moon', l: 'Toggle theme', s: 'studio black / graphite', act: 'theme', k: 'T' },
    { g: 'Actions', ic: 'circle-dashed', l: 'Keyboard shortcuts', s: '', act: 'keys', k: '?' },
    { g: 'Actions', ic: 'check', l: 'Acknowledge ep16 flags…', s: 'opens the confirm, places an ack order', act: 'ack' },
    { g: 'Actions', ic: 'pause', l: 'Hold studio…', s: 'stops every run before its next GPU step', act: 'hold' }
  ];
  var CHORDS = { h: 'index.html', n: 'index.html', a: 'architecture.html', i: 'index.html#needs', q: 'queue.html', b: 'books.html', r: 'unit-running.html', e: 'department.html?stage=episode', o: 'http://127.0.0.1:8700/org' };

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
          '<dt><span class="kbd">G</span><span class="kbd">H</span></dt><dd>Home (G N too)</dd>' +
          '<dt><span class="kbd">G</span><span class="kbd">I</span></dt><dd>Needs you</dd>' +
          '<dt><span class="kbd">G</span><span class="kbd">Q</span></dt><dd>Queue</dd>' +
          '<dt><span class="kbd">G</span><span class="kbd">B</span></dt><dd>Books</dd>' +
          '<dt><span class="kbd">G</span><span class="kbd">R</span></dt><dd>the running unit</dd>' +
          '<dt><span class="kbd">G</span><span class="kbd">E</span></dt><dd>episode department</dd>' +
          '<dt><span class="kbd">G</span><span class="kbd">A</span></dt><dd>Architecture</dd>' +
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
  function toggleTheme() {            /* v2: Studio black is the default, Graphite the light option */
    var p = document.documentElement.dataset.palette === 'graphite' ? 'studio' : 'graphite';
    setPalette(p);
  }
  function setPalette(p) {
    var root = document.documentElement;
    root.dataset.palette = p; root.dataset.theme = p === 'studio' ? 'dark' : 'light';
    store('palette', p);
  }
  var tt;
  function toast(msg) {
    var t = document.getElementById('toast');
    t.innerHTML = icon('check') + '<span>' + esc(msg) + '</span>'; t.hidden = false;
    clearTimeout(tt); tt = setTimeout(function () { t.hidden = true; }, 3600);
  }
  window.board = { toast: toast, icon: icon, openPalette: openPalette, toggleTheme: toggleTheme };

  /* ---------------------------------------------------------- v2 shell: sidebar, slim header, phone tabs
     One place for every page: <body data-page="now|inbox|queue|books|book|department|unit">.
     Values captured read-only 2026-10-04 19:21 PDT. The build renders this server-side. */
  var THUMB = 'http://127.0.0.1:8700/thumb/20260827135508/';
  var GPU = { unit: 'ep17', title: 'The Thunder Child', step: '07 board', eta: '21:35', pct: 16,
    face: THUMB + '160/episodes/ep17/storyboard/anchors/steamer_forward.png', h: 'unit-running.html' };
  var NAV = [
    { id: 'now', ic: 'house', l: 'Home', h: 'index.html', k: 'G H' },
    { id: 'inbox', ic: 'inbox', l: 'Inbox', h: 'index.html#needs', bdg: 5, k: 'G I' },
    { id: 'queue', ic: 'list-ordered', l: 'Queue', h: 'queue.html', n: 92, k: 'G Q' },
    { id: 'books', ic: 'library', l: 'Books', h: 'books.html', n: 30, k: 'G B' },
    { id: 'arch', ic: 'network', l: 'Architecture', h: 'architecture.html', k: 'G A' }
  ];
  var DEPTS = [   /* units in the department; dots = the state tally (running blue, flagged amber) */
    { id: 'analysis', ic: 'search', n: 30, dots: [['done', 30, 'all 30 done']] },
    { id: 'screenplay', ic: 'scroll-text', n: 30, dots: [] },
    { id: 'trailer', ic: 'film', n: 30, dots: [] },
    { id: 'refs', ic: 'user-round', n: 30, dots: [['flag', 1, '1 flagged (The War of the Worlds)']] },
    { id: 'episode', ic: 'clapperboard', n: 31, dots: [['run', 1, '1 running'], ['flag', 5, '5 flagged, not acknowledged']] }
  ];
  var PINS = [
    { u: 'ep17', l: 'The Thunder Child', sub: 'running', st: 'running', h: 'unit-running.html', face: THUMB + '160/episodes/ep17/storyboard/anchors/steamer_forward.png' },
    { u: 'ep16', l: 'The Exodus Northward', sub: 'flagged', st: 'flagged', h: 'unit-finished.html?u=ep16', face: THUMB + '160/episodes/ep16/storyboard/shot_05.png' }
  ];
  var MOCKS = [['index.html', 'Home'], ['queue.html', 'Queue'], ['unit-running.html', 'Unit · running'], ['unit-finished.html', 'Unit · finished'],
    ['department.html', 'Department'], ['book.html', 'Book'], ['books.html', 'Books'], ['architecture.html', 'Architecture']];
  var MARK = '<svg viewBox="0 0 32 32" aria-hidden="true"><circle cx="16" cy="16" r="10" fill="none" stroke="#d6d8dd" stroke-width="4.5"/><path d="M16 6a10 10 0 0 1 10 10" fill="none" stroke="#7db6e3" stroke-width="4.5"/><circle cx="26" cy="6" r="4" fill="#e9b44c"/></svg>';

  function here() {
    var b = document.body, page = b.dataset.page || 'now', file = location.pathname.split('/').pop() || 'index.html';
    var stage = new URLSearchParams(location.search).get('stage') || 'episode';
    return { page: page, file: file, unit: b.dataset.unit || '', dept: page === 'department' ? stage : (page === 'unit' && !PINS.some(function (p) { return p.u === b.dataset.unit; }) ? 'episode' : '') };
  }
  function cur(on) { return on ? ' aria-current="page"' : ''; }
  function navHTML(at) {
    return NAV.map(function (x) {
      var on = x.id === at.page || (x.id === 'books' && at.page === 'book');
      return '<a class="sb-item" href="' + x.h + '"' + cur(on) + ' title="' + x.l + ' (' + x.k + ')">' + icon(x.ic) + '<span class="lbl">' + x.l + '</span>' +
        (x.bdg ? '<span class="bdg" data-needs>' + x.bdg + '</span>' : (x.n ? '<span class="n">' + x.n + '</span>' : '')) + '</a>';
    }).join('');
  }
  function deptHTML(at) {
    return DEPTS.map(function (d) {
      var dots = d.dots.map(function (t) { return '<i class="' + t[0] + '" title="' + t[2] + '">' + (t[0] === 'done' ? '' : t[1]) + '</i>'; }).join('');
      var lead = d.dots.length ? d.dots[d.dots.length - 1][0] : '';
      return '<a class="sb-item dept" href="department.html?stage=' + d.id + '"' + cur(at.dept === d.id) + (lead ? ' data-dot="' + lead + '"' : '') +
        ' title="' + d.id + ' · ' + d.n + ' units">' + icon(d.ic) + '<span class="lbl">' + d.id + '</span><span class="sb-dots">' + dots + '</span><span class="n">' + d.n + '</span></a>';
    }).join('');
  }
  function pinHTML(at) {
    return PINS.map(function (p) {
      return '<a class="sb-item sb-pin" href="' + p.h + '"' + cur(at.unit === p.u) + ' title="' + p.u + ' ' + p.l + ' · ' + p.sub + '">' +
        '<span class="sb-face"><img src="' + p.face + '" alt="" width="24" height="24"><span class="st ' + p.st + '"></span></span>' +
        '<span class="lbl"><b class="pin-id">' + p.u + '</b>' + p.l + '</span></a>';
    }).join('');
  }
  function footHTML() {
    return '<div class="sb-foot"><a class="gpu-card" href="' + GPU.h + '" title="On the GPU: ' + GPU.unit + ' ' + GPU.title + ', ' + GPU.step + ', done around ' + GPU.eta + ' (20:20–22:40)">' +
        '<span class="face"><img src="' + GPU.face + '" alt="" width="40" height="40"></span>' +
        '<span class="t1"><span class="live"></span>On the GPU<span class="eta">~' + GPU.eta + '</span></span>' +
        '<span class="t2"><b>' + GPU.unit + '</b>' + GPU.step + '</span>' +
        '<span class="prog" aria-label="run ' + GPU.pct + '% of its p50"><i style="width:' + GPU.pct + '%"></i></span></a>' +
      '<button class="sb-search" type="button" data-palette>' + icon('search') + '<span>Search or jump</span><span class="kbd">Ctrl K</span></button>' +
      '<div class="sb-tools"><button type="button" data-theme-toggle title="Theme (T)" aria-label="Toggle theme">' + icon('sun-moon') + '</button>' +
        '<button type="button" data-keys title="Keyboard (?)" aria-label="Keyboard shortcuts">' + icon('keyboard') + '</button>' +
        '<a href="http://127.0.0.1:8700/org" title="Org chart (G O)" aria-label="Org chart">' + icon('layers') + '</a>' +
        '<span class="who">19:21 PDT</span></div></div>';
  }
  function sideHTML(at) {
    var mocks = MOCKS.map(function (m) { return '<a href="' + m[0] + '"' + cur(m[0] === at.file) + '>' + m[1] + '</a>'; }).join('');
    return '<div class="sb-top"><a class="sb-mark" href="index.html" aria-label="Visurena Studio, Home">' + MARK + '</a>' +
        '<a class="sb-brand" href="index.html">Visurena</a><button class="sb-studio" type="button" data-palette title="Jump anywhere (Ctrl K)" aria-label="Jump anywhere">' + icon('chevrons-up-down') + '</button></div>' +
      '<div class="sb-scroll"><nav aria-label="Board">' + navHTML(at) + '</nav>' +
        '<div class="sb-sec"><div class="sb-h">Departments</div>' + deptHTML(at) + '</div>' +
        '<div class="sb-sec"><div class="sb-h">Pinned</div>' + pinHTML(at) + '</div>' +
        '<details class="sb-mock"><summary>' + icon('chevron-right') + 'Mockup pages</summary>' + mocks + '</details></div>' +
      footHTML();
  }
  function tabsHTML(at) {
    var t = [['now', 'house', 'Home', 'index.html'], ['inbox', 'inbox', 'Inbox', 'index.html#needs'], ['queue', 'list-ordered', 'Queue', 'queue.html'], ['books', 'library', 'Books', 'books.html']];
    return t.map(function (x) {
      var on = x[0] === at.page || (x[0] === 'books' && at.page === 'book');
      return '<a href="' + x[3] + '"' + cur(on) + '>' + icon(x[1]) + x[2] + (x[0] === 'inbox' ? '<span class="bdg" data-needs>5</span>' : '') + '</a>';
    }).join('') + '<button type="button" data-sheet>' + icon('menu') + 'More</button>';
  }
  function headerFor() {   /* a page may write its own <header class="ph">; else the shell builds one from its crumbs */
    var ph = document.querySelector('header.ph');
    if (!ph) {
      ph = document.createElement('header'); ph.className = 'ph';
      var crumbs = document.querySelector('nav.crumbs');
      if (!crumbs) { crumbs = document.createElement('nav'); crumbs.className = 'crumbs'; crumbs.innerHTML = '<span>' + esc(document.title.split('·').pop().split('—')[0].trim()) + '</span>'; }
      ph.appendChild(crumbs);
      ph.insertAdjacentHTML('beforeend', '<span class="spacer"></span><div class="ph-actions"></div>');
      var acts = document.querySelector('[data-ph-actions]');
      ph.querySelector('.ph-actions').appendChild(acts || document.createRange().createContextualFragment('<span class="livechip"><i></i>live · 19:21</span>'));
      document.body.insertBefore(ph, document.body.firstChild);
    }
    var pa = ph.querySelector('.ph-actions');
    if (pa && !pa.querySelector('.gpuchip')) pa.insertAdjacentHTML('beforeend', '<a class="gpuchip" href="' + GPU.h + '"><i></i>' + GPU.unit + ' · ~' + GPU.eta + '</a>');
  }
  function mountShell() {
    var at = here();
    document.querySelectorAll('.mock-ribbon, header.topbar, nav.tabs').forEach(function (n) { n.remove(); });   /* v1 shell, if a page still has it */
    headerFor();
    var side = document.getElementById('side') || document.createElement('aside');
    side.id = 'side'; side.className = 'side'; side.setAttribute('aria-label', 'Studio'); side.innerHTML = sideHTML(at);
    document.body.insertBefore(side, document.body.firstChild);
    var tabs = document.createElement('nav'); tabs.className = 'btabs'; tabs.setAttribute('aria-label', 'Phone'); tabs.innerHTML = tabsHTML(at);
    document.body.appendChild(tabs);
    var sheet = document.createElement('dialog'); sheet.className = 'sheet'; sheet.id = 'sheet'; sheet.setAttribute('aria-label', 'Studio menu');
    sheet.innerHTML = '<div class="grab"></div><div class="side">' + sideHTML(at) + '</div>';
    document.body.appendChild(sheet);
    sheet.addEventListener('click', function (ev) { if (ev.target === sheet || ev.target.closest('a')) sheet.close(); });
  }

  /* ---------------------------------------------------------- the Viewer (SPEC_v3): one <dialog id="viewer"> on every page.
     Loads viewer.css + docview.js + viewer.js + prov.js in order, then mounts the dialog once. */
  var VWV = Date.now();   /* mockup: never serve a stale viewer from the browser cache */
  function injectViewer() {
    if (document.getElementById('vw-css')) return;
    var css = document.createElement('link'); css.id = 'vw-css'; css.rel = 'stylesheet'; css.href = 'assets/viewer.css?v=' + VWV;
    document.head.appendChild(css);
    ['docview.js', 'viewer.js', 'prov.js'].forEach(function (f) {
      var sc = document.createElement('script'); sc.src = 'assets/' + f + '?v=' + VWV; sc.async = false;
      if (f === 'viewer.js') sc.onload = function () { if (window.Viewer) window.Viewer.mount(); };
      document.head.appendChild(sc);
    });
  }

  /* ---------------------------------------------------------- wiring */
  var saved = store('palette'); setPalette(saved === 'graphite' ? 'graphite' : 'studio');
  document.addEventListener('DOMContentLoaded', function () {
    mountShell();
    inject();
    injectViewer();
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
  });
  document.addEventListener('click', function (ev) {   /* delegated, so the injected sidebar's controls work too */
    var t = ev.target.closest('[data-palette]:not(html),[data-theme-toggle],[data-keys],[data-order],[data-sheet]');
    if (!t) return;
    ev.preventDefault();
    var sh = document.getElementById('sheet');
    if (sh && sh.open && !t.hasAttribute('data-sheet')) sh.close();
    if (t.hasAttribute('data-palette')) openPalette();
    else if (t.hasAttribute('data-theme-toggle')) toggleTheme();
    else if (t.hasAttribute('data-keys')) document.getElementById('keysheet').showModal();
    else if (t.hasAttribute('data-sheet')) sh.showModal();
    else { var m = t.closest('details'); if (m) m.open = false; toast('Mockup: order “' + t.dataset.order + '” would be placed · pending until a run takes it.'); }
  });
  document.addEventListener('click', function (ev) {   /* close open ⋯ / ▾ menus on outside click */
    document.querySelectorAll('details.rowmenu[open], details.menu[open]').forEach(function (d) { if (!d.contains(ev.target)) d.open = false; });
  });

  var gPending = 0;
  document.addEventListener('keydown', function (ev) {
    var tag = (ev.target.tagName || '').toLowerCase();
    var vw = document.getElementById('viewer'); if (vw && vw.open) return;   /* the Viewer owns every key while open */
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

