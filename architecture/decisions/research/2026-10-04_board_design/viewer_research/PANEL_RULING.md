# Panel ruling: a living board (moderator, 2026-10-04)

Inputs: PANEL_BRIEF.md, P01–P10, prior rulings (report 09: pulse + morph, no SSE, one loop per viewport;
SPEC_v3: the Viewer). The owner asked for a board that is "more dynamic, refresh and updating". The panel
agreed on what that means. **Every page is live from a single 2 s heartbeat. A section changes only when the studio
changed. The change is shown once, in place, and never moves the page, the focus or a playing video. The board
says how old its data is, and it says so when it is broken.** Measured today (P01, P08): 74–84 req/min and
196–491 KB/min of mostly identical HTML, seven timers per page drifting apart, no 204, `innerHTML` swaps
that drop focus and video, a sidebar and GPU card that are static pictures, a cold ep17 TTFB of 63 s behind
thumbnail renders, and nothing on screen when the server 500s.

Hard limits on every package: files only under `studio/command_center/**`, `command_center.py`, board tests
in `tests/`, and additive read helpers in `studio/db.py`. No npm. htmx 2.0.4 plus small vendored JS. The web process
stays read-only (writes only through the existing `/act/` → `work_orders`), never decodes video, never writes
under `library/`. Test-first, 10–20-line functions, $0 tests. Progress-tracker files (`_live_*.html`,
`_unit_live.html`, `progress.js`, `progress_view.py`) belong to another session's design, so only additive,
behaviour-preserving edits are allowed there (P5 owns them). No stage, step or agent changes, so `architecture/index.html` is untouched.

## 0. Shared contracts (fixed now so the six packages can build in parallel)

- **C1 Pulse:** `GET /api/pulse.json?since=<event_id>` → `{boot, now, fp:{shell, floor, attention, orders,
  lanes, "dept:<stage>", "book:<codex>", "unit:<stage>/<codex>/<unit>"}, shell:{needs, queue,
  dept_dots:{<stage>:{<state>:n}}, pins:[{href,label,state}], gpu:{href,unit,step,frac,finish,vital,held},
  hold:{id,since,reason}|null}, events:[{id,ts,href,unit,text}], cursor}`. A fingerprint comes from cheap DB
  aggregates (max event id, orders max id, holds, unit updated_at) plus a minute bucket for sections that print
  ages. One `views.inbox_count()` is the **only** source of "needs you" (fixes 5 vs 6).
- **C2 Partials:** every `/partials/*` accepts `?v=<fp>` and answers **204** when it is equal. Rows carry
  stable ids (`id="wo-<codex>-<unit>"`, `att-…`, `ord-<id>`).
- **C3 Client events:** `pulse.js` fires `htmx.trigger(body, 'pulse:<fp-key>')` only for keys whose fp changed.
  Templates poll with `hx-trigger="pulse:attention from:body"`, `hx-swap="morph:innerHTML"`, `hx-ext="morph"` is on `<body>`, and there is no `every Ns`.
  Changed rows get the class `.chg` (P3 styles it). `<html data-stale>` is set when the pulse is late or failing.
- **C4 Keys:** `board.js` binds the `KEYS` table from `shell.py` (serialized JSON). Page templates expose
  page keys by marking a control `data-key="["`, `"]"`, `"w"`, `"A"`, and board.js clicks it. Templates write no JS.
- **C5 Announce:** `board.announce(text,{key,urgent})` writes to persistent `#sr-status` / `#sr-alert` in base.
  Receipts and the tracker call it. Nothing else speaks.

## 1. Accepted build list: six packages, disjoint files

