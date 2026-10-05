# 09 — Live-ness, motion and notifications

Researcher 09, 2026-10-04. Scope: how the whole board (`/`, `/floor`, `/d/{stage}`, unit, `/b/{codex}`, `/org`) stays current, what moves and what never does, and which events reach the owner when he is not looking. Grounded in `studio/command_center/app.py`, `static/progress.js`, `templates/*.html`, `vitals.py`, the progress tracker spec (`docs/audit/2026-10-04_progress_tracker_spec.md`), and measurements against the live board at http://127.0.0.1:8700 (curl, read-only).

## 0. The brick

The board's truth is a SQLite file and a log folder **written by other processes** (runners, `drive.py`). Nothing tells the web process that a row changed. So every transport, whether a browser poll, SSE or a websocket, is a poll at some layer. SSE would only move the poll into the server, one loop per open tab. The cheapest correct design follows from that:

> **One small fingerprint poll per tab. HTML is fetched only for the sections whose fingerprint
> changed, and it is morphed in place, never replaced.**

Notifications, title and favicon badges, and "since you looked" fall out of the same fingerprint response. That is the closure test: one rule regenerates every live behaviour below.

## 1. What the board does today (measured)

| Page | Polls (from templates) | Requests / 10 s | Bytes / 10 s | Problem |
|---|---|---|---|---|
| `/` | floor 2 s, attention 2 s, orders 5 s, lanes 10 s | 13 | ~5.5 KB (620 B + 119 B + 766 B + 9.2 KB) | four timers for one state; every swap is `innerHTML`, even when nothing changed |
| `/floor` | floor 2 s | 5 | 3 KB | page is 140 KB; the rest never refreshes |
| `/d/episode` | rows 10 s | 1 | **77.5 KB** | the whole table is re-sent and re-built every 10 s; open `<details>`, hover and scroll inside the table are lost |
| unit (ep17) | head 3 s `outerHTML`, live JSON 2 s, tails 5 s (when open), orders 10 s | ~10 | head 4.2 KB×3.3 + progress 2.1 KB×5 + tails 31.5 KB×2 ≈ 87 KB | the head swap is why the live card had to move outside `#head` (spec §0) |
| `/b/{codex}`, `/org` | none | 0 | 0 | a book page goes stale silently |

