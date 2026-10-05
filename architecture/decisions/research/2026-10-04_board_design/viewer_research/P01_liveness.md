# P01: Real-time and liveness

Panelist P01, 2026-10-04. Lens: what updates without a reload, how fast it updates, and how the change is shown.
I built on research report 09 (`architecture/decisions/research/2026-10-04_board_design/09_liveness_motion.md`).
I re-measured it against today's board and the half-finished re-skin, and I do not repeat its rulings
(fingerprint pulse, idiomorph, no SSE, the notification table). I add what the v2 shell changes: a
GPU card on every page, live counts in the sidebar, the "live · 19:21" chip, and order receipts.

Measurement script: `research\p01\measure.py`. Raw output: `research\p01\measure.json`.
Screenshot of the approved Home mockup: `mockups\shots\panel\P01_home_mock.png`.

## 1. Today's polling on :8700 (measured 2026-10-04, read-only)

For each page, the script parsed every `hx-trigger="every Ns"` and the `#live` card's JSON poll,
fetched each one with `HX-Request: true`, and multiplied the bytes by the rate. Times are warm repeats.
The first cold pass was slower, see §1.2.

| Page | Timers | Req/min | KB/min | Largest poll | Swap |
|---|---|---|---|---|---|
| `/` | count 10 s, floor 2 s, attention 2 s, orders 5 s, lanes 10 s | **84** | **196** | attention 3.9 KB every 2 s (117 KB/min alone) | innerHTML ×5 |
| `/floor` (page 140 KB) | count 10 s, floor 2 s | 36 | 18 | floor 622 B | innerHTML |
| `/d/episode` (page 115 KB) | count 10 s, rows 10 s | 12 | **454** | rows **77.5 KB** every 10 s | innerHTML of the whole table |
| unit ep17, running (page 127 KB) | count 10 s, head 3 s, orders 10 s, tails 5 s (only while open), progress JSON 2 s | **74** | **491** | tails 25.6 KB every 5 s; head 4.1 KB every 3 s (**outerHTML**) | mixed |
| unit ep12, done (page 174 KB) | count 10 s, orders 10 s | 12 | 0.6 | orders 93 B | innerHTML |
| `/b/{codex}` | count 10 s | 6 | 0 | none | the book grid never refreshes |
| `/org` | none | 0 | 0 | none | none |

### 1.1 What the numbers say

- **The rate is backwards.** Home, which mostly shows things that change hourly, sends 84 requests
  a minute. The book page, where a whole season's state lives, sends none. Nothing in today's code
  ties a request rate to whether anything changed.
- **Bytes go into re-sending things that did not change.** On a quiet studio, close to 100 % of the 196 KB/min on Home
  and the 454 KB/min on the department page is identical HTML. No route answers 304 or 204, so
  every tick is a full body plus a full DOM rebuild. That rebuild drops hover video, open `<details>`, selections and
  scroll position inside `.tbl-wrap`. The server does not support HEAD (405) and sends no ETag.
- **Server speed is fine when warm.** Warm times: partials take 2–27 ms and the progress JSON 6–9 ms.
- **Seven separate timers per page and no single clock.** On Home the five timers drift apart, so the
  "needs you" count (10 s) and the attention strip (2 s) can disagree for up to 8 s. That is
  exactly what makes a dashboard feel cheap: two numbers on one screen saying different things.

### 1.2 What I saw happen while measuring (these are liveness bugs in their own right)