### PKG-1 PULSE SERVER: `pulse.py` (new), `app.py`, `views.py`, `models.py`, `thumbs.py`, `library_paths.py`, `studio/db.py` (additive reads)
| id | page | change (merged from) | test idea | verify live |
|---|---|---|---|---|
| 1.1 | all | `/api/pulse.json` per C1, with `boot` = server start ts (P01.1, P04.2, P08.2, P03.1, P10.2 hold data) | FakeConn fixture: fp changes when an event row is added, and not otherwise; `shell.needs == inbox_count()` | `curl` twice on a quiet studio: the same fp; JSON ≤ 1.5 KB |
| 1.2 | all partials | `?v=` → 204 on an equal fp (C2) (P01.3, P08.2) | parametrized over every partial route: equal v → 204 and empty body; stale v → 200 | rerun `research\p01\measure.py`: quiet-studio KB/min ≤ 35 on every page, req/min ≤ 31 |
| 1.3 | all | `events_since(cursor)` for the "Since you looked" feed and order-taken receipts (P01.6, P01.5) | events after the cursor only, newest first, capped at 20 | the pulse shows an event the runner just wrote, within 2 s |
| 1.4 | inbox | `/inbox` route (the sidebar's place as a real address) and `section('/inbox')`; every `PAGES` href returns 200 (P04.1, D1/D3) | route test over all `shell.PAGES` hrefs → 200 | click every sidebar item: no 404 |
| 1.5 | thumbs | `thumb` route made `async`, rendering through `anyio.to_thread` under a `CapacityLimiter(2)`; WebP `method=2`; add widths 1024 (the lightbox) (P08.1 *modified*, P08.7) | the limiter caps concurrency at 2 (fake render with a barrier); 1024 accepted, 777 → 404 | cold ep17: page HTML TTFB ≤ 300 ms while 48 thumbs render |
| 1.6 | /lib | ETag from (mtime, size) + `If-None-Match` → 304 for `/lib`; never on Range; fonts as `font/woff2` (P05.4, P08.10 part) | 304 on a matching ETag; a Range request still 206 | re-hover a take: 304 in the network log |
| 1.7 | 404/500 | `_not_found` passes the shell context and `request.url.path` so the error page sits in the shell (P09.4 server half) | the 404 body contains the sidebar and the asked path | `/d/episode/x/ep99` shows the shell plus links to Home and the parent |
| 1.8 | ages | views emit `age` ("9 d", "2 m") next to every ISO ts in rows (P03.11, P10.8) | `age(now, ts)` table test | Inbox rows show ages, with the ISO in `title` |
| 1.9 | queue/home | queue ETA carries `clean` and `as_run` (the text qualifier "if clean") (P06.4 *modified*) | fixture with known p50s | Home KPI reads "~Mon 05:29 if clean" |
| 1.10 | tests | perf budget over every page with TestClient: warm ≤ 50 ms, partial ≤ 6 KB, element counts reported, every `<img>` outside a template has width/height (P08.9) | itself | `uv run pytest tests/test_the_board_stays_within_budget.py` |

### PKG-2 SHELL CLIENT: `shell.py`, `templates/base.html`, `_shell.html`, `static/board.js`, `static/pulse.js` (new), `static/idiomorph-ext.min.js` (new, vendored)
| id | page | change (merged from) | test idea | verify live |
|---|---|---|---|---|
| 2.1 | all | `pulse.js`: one 2 s loop, 10 s when hidden (on a Worker timer); fires C3 events; patches the GPU card (`--p`, step, `~finish`, face), sidebar counts and dots, pins, Inbox badge; deletes board.js's `needs()`/`eta()` timers (P01.1, P01.4, P04.2, P08.3) | template test: `pulse.js` is loaded once and no `every Ns` is left in base or the shell | leave `/d/episode` open while ep17 changes step: the GPU card, the dot and the title update within 2 s, and `scrollY` is unchanged |
| 2.2 | all | Heartbeat chip `● live` / `◌ N s old` / `✕ offline · retrying in N s` (backoff 2→30 s) / `↻ board restarted · reload` (`boot` changed). On stale: `<html data-stale>` and every client clock freezes (P01.2, P09.8, P06.7) | pure JS fn `chipState(age, err, bootChanged)` mirrored by a Python table test of the thresholds | stop uvicorn: within 8 s the chip reads offline and the clocks freeze (screenshot). Restart: it offers reload |
| 2.3 | all | Live `document.title` (`● ep17 · 07 board · ~21:35`) and favicon arc; Notify moves into the shell watcher and works from any page while hidden; `new Notification` wrapped (P01.4, P04.11, P10.6) | title formatter test from a pulse fixture | hide the tab and kill a unit in a fixture DB: a notification arrives within 15 s |
| 2.4 | all | `hx-ext="morph"` on body (vendored idiomorph); persistent `#sr-status`/`#sr-alert` + `board.announce()` dedupe/coalesce (C5); skip link + `main#main` (P07.1, P07.2 plumbing, P07.6) | `#sr-status` exactly once in the rendered shell and in no partial; the first focusable element is the skip link | Tab once: "Skip to content". NVDA hears "ep17 now 08 panels" once |
| 2.5 | all | Receipt toast region outside every polled block: own-action receipts only, ≥ 6 s and longer while hovered or focused, spoken via announce (P10.4, P07.10 *modified*) | the region exists once; no `.receipt` sits inside an element with `hx-trigger` | press acknowledge: the toast is still readable after 5 s |
| 2.6 | all | Held banner in the header ("Studio held since 19:21 · 'reason' · Lift") and the GPU card reads "Held", never "idle" (P10.2) | the shell renders the banner from a hold fixture; not from an empty one | place a hold on a test DB: every page shows the bar within 2 s |
| 2.7 | ⌘K | The palette indexes every unit (state glyph, book), ranked running › needs-you › recent › rest; Recent (localStorage, try/catch); data refetched on open if older than 10 s; actions limited to hold (opens reason chips), lift, acknowledge (P04.3, P10.10 *modified*) | `palette()` includes ep12 (done) and ep16 (flagged) | ⌘K "ep12" finds it |
| 2.8 | all | One `KEYS` registry → the `?` sheet, `title`s, `aria-keyshortcuts` and the JS map; C4 page keys; `g i` → `/inbox`; single-key on/off switch (`cc-keys`) (P04.6, P07.10, P10.10 keys) | both directions: every sheet chord is in the map, and the reverse | `?` lists `[ ] w A`; turning them off stops `t` |
| 2.9 | all | Crumbs from `shell.crumbs(path)`: `Home › Books › <book> › <stage> › <unit>`, ARIA breadcrumb, last one not a link; base renders `{% block crumbs %}` by default (P04.5, P09.3) | one table test per route shape | every page's crumb starts at Home |
| 2.10 | sidebar | Dept dots: only non-zero state dots, with their meaning in sr text and dots `aria-hidden`; totals kept but muted; "Needs you" is the one name for the place (sidebar label, `/inbox` title) (P03.9 *modified*, P07.6, P09.3) | the accessible name of the episode row = "episode, 1 running, 5 flagged" | screen-reader name check in browse |
| 2.11 | all | Cross-document View Transition: root crossfade at `--d2`, sidebar/header/GPU card named and frozen; never on swaps; skipped on traverse. Speculation-rules **prefetch** (moderate) for `/d/*`, `/b/*` and unit links; preload the two text fonts (P02.5 *modified*, P08.5, P08.10) | template test: one `speculationrules` script, prefetch only, no prerender | 10-frame burst `/`→unit: sidebar pixels identical |
| 2.12 | phone | The More sheet lists departments + pins first; tab badges from the pulse (P04.10) | sheet order test | 400 px screenshot |
| 2.13 | shell | GPU-card dot renamed `.gc-dot` (the 0 px sliver, the `.live` layer clash) (P09.1, template half) | no `class="live"` in `_shell.html` | the dot is 6 px in the screenshot |

### PKG-3 STYLE SYSTEM: `static/css/tokens.css`, `components.css`, `pages.css`, `templates/404.html`, `_icon.html`
| id | page | change (merged from) | test idea | verify live |
|---|---|---|---|---|
| 3.1 | all | One motion token set (`--d0..d4`, `--d-exit`, `--d-wash`, 3 easings) in tokens.css; delete the pages.css `:root` redefinition; tokenise raw durations (P02.1) | `test_the_board_moves_by_tokens.py`: no `ms`/`s` literal outside tokens.css; one `:root` defines `--d*` | computed `--d2` = 200ms on 8700 |
| 3.2 | all | Still mode is a token flip under reduced-motion **and** `[data-motion=still]` (keeps `--d1` hover feedback), replacing the blanket `*{transition:none}` (P02.2, P07.3) | grep: every `infinite` sits under the still guard | emulate reduced motion: `getAnimations()` infinite count 0 |
| 3.3 | all | One-loop law: the GPU card dot is the only infinite animation (the rail's running step on the running unit's page); the heartbeat dot, the Running chip and `.c.running` are static; a failure never loops (P02.3, P07.3, P01.2 *modified*) | allowlist of ≤ 3 selectors may hold `infinite` | browse on 5 pages: infinite animations ≤ 1 |
| 3.4 | all | `.chg` wash (`--think`, `--accent` on failure, `--qc` on a flag, `--d-wash`, once); `.htmx-added` opacity fade only; check-draw on done; `[data-stale]` → `saturate(.4)` + accent "as of"; `.tile:target` static outline plus one wash (P01.7, P02.4 CSS, P03.10, P06.7, P02.10) | CSS presence tests | force a `data-state` flip: a `CSSTransition` on color exists (the node survived) |
| 3.5 | unit live card | Rail fill and done sweep on `transform:scaleX` instead of width; `.live` page rule scoped to `section.live`; `.gc-dot{flex:none}`; CSS-only demotion of the hero log line and the rail's "cached" labels (P02.8, P09.1, P03.4 *modified*) | no `width` keyframes in pages.css | screenshot of ep17 |
| 3.6 | all | Type roles `--t-micro 11 … --t-hero 60`, an 11 px floor, mono only for ids/numbers/times; `button,input,select,textarea{font:inherit}` (P09.2) | pytest CSS census: no font-size < 11 px; no raw px outside tokens | census script on 5 pages: ≤ 10 text styles, no Arial |
| 3.7 | all | Radii only `var(--r-*)`, 0 or 50%; elevation = surface + ring, with a real shadow only on floating layers (P09.7, P09.11) | pytest allow-list over `border-radius` / `box-shadow` | visual compare with the mockup |
| 3.8 | all | `--ctl-line` 3:1 token for inputs, buttons and waiting states; 24 px target floor, 44 px on coarse pointers; `scroll-margin-top` on gate/shot/take anchors; `scroll-padding` for the sticky bars (P07.7, P07.9, P04.9) | extend `test_tokens_meet_contrast` with the non-text pairs | target sweep: 0 under 24 px at 400 px width |
| 3.9 | all | Reserved boxes: `aspect-ratio` on every thumb and chart, `contain:layout paint`, `tabular-nums`; a **static** placeholder shown only after 300 ms, plus a clapperboard glyph slot (P02.7, P06.9, P09.5 *modified*) | no `@keyframes` shimmer in any sheet | layout-shift sum 0 over 10 min on ep17 |
| 3.10 | 404/500 | The error page extends base: a shell card with the code, a sentence, the asked path, and links to Home and its parent; the beige inline style retired (P09.4) | renders with Studio-black tokens, no hex literal | `/nope` screenshot |

### PKG-4 LISTS & HOME: `home.html`, `floor.html`, `department.html`, `book.html`, `books.html`, `architecture.html`, `inbox.html` (new), `_rows.html`, `_floor.html`, `_attention.html`, `_orders.html`, `_lanes.html`, `_today.html`, `viz.py` (new), `_viz.html` (new)
| id | page | change (merged from) | test idea | verify live |
|---|---|---|---|---|
| 4.1 | home, floor, dept, book | Every `every Ns` becomes `pulse:<key> from:body` + morph (C3); stable row ids; the book grid goes live (P01.3, P01.9, P07.2, P04.8, P08.2) | template test: no `every ` in these templates; each row has an id | focus Acknowledge on Home, wait 10 s: the same `activeElement`; a hover video keeps `currentTime` |
| 4.2 | home | Re-rank inside the approved layout: hero, then **Needs you** directly under it (above the fold at 1440×900, the first card on the phone), then the burn line ("34 of 75 GPU-h · lever: 09 shoot 55 %"); drop the duplicate "Shipped with flags" shelf and KPI tile 3; zero-only groups collapse to one line (P03.2, P03.3 *modified*) | the Needs-you section precedes lanes in the DOM; there is no second list of the same units | 1440 and 400 screenshots |
| 4.3 | home | "Since you looked" card as `role=log`, fed by `pulse.events`; new items prepended at the top with a 240 ms fade; an "N new" pill when the feed is scrolled; Mark seen (`cc-seen`) (P01.6, P07.5) | partial renders events newest first with `role=log` | write an event: it appears within 2 s, and focus is unmoved |
| 4.4 | department | No per-row "not acked" text, no "12 steps · 6 gates"; Done collapsed by default; no empty face box; gate chips ordered by severity and capped at 99+; the state bar under the book title (P03.5) | macro tests for chip order and the cap | screenshot vs the mockup |
| 4.5 | lists | Plain gate words with a noun count in `title` ("531 panel faults, kept best of 5"); the state said once per section; "run 6 · 3 h 52" with the run id behind a copy control; ages (P10.8, P03.11) | the row macro output | Inbox row has no ISO timestamp |
| 4.6 | floor, dept | DOM budget: `content-visibility:auto` on below-fold groups, `/floor` done group collapsed; 160 px thumbs with a `srcset` 2x (P08.6, P08.8) | `/floor` ≤ 1 400 elements (the budget test from 1.10) | Lighthouse dom-size passes |
| 4.7 | home, book | Poster tiles un-nested (a stretched link with a sibling button); a "Watch" link → `unit#master?play` (P07.8, P10.11 *modified*) | no `a button` / `button a` in the rendered HTML | Watch → the master playing in one click |
| 4.8 | home, queue | Charts as server SVG from a pure `viz.py` with keyed mark ids and chart-scoped `<defs>`; today's column drawn with an "elapsed so far" ceiling; no tick label within 36 px of now; no tween (P06.1, P06.2, P06.8, P06.11) | `viz.py` pure-function tests (marks, ceilings, tick collisions) | node identity holds across 3 pulses (expando survives) |
| 4.9 | home, floor | Empty states in sentence case with a reason and a next step; the one hold sentence via `actions.HOLD_EFFECT` (P09.9, P10.3) | grep: floor.html has no inline hold text | `/queue` reads "…before its next GPU step" |
| 4.10 | Inbox, architecture | `inbox.html` (the attention list as a page, `Shift+A` = "Acknowledge all N" with `data-key`); a "Standalone ↗ /org" link on `/architecture` (P04.1, P10.5, P04.7 *modified*) | `/inbox` lists exactly `inbox_count()` rows | `g i` lands on /inbox, and the sidebar item is current |

### PKG-5 UNIT & MEDIA: `unit.html`, `_unit_head.html`, `_tails.html`, `_unit_orders.html`, `unit_view.py`, `unit_parse.py`, `static/media.js` (new), plus the tracker files `_live_*.html`, `_unit_live.html`, `static/progress.js`, `progress_view.py` (additive only)
| id | page | change (merged from) | test idea | verify live |
|---|---|---|---|---|
| 5.1 | all media | `media.js`: one play owner (one at a time); a `checkVisibility()` watchdog on `timeupdate`; every `<dialog>` `close` pauses and empties its media; waiting ring after 300 ms, error card with the path, ended → replay; start unmuted, with a "sound blocked · M" chip as the fallback. **Fixes the lightbox Esc-keeps-playing bug and the muted live master** (P05.1) | template test: the lightbox has a close handler and the live master is not `muted` | probe: open take → Esc → zero media with `paused===false` |
| 5.2 | tests | `media_probe` browse script: every play path presents 3 rVFC frames and is visible; every close leaves 0 playing (`@pytest.mark.local`) (P05.2) | itself | run on ep12 and ep17 |
| 5.3 | unit | Head morphs on `pulse:unit:…` instead of the 3 s `outerHTML`; orders and tails refresh on the pulse only (tails only while open); no player sits inside a polled region, and players carry `hx-preserve` (P01.8 *modified*, P05.3, P08.2) | template: no `every ` and no `outerHTML` in unit templates | while ep12 plays, a pulse lands, and the video is unaffected |
| 5.4 | unit | Sibling nav `‹ ep11 · ep13 ›` (`rel=prev/next`, `data-key="[" "]"`), with the neighbours prefetched (P04.4) | ep12 links ep11/ep13; ep01 has no prev | `]` on ep12 → ep13 |
| 5.5 | unit | Truthful posters: a take tile uses its own `TNN_0.png`, the master uses the publish thumbnail, and missing media gets a "why" slot; the lightbox uses the 1024 WebP with the full PNG behind a link (P05.5, P08.7) | `unit_view` poster picks from a fixture tree | tiles show the take, not the panel |
| 5.6 | unit finished | `QC 5/5 ✓` collapses the pass chips (failures in full); the hash moves to properties; one state word per gate; the display question has its appearance parentheticals stripped; "Last words" becomes a muted log line (P03.8, P03.7, P09.13) | `display_question()` strip test | ep17 question has no "(grey eyes…)" |
| 5.7 | unit running | Shots open on the newest panels/takes when ≥ 1 exists; no tab row (SPEC: no tabs), so sections stack with anchors (P03.7, P09.12 moot) | no empty-state paragraph when tiles exist | screenshot |
| 5.8 | unit finished | A new master iteration landing while the page is open shows a `v8 •` badge and a toast; the playing player is never reloaded (P05.6) | badge renders when `latest != shown` | write a fixture iter: the badge appears, playback continues |
| 5.9 | live card (tracker) | Additive only: `aria-valuetext` patched; `announce()` called before `swap()`; `swap()` via `Idiomorph.morph`; `decode()`-then-swap for new panels; the stall-budget marker on the trace; vital goes amber once the heartbeat is 2 pulses old; clocks freeze under `data-stale` (P07.4, P07.1, P07.2, P05.3, P06.6 part, P03.6 *modified*) | existing progress-card tests stay green, plus one per addition | step change on ep17: no blank panel, one spoken sentence |

### PKG-6 ORDERS: `actions.py`, `templates/_macros.html`, `_receipt.html`, `_refused.html`
| id | page | change (merged from) | test idea | verify live |
|---|---|---|---|---|
| 6.1 | every `/act/` form | `hx-disabled-elt="find button"`, `hx-sync="this:drop"`, `:active` press, "sending…" at 0 ms (P08.4, P10.4) | macro output has the disabled-elt; a double submit → one order (FakeConn) | double-click redo: one row |
| 6.2 | receipts | The receipt is a live chip bound to its order id: `pending` → `taken by run …` / `refused: reason`, via `HX-Trigger` detail + `pulse.events`; never claims the effect early (P01.5) | the receipt carries `data-order`; the trigger detail holds the id | redo on ep17: pending → taken within one pulse |
| 6.3 | receipts | Tell the truth about dead letters: an order on a unit that no run will take says so and offers **[Queue now]** (an explicit second order). No silent auto-requeue (P10.1 *modified*) | redo on a done-unit fixture → receipt text plus a Queue-now form | ep12 redo receipt names the gap |
| 6.4 | hold | One `HOLD_EFFECT` sentence: "The step on the GPU now finishes; then every run stops before its next GPU step. Nothing new starts until you lift." Reason chips fill the field; Enter submits; the server still requires a reason (P10.3, P10.8 F8) | a single definition; the chips are present in the macro | panic hold in 2 presses |
| 6.5 | acknowledge | Deferred commit: "Acknowledging ep12 · Undo (5 s)" and the POST fires at expiry or on `pagehide` (sendBeacon); copy matches the backend ("off Needs you until its flags change") (P10.5) | macro test; Undo within 5 s → no POST (JS unit table) | ack then Undo: no `orders` row |
| 6.6 | buttons | Verb labels: "Retry from 09 shoot", "Queue again", "Move to front", "Hold this episode" (P10.9) | label table test | screenshot |

Order of landing: PKG-1 → PKG-2 (both are needed for C1–C5), with PKG-3 and PKG-6 in parallel at any time, and
PKG-4 and PKG-5 in parallel against the contracts. Each package restarts the board and verifies with browse at 1440 and 400, in
Studio black and Graphite, with screenshots under `shots\board\`. Publishable: 1.1+1.2+2.1 as `htmx-pulse`
(fingerprint heartbeat + 204 + morph, report 09), and 5.1+5.2 as `media-contract` (P05). Both are small, MIT, and general.

## 2. Rejected or deferred
| item | from | why |
|---|---|---|
| SSE / WebSocket push | (no one proposed it; P01, P04, P05, P07, P08, P10 argued against) | The truth is SQLite written by other processes, so a push channel is a server poll per tab that holds threadpool slots (scarce, P08) and the HTTP/1.1 connection cap. A 2 s pulse + 204 is glance-instant |
| hx-boost / SPA routing | (P04, P08 against) | Breaks cold-URL = warm render; timers pile up across body swaps; full loads take 10–35 ms + prefetch |
| Skeleton shimmer, streaming shell-first | P09.5 (part) | Pages answer in 2–35 ms, so a shimmer only flashes (NN/g). The slow path was cold thumbs, fixed at 1.5. A static delayed slot is kept (3.9) |
| Count-up / rolling digits, Inbox badge count-up | P04.2 (part) | A rolling digit reads as a change in meaning; it adds a loop. The `.chg` wash replaces it |
| Toasts for background changes | (P07, P09 against) | Vanish, miss the viewer, render under dialogs; the Since feed + wash + announce carry changes. Toasts only echo own actions (2.5) |
| Animated re-sort (FLIP), pulsing alarm badges | (P02, P07 against) | A slide is an event that did not happen; a looping alarm fails WCAG 2.2.2 and trains the eye to ignore it |
| Heartbeat-chip dot breathing | P01.2 (part) | A second loop beside the GPU dot breaks the one-loop law; the chip is static colour, and the dot stops when stale |
| Thumb disk cache under `library/<book>/.thumbs` | P08.1 (part) | The web process is read-only and writes nothing under library. The concurrency limiter + `method=2` addresses the starvation |
| Trickplay sprite, review proxy | P05.7, P05.8 | The board must never decode video. These are good as a **pipeline step** writing `cut/.proxy` (a future decision, publishable) |
| Two-player compare, attempt stacks, Viewer exit motion, hard cuts | P05.9, P05.10, P02.6, P02.7 (viewer part) | They belong to the Viewer build (SPEC_v3), not yet on the board; P02.6/P02.7 recorded as that build's motion rules |
| Home micro-trace on the GPU card, 1 Hz GPU/VRAM chart, run matrix on the live unit | P06.6 (part), P06.10 | A new focal point on Home (P03); run matrix M-effort with events-pairing traps. Deferred; the stall marker on the existing trace stays (5.9) |
| ETA band rebuilt as HTML, hero content diet | P06.5, P03.4 (content) | Lives in tracker-owned `_live_hero.html`; only CSS demotion now (3.5). Raise with the tracker's owner |
| Chart libraries (Chart.js/ECharts) | (P06 against) | Canvas redraws whole, can't morph by key or be asserted in pytest; the bugs are mark-spec bugs |
| stylelint + Playwright snapshots via npm | P09.10 | No npm. Ported to pytest file-read lints (3.1, 3.6, 3.7) + browse screenshots |
| Auto-requeue on redo/retry | P10.1 (part) | Silently starting a run competes for the GPU while an episode is being driven; the receipt says so and offers an explicit Queue now (6.3) |
| Confirm dialogs on reversible actions, bulk checkbox column | (P10 against) | Undo (6.5) and `Shift+A` (4.10) cover them |
| Edits to `architecture/index.html` (`#future/<team>` deep links, per-team notes) | P10.7, P10.12, P04.7 (part) | Outside the allowed file set; P10.12 also adds a write path to a read-only process. Needs its own architecture commit |
| gzip middleware | P08.10 (part) | 127.0.0.1 gains nothing; revisit if the phone reaches the board over the LAN |
| `data-palette` cleanup in mockups, mockup type/colour fixes | P09.14, P09.6 | Mockups are not board files; the board already uses `data-theme`, and 3.6/3.7 lints stop literals on port |
| `pageswap` unit-name morph | P02.5 (part) | Defer until the root crossfade + frozen shell has been seen live |

## 3. Debate table (one line per side, then the ruling)
| # | proposal | for | against | ruling |
|---|---|---|---|---|
| 1 | Shell transport: JSON pulse (P01.1) vs OOB HTML poll at 5 s (P04.2) | One ~1 KB JSON at 2 s drives sidebar, chip, title and section triggers | OOB morph needs no client patching code | **JSON pulse**: one request carries fps and shell numbers; HTML only on change (C1, C3) |
| 2 | Hidden-tab cadence 10 s Worker (P01.4) vs 30 s (P08.3, P10.6) | Death notice within 15 s | Fewer wakeups | **10 s on a Worker**: report 09's notification table needs it; the cost is 1 KB |
| 3 | Skeletons (P09.5) | A blank strip on first paint looks broken | A shimmer flashes at 2–35 ms and adds loops (P02, P05, P08) | **Modify**: reserved box + static slot after 300 ms + "why" glyph |
| 4 | Inbox badge count-up (P04.2) | Draws the eye to a new item | It reads as a value change; it adds motion (P01, P02, P03, P06, P09) | **Reject**: a single wash |
| 5 | Receipt toasts (P10.4) | Polls ate the inline receipt (F7) | Toasts vanish and are not announced (P07, P09) | **Modify**: own-action receipts only, persistent ≥ 6 s, via announce |
| 6 | View Transitions (P02.5) | Navigation feels continuous; the shell is frozen | They block input; dangerous on swaps (P08, P02) | **Accept for navigation only**, never on htmx swaps; pageswap morph deferred |
| 7 | Heartbeat dot breathes (P01.2) | Shows life at a glance | A second loop (P02.3, P07.3) | **Static**; the GPU dot is the one loop |
| 8 | Re-rank Home, drop the poster's weight (P03.2/3) | Five-second test: Needs you is below the fold | The owner approved the mockup look (P05: pictures lead) | **Modify**: keep the approved layout and poster; move Needs you up and drop the duplicate shelf and tile |
| 9 | Remove sidebar totals (P03.9) | Constants compete with dots that move | They are in the approved mockup | **Modify**: totals muted; only non-zero dots, with sr text |
| 10 | Dock tabs: fix wrapping (P09.12) vs remove (P03.7) | Tabs save height | SPEC: "a glance must not need a click" | **Remove** (SPEC); stacked anchored sections |
| 11 | Thumb disk cache (P08.1) | Survives restarts; 63 s TTFB | The web process is read-only | **Modify**: async route + limiter(2) + method=2; RAM LRU stays |
| 12 | Trickplay/proxy (P05.7/8) | Real master frames, instant seek | The board never decodes video | **Reject here**; propose as a pipeline step |
| 13 | Redo auto-queues (P10.1) | Fixes dead-letter orders | Silent GPU work during a driven episode | **Modify**: truthful receipt + explicit Queue now |
| 14 | Ack Undo (P10.5) | Reversible, no new order kind | "Optimistic UI lies" (P01) | **Accept**: deferred commit claims nothing; ack applies on POST |
| 15 | Palette verbs (P04.3/P10.10) | One-keystroke ops | Redo from a palette is unreviewed GPU work | **Modify**: navigation + hold/lift/acknowledge only |
| 16 | Micro-trace on Home (P06.6) | One honest live graphic | A new focal point (P03); a second loop risk | **Defer**; stall marker on the unit trace accepted |
| 17 | Server SVG charts (P06.1) vs mockup inline JS | Morphable, testable at $0 | Port effort | **Accept** for any chart ported (4.8) |
| 18 | Still mode: blanket kill (P07) vs token flip (P02.2) | Simplest | Kills hover/focus feedback that is not motion | **Token flip**, toggle in the shell (3.2 + 2.8) |
| 19 | Crumbs root Home vs per-section (P04.5, P09.3) | One chain from Home | The section is in the sidebar | **Home › Books › book › stage › unit**; h1 never repeats the last crumb |
| 20 | One name: Inbox vs Needs you (P09.3) | Mockup sidebar says Inbox | Four names for one thing | **"Needs you"** everywhere (route stays `/inbox`); "flagged" is the state |
| 21 | Unmuted master (P05.1) | The owner reviews sound | Autoplay policy may block it | **Accept** with the blocked-sound chip fallback |
| 22 | P09 type/radius/elevation lint via stylelint (P09.10) | Drift control | No npm | **Modify**: pytest file-read lints |
