/* live_card_dom.js -- progress.js (the live card's client) under node against a small page
   double (page experts 2026-10-18, D1).  The card's shape changes, so apply() swaps the card
   from its partial; the partial answers empty (the run went idle: app.py returns ""), then
   the partial's fetch fails.  Either way the loop must schedule its next poll -- a swap that
   returns without one froze the card while its clock kept ticking.  It also proves the hero
   and the rail are patched with the episode finish, the step's end and each later window.
   Usage: node live_card_dom.js <path to progress.js>; prints base64(JSON {checks}). */
'use strict';
const fs = require('fs');
const vm = require('vm');

const checks = [];
function check(name, pass, got) { checks.push({ name, pass: !!pass, got: got === undefined ? null : got }); }

function node(props) {
  const n = Object.assign({ dataset: {}, attrs: {}, style: { setProperty() {} }, textContent: '', innerHTML: '',
    className: '', listeners: {} }, props || {});
  n.setAttribute = (k, v) => { n.attrs[k] = String(v); };
  n.getAttribute = k => (k in n.attrs ? n.attrs[k] : null);
  n.removeAttribute = k => { delete n.attrs[k]; };
  n.hasAttribute = k => k in n.attrs;
  n.addEventListener = (k, f) => { n.listeners[k] = f; };
  n.classList = { add() {}, remove() {}, toggle() {}, contains: () => false };
  n.querySelector = sel => (n.kids || {})[sel] || null;
  n.querySelectorAll = () => [];
  return n;
}

const finish = node(), stepend = node(), range = node(), win10 = node({ className: 'win' });
const seg10 = node({ className: 'seg st-waiting', kids: { '.win': win10 } });
const card = node({ id: 'live', dataset: { now: '1000', src: '/api/p.json', partial: '/partials/live', vital: 'live', shape: 'run|02|loop|0' } });
card.kids = { '[data-k="finish"]': finish, '[data-k="stepend"]': stepend, '[data-k="range"]': range,
  '.seg[data-id="10"]': seg10 };

const timers = [];
let partial = 'empty';
const P = { vital: 'live', now: 1000, unit: 'ep01', title: 't', run_started: 900, step_started: 950,
  now_step: { id: '02', name: 'plan', kind: 'loop' }, items: [],
  eta: { finish: '16:40', step_end: '13:58', range: '15:55–17:50', steps_left: 11, n_runs: 15, basis: 'measured' },
  steps: [{ id: '10', state: 'waiting', window: '15:10–15:20', will_run: true }] };

const doc = node({ visibilityState: 'visible', title: '' });
doc.documentElement = node();
doc.head = node({ appendChild: x => x });
doc.getElementById = id => (id === 'live' ? card : null);
doc.createElement = tag => node({ tag, getContext: () => ({ beginPath() {}, arc() {}, stroke() {} }), toDataURL: () => '' });
doc.querySelector = () => null;

const sandbox = {
  document: doc, window: {}, console, Promise, JSON, Math, String, Number, Date, Object, Array, parseFloat, isNaN,
  localStorage: { getItem: () => null, setItem() {} },
  getComputedStyle: () => ({ getPropertyValue: () => '' }),
  setTimeout: (f, ms) => { timers.push(f); return timers.length; },
  setInterval: () => 0,
  fetch: url => {
    if (url === '/api/p.json') return Promise.resolve({ ok: true, json: () => Promise.resolve(P) });
    if (partial === 'fail') return Promise.reject(new Error('net'));
    return Promise.resolve({ text: () => Promise.resolve('') });
  },
};
sandbox.window = sandbox;
const drain = () => new Promise(r => setImmediate(r));
function next() { const f = timers.shift(); if (typeof f !== 'function') throw new Error('no poll scheduled'); f(); }

(async () => {
  try { await run(); } catch (e) { check('the harness ran to the end', false, String(e && e.message || e)); }
  process.stdout.write(Buffer.from(JSON.stringify({ checks })).toString('base64'));
})();

async function run() {
  vm.runInNewContext(fs.readFileSync(process.argv[2], 'utf8'), sandbox);
  check('the card schedules its first poll', timers.length === 1, timers.length);

  card.dataset.shape = 'run|02|loop|0';
  next(); await drain(); await drain(); await drain();
  check('a quiet poll patches the episode finish', /episode done ~<b>16:40<\/b>/.test(finish.innerHTML), finish.innerHTML);
  check('a quiet poll patches the step end', stepend.textContent === '02 plan ends ~13:58', stepend.textContent);
  check('a quiet poll patches a later window', win10.textContent === '15:10–15:20', win10.textContent);
  check('a quiet poll schedules the next', timers.length === 1, timers.length);

  card.dataset.shape = 'stale';
  next(); await drain(); await drain(); await drain();
  check('an empty partial still schedules the next poll', timers.length === 1, timers.length);

  partial = 'fail';
  card.dataset.shape = 'stale';
  next(); await drain(); await drain(); await drain();
  check('a failed partial still schedules the next poll', timers.length === 1, timers.length);
  check('the harness ran to the end', true);
}
