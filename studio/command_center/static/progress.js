/* The live card's client (progress tracker spec §3, §5).  Polls the JSON twin
   every 2 s while the tab is visible, patches the nodes that stay in place,
   ticks the clocks every second from the server's `now` (so a skewed browser
   clock does not matter), and swaps the whole card only when the run's shape
   changes (another step, another vital kind, another plan size).  No ETA math
   here: the finish is the server's. */
(function () {
  'use strict';
  var card = document.getElementById('live');
  if (!card || card.dataset.wired) return;
  card.dataset.wired = '1';
  var STOP = { done: 1, dead: 1 }, RUN = { live: 1, quiet: 1, stalled: 1 };
  var skew = num(card.dataset.now) - Date.now() / 1000, last = null, timer = null, lastSign = 0, lastOk = Date.now();

  function num(x) { var n = parseFloat(x); return isNaN(n) ? null : n; }
  function now() { return Date.now() / 1000 + skew; }
  function $(k, root) { return (root || card).querySelector('[data-k="' + k + '"]'); }
  function text(k, v) { var n = $(k); if (n && n.textContent !== v) n.textContent = v; }
  function span(s) {
    s = Math.max(0, Math.floor(s || 0));
    if (s >= 3600) return Math.floor(s / 3600) + 'h' + String(Math.floor(s % 3600 / 60)).padStart(2, '0');
    return s >= 60 ? Math.floor(s / 60) + 'm' : s + 's';
  }
  function mmss(s) {
    s = Math.max(0, Math.floor(s || 0));
    var m = String(Math.floor(s % 3600 / 60)), ss = String(s % 60).padStart(2, '0');
    return s >= 3600 ? Math.floor(s / 3600) + ':' + m.padStart(2, '0') + ':' + ss : m + ':' + ss;
  }
  function shape(p) {
    var st = p.now_step || {}, group = RUN[p.vital] ? 'run' : p.vital;
    return group + '|' + st.id + '|' + st.kind + '|' + (p.items || []).length;
  }

  /* --- every second: the clocks and the developing tile --- */
  function tick() {
    if (document.documentElement.hasAttribute('data-stale')) return;   /* the board is stale: every clock freezes (5.9) */
    var t = now(), stepT = num(card.dataset.step), runT = num(card.dataset.run);
    card.querySelectorAll('[data-clock]').forEach(function (n) {
      var k = n.dataset.clock, v = '';
      if (k === 'step' && stepT) v = span(t - stepT);
      else if (k === 'step-mmss' && stepT) v = mmss(t - stepT);
      else if (k === 'work' && runT) v = span(num(n.dataset.base) + t - runT);
      else if (k === 'quiet' && num(n.dataset.at)) v = span(t - num(n.dataset.at));
      if (v && n.textContent !== v) n.textContent = v;
    });
    var hot = card.querySelector('.lt.st-rendering[data-prior]');
    var began = num(card.dataset.inflight);
    if (hot && began) hot.style.setProperty('--dev', Math.min(0.92, (t - began) / num(hot.dataset.prior)).toFixed(3));
  }

  /* --- every poll: patch in place --- */
  function tracePoints(p) {
    var pts = ['0,18'];
    (p.trace || []).map(function (s) { return 240 - (p.now - s) / 1800 * 240; }).sort(function (a, b) { return a - b; })
      .forEach(function (x) { x = Math.min(Math.max(x, 3), 237); pts.push((x - 3).toFixed(1) + ',18', x.toFixed(1) + ',4', (x + 3).toFixed(1) + ',18'); });
    return pts.concat(['240,18']).join(' ');
  }
  function patchVital(p) {
    card.dataset.vital = p.vital;
    if (p.vital === 'live') card.removeAttribute('data-still'); else card.setAttribute('data-still', '');
    text('vword', p.vital);
    if (p.now_step) text('where', p.now_step.id + ' ' + p.now_step.name);
    text('reason', p.vital === 'quiet' || p.vital === 'stalled' ? (p.vital_reason || '') : '');
    var line = $('trace'); if (line) line.setAttribute('points', tracePoints(p));
    var newest = (p.trace || []).slice(-1)[0] || 0, dot = $('dot');
    if (newest > lastSign && lastSign && dot) { dot.classList.remove('beat'); void dot.offsetWidth; dot.classList.add('beat'); }
    lastSign = newest;
    var q = card.querySelector('[data-clock="quiet"]'); if (q) q.dataset.at = newest || '';
  }
  function valuetext(p) {             /* progress_view.valuetext's words: `take 11 of 26, episode done around 02:45` */
    var st = p.now_step, e = p.eta || {};
    if (!st) return 'no run';
    var head = st.kind === 'counted' ? (st.id === '09' ? 'take' : 'panel') + ' ' + st.done + ' of ' + st.total : st.id + ' ' + st.name;
    var tail = e.finish ? 'episode done around ' + e.finish : '';
    return tail ? head + ', ' + tail : head;
  }
  function finishHtml(e) {            /* _live_hero.html's finish line: the EPISODE's, never the step's */
    if (!e.finish) return '';
    return 'done ~<b>' + e.finish + '</b>' + (e.long ? ' <span class="lv-why">at the earliest</span>' : '') +
      (e.capped ? ' <span class="lv-why">at the 5 h ceiling</span>' : '');
  }
  function rangeText(e) {            /* progress_view.range_words: the range, the steps, the runs */
    var out = [];
    if (e.range && !e.long) out.push('range ' + e.range);
    if (e.finish) out.push(e.steps_left + ' step' + (e.steps_left === 1 ? '' : 's') + ' to run');
    if (e.n_runs) out.push(e.n_runs + ' runs' + (e.basis ? ' · ' + e.basis : ''));
    return out.join(' · ');
  }
  function stepEnd(st, e) {           /* _live_hero.html's step line */
    return st.id + ' ' + st.name + ' ' + (e.step_end ? 'ends ~' + e.step_end : (e.long ? 'running long, past every measured full run' : ''));
  }
  function patchHero(p) {
    var st = p.now_step, e = p.eta || {};
    var bar = $('hero'); if (bar && bar.getAttribute('aria-valuetext') !== valuetext(p)) bar.setAttribute('aria-valuetext', valuetext(p));
    if (st && st.kind === 'counted') {
      var big = $('big'); if (big) big.innerHTML = st.done + '<span class="of">/' + st.total + '</span>';
      var hero = $('hero'); hero.setAttribute('aria-valuenow', st.done); hero.setAttribute('aria-valuemax', st.total);
    }
    if (st) text('current', st.current ? '· ' + st.current : '');
    var f = $('finish');
    if (f && e.finish && f.innerHTML !== finishHtml(e)) f.innerHTML = finishHtml(e);
    if (st) text('stepend', stepEnd(st, e));
    if (st && p.vital !== 'done') text('left', e.left || '–');
    text('range', rangeText(e));
    if (p.last_words) text('words', p.last_words);
    text('why', p.why || '');
    var why = $('why'); if (why && why.parentNode) why.parentNode.hidden = !p.why || p.vital === 'done';
  }
  function patchRail(p) {
    var st = p.now_step;
    (p.steps || []).forEach(function (s) {
      var seg = card.querySelector('.seg[data-id="' + s.id + '"]'); if (!seg) return;
      var was = (seg.className.match(/st-(\w+)/) || [])[1];
      if (was !== s.state) {
        seg.className = seg.className.replace(/st-\w+/, 'st-' + s.state);
        if (s.state === 'done') seg.classList.add('just');
        seg.classList.toggle('is-moving', s.state === 'running' && p.vital in RUN);
      }
      if (st && st.id === s.id && st.kind === 'counted' && st.weight_total) seg.style.setProperty('--p', (st.weight_done / st.weight_total).toFixed(4));
      var win = seg.querySelector('.win'); if (win && s.window && win.textContent !== s.window) win.textContent = s.window;
      var fin = seg.querySelector('.fin'); if (fin && s.fin && fin.textContent !== s.fin) fin.textContent = s.fin;
    });
  }
  function patchSheet(p) {
    card.dataset.inflight = p.inflight_started || '';
    (p.items || []).forEach(function (it) {
      var tile = card.querySelector('.lt[data-id="' + it.id + '"]'); if (!tile) return;
      var was = (tile.className.match(/st-(\w+)/) || [])[1];
      if (was !== it.state) {
        tile.className = tile.className.replace(/st-\w+/, 'st-' + it.state);
        if (it.state === 'landed' || it.state === 'retake') tile.classList.add('just');
      }
      if (it.prior_s) tile.dataset.prior = it.prior_s; else delete tile.dataset.prior;
      if (it.video) tile.dataset.video = it.video;
      var img = tile.querySelector('img');
      if (img && it.panel && img.getAttribute('src') !== p.media_base + it.panel) reveal(img, p.media_base + it.panel);
      tile.title = it.id + ' · ' + it.state + (it.secs ? ' · ' + Math.round(it.secs) + ' s' : '');
    });
  }
  function reveal(img, src) {        /* a new panel is decoded off-screen, then shown: never a blank tile (5.9) */
    var pre = new Image(); pre.src = src;
    (pre.decode ? pre.decode() : Promise.resolve()).then(function () { img.setAttribute('src', src); }, function () { img.setAttribute('src', src); });
  }
  function say(p, prev) {             /* the step change, spoken once before the card is replaced (C5) */
    var st = p.now_step || {}, text = p.unit + (p.vital !== prev ? ' ' + p.vital : '') + (st.id ? ' now ' + st.id + ' ' + st.name : '');
    if (window.board && window.board.announce) window.board.announce(text, { key: 'live:' + p.unit, urgent: p.vital === 'dead' || p.vital === 'refused' });
  }
  function watchLate() {             /* the card's own poll two beats late: the vital turns amber (5.9) */
    var late = lastOk && Date.now() - lastOk > 2 * 2000 + 1500;
    if (late) card.setAttribute('data-late', ''); else card.removeAttribute('data-late');
  }
  function favicon(p) {
    var c = document.createElement('canvas'); c.width = c.height = 32;
    var g = c.getContext('2d'), st = p.now_step || {}, css = getComputedStyle(document.documentElement);
    var frac = st.kind === 'counted' && st.total ? st.done / st.total : (p.vital === 'done' ? 1 : 0.25);
    var col = css.getPropertyValue(p.vital === 'done' ? '--ok' : (RUN[p.vital] ? '--think' : '--accent')).trim() || '#2c4f6b';
    g.lineWidth = 5; g.strokeStyle = css.getPropertyValue('--rule').trim() || '#d6cfc0';
    g.beginPath(); g.arc(16, 16, 12, 0, 2 * Math.PI); g.stroke();
    g.strokeStyle = col; g.beginPath(); g.arc(16, 16, 12, -Math.PI / 2, -Math.PI / 2 + frac * 2 * Math.PI); g.stroke();
    var link = document.querySelector('link[rel="icon"]') || document.head.appendChild(Object.assign(document.createElement('link'), { rel: 'icon' }));
    link.href = c.toDataURL('image/png');
  }
  function notify(prev, p) {
    var on = false; try { on = localStorage.getItem('cc-notify') === '1'; } catch (e) {}
    if (!on || !window.Notification || Notification.permission !== 'granted' || prev === p.vital) return;
    if ({ dead: 1, stalled: 1, refused: 1, done: 1 }[p.vital]) new Notification(p.title, { body: p.vital_reason || p.last_words || '', tag: p.unit + ':' + p.vital });
  }

  /* --- the loop --- */
  function swap(p, prev) {           /* every path schedules the next poll: an empty or failed partial froze the card (D1) */
    fetch(card.dataset.partial, { headers: { 'HX-Request': 'true' } }).then(function (r) { return r.text(); }).then(function (html) {
      var box = document.createElement('div'); box.innerHTML = html || '';
      var fresh = html && html.trim() ? box.querySelector('#live') : null;
      if (fresh) morph(fresh, p, prev);
      schedule(p);
    }, function () { schedule(p); });
  }
  function morph(fresh, p, prev) {
    if (window.Idiomorph) { window.Idiomorph.morph(card, fresh); card = document.getElementById('live') || card; }   /* nodes survive: no blank frame */
    else { card.replaceWith(fresh); card = fresh; }
    card.dataset.wired = '1';
    if (p.vital === 'done' && prev !== 'done') { var r = card.querySelector('.lv-rail'); if (r) r.classList.add('sweep'); }
    wireHover(); wireNotify();
  }
  function apply(p) {
    var prev = card.dataset.vital;
    skew = p.now - Date.now() / 1000;
    card.dataset.step = p.step_started || ''; card.dataset.run = p.run_started || '';
    document.title = p.title; favicon(p); notify(prev, p); lastOk = Date.now(); watchLate();
    if (shape(p) !== card.dataset.shape) { say(p, prev); swap(p, prev); return; }
    patchVital(p); patchHero(p); patchRail(p); patchSheet(p); tick(); schedule(p);
  }
  function poll() {
    timer = null;
    if (document.visibilityState !== 'visible') return;
    fetch(card.dataset.src, { cache: 'no-store' }).then(function (r) { return r.ok ? r.json() : null; })
      .then(function (p) { if (p) { last = p; apply(p); } else schedule(last); }, function () { schedule(last); });
  }
  function schedule(p) { if (!timer && !(p && STOP[p.vital])) timer = setTimeout(poll, 2000); }
  function wireHover() {
    if (card._hover) return; card._hover = 1;   /* a morphed card keeps its node and its listeners */
    card.addEventListener('mouseover', function (e) {
      var t = e.target.closest('.lt[data-video]'); if (!t || t.querySelector('video')) return;
      var v = document.createElement('video'); v.muted = true; v.loop = true; v.playsInline = true; v.preload = 'auto';
      v.src = card.dataset.lib + t.dataset.video; t.insertBefore(v, t.querySelector('.lt-id')); v.play().catch(function () {});
    });
    card.addEventListener('mouseout', function (e) {
      var t = e.target.closest('.lt'); if (t && !t.contains(e.relatedTarget)) { var v = t.querySelector('video'); if (v) v.remove(); }
    });
    wireNotify();
  }
  function wireNotify() {
    var b = $('notify');
    if (b && window.Notification) {
      b.hidden = false;
      try { if (localStorage.getItem('cc-notify') === '1') b.textContent = 'notifying'; } catch (e) {}
      b.onclick = function () { Notification.requestPermission().then(function (ok) {
        if (ok !== 'granted') return; try { localStorage.setItem('cc-notify', '1'); } catch (e) {} b.textContent = 'notifying'; }); };
    }
  }

  wireHover();
  setInterval(tick, 1000); tick();
  setInterval(function () { if (!STOP[card.dataset.vital] && document.visibilityState === 'visible') watchLate(); }, 1000);
  document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'visible' && !timer) poll(); });
  if (!STOP[card.dataset.vital]) schedule(null);
})();
