/* pulse.js -- the board's one heartbeat (panel ruling PKG-2, contracts C1 and C3; no dependency, MIT).
   One loop per tab: GET /api/pulse.json every 2 s (10 s on a Worker timer while the tab is hidden,
   2 -> 30 s backoff on failure). Each answer
     - patches the shell in place: the Needs-you badges, the queue count, the department dots and
       their spoken names, the pins, the GPU card (label, unit, step, ~finish, --p), the header chip,
       the held bar, the tab's title and favicon arc;
     - fires `pulse:<key>` on <body> for every fingerprint that changed (C3), so a section polls
       with hx-trigger="pulse:<key> from:body"; the request carries ?v=<the fp it last drew>, and the
       rows that changed in the morph get the class .chg;
     - dispatches `pulse` (and `pulse:events` when events arrived) on document for page scripts;
     - drives the heartbeat chip: live / N s old / offline, retrying / board restarted, reload,
       and <html data-stale> while the data is late or the board is down.
   The pure core at the top (chipState, chipText, delay, changedKeys, liveTitle, dots, deptLabel,
   hhmm) is exported for node, where the tests run it. */
(function (root) {
  'use strict';

  /* ------------------------------------------------------------ the pure core */
  var DOTS = [['run', 'running'], ['fail', 'failed'], ['flag', 'flagged']];
  var STOPS = { dead: 1, stalled: 1, refused: 1, done: 1 };

  function chipState(age, err, bootChanged, cfg) {      /* mirrors shell.chip_state */
    if (bootChanged) return 'restart';
    if (err) return 'offline';
    return age > cfg.stale ? 'stale' : 'live';
  }
  function chipText(state, age, retryIn) {
    return { live: '● live', stale: '◌ ' + Math.round(age) + ' s old',
      offline: retryIn >= 1 ? '✕ offline · retrying in ' + Math.round(retryIn) + ' s' : '✕ offline · retrying now',
      restart: '↻ board restarted · reload' }[state];
  }
  function delay(fails, hidden, cfg) {                  /* seconds to the next pulse */
    if (fails > 0) return cfg.backoff[Math.min(fails, cfg.backoff.length) - 1];
    return hidden ? cfg.hidden : cfg.period;
  }
  function changedKeys(prev, next) {                    /* every key on the first pulse */
    return Object.keys(next || {}).filter(function (k) { return !prev || prev[k] !== next[k]; });
  }
  function pageName(base) { return String(base || '').replace(/ · Visurena Studio$/, ''); }
  function liveTitle(sh, base) {
    var g = sh && sh.gpu;
    if (g) return ['● ' + g.unit, g.step, g.finish ? '~' + g.finish : '', pageName(base)].filter(Boolean).join(' · ');
    if (sh && sh.hold) return '⏸ held · ' + pageName(base);
    return base;
  }
  function dots(counts, total) {                        /* mirrors shell.dots */
    var out = DOTS.filter(function (d) { return counts[d[1]]; })
      .map(function (d) { return [d[0], counts[d[1]], counts[d[1]] + ' ' + d[1]]; });
    if (!out.length && total && counts.done === total) out.push(['done', total, 'all ' + total + ' done']);
    return out;
  }
  function deptLabel(stage, d, total) {                 /* mirrors shell.dept_label */
    var words = d.map(function (x) { return x[2]; });
    return [stage].concat(words.length ? words : [total + ' units']).join(', ');
  }
  function hhmm(iso) {                                  /* local HH:MM; a zoneless ISO is UTC */
    var t = new Date(/Z$|[+-]\d\d:?\d\d$/.test(iso || '') ? iso : (iso || '') + 'Z');
    return isNaN(t) ? '' : String(t.getHours()).padStart(2, '0') + ':' + String(t.getMinutes()).padStart(2, '0');
  }
  var core = { chipState: chipState, chipText: chipText, delay: delay, changedKeys: changedKeys,
    liveTitle: liveTitle, dots: dots, deptLabel: deptLabel, hhmm: hhmm };
  if (typeof module === 'object' && module.exports) { module.exports = core; return; }
  root.PulseCore = core;

  /* ------------------------------------------------------------ the page */
  var doc = document, html = doc.documentElement;
  function $(id) { return doc.getElementById(id); }
  function all(sel, el) { return Array.prototype.slice.call((el || doc).querySelectorAll(sel)); }
  function text(el, sel, value) { var n = el && el.querySelector(sel); if (n && n.textContent !== value) n.textContent = value; return n; }
  function readJSON(id) { try { return JSON.parse(($(id) || {}).textContent || 'null'); } catch (e) { return null; } }
  function store(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function wash(el) {                                   /* .chg once (C3): the CSS draws it */
    if (!el) return;
    el.classList.remove('chg'); void el.offsetWidth; el.classList.add('chg');
    setTimeout(function () { el.classList.remove('chg'); }, 3000);
  }
  function svgIcon(id) {
    var ns = 'http://www.w3.org/2000/svg', s = doc.createElementNS(ns, 'svg'), u = doc.createElementNS(ns, 'use');
    var any = doc.querySelector('svg.i use'), sprite = any ? any.getAttribute('href').split('#')[0] : '/static/icons.svg';
    s.setAttribute('class', 'i'); s.setAttribute('aria-hidden', 'true'); u.setAttribute('href', sprite + '#' + id);
    s.appendChild(u); return s;
  }

  var cfg = readJSON('pulse-cfg') || { period: 2, hidden: 10, stale: 5, timeout: 8, backoff: [2, 4, 8, 16, 30] };
  var S = { fp: null, boot: null, okAt: Date.now(), fails: 0, busy: false, nextAt: 0, restart: false,
    last: null, cursor: null, base: doc.title, gen: 0, timer: 0, chipTimer: 0, icon: '' };

  /* --- the shell patches --- */
  function patchCounts(sh) {
    all('[data-needs]').forEach(function (b) {
      if (b.textContent === String(sh.needs)) return;
      b.textContent = sh.needs; b.dataset.n = sh.needs; wash(b);
    });
    all('[data-queue]').forEach(function (n) { if (n.textContent !== String(sh.queue)) { n.textContent = sh.queue; wash(n); } });
    all('[data-running]').forEach(function (n) {
      var want = String((sh.pins || []).length);
      if (n.textContent !== want) { n.textContent = want; wash(n); }
    });
  }

  /* --- the Today feed: pulse events land as rows, once each, newest first --- */
  function feedRow(ev) {
    var li = doc.createElement('li'), ic = doc.createElement('span'), s = doc.createElement('span');
    var b = doc.createElement('b'), t = doc.createElement('time'), d = new Date((ev.ts || 0) * 1000);
    li.id = 'pulse-ev-' + ev.id; li.className = 'fe chg';
    ic.className = 'ic'; b.textContent = ev.unit || ''; s.appendChild(b);
    s.appendChild(doc.createTextNode(' ' + (ev.text || '')));
    t.textContent = String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0');
    li.appendChild(ic); li.appendChild(s); li.appendChild(t);
    return li;
  }
  function feedEvents(evs) {
    var feed = $('since-feed');
    if (!feed) return;
    evs.slice().reverse().forEach(function (ev) {
      if (String(ev.id).indexOf('ord-') === 0 || feed.querySelector('#pulse-ev-' + ev.id)) return;
      feed.insertBefore(feedRow(ev), feed.querySelector('.fe'));
    });
    var rows = all('.fe', feed);
    for (var i = rows.length - 1; i >= 40; i--) rows[i].remove();
    var empty = feed.parentElement && feed.parentElement.querySelector('.empty');
    if (empty && rows.length) empty.hidden = true;
  }
  function patchDept(a, counts) {
    var total = +a.dataset.total || 0, d = dots(counts || {}, total), sig = JSON.stringify(d);
    if (a.__dots === sig) return;
    var box = a.querySelector('.sb-dots'), first = a.__dots === undefined;
    a.__dots = sig;
    a.setAttribute('aria-label', deptLabel(a.dataset.dept, d, total));
    if (d.length) a.dataset.dot = d[0][0]; else delete a.dataset.dot;
    if (!box) return;
    box.textContent = '';
    d.forEach(function (x) { var i = doc.createElement('i'); i.className = x[0]; i.title = x[2]; if (x[0] !== 'done') i.textContent = x[1]; box.appendChild(i); });
    if (!first) wash(box);                               /* the first pulse only confirms the server's drawing */
  }
  function makePin(p) {
    var a = doc.createElement('a'), face = doc.createElement('span'), dot = doc.createElement('span');
    var lbl = doc.createElement('span'), b = doc.createElement('b'), parts = String(p.label || '').split(' · ');
    a.className = 'sb-item sb-pin'; a.href = p.href; a.dataset.testid = 'pin'; a.dataset.pin = p.href; a.title = p.label;
    face.className = 'sb-face'; face.appendChild(svgIcon('loader')); dot.className = 'sdot'; face.appendChild(dot);
    lbl.className = 'lbl'; b.className = 'pin-id'; b.textContent = parts[0]; lbl.appendChild(b);
    lbl.appendChild(doc.createTextNode(parts.slice(1).join(' · ')));
    a.appendChild(face); a.appendChild(lbl); wash(a); return a;
  }
  function patchPins(pins) {
    var sig = pins.map(function (p) { return p.href + '|' + p.state; }).join(',');
    all('[data-pins]').forEach(function (box) {
      if (box.__sig === sig) return;
      box.__sig = sig;
      var have = {}, empty = box.querySelector('.sb-empty');
      all('[data-pin]', box).forEach(function (a) { have[a.dataset.pin] = a; });
      pins.forEach(function (p) {
        var a = have[p.href] || makePin(p); delete have[p.href];
        var dot = a.querySelector('.sdot'); if (dot) dot.className = 'sdot ' + p.state;
        if (p.href === location.pathname) a.setAttribute('aria-current', 'page');
        box.insertBefore(a, empty);
      });
      Object.keys(have).forEach(function (k) { have[k].remove(); });
      if (empty) empty.hidden = pins.length > 0;
    });
  }
  function gpuLabel(g, hold) { return g ? (hold ? 'Held · finishing its step' : 'On the GPU') : (hold ? 'Studio held' : 'GPU idle'); }
  function patchFace(card, g) {
    var key = g ? g.href : '', face = card.querySelector('[data-gc-face]');
    var drawn = card.__face !== undefined ? card.__face : (card.classList.contains('idle') ? '' : card.getAttribute('href'));
    card.__face = key;
    if (!face || drawn === key) return;
    var img = g && doc.querySelector('[data-pin="' + CSS.escape(g.href) + '"] img');
    face.textContent = '';
    if (img) { var n = img.cloneNode(); n.width = n.height = 40; face.appendChild(n); } else face.appendChild(svgIcon('cpu'));
  }
  function patchGpu(card, g, hold) {
    var step = g ? (g.step || '') : (hold ? 'nothing starts until you lift' : 'nothing running');
    patchFace(card, g);
    card.classList.toggle('idle', !g); card.classList.toggle('held', !!hold);
    card.setAttribute('href', g ? g.href : '/queue');
    card.title = g ? 'On the GPU: ' + g.unit + ' · ' + step : gpuLabel(g, hold);
    text(card, '[data-gc-label]', gpuLabel(g, hold)); text(card, '[data-gc-unit]', g ? g.unit : '');
    text(card, '[data-gc-eta]', g && g.finish ? '~' + g.finish : '');
    if (text(card, '[data-gc-step]', step) && card.__step !== undefined && card.__step !== step) wash(card.querySelector('.t2'));
    card.__step = step;
    var f = g && typeof g.frac === 'number' ? Math.max(0, Math.min(1, g.frac)) : 0, bar = card.querySelector('[data-prog]');
    card.style.setProperty('--p', f); if (bar) bar.style.width = (100 * f).toFixed(1) + '%';
    var prog = card.querySelector('.prog'); if (prog) prog.hidden = !g;
    card.dataset.vital = g ? g.vital || '' : '';
  }
  function patchChip(g) {
    all('[data-gpuchip]').forEach(function (c) {
      c.hidden = !g; if (!g) return;
      c.setAttribute('href', g.href); text(c, '[data-gc-unit]', g.unit); text(c, '[data-eta]', g.finish ? ' · ~' + g.finish : '');
    });
  }
  function patchHold(h) {
    var bar = $('holdbar'); if (!bar) return;
    bar.hidden = !h; if (!h) return;
    var at = text(bar, '[data-hold-at]', hhmm(h.since)); if (at) at.setAttribute('datetime', h.since);
    text(bar, '[data-hold-reason]', '· “' + h.reason + '”');
    var lift = bar.querySelector('[data-lift]'); if (lift) lift.dataset.lift = h.id;
  }
  function favicon(sh) {
    if ($('live')) return;                               /* the tracker draws its own on a live unit */
    var g = sh.gpu, frac = g && typeof g.frac === 'number' ? g.frac : 0, sig = (g ? g.href : '') + frac + !!sh.hold;
    if (S.icon === sig) return;
    S.icon = sig;
    try {
      var c = doc.createElement('canvas'), x = c.getContext('2d'), css = getComputedStyle(html);
      c.width = c.height = 32; x.lineWidth = 5;
      x.strokeStyle = css.getPropertyValue('--rule').trim() || '#2a2d33'; x.beginPath(); x.arc(16, 16, 12, 0, 2 * Math.PI); x.stroke();
      x.strokeStyle = css.getPropertyValue(sh.hold ? '--st-held' : '--st-running').trim() || '#7db6e3';
      x.beginPath(); x.arc(16, 16, 12, -Math.PI / 2, -Math.PI / 2 + Math.max(g ? 0.04 : 0, frac) * 2 * Math.PI); x.stroke();
      var link = doc.querySelector('link[rel="icon"]') || doc.head.appendChild(Object.assign(doc.createElement('link'), { rel: 'icon' }));
      link.href = c.toDataURL('image/png');
    } catch (e) { /* no canvas: keep the default icon */ }
  }
  function patchShell(sh) {
    if (typeof sh.needs === 'number') patchCounts(sh);
    if (sh.dept_dots) all('[data-dept]').forEach(function (a) { patchDept(a, sh.dept_dots[a.dataset.dept]); });
    if (sh.pins) patchPins(sh.pins);
    all('[data-gpu]').forEach(function (c) { patchGpu(c, sh.gpu || null, sh.hold || null); });
    patchChip(sh.gpu || null); patchHold(sh.hold || null); favicon(sh);
    if (!$('live')) doc.title = liveTitle(sh, S.base);
  }

  /* --- notifications: the shell watches from any page while the tab is hidden --- */
  function notify(title, body, tag) {
    if (!doc.hidden || store('cc-notify') !== '1' || !root.Notification || Notification.permission !== 'granted') return;
    try { new Notification(title, { body: body, tag: tag }); } catch (e) { /* a platform without page notifications */ }
  }
  function watch(prev, sh) {
    if (!prev) return;
    var a = prev.gpu, b = sh.gpu;
    if (a && (!b || b.href !== a.href)) notify(a.unit + ' left the GPU', b ? b.unit + ' is on it now' : 'the GPU is idle', a.unit + ':left');
    else if (a && b && b.vital !== a.vital && STOPS[b.vital]) notify(b.unit + ' · ' + b.vital, b.step || '', b.unit + ':' + b.vital);
    if ((sh.needs || 0) > (prev.needs || 0)) notify(sh.needs + ' need you', 'Needs you went from ' + prev.needs + ' to ' + sh.needs, 'needs');
  }
  function wireNotify() {
    var on = function () { return store('cc-notify') === '1' && root.Notification && Notification.permission === 'granted'; };
    all('[data-notify]').forEach(function (b) {
      if (!root.Notification) return;
      b.hidden = false; b.setAttribute('aria-pressed', String(!!on()));
      b.addEventListener('click', function () {
        if (on()) { try { localStorage.setItem('cc-notify', '0'); } catch (e) {} b.setAttribute('aria-pressed', 'false'); return; }
        Notification.requestPermission().then(function (p) {
          if (p !== 'granted') return; try { localStorage.setItem('cc-notify', '1'); } catch (e) {}
          all('[data-notify]').forEach(function (x) { x.setAttribute('aria-pressed', 'true'); });
        });
      });
    });
  }

  /* --- the heartbeat chip --- */
  function paintChip() {
    var age = (Date.now() - S.okAt) / 1000, st = chipState(age, S.fails > 0, S.restart, cfg);
    var hb = $('hb'), retry = S.fails ? (S.nextAt - Date.now()) / 1000 : 0;
    if (hb) { hb.dataset.hb = st; text(hb, '[data-hb-text]', chipText(st, age, retry)); }
    if (st === 'stale' || st === 'offline') html.setAttribute('data-stale', ''); else html.removeAttribute('data-stale');
    clearTimeout(S.chipTimer);
    if (st === 'stale' || st === 'offline') S.chipTimer = setTimeout(paintChip, 1000);   /* only while degraded */
  }

  /* --- the loop: one timer, a Worker's while hidden (Chrome throttles hidden-tab timers) --- */
  var worker;
  function hiddenTimer() {
    if (worker !== undefined) return worker;
    try {
      var src = 'onmessage=function(e){setTimeout(function(){postMessage(e.data.g)},e.data.ms)}';
      worker = new Worker(URL.createObjectURL(new Blob([src], { type: 'text/javascript' })));
      worker.onmessage = function (e) { fire(e.data); };
    } catch (e) { worker = null; }
    return worker;
  }
  function fire(g) { if (g === S.gen) tick(); }
  function later(sec) {
    var g = ++S.gen; clearTimeout(S.timer); S.nextAt = Date.now() + sec * 1000;
    if (doc.hidden && hiddenTimer()) worker.postMessage({ ms: sec * 1000, g: g });
    else S.timer = setTimeout(function () { fire(g); }, sec * 1000);
  }
  function fireSections(keys) {
    if (S.restart || !root.htmx) return;                 /* a new board: offer a reload, never morph into an old page */
    keys.forEach(function (k) { htmx.trigger(doc.body, 'pulse:' + k, { fp: S.fp[k] }); });
  }
  function ok(p) {
    var prev = S.last && S.last.shell, keys;
    S.fails = 0; S.okAt = Date.now();
    if (S.boot === null) S.boot = p.boot; else if (p.boot !== S.boot) S.restart = true;
    keys = changedKeys(S.fp, p.fp || {}); S.fp = p.fp || {};
    if (p.cursor !== undefined && p.cursor !== null) S.cursor = p.cursor;
    fireSections(keys);                                  /* sections first: a shell-patch error must not eat them */
    patchShell(p.shell || {}); watch(prev, p.shell || {});
    S.last = p;
    doc.dispatchEvent(new CustomEvent('pulse', { detail: p }));
    if (p.events && p.events.length) { feedEvents(p.events); doc.dispatchEvent(new CustomEvent('pulse:events', { detail: p.events })); }
  }
  function tick() {
    if (S.busy) return;
    S.busy = true;
    var ctl = root.AbortController ? new AbortController() : null;
    var stop = setTimeout(function () { if (ctl) ctl.abort(); }, cfg.timeout * 1000);
    fetch('/api/pulse.json' + (S.cursor !== null ? '?since=' + encodeURIComponent(S.cursor) : ''), { cache: 'no-store', signal: ctl && ctl.signal })
      .then(function (r) { if (!r.ok) throw new Error('pulse ' + r.status); return r.json(); })
      .then(ok)
      .catch(function () { S.fails += 1; })                /* a throw INSIDE ok() too: the loop must never die */
      .then(function () { clearTimeout(stop); S.busy = false; later(delay(S.fails, doc.hidden, cfg)); paintChip(); });
  }
  function now() { if (!S.busy) { S.gen++; tick(); } }

  /* --- C3: a pulse-fired request carries the fp it last drew; the rows that changed wash --- */
  function pulseKey(evt) { var t = evt && evt.type; return t && t.indexOf('pulse:') === 0 ? t.slice(6) : null; }
  function signature(n) { return n.textContent.replace(/\s+/g, ' ') + '|' + (n.getAttribute('data-state') || ''); }
  function snapshot(el) { var m = {}; all('[id]', el).forEach(function (n) { m[n.id] = signature(n); }); return m; }
  function markChanged(el, before) {
    var changed = all('[id]', el).filter(function (n) { return before[n.id] !== signature(n); });
    changed.forEach(function (n) {
      var up = n.parentElement && n.parentElement.closest('[id]');
      if (!(up && el.contains(up) && changed.indexOf(up) >= 0)) wash(n);
    });
  }
  doc.addEventListener('htmx:configRequest', function (e) {
    var key = pulseKey(e.detail.triggeringEvent); if (!key || !S.fp) return;
    e.detail.parameters.v = e.detail.elt.getAttribute('data-v') || '';
    e.detail.elt.__pulseFp = S.fp[key];
  });
  doc.addEventListener('htmx:beforeSwap', function (e) {
    var rc = e.detail.requestConfig || {}; if (!pulseKey(rc.triggeringEvent) || !e.detail.target) return;
    e.detail.target.__pulseSnap = snapshot(e.detail.target);
  });
  doc.addEventListener('htmx:afterSettle', function (e) {
    var t = e.detail.target, snap = t && t.__pulseSnap; if (!snap) return;
    t.__pulseSnap = null; markChanged(t, snap);
  });
  doc.addEventListener('htmx:afterRequest', function (e) {
    var elt = e.detail.elt, x = e.detail.xhr, fp = elt && elt.__pulseFp;
    if (!fp) return;
    elt.__pulseFp = null;                               /* 204 = "you already draw this fp": land it too */
    if (x && (x.status === 200 || x.status === 204)) elt.setAttribute('data-v', fp);
  });

  /* --- wiring --- */
  function start() {
    var hb = $('hb');
    if (hb) hb.addEventListener('click', function () { if (S.restart) location.reload(); else now(); });
    doc.body.addEventListener('orders-changed', now);    /* an order given here shows at once */
    doc.addEventListener('visibilitychange', function () { if (!doc.hidden) now(); else later(delay(S.fails, true, cfg)); });
    root.addEventListener('online', now);
    wireNotify(); tick();
  }
  root.pulse = { now: now, last: function () { return S.last; }, core: core };
  if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', start); else start();
})(typeof window !== 'undefined' ? window : this);
