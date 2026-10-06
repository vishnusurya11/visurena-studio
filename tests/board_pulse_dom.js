/* board_pulse_dom.js -- pulse.js's PAGE half under node (board refresh brief, row A2).
   A small DOM double (elements that answer [data-*], .class and #id selectors) hosts the real
   script via vm, a scripted fetch feeds it pulses, and scripted timers step the loop.  It proves:
   the first pulse fires every section and a quiet one none; the shell is patched in place
   (badges, dots, pins, GPU card, title, heartbeat chip, held bar); the since cursor rides every
   poll; a pulse-fired request carries ?v= and lands data-v on 200 AND 204; a '·' label
   survives; a failing fetch backs off and recovers; and an error thrown while patching still
   schedules the next pulse (the heartbeat must never die).
   Usage: node board_pulse_dom.js <path to pulse.js>; prints base64(JSON {checks, requests}). */
'use strict';
const fs = require('fs');
const vm = require('vm');

const leaks = [];
process.on('unhandledRejection', e => { leaks.push(String(e && e.message || e)); });

const checks = [];
function check(name, pass, got) {
  checks.push({ name: name, pass: !!pass, got: got === undefined ? null : got });
}
function camel(s) { return s.replace(/-([a-z])/g, (_, c) => c.toUpperCase()); }