- The **first cold pass** took **18.3 s** for the ep17 page, **4.6 s** for its head partial and **3.4 s** for `/b`.
  This happened while the re-skin builder was editing files and uvicorn was reloading. Ninety seconds later every full page
  (`/`, unit, `/b`) answered **500 Internal Server Error** (21 B). The partials kept answering 200.
  An open tab therefore kept polling green partials into a page that could no longer be loaded.
  Nothing on screen said anything was wrong. htmx 2 does not swap a 4xx/5xx by default
  ([htmx docs, response handling](https://htmx.org/docs/#response-handling)), and no
  `htmx:responseError`/`htmx:sendError` handler exists in `base.html`. **The board cannot tell
  "nothing changed" from "the board is broken".**
- The new shell (`templates/_shell.html`) puts a **GPU card on every page** with `data-progress`,
  `data-eta` and `data-prog style="width:0%"`. The `gpuchip` in the page header has `data-eta` too.
  The script that would fill them, `static/board.js`, is referenced by `base.html:13` but **does not exist yet**.
  The sidebar's counts, dots and pins are also rendered once per page load (`shell.py`). As built
  today the shell is a **static picture of a live thing**: the progress bar sits at 0 %, the ETA is
  empty, and the pin stays after ep17 finishes until you navigate.
- `progress.js` still has the bugs report 09 listed: it skips the poll when the tab is hidden, its
  `new Notification` is not wrapped, and a failed fetch keeps the client clocks ticking as if the
  board were alive.

## 2. What "living" means for one owner on one GPU

He keeps the board open beside a terminal all day and glances at it. A glance has to answer three
things in under 1 s ([NN/g response-time limits](https://www.nngroup.com/articles/response-times-3-important-limits/)):
**Is the GPU working? On what, and until when? Has anything happened that needs me since I last looked?**
Each answer is trustworthy only if the screen also shows **how old it is**. Grafana shows a
"last refreshed" time, and Vercel's deployment page shows a live status dot with a relative time.
The mock's "● live · Sun 4 Oct, 19:21" chip (top right) is the right element. It has to stop being
decoration and become the board's **heartbeat**.

## 3. Proposals in detail

### A. One heartbeat drives everything: the shell becomes the subscriber
Report 09's `/api/pulse.json` (fingerprints, events since the cursor, the running vitals) is the transport.
My addition: **the shell is its first consumer, not the page content**. The pulse response adds
`shell: {inbox, queue, dept_dots:{stage:[...]}, pins:[...], gpu:{unit, step, frac, finish, vital}}`,
about 400 B, all from the same `views` calls `shell.py` already makes. On each pulse `board.js` patches:
- **the GPU card**: progress `--p` width (900 ms ease-out, as with `--d4`), step text, `~21:35` finish, face swap
  when the unit changes (a 240 ms cross-fade on the `<img>` only);
- **the sidebar counts**: Inbox `5`, Queue `92`, and the department dots. A count change shows the digit
  in `--think` for 1.6 s (the wash), then plain. **No rolling digits**;
- **the pins**: added or removed in place;
- **the heartbeat chip**: `● live · 19:21:04`.
Because every page has the shell, every page becomes live at about 1 KB per 2 s (≈30 KB/min), and the
seven timers per page go away.

### B. Heartbeat chip = staleness = offline state
The `.ph-actions` chip shows the age of the last good pulse, not the client clock:
- `● live`: last pulse under 5 s ago. The dot is the **only** looping element in the header, a 2.8 s
  breathe, and it stops under `data-motion="still"`.
- `◌ 34 s old`: the pulse is late (5–60 s). The dot stops and the text goes `--muted`.
- `✕ board offline · data 3 m old · retrying in 8 s`: fetch error or 5xx. Shown in `--accent`, and the whole
  `<main>` gets `data-stale` so it reads as `filter: saturate(.4)`. **Every client-ticking clock freezes**:
  the GPU card ETA and the live card's `run 26 min`. A clock that ticks while its source is dead is a lie.
- `↻ board restarted · reload`: the pulse carries `boot: <server start ts>`. A changed `boot` means
  templates or static changed under the tab (today's re-skin case), so the chip offers a reload
  instead of morphing new partial markup into an old page.
Backoff: 2→4→8→16→30 s. On `online`/`visibilitychange` an immediate retry
([MDN `navigator.onLine`](https://developer.mozilla.org/en-US/docs/Web/API/Navigator/onLine) is only a
hint, so the fetch result decides).

### C. Partials answer 204 when nothing changed, and morph when something did
This is report 09's rule, and I endorse it with today's numbers. Each polled section carries `data-v`
(its fingerprint). The request sends `v` and the route answers **204** when it is unchanged.
On a quiet studio the department page drops from **454 KB/min to ~0**. Home drops from
**196 KB/min to the 30 KB/min heartbeat**. Partial swaps use `hx-swap="morph:innerHTML"` (idiomorph,
[htmx idiomorph](https://htmx.org/extensions/idiomorph/)) with `id="wo-{id}"` on rows. One test makes the rule enforceable:
`test_partial_204_when_fingerprint_matches` for each partial route.

### D. "Changed while you watched": pulse + morph, shown once
When a morph changes a row, `board.js` adds `.chg` (a 1.6 s `--think` wash) to that row. On the
GPU card a step change (07 board → 08 panels) gets a 480 ms tick on the progress line: the segment
fills, then the label slides **in place**, with no layout shift. A finished unit gets one still `✓` that
draws its stroke over 480 ms (`stroke-dashoffset`), then nothing moves. A **failure never animates**,
as report 09 §4 and WCAG 2.2.2 require ([W3C](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html)).

### E. "Since you looked": the mock's card, fed by the events cursor
The mockup's "Since 14:02 · ep17 · 4 events · Mark seen" card (Home, right column) is the
right shape. It reads `events.id > cc-seen` from the pulse. New items enter **at the top**
with a 240 ms fade, and the timestamp is relative (`2 m`) with an absolute `title`. Units on any list with
unseen events get a 6 px dot plus the hidden word "new". The sidebar's Home item carries the
unseen count when you are on another page. `cc-seen` advances when you press "Mark seen", or on `pagehide`
after the page has been visible for at least 3 s. This is per-viewer convenience state, so localStorage is acceptable here.

### F. Order receipts: immediate, honest, then they progress
Today a receipt is a `<span class="ok">` that never changes, and the Orders table on Home refreshes
every 5 s, separately. Proposal: the receipt becomes a **live chip bound to its order id**:
`#412 redo ep17 · ○ pending` → (next pulse whose `orders` fingerprint changed) `● taken by run 0405`
or `⊘ refused: <reason>`. It **does not claim the effect optimistically**. The order is "pending until a
run takes it" (`_orders.html`), and Linear-style optimistic UI fits only a local store that is always
right ([Linear sync engine](https://github.com/wzhudev/reverse-linear-sync-engine)). What *is* immediate:
`hx-disabled-elt="find button"`, the receipt within one frame of the 5 ms response, and the
`orders-changed` event that already exists (`HX-Trigger`), which also pokes the pulse so the floor
reflects a hold **now** instead of in 2 s. The chip clears itself 10 s after a terminal state.

### G. Hidden tab, title and favicon on every page
Report 09 §3.3/§6 applies unchanged, now owned by the shell. The rates are 2 s visible and 10 s hidden on a
Worker timer, because Chrome throttles hidden-tab timers to 1/min after 5 min
([Chrome intensive throttling](https://developer.chrome.com/blog/timer-throttling-in-chrome-88)).
The title becomes `● ep17 07 board ~21:35`, or `✕ ep17 dead` / `○ idle`, and the favicon arc is the GPU
card's `frac`. The pinned tab then tells him the same thing the GPU card does without being opened (GitHub's PR tab icon
does this for checks).

### H. The ep17 unit page: one clock for the whole page
Today the unit page runs a 3 s head `outerHTML` swap, a 2 s JSON poll and a 5 s tails poll. The head swap
is why the live card had to live outside `#head`. With the pulse, the head morphs only when
`fp["unit:ep17"]` changes. Tails (25.6 KB every 5 s) fetch only while open **and** on change, with a `since=<byte offset>`
so only new log lines are appended (`hx-swap="beforeend"`), the way GitHub Actions streams log lines. The
page's traffic drops from 491 KB/min to about 35 KB/min (heartbeat + progress JSON).

## 4. How we know it worked (acceptance, measured on :8700)

1. Re-run `research\p01\measure.py` with a pulse-aware variant: requests per minute on **any** page ≤ 31
   (one pulse every 2 s + one progress JSON on a unit page), and KB/min on a quiet studio ≤ 35 on every page.
2. Stop uvicorn with a tab open: within 8 s the chip reads "board offline", the GPU ETA and run clocks
   freeze, and a screenshot proves it. Start uvicorn again: the chip reads "board restarted · reload" (or `live`
   if `boot` matched).
3. Hover a take tile's video on `/d/episode`, then make a runner write an event. The video keeps playing and only the
   changed row washes. This checks that morph preserved the node: `document.activeElement` and `video.currentTime` are unchanged.
4. Hide the tab for 6 min while a unit is killed: an OS notification arrives within 15 s.
5. Place a redo: the receipt reads `pending` in under 100 ms, and `taken`/`refused` within one pulse of the
   runner's write.

## Proposals

| Id | Page | Change | Effort | Files |
|---|---|---|---|---|
| P01.1 | all | `/api/pulse.json` with a `shell` block + `board.js` that patches the GPU card, sidebar counts, pins and the heartbeat chip from it; delete the per-page `every Ns` timers | M | app.py, views.py, shell.py, static/board.js (new), templates/_shell.html, base.html, home/floor/department/unit.html |
| P01.2 | all | Heartbeat chip = staleness: live / N s old / offline + backoff / "board restarted · reload" via `boot`; freeze client clocks when stale | S | static/board.js, static/progress.js, base.html, app.py (boot ts) |
| P01.3 | home, dept, floor, unit, book | Partials answer **204** on an equal fingerprint `v`; `morph:innerHTML` with stable row ids (idiomorph vendored) | M | app.py, views.py, static/idiomorph-ext.min.js (new), _rows/_floor/_attention/_orders/_lanes/_unit_head.html |
| P01.4 | all | Hidden-tab Worker pulse at 10 s + wrapped notifications + title/favicon owned by the shell (moves out of progress.js) | S | static/board.js, static/progress.js |
| P01.5 | all | Order receipt as a live chip bound to the order id: pending → taken / refused; `hx-disabled-elt`; `orders-changed` triggers an immediate pulse | S | templates/_receipt.html, _macros.html, static/board.js, actions.py (order id in HX-Trigger detail) |
| P01.6 | home + sidebar | "Since you looked" card + unread dots from the events cursor; Home item badge off-page | M | views.py (events_since), templates/home.html, _shell.html, static/board.js |
| P01.7 | rows, GPU card | Change wash 1.6 s on morphed rows/counts; GPU card step tick + face cross-fade; still alarms | S | static/css/*.css, static/board.js |
| P01.8 | unit (running) | Tails append-only by byte offset, on change only; head morph replaces the 3 s outerHTML | M | app.py, unit_view.py, templates/unit.html, _tails.html |
| P01.9 | `/b/{codex}`, `/org` | Opt into the pulse with a fingerprint per book; the grid morphs per cell | S | views.py, templates/book.html |

## I will argue against

1. **SSE or WebSockets "for real-time"** (likely from a SaaS-craft or performance lens). The truth is a
   SQLite file written by other processes, so a push channel is a server-side poll per open tab. uvicorn
   serves HTTP/1.1, which caps a browser at 6 connections per origin, shared with `/lib` video range requests
   ([MDN SSE](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)).
   A 2 s pulse that usually answers in under 1 KB is already "instant" at glance speed. The 204+morph saving is 400 KB/min;
   push saves about 1 s of latency nobody can perceive at a glance.
2. **Skeleton loaders, shimmer and count-up numbers** (likely from a visual-polish lens). Responses take 2–27 ms. A
   skeleton only flickers, and a rolling digit makes a stable count look as if it changed. Premium here
   means *nothing moves unless the studio moved*.
3. **Optimistic order state** ("show ep17 as redoing the moment you click"). A runner may refuse the order
   (plan_check), and a hold acts only before the next GPU step. The honest version is the receipt's state
   machine (P01.5). Showing the effect before it happens would teach him to distrust the board the first time it
   is refused.