Server time is 2–17 ms per request (`progress` 17 ms, 2 113 B; the spec's budget is under 30 ms and under 6 KB). Load is not the problem. The problems are **churn** (DOM replaced when nothing changed, which resets focus, hover, open details and animations) and **coverage** (live-ness lives on one page only).

**Bugs found in `static/progress.js`:**

1. **Notifications cannot fire when they matter.** `poll()` returns early unless `document.visibilityState === 'visible'`, so while the tab is hidden nothing is fetched and `notify()` never runs. The owner learns that ep17 died only when he switches back, and that is exactly when he no longer needs the OS toast.
2. `new Notification(...)` throws a `TypeError` in almost every mobile browser ([MDN](https://developer.mozilla.org/en-US/docs/Web/API/Notification/Notification)), and the call is not wrapped. On the phone layout (≥400 px), one bad transition stops `apply()` before it reaches `patchVital`.
3. No hysteresis: a run flapping quiet→stalled→quiet→stalled re-fires on every entry into `stalled`. The `tag` dedupes the OS toast, but on Windows it can still re-alert.
4. Notifications, the title and the favicon exist **only on an episode unit page**. Home and floor, the pages he keeps open, show a static "Visurena Studio" and no icon at all (`base.html:6`, no `<link rel=icon>`).
5. Nothing tells him the board itself is down. If uvicorn exits, the card keeps saying `live` with a ticking clock, because the ticks run on the client clock and the poll errors are swallowed (`schedule(last)`).

## 2. Transport: poll vs SSE vs websocket

| | Fingerprint poll (recommended) | htmx SSE extension | WebSocket |
|---|---|---|---|
| Change source | SQLite `MAX(id)`/`MAX(updated_at)`, ~1 ms | the same queries, run in a server loop per connection | the same |
| Connections | short, none held | **one held per tab**. Without HTTP/2 the browser caps it at 6 per origin across all tabs, marked "won't fix" ([MDN](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)). uvicorn serves HTTP/1.1, and `/lib` video range requests share the same 6 slots | one held per tab |
| Hidden tab | timer throttled: 1 wake-up/min after 5 min hidden ([Chrome intensive throttling](https://groups.google.com/a/chromium.org/g/blink-dev/c/8En_5DqV_fU/m/I8e9vaecAgAJ)); a Worker timer is exempt | the stream stays open (an advantage) | the same |
| Shutdown | instant | held streams delay `--reload` and Ctrl-C (the spec already added `timeout_graceful_shutdown=3` for this) | the same |
| Dependencies | none | `htmx-ext-sse` 2.2.4, documented for newer htmx than the vendored **2.0.4** ([htmx SSE](https://htmx.org/extensions/sse/)): an htmx upgrade first | `uv add websockets` plus a client |
| Tests | a plain GET; `TestClient` | streaming responses in tests | the same |

**Ruling: keep polling, and change the unit polled from "a partial on a timer" to "one pulse,
then partials on change".** This keeps the progress spec's ruling (no SSE in v1) and widens it to every page. `pulse.js` is the only code that knows the transport, so if a real push source ever appears (the ComfyUI `/ws` bridge, spec commit 7), only its fetch loop changes, to an `EventSource` on `/api/pulse/stream`.

What the references do: Linear sends server deltas over a websocket into a local object graph ([reverse-engineered](https://github.com/wzhudev/reverse-linear-sync-engine)). That pays off for multi-user writes, which this board does not have. Grafana defaults to a **5 s minimum refresh** and uses websockets (Grafana Live) only for streaming panels ([metricfire](https://www.metricfire.com/blog/real-time-data-visualization-grafana/)). GitHub Actions streams log lines but shows step state as a coarse refresh, with a spinner on the running step. The board needs Grafana's rhythm, not Linear's machinery.

## 3. The live architecture

### 3.1 `GET /api/pulse.json` (new, read-only, `Cache-Control: no-store`)

Query: `?since=<events.id>`. Response budget: **≤ 1 KB typical, ≤ 4 KB worst case, ≤ 5 ms** (plus one `progress()` call per running episode unit, cached 2 s in process, ~17 ms).

```json
{"now": 1791158129.4,
 "fp": {"floor": "a91c", "attention": "07e2", "orders": "412", "lanes": "c3d0",
        "d/episode": "b81f", "d/refs": "11aa", "b/20260827135508": "e0c4"},
 "running": [{"stage": "episode", "codex": "20260827135508", "unit": "ep17", "step": "02 plan",
              "vital": "stalled", "vital_reason": "quiet 22m · budget 10m", "frac": 0.0,
              "finish": null, "attempt": 3}],
 "needs": 2, "idle": false,
 "events": [{"id": 9182, "ts": "2026-10-05T01:55:29Z", "stage": "episode", "unit": "ep17",
             "step": "02", "event": "failed", "detail": "..."}],
 "cursor": 9182}
```

- **Fingerprints** are short hashes of `(MAX(events.id), MAX(work_orders.updated_at), COUNT(*), MAX(orders.id), MAX(holds.id))` scoped to each section. Each section's scope is already in `views.py`: floor = running+next, attention = needs-you rows, d/{stage} = rows of that stage, b/{codex} = rows of that book.
- **Events** are rows of the `events` table with `id > since`, capped at 20 and newest last. The table is append-only with a monotonic `INTEGER PRIMARY KEY` (`studio/db.py:40`), so it is a free cursor. Its `event` values (started/completed/failed/skipped/escalated/deferred) plus the work_orders transitions (flagged verdicts, `stale`, `held`) are the notification feed.
- `running[].vital` reuses `vitals.vital()` through `progress_view.progress()`, so the pulse and the live card can never disagree.

### 3.2 `static/pulse.js` (new, vendored, ~100 lines, loaded from `base.html` on every page)

- Holds `{fp, cursor}`. On each response, for every section key whose fp changed, it calls `htmx.trigger(document.body, 'pulse:' + key)`.
- The partials change their trigger from `every Ns` to `hx-trigger="pulse:floor from:body"` (etc.) with `hx-swap="morph:innerHTML"`. They keep their existing focus guard, `[!document.activeElement.closest('form,dialog')]`; a guarded refresh is retried on the next pulse.
- `progress.js` keeps its 2 s JSON poll **only while its card is visible and running**. Its `notify()` is deleted and its `document.title`/favicon write moves to `pulse.js`, so one place owns every badge.

### 3.3 Rates

| Tab state | Pulse interval | Why |
|---|---|---|
| visible (focused or not; he reads it beside a terminal) | **2 s** | matches the live card; ~200 B/s |
| hidden < 5 min | **10 s** | notifications are the only consumer |
| hidden ≥ 5 min | 10 s from a **Web Worker timer**, so Chrome's 1/min throttle does not apply | a death must reach him within ~10 s, not 60 s |
| nothing running and nothing queued | 10 s visible / 30 s hidden | idle studio |
| fetch error | back off 2→4→8→16→30 s; header shows **"board offline · data 34 s old"** in `--accent` | fixes bug 5; Grafana-style staleness |

### 3.4 Swapping without flicker

- Vendor **idiomorph** `idiomorph-ext.min.js` 0.7.x next to `htmx.min.js` and put `hx-ext="morph"` on `<body>` ([htmx idiomorph](https://htmx.org/extensions/idiomorph/)). A morph reuses nodes by id, so focus, `<details open>`, hover video, scroll position inside `.tbl-wrap` and running CSS animations survive. Every row needs a stable id: `id="wo-{{ r.id }}"` on department, floor and attention rows, and `id="o-{{ o.id }}"` on order rows.
- **Unchanged means no body at all.** A partial request carries `hx-vals='js:{v: this.dataset.v}'`. When it equals the current fingerprint the route answers **204**, which htmx 2 does not swap by default ([htmx docs, response handling](https://htmx.org/docs/#response-handling)). With the pulse this rarely happens, but it makes a direct timer-poll fallback cheap too: the 77.5 KB department table becomes ~0 B on most ticks.
- With morph, `#head` on the unit page no longer resets the live card's animations. The live card may stay where it is, but the constraint that put it there goes away.

### 3.5 Page transitions (View Transitions API)

- Add `@view-transition{navigation:auto}` inside `@media (prefers-reduced-motion: no-preference)`. Cross-document transitions ship in Chromium 126+ and Safari 18.2+; Firefox does not support them yet and gets a plain navigation, which is acceptable progressive enhancement ([MDN](https://developer.mozilla.org/en-US/docs/Web/API/View_Transition_API), [CSS-Tricks](https://css-tricks.com/cross-document-view-transitions-part-1/)).
- One named pair only: `view-transition-name: u-{{unit}}` on the unit name in a department or floor row and on `.lv-name` / the unit head. Clicking ep17 lets the name glide into the page header over `--d2`. Everything else cross-fades at the default.
- **Never** on a poll: `startViewTransition` freezes input for its duration and snapshots the page, so at 2 s it would flicker and block clicks. No `transition:true` on any `hx-swap` that a pulse drives.

### 3.6 Loading, skeletons, optimistic UI

- Responses take 2–17 ms on localhost, so a skeleton would only flash. **No skeletons anywhere.** Pages render complete on the server (they already work without JS). Thumbnails keep `aspect-ratio:1` plus `width/height` so a landing tile never shifts the layout.
- Busy indicator for actions only: `hx-disabled-elt="find button"` on every `/act/` form (`_macros.html`), and an `.htmx-request` spinner glyph with `transition-delay:400ms` so it never appears on a fast answer.
- **No optimistic state change.** An order is "pending until a run takes it" (`_orders.html` header), and a runner may refuse it. The honest version is an immediate receipt ("order #412 placed · pending"), which is already the server's answer in ~5 ms, and then the order row moves through `pending ○ → taken by run ● → (refused ✕)` on later pulses. Linear's optimistic writes rely on a local DB that is always right; this board would be lying.

## 4. Motion vocabulary

The existing tokens (`base.html:300`) are kept: `--d1 120ms --d2 240ms --d3 480ms --d4 900ms`, `--ease-out cubic-bezier(.22,1,.36,1)`, `--ease-std cubic-bezier(.4,0,.2,1)`. These match Material 3's "short = functional, long + emphasized = expressive" split ([M3 easing & duration](https://m3.material.io/styles/motion/easing-and-duration/tokens-specs)). One token is new: `--d-wash: 1600ms` for the change wash.

| Purpose | Duration · easing | What animates | Pages |
|---|---|---|---|
| Feedback (hover, press, focus ring) | `--d1` · std | background, outline colour | all |
| State change of a glyph or pill (queued→running→done) | `--d2` · std | `color`, `background-color` only | rows, pills, rail |
| Arrival (a tile lands, a check draws, a receipt appears) | `--d3` · out | `clip-path`, `stroke-dashoffset`, `opacity` | live card, receipts |
| Progress fill | `--d4` · out | `width` via `--p` | rail, `.sbar` |
| **Change wash** (a row changed while you watched) | `--d-wash` · out | background `color-mix(var(--think) 14%, transparent)`→transparent | dept, floor, home, book |
| Page navigation | `--d2` · std | view transition, one named element | all |
| Liveness (the only loops) | `--breathe` 2.8 s, `--sheen` 2.4 s, `--stripe` 1.6 s | vital halo on a **new signal**; sheen or stripes on the running rail segment | live card only |

**Never animates:**

- digits, clocks or counts (no rolling numbers; tabular-nums only, spec §5);
- row order: a re-sorted queue jumps, it does not slide (a slide reads as an event that did not happen);
- layout size or height (no expanding cards on poll);
- **any terminal or alarm state.** dead, failed, refused and flagged are *still*. They are loud through `--accent`, a ✕ or ⊘ glyph and a sentence, never through a blink. A pulsing red dot is the classic ops-dashboard mistake: it trains the eye to ignore it, and it violates the 5-second rule below;
- anything on `/org` and `/b/{codex}` beyond the change wash;
- more than **one** looping animation on screen at a time (spec §5, extended to every page). On the floor and home, the running unit's glyph is a static `●` in `--think`; it is not animated, and the `.st.blue` pulse stays disabled (`base.html:310`).

**Reduced motion and the 5-second rule.** WCAG 2.2.2 requires a way to pause any motion that starts
automatically and lasts over 5 s, and any auto-updating content ([W3C](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html)). The sheen and stripes run for hours. So:

- `prefers-reduced-motion: reduce` keeps the existing rule (`base.html:414`), extended from `.live *` to `*`. The wash becomes a static tint for 1.6 s, view transitions are off, and values still update.
- A header toggle **"◐ ◼ still"** next to the theme button sets `data-motion="still"` on `<html>` (localStorage `cc-motion`). It has the same effect as reduced-motion and also slows the pulse to 10 s. This is the pause control 2.2.2 asks for.

## 5. "What changed since you last looked"

Two different needs, with two different marks:

1. **Changed while you watched:** the morph sees a row's `data-v` change and adds `.chg` for `--d-wash`. It fades out because you saw it happen.
2. **Changed while you were away:** a **persistent mark** until seen, the way Linear's inbox and Frame.io's comment list show unread items. `pulse.js` keeps `cc-seen` (the last `events.id` seen while the tab was visible, stored in localStorage and per-viewer, which suits a convenience). On load, the rows of units with events above `cc-seen` get `data-new`: a 6 px `--think` dot left of the glyph, plus the visually hidden word "new" (so it is not colour alone). Home gets a one-line strip, **"Since 14:02 — ep17 failed at 02 plan · ep12 MASTER flagged · 3 takes landed · mark seen"**, built from the pulse's `events`, grouped by unit, at most 8 items, with failures first. `cc-seen` advances on "mark seen" and on `pagehide` after the tab has been visible for at least 3 s.

## 6. Notifications, title, favicon, sound

**Who sends them.** `pulse.js`, on **every** page, from the pulse's `running[].vital` transitions
and its `events`. This fixes bugs 1 and 4. It keeps polling when the tab is hidden (§3.3). Every `new Notification` is wrapped in try/catch (bug 2). Several board tabs can be open; OS toasts collapse on the same `tag`, so no tab coordination is needed (BroadcastChannel stays cut, as in spec §0). When the tab has focus (`document.hasFocus()`), the event shows as an in-page line in the "since" strip, not an OS toast.

| Event | Detected from | Notify? | Options | Click opens |
|---|---|---|---|---|
| Unit **done** (episode master cut, other stages completed) | vital→done / `completed` on last step | yes | `tag=unit:done`, `silent:true` | unit page (master player) |
| Run **dead / failed** | vital→dead, `events.failed` | yes, loud | `requireInteraction:true`, `renotify:true` | unit page, retry action |
| Run **refused** (plan_check) | vital→refused, `escalated` | yes, loud | `requireInteraction:true` | unit page |
| Gate **flagged** (judge signed flagged: PLAN, EYE_TAKES, MASTER…) | verdict on the work order | yes | `tag=unit:gate:NAME` | unit page at the verdict |
| **Stalled** | vital=stalled on **2 consecutive pulses**, at most once per unit per 15 min | yes | `tag=unit:stalled` | unit page |
| **Looping**: the same step started ≥ 3 times in one run, or a ladder reaching a terminal rung ("kept, not passed") | `events` started count / `rounds[].terminal` | yes, once per run | `tag=unit:loop` | unit page, ladder |
| **GPU idle**: the floor goes from running to nothing running and nothing queued | `running` becomes empty and `idle:true` | yes, once | `silent:true` | `/floor` |
| Stale lease **with the PID alive** | work_orders `stale` + proc alive | **no**: grey text only (spec §7) | — | — |
| Stale lease with no process | this is `dead` | (see dead) | | |
| Deferred, held, order taken, step completed, take landed | events | **never** a notification: title badge or "since" strip only | | |

The rule behind the table: **notify when the owner must decide, or when a decision he made can now be checked.** Twelve step completions per unit are progress, not decisions. The drive's Telegram `notify()` (spec §7, W6) stays the away-from-desk channel for done and dead. The browser is the at-desk channel; both channels firing on done and dead is acceptable because they reach him in different places.

**Title** (every page, written only by `pulse.js`, with the leading glyph in a fixed position so
tabs line up): `✕ ep17 dead · Visurena` > `(2) ● ep17 09 shoot 11/26 · ~02:45` > `● ep17 plan 1h48` > `○ idle · Visurena`. The `(n)` is the needs-you count. The page name follows the status, so a pinned tab still says what it is.

**Favicon** (32 px canvas, reusing `progress.js` `favicon()`, redrawn **only when the state key
changes**, not on every poll): idle = hollow `--rule` ring. Running = `--think` arc whose sweep is the counted fraction, a quarter arc for a loop step. Needs you = the same plus a `--qc` corner dot. Dead or failed = a solid `--accent` disc with a white ✕. The title text always carries the word, so colour is never the only signal (GitHub's PR tab favicon swaps for pending, success and failure the same way). Add a static `<link rel=icon>` SVG to `base.html` so pages without JS get a mark.

**Sound.** No custom audio. The OS notification sound is the cue, and the `silent` flag carries
meaning: **sound = act now** (dead, refused, flagged, stalled, loop), silence = good news (done, idle). A Web Audio chime would need an unlocked AudioContext and a mute UI, which is cost for no gain on a desktop that already plays the OS sound.

**Opt-in.** The "notify me" button moves from the live card to the header, next to the theme
toggle, as one bell: `🔔 off / on / blocked`, shown only when `window.Notification` exists. The storage key stays `cc-notify`.

## 7. Build shape and publishable artifact

Test-first, $0: `views.fingerprints(conn)`, `views.events_since(conn, cursor, limit=20)`, `/api/pulse.json`, partials answering 204 on an equal `v`; a pure `transitions(prev, next) -> [notification]` in `pulse.js`. Adding the pulse is a shared service, so `architecture/index.html` changes in the same commit. **Publishable:** "fingerprint pulse + morph for htmx boards over files written by another process" generalises to any htmx-over-SQLite dashboard; it could ship as `htmx-pulse` (pulse.js + a Starlette helper) with a write-up comparing it to SSE under the 6-connection limit.

## Top 10 recommendations for this board

1. Add `/api/pulse.json` (fingerprints + events since cursor + running vitals, ≤1 KB) and `pulse.js` on every page — **all pages**.
2. Keep polling while the tab is hidden (10 s, Worker timer) so dead/failed notifications actually fire — **all pages** (fixes `progress.js` bug).
3. Partials refresh on `pulse:<section>` events, not their own timers; unchanged → 204 — **home, floor, department, unit, book**.
4. Vendor idiomorph and switch every polled swap to `morph`, with stable row ids — **department (77.5 KB table), unit `#head`, home strips**.
5. Notification table §6: done, dead, refused, flagged, stalled (2-pulse hysteresis, 15-min cooldown), loop ≥3, GPU idle; never step-level — **all pages**.
6. Title + state favicon written by one owner (`pulse.js`) with the needs-you count, redrawn only on state change — **all pages**.
7. "Board offline · data N s old" header state on fetch failure; stop the client clocks from implying life — **all pages, unit live card**.
8. Persistent unread dot + "Since 14:02 …" strip from the events cursor; 1.6 s wash for changes seen live — **home, department, floor**.
9. Motion law: one loop on screen, terminal states never animate, no rolling digits, no row-reorder animation; header "still" toggle + reduced-motion = WCAG 2.2.2 — **all pages**.
10. Cross-document view transition with one named element (unit name row→head), off under reduced motion, never on polls; no skeletons, no optimistic state — **department/floor → unit**.

## 3 disagreements I expect with other researchers

1. **"Premium means realtime push."** A SaaS-leaning seat will propose SSE or websockets "like Linear". I say no: the source is a SQLite file written by another process, so push only hides a server-side poll, and it costs held connections under HTTP/1.1's 6-per-origin cap, slower shutdown, and an htmx upgrade. The polish comes from morph + 204, not from the pipe.
2. **"Motion signals quality."** A visual-polish seat will want skeleton shimmer, count-up numbers, animated row re-sorting and a pulsing red failure badge. I say the premium tools (Linear, Vercel, Frame.io) earn calm with still alarms and one moving thing. Localhost answers in 2–17 ms, so a skeleton is only a flash, and a blinking failure fails WCAG 2.2.2 and trains the eye to ignore it.
3. **"Notify everything, add a notification centre."** An ops or Grafana seat may want an alert rule per step event, toasts per landed take, or a bell inbox. I say notify only on a decision or a checkable outcome, around eight event types, with hysteresis. Everything else goes to the title badge and the "since you looked" strip, which is the inbox.
