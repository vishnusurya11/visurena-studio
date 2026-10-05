/* Visurena Studio board -- the owner's orders, client half (panel ruling PKG-6; vendored, no build).
   The forms come from templates/_macros.html and post to /act/ through htmx; this file only:
   - keeps the ONE receipts region (#receipts, outside every polled block) and each receipt chip's
     life: >= 6 s, longer while hovered or focused, 10 s after its order reached a final state,
     30 s while it is still pending (the Orders strip carries it on);
   - moves a pending chip to "taken by the 04:00 run" when the pulse's events carry its order
     (pulse.js dispatches `pulse:events`; an order-taken item is {id: "ord-<n>", order: <n>, text});
   - says every receipt once through board.announce (C5) -- it speaks nothing itself;
   - shows "Sending…" on the pressed button and resets a hold form after it lands;
   - fills a hold's reason from its chips (Enter submits; the server still requires a reason);
   - defers an acknowledge 5 s with an Undo: the POST fires at the deadline, or as a beacon
     when the page is left; Undo inside the window sends nothing (no new order kind).
   The pure core (undoStep, orderWords, takenFrom) is exported for node tests and runs without a DOM. */
(function (root) {
  'use strict';
  var UNDO_MS = 5000, KEEP_MS = 6000, AFTER_MS = 10000, PENDING_MS = 30000, MAX_CHIPS = 3;
  var FINAL = { applied: 1, taken: 1, refused: 1 };

  /* The acknowledge's deferred commit: a state and an event in, the next state and what to send. */
  function undoStep(s, ev) {
    if (ev.type === 'press') {
      return s.phase === 'wait' ? { s: s, send: null } : { s: { phase: 'wait', until: ev.now + UNDO_MS }, send: null };
    }
    if (s.phase !== 'wait') return { s: s, send: null };
    if (ev.type === 'undo') return { s: { phase: 'undone' }, send: null };
    if (ev.type === 'hide') return { s: { phase: 'sent' }, send: 'beacon' };
    if (ev.type === 'tick' && ev.now >= s.until) return { s: { phase: 'sent' }, send: 'post' };
    return { s: s, send: null };
  }

  /* What a receipt chip says once its order's state is read back; null when it could not be read. */
  function orderWords(o) {
    if (!o) return null;
    if (o.state === 'taken') return '● taken by ' + (o.run_at ? 'the ' + o.run_at + ' run' : 'a run');
    if (o.state === 'applied') return '● applied';
    return '○ pending';
  }

  /* A pulse event in, the taken order it reports out ({id, state, run, run_at}); null for any other event. */
  function takenFrom(item) {
    if (!item || typeof item.order !== 'number') return null;
    var run = (/taken by run (\S+)\s*$/.exec(item.text || '') || [])[1] || '';
    var stamp = /(\d{8})(\d{2})(\d{2})\d{2}$/.exec(run);
    return { id: item.order, state: 'taken', run: run, run_at: stamp ? stamp[2] + ':' + stamp[3] : '' };
  }

  var core = { UNDO_MS: UNDO_MS, undoStep: undoStep, orderWords: orderWords, takenFrom: takenFrom };
  if (typeof module === 'object' && module.exports) module.exports = core;
  if (typeof document === 'undefined') return;
  root.boardOrders = core;

  var deferrals = [], timer = null;
  function now() { return Date.now(); }
  function say(text, urgent) {
    if (text && root.board && root.board.announce) root.board.announce(text, { urgent: !!urgent });
  }
  function region() {
    var r = document.getElementById('receipts');
    if (!r) {
      r = document.createElement('div');
      r.id = 'receipts'; r.className = 'toast receipts'; r.hidden = true;
      document.body.appendChild(r);
    }
    return r;
  }
  function tidy() {
    var r = region();
    while (r.children.length > MAX_CHIPS) r.removeChild(r.lastElementChild);
    r.hidden = !r.children.length;
    if (!r.children.length && !deferrals.length && timer) { clearInterval(timer); timer = null; }
  }
  function wake() { if (!timer) timer = setInterval(tick, 1000); }

  /* ---------------------------------------------------------- a receipt's life */
  function keep(chip, ms) { chip.dataset.until = String(Math.max(Number(chip.dataset.until || 0), now() + ms)); }
  function arrive(chip) {
    if (!chip || !chip.classList.contains('rcpt')) return;
    chip.dataset.born = String(now());
    keep(chip, FINAL[chip.dataset.state] ? Math.max(KEEP_MS, AFTER_MS) : PENDING_MS);
    say(chip.dataset.say, chip.dataset.state === 'refused');
    tidy(); wake();
  }
  function expire() {
    Array.prototype.slice.call(region().querySelectorAll('.rcpt[data-until]')).forEach(function (chip) {
      if (chip.matches(':hover') || chip.contains(document.activeElement)) return keep(chip, 1000);
      if (now() >= Number(chip.dataset.until)) chip.remove();
    });
    tidy();
  }
  function settle(chip, o) {
    var words = orderWords(o);
    if (!words || o.state === 'pending') return;
    chip.dataset.state = o.state;
    var st = chip.querySelector('[data-k="state"]'); if (st) st.textContent = words;
    if (o.run) chip.title = o.run;
    keep(chip, AFTER_MS);
    say('Order ' + o.id + ' ' + words.replace(/^[●○] /, '') + '.');
  }
  function taken(e) {
    (e.detail || []).forEach(function (item) {
      var o = takenFrom(item), chip = o && region().querySelector('.rcpt[data-state="pending"][data-order="' + o.id + '"]');
      if (chip) settle(chip, o);
    });
  }

  /* ---------------------------------------------------------- the acknowledge's Undo */
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text) e.textContent = text; return e; }
  function submitOf(form) { return form.querySelector('button[type="submit"]'); }
  function undoChip(d) {
    var chip = el('div', 'rcpt'), b = el('button', 'btn ghost sm', '');
    chip.dataset.state = 'deferred';
    chip.appendChild(el('span', 'rc-what', 'Acknowledging ' + d.unit + ' · '));
    b.type = 'button'; b.setAttribute('data-undo-cancel', '');
    chip.appendChild(b);
    return chip;
  }
  function countdown(d) {
    var b = d.chip.querySelector('[data-undo-cancel]');
    if (b) b.textContent = 'Undo (' + Math.max(0, Math.ceil((d.s.until - now()) / 1000)) + ' s)';
  }
  function defer(form) {
    var d = { form: form, unit: form.dataset.unit || 'this unit', path: form.getAttribute('hx-post'),
              params: new URLSearchParams(new FormData(form)), s: { phase: 'idle' } };
    d.s = undoStep(d.s, { type: 'press', now: now() }).s;
    d.chip = undoChip(d); countdown(d);
    region().insertBefore(d.chip, region().firstChild);
    var b = submitOf(form); if (b) b.disabled = true;
    deferrals.push(d); tidy(); wake();
    say('Acknowledging ' + d.unit + '. Undo within ' + UNDO_MS / 1000 + ' seconds.');
  }
  /* the server's own receipt fragment (escaped by Jinja), never a value */
  function receiptHTML(chip, html) { chip.insertAdjacentHTML('afterend', html); var next = chip.nextElementSibling; chip.remove(); arrive(next); }
  function post(d) {
    fetch(d.path, { method: 'POST', body: d.params, headers: { 'HX-Request': 'true' }, credentials: 'same-origin' })
      .then(function (r) { return r.text(); })
      .then(function (html) { receiptHTML(d.chip, html); if (root.htmx) root.htmx.trigger(document.body, 'orders-changed'); })
      .catch(function () { d.chip.textContent = '⊘ not sent: the board did not answer'; d.chip.dataset.state = 'refused'; arrive(d.chip); });
  }
  function apply(d, r) {
    d.s = r.s;
    if (r.send === 'post') post(d);
    if (r.send === 'beacon' && navigator.sendBeacon) navigator.sendBeacon(d.path, d.params);
    if (d.s.phase !== 'wait') deferrals = deferrals.filter(function (x) { return x !== d; });
  }
  function undo(d) {
    apply(d, undoStep(d.s, { type: 'undo', now: now() }));
    d.chip.remove();
    var b = submitOf(d.form); if (b) b.disabled = false;
    tidy(); say('Acknowledge of ' + d.unit + ' undone. Nothing was sent.');
  }
  function tick() {
    deferrals.slice().forEach(function (d) { countdown(d); apply(d, undoStep(d.s, { type: 'tick', now: now() })); });
    expire();
  }

  /* ---------------------------------------------------------- wiring */
  var body = document.body;
  region();
  body.addEventListener('htmx:confirm', function (e) {
    var f = e.target;
    if (!f.matches || !f.matches('form[data-undo]')) return;
    e.preventDefault();
    if (!deferrals.some(function (d) { return d.form === f; })) defer(f);
  });
  body.addEventListener('htmx:beforeSwap', function (e) {        /* a refused order shows its reason */
    var x = e.detail.xhr, path = (e.detail.requestConfig || {}).path || '';
    if (x && x.status >= 400 && x.status < 500 && path.indexOf('/act/') === 0) { e.detail.shouldSwap = true; e.detail.isError = false; }
  });
  body.addEventListener('htmx:afterSwap', function (e) {
    if (e.detail.target && e.detail.target.id === 'receipts') arrive(e.detail.target.firstElementChild);
  });
  body.addEventListener('htmx:beforeRequest', function (e) {
    var b = e.target.matches && e.target.matches('form.act') ? submitOf(e.target) : null;
    if (b) { b.dataset.label = b.textContent; b.textContent = 'Sending…'; }
  });
  body.addEventListener('htmx:afterRequest', function (e) {
    var f = e.target, b = f.matches && f.matches('form.act') ? submitOf(f) : null;
    if (b && b.dataset.label) { b.textContent = b.dataset.label; delete b.dataset.label; }
    if (b && e.detail.successful && f.hasAttribute('data-reset')) { f.reset(); var r = f.querySelector('.reasons'); if (r) r.hidden = true; }
  });
  document.addEventListener('pulse:events', taken);
  document.addEventListener('click', function (e) {
    var t = e.target.closest('[data-reason],[data-dismiss],[data-undo-cancel]'); if (!t) return;
    if (t.hasAttribute('data-reason')) {
      var input = t.closest('form').querySelector('input[name="reason"]');
      input.value = t.dataset.reason; input.focus();
    } else if (t.hasAttribute('data-dismiss')) { t.closest('.rcpt').remove(); tidy(); }
    else { deferrals.filter(function (d) { return d.chip.contains(t); }).forEach(undo); }
  });
  document.addEventListener('focusin', function (e) {             /* a hold's reasons show while it has focus */
    var f = e.target.closest && e.target.closest('form.act.hold'), r = f && f.querySelector('.reasons');
    if (r) r.hidden = false;
  });
  document.addEventListener('focusout', function (e) {
    var f = e.target.closest && e.target.closest('form.act.hold'), r = f && f.querySelector('.reasons');
    if (r) setTimeout(function () { if (!f.contains(document.activeElement)) r.hidden = true; }, 200);
  });
  root.addEventListener('pagehide', function () {
    deferrals.slice().forEach(function (d) { apply(d, undoStep(d.s, { type: 'hide', now: now() })); });
  });
})(typeof window !== 'undefined' ? window : this);