/* ------------------------------------------------------------------ the DOM double */
function el(tag, props) {
  const e = Object.assign({
    tag: tag || 'div', id: '', kids: [], parentElement: null, _text: '', title: '',
    hidden: false, dataset: {}, attrs: {}, _cls: new Set(), offsetWidth: 1, listeners: {},
    style: { _p: {}, width: '', setProperty(k, v) { this._p[k] = v; } },
  }, props || {});
  if (props && 'textContent' in props) e._text = String(props.textContent);
  Object.defineProperty(e, 'textContent', {        /* the real DOM stringifies on assignment */
    get() { return e._text; }, set(v) { e._text = String(v); },
  });
  Object.defineProperty(e, 'className', {
    get() { return [...e._cls].join(' '); },
    set(v) { e._cls = new Set(String(v).split(/\s+/).filter(Boolean)); },
  });
  e.classList = {
    add: c => e._cls.add(c), remove: c => e._cls.delete(c), contains: c => e._cls.has(c),
    toggle(c, on) { (on === undefined ? !e._cls.has(c) : on) ? e._cls.add(c) : e._cls.delete(c); },
  };
  e.matches = sel => {
    if (sel === '[id]') return !!e.id;
    let m;
    if ((m = /^\[data-([a-z-]+)="(.*)"\]$/.exec(sel))) return e.dataset[camel(m[1])] === m[2];
    if ((m = /^\[data-([a-z-]+)\]$/.exec(sel))) return camel(m[1]) in e.dataset;
    if ((m = /^\.([\w-]+)$/.exec(sel))) return e._cls.has(m[1]);
    if ((m = /^#([\w-]+)$/.exec(sel))) return e.id === m[1];
    return false;
  };
  e.setAttribute = (k, v) => { e.attrs[k] = String(v); };
  e.getAttribute = k => (k in e.attrs ? e.attrs[k] : null);
  e.removeAttribute = k => { delete e.attrs[k]; };
  e.appendChild = n => { n.parentElement = e; e.kids.push(n); return n; };
  e.insertBefore = (n, ref) => {
    if (n.parentElement) n.remove();
    n.parentElement = e;
    const i = ref ? e.kids.indexOf(ref) : -1;
    if (i < 0) e.kids.push(n); else e.kids.splice(i, 0, n);
    return n;
  };
  e.remove = () => {
    const p = e.parentElement;
    if (p && p.kids) p.kids.splice(p.kids.indexOf(e), 1);
    e.parentElement = null;
  };
  e.cloneNode = () => el(e.tag, { attrs: Object.assign({}, e.attrs), dataset: Object.assign({}, e.dataset) });
  e.querySelectorAll = sel => collect(e, sel, []);
  e.querySelector = sel => collect(e, sel, [])[0] || null;
  e.closest = sel => { let n = e; while (n) { if (n.matches && n.matches(sel)) return n; n = n.parentElement; } return null; };
  e.contains = n => { while (n) { if (n === e) return true; n = n.parentElement; } return false; };
  e.addEventListener = (t, f) => { (e.listeners[t] = e.listeners[t] || []).push(f); };
  e.dispatchEvent = ev => { (e.listeners[ev.type] || []).forEach(f => f(ev)); return true; };
  return e;
}
function collect(node, sel, out) {
  (node.kids || []).forEach(k => {
    if (k.matches && k.matches(sel)) out.push(k);
    if (k.kids) collect(k, sel, out);
  });
  return out;
}

/* ------------------------------------------------------------------ the page under test */
const body = el('body');
const htmlEl = el('html');
const byId = {};
function make(tag, id, props) { const e = el(tag, props); e.id = id || ''; if (id) byId[id] = e; return e; }
function mount(parent, e) { parent.appendChild(e); return e; }

const docListeners = {};
const doc = {
  documentElement: htmlEl, body: body, title: 'Episode · Visurena Studio', hidden: false,
  readyState: 'complete', head: el('head'),
  getElementById: id => byId[id] || null,
  querySelectorAll: sel => collect(body, sel, []),
  querySelector: sel => collect(body, sel, [])[0] || null,
  createElement: tag => el(tag),
  createElementNS: (ns, tag) => el(tag),
  createTextNode: s => ({ text: String(s), kids: [] }),
  addEventListener: (t, f) => { (docListeners[t] = docListeners[t] || []).push(f); },
  dispatchEvent: ev => { (docListeners[ev.type] || []).forEach(f => f(ev)); return true; },
};

/* the shell the templates would have rendered */
const hb = mount(body, make('button', 'hb'));
mount(hb, el('span', { dataset: { hbText: '' } }));
const needsBadge = mount(body, el('b', { dataset: { needs: '' }, textContent: '0' }));
const queueCount = mount(body, el('span', { dataset: { queue: '' }, textContent: '0' }));
const dept = mount(body, el('a', { dataset: { dept: 'episode', total: '9' } }));
const dotBox = mount(dept, el('span')); dotBox.className = 'sb-dots';
const pinBox = mount(body, el('div', { dataset: { pins: '' } }));
const pinEmpty = mount(pinBox, el('p')); pinEmpty.className = 'sb-empty';
const card = mount(body, el('a', { dataset: { gpu: '' }, attrs: { href: '/queue' } }));
card.className = 'gpu idle';
const face = mount(card, el('span', { dataset: { gcFace: '' } }));
const label = mount(card, el('span', { dataset: { gcLabel: '' } }));
const unitEl = mount(card, el('span', { dataset: { gcUnit: '' } }));
const eta = mount(card, el('span', { dataset: { gcEta: '' } }));
const t2 = mount(card, el('span')); t2.className = 't2';
const stepEl = mount(t2, el('span', { dataset: { gcStep: '' } }));
const prog = mount(card, el('span')); prog.className = 'prog';
const bar = mount(prog, el('i', { dataset: { prog: '' } }));
const holdbar = mount(body, make('div', 'holdbar', { hidden: true }));
const holdAt = mount(holdbar, el('time', { dataset: { holdAt: '' } }));
const holdWhy = mount(holdbar, el('span', { dataset: { holdReason: '' } }));
const lift = mount(holdbar, el('button', { dataset: { lift: '' } }));
const sec = mount(body, make('section', 'att', { attrs: { 'data-v': 'a1' } }));
const row = mount(sec, make('div', 'att-1', { textContent: 'old words' }));
const sec2 = mount(body, make('section', 'ord', { attrs: { 'data-v': 'x1' } }));

/* ------------------------------------------------------------------ timers, fetch, htmx */
const timers = []; let tid = 1;
const requests = []; let respond = null;
const fired = []; let htmxThrow = false;
const sandbox = {
  document: doc, location: { pathname: '/d/episode/C1/ep18' },
  setTimeout: (fn, ms) => { const id = tid++; timers.push({ id, fn, ms }); return id; },
  clearTimeout: id => { const i = timers.findIndex(t => t.id === id); if (i >= 0) timers.splice(i, 1); },
  addEventListener: () => {},
  fetch: url => { requests.push(String(url)); return respond(); },
  CSS: { escape: s => s },
  CustomEvent: function (type, opts) { this.type = type; this.detail = opts && opts.detail; },
  htmx: { trigger: (elt, name) => { if (htmxThrow) { htmxThrow = false; throw new Error('a page handler broke'); } fired.push(name); } },
  localStorage: { getItem: () => null, setItem: () => {} },
};
sandbox.window = sandbox;

function drain() { return new Promise(r => setImmediate(() => setImmediate(() => setImmediate(r)))); }
function stepPulse() {                       /* run the loop's own timers, never wash (3 s) or chip (1 s) */
  const due = timers.filter(t => t.ms !== 3000 && t.ms !== 1000);
  due.forEach(t => timers.splice(timers.indexOf(t), 1));
  due.forEach(t => t.fn());
  return due.map(t => t.ms);
}
function pulseOf(body) { respond = () => Promise.resolve({ ok: true, json: () => Promise.resolve(JSON.parse(JSON.stringify(body))) }); }

const FP = { shell: 's1', floor: 'f1', attention: 'a1', orders: 'o1', lanes: 'l1',
  'dept:episode': 'd1', 'book:C1': 'b1', 'unit:episode/C1/ep18': 'u1' };
const GPU = { href: '/d/episode/C1/ep18', unit: 'ep18', step: '07 board', frac: 0.4,
  finish: '21:35', vital: 'working', held: false };
const P1 = { boot: 1000, now: 2000, cursor: 7, events: [],
  fp: FP,
  shell: { needs: 3, queue: 1, dept_dots: { episode: { running: 1, flagged: 5 } },
    pins: [{ href: '/d/episode/C1/ep18', label: 'ep18 · 11 qc', state: 'running' }],
    gpu: GPU, hold: null } };

/* ------------------------------------------------------------------ the scenarios */
async function main() {
  pulseOf(P1);
  vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(process.argv[2], 'utf8'), sandbox, { filename: 'pulse.js' });
  await drain();

  /* 1. the first pulse fires every section, patches the whole shell */
  check('first pulse fires every key', JSON.stringify(fired.slice().sort()) ===
    JSON.stringify(Object.keys(FP).map(k => 'pulse:' + k).sort()), fired.slice());
  check('needs badge patched and washed', needsBadge.textContent === '3' && needsBadge._cls.has('chg'),
    needsBadge.textContent);
  check('queue count patched', queueCount.textContent === '1', queueCount.textContent);
  check('dept dot drawn', dept.dataset.dot === 'run' && dotBox.kids.length === 2 &&
    dotBox.kids[0].textContent === '1' && dotBox.kids[1].textContent === '5', dept.dataset.dot);
  check('dept speaks its dots', dept.getAttribute('aria-label') === 'episode, 1 running, 5 flagged',
    dept.getAttribute('aria-label'));
  const pin = pinBox.querySelector('[data-pin]');
  check('pin appears', !!pin && pin.dataset.pin === '/d/episode/C1/ep18' && pinEmpty.hidden === true,
    pin && pin.dataset.pin);
  check('pin label keeps its middle dot', !!pin && pin.title === 'ep18 · 11 qc' &&
    pin.title.indexOf('Â') < 0, pin && pin.title);
  const pinText = pin ? pin.querySelector('.lbl') : null;
  check('pin splits id from the rest', !!pinText && pinText.kids[0].textContent === 'ep18' &&
    pinText.kids[1].text === '11 qc', pinText && pinText.kids.map(k => k.textContent || k.text));
  check('gpu card runs', !card._cls.has('idle') && card.getAttribute('href') === GPU.href &&
    label.textContent === 'On the GPU' && unitEl.textContent === 'ep18' &&
    stepEl.textContent === '07 board' && eta.textContent === '~21:35', label.textContent);
  check('gpu progress drawn', card.style._p['--p'] === 0.4 && bar.style.width === '40.0%' &&
    card.dataset.vital === 'working', bar.style.width);
  check('title goes live', doc.title === '● ep18 · 07 board · ~21:35 · Episode', doc.title);
  check('chip reads live', hb.dataset.hb === 'live' && !('data-stale' in htmlEl.attrs), hb.dataset.hb);

  /* 2. the since cursor rides the next poll; a changed key fires alone; quiet fires none */
  fired.length = 0;
  pulseOf(Object.assign({}, P1, { cursor: 9, fp: Object.assign({}, FP, { attention: 'a2' }) }));
  stepPulse(); await drain();
  check('second poll carries since=7', requests[1] === '/api/pulse.json?since=7', requests[1]);
  check('only the changed key fires', JSON.stringify(fired) === JSON.stringify(['pulse:attention']), fired.slice());
  fired.length = 0;
  pulseOf(Object.assign({}, P1, { cursor: 9, fp: Object.assign({}, FP, { attention: 'a2' }) }));
  stepPulse(); await drain();
  check('third poll carries since=9', requests[2] === '/api/pulse.json?since=9', requests[2]);
  check('a quiet pulse fires nothing', fired.length === 0, fired.slice());

  /* 3. a pulse-fired request carries ?v= and lands data-v on 200 and on 204 */
  const params = {};
  doc.dispatchEvent({ type: 'htmx:configRequest',
    detail: { parameters: params, elt: sec, triggeringEvent: { type: 'pulse:attention' } } });
  check('request carries the drawn v', params.v === 'a1' && sec.__pulseFp === 'a2', params.v);
  doc.dispatchEvent({ type: 'htmx:beforeSwap',
    detail: { requestConfig: { triggeringEvent: { type: 'pulse:attention' } }, target: sec } });
  row.textContent = 'new words';
  doc.dispatchEvent({ type: 'htmx:afterRequest', detail: { elt: sec, xhr: { status: 200 } } });
  doc.dispatchEvent({ type: 'htmx:afterSettle', detail: { target: sec } });
  check('200 lands data-v', sec.getAttribute('data-v') === 'a2' && !sec.__pulseFp, sec.getAttribute('data-v'));
  check('the changed row washes', row._cls.has('chg'), [...row._cls]);
  doc.dispatchEvent({ type: 'htmx:configRequest',
    detail: { parameters: {}, elt: sec2, triggeringEvent: { type: 'pulse:orders' } } });
  doc.dispatchEvent({ type: 'htmx:afterRequest', detail: { elt: sec2, xhr: { status: 204 } } });
  check('204 lands data-v too', sec2.getAttribute('data-v') === 'o1' && !sec2.__pulseFp,
    sec2.getAttribute('data-v'));

  /* 4. a failing fetch backs off, says so, and recovers */
  respond = () => Promise.resolve({ ok: false, status: 500, json: () => Promise.reject(new Error('500')) });
  stepPulse(); await drain();
  check('a bad answer backs off', hb.dataset.hb === 'offline' && 'data-stale' in htmlEl.attrs &&
    timers.some(t => t.ms === 2000), hb.dataset.hb);
  pulseOf(Object.assign({}, P1, { cursor: 9 }));
  stepPulse(); await drain();
  check('a good answer recovers the chip', hb.dataset.hb === 'live' && !('data-stale' in htmlEl.attrs),
    hb.dataset.hb);

  /* 5. the owner's complaint: an error while handling a pulse must never kill the loop */
  fired.length = 0; htmxThrow = true;
  pulseOf(Object.assign({}, P1, { cursor: 10, fp: Object.assign({}, FP, { attention: 'a3', floor: 'f3' }) }));
  stepPulse(); await drain();
  const alive = timers.filter(t => t.ms !== 3000 && t.ms !== 1000);
  check('a patch error still schedules the next pulse', alive.length > 0, timers.map(t => t.ms));
  fired.length = 0;
  pulseOf(Object.assign({}, P1, { cursor: 11, fp: Object.assign({}, FP, { attention: 'a4', floor: 'f3' }) }));
  stepPulse(); await drain();
  check('the loop goes on after the error', fired.indexOf('pulse:attention') >= 0 && hb.dataset.hb === 'live',
    fired.slice());

  /* 6. a held studio patches the bar, the card and the title */
  pulseOf(Object.assign({}, P1, { cursor: 11, fp: Object.assign({}, FP, { shell: 's2', attention: 'a4', floor: 'f3' }),
    shell: Object.assign({}, P1.shell, { gpu: null,
      hold: { id: 4, since: '2026-10-04T19:21:00Z', reason: 'checking the grids' } }) }));
  stepPulse(); await drain();
  const hm = new Date('2026-10-04T19:21:00Z');
  const want = String(hm.getHours()).padStart(2, '0') + ':' + String(hm.getMinutes()).padStart(2, '0');
  check('held bar shows and reads local time', holdbar.hidden === false && holdAt.textContent === want &&
    holdWhy.textContent.indexOf('checking the grids') >= 0 && String(lift.dataset.lift) === '4', holdAt.textContent);
  check('held card never says idle', card._cls.has('held') && label.textContent === 'Studio held' &&
    stepEl.textContent === 'nothing starts until you lift', label.textContent);
  check('held title', doc.title === '⏸ held · Episode', doc.title);

  await drain();
  check('no promise leaks from the loop', leaks.length === 0, leaks);
  process.stdout.write(Buffer.from(JSON.stringify({ checks: checks, requests: requests })).toString('base64'));
}
main().catch(e => { process.stderr.write(String(e.stack || e)); process.exit(1); });
