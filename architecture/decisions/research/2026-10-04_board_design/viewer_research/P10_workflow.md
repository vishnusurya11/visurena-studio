# P10 — Owner workflows and microcopy

Lens: the owner's seven real jobs, measured as clicks, waits and words, on today's live board
(:8700, code read in `studio/command_center/`) and on the approved v2 mockups (:8710).
During this pass the live board answered **500** on `/` and the unit page because the re-skin was half done, so the live counts below come
from the templates plus `shots/panel/P03_live_home.png`. The mockup counts come from `index.html`,
`assets/shell.js`, `unit.js` and `dept.js`. A "click" is a pointer press or a key press. Typing a reason or a note counts as **T**.

## 1. Clicks per job: today, mockup, and the proposed target

| # | Job | Live :8700 today | Mockup v2 | Target |
|---|---|---|---|---|
| J1 | What is running, when does it end | Home shows "running 3h50", **no ETA**. The ETA ("done around") exists only on the unit page: 1 click plus a page load | 0 (hero "Done around 21:35", sidebar GPU card on every page, tab title) | 0 on every page, including other tabs and other windows (tab title and favicon) |
| J2 | React to a failure | Home Needs you → unit (1) → scroll to Actions → `retry` (1) = **2 + scroll**. Then nothing runs it (see F1) | 2 (card → Open → Retry) | 1 from the card, and the receipt says who will run it |
| J3 | Acknowledge flags (6 units) | 6 presses, one per row. No undo. The receipt is wiped within ≤2 s by the `every 2s` re-poll of `#attention` | 6, with an Undo that has no backend (F3) | 1 ("Acknowledge all 5", after a look) or `a` per focused card, with a 5 s undo |
| J4 | Redo a shot | Unit (1) → tile (1) → lightbox "redo" (1) → write a note **T** → `redo` (1) = **4 + T**. On a finished unit it then waits for a run that never comes (F1) | 4 + T ("Redo this shot" in the viewer) | 3 + T, and the order also queues the unit |
| J5 | Hold the studio | Go to /floor (1) → write a reason **T** → `hold studio` (1) = **2 + T**. After that, no page except /floor shows that the studio is held (F2) | 2 + T (header "Hold studio…" dialog, or ⌘K) | 2 with a reason chip, and a held banner on every page |
| J6 | Watch an episode | Needs you → ep12 (1) → scroll to the master → play (1) = **2 + scroll** | 2 (poster → Space/play) | 1: a poster's "Watch" opens the Viewer already playing |
| J7 | Refine a team in Architecture | Nav "Org chart" (1) → "Future" tab (1) → find the team by eye. The dept page's `org chart ▸` link goes to `/org#episode`, and **that hash is ignored** (F5). The owner cannot leave a note on a team on the page; refining happens in chat | Same, framed in an iframe pinned to `?theme=dark` | 1 (deep link to the team) + T (a "Suggest a change" note) |

Rule of thumb from the table: the mockup already removes most of the navigation cost (J1, J5, J6). What it does not fix
is **what happens after the click**. On J2, J3, J4 and J5 the owner presses the button and the
studio either does nothing, does it silently, or says something untrue. Those findings matter more than shaving clicks.

## 2. Findings (each one is verified in code, not judged by feel)

**F1. Ordering a unit that is not running is a dead letter, and the receipt hides that.**
`work_orders.take_orders` applies bump, retry, requeue and redo only when *a run of that unit* starts
(`step_runner.run_steps` → `_orders_taken`). The queue claims only `state='queued'` rows
(`queue.claim`). So a `retry` on a failed unit, or a `redo` on a done unit such as ep12, sits pending until
someone starts that unit by hand. The receipt still says "queued at next run — …"
(`actions.QUEUED`). The only order in the db (redo ep14 step 09, 09-29) was taken 11 s later
because an agent started the run, not because the board did. A redo on a done unit needs a
second, hidden order (`requeue`, which lives in the ⋯ menu) to ever run.
→ The receipt must name what will take the order: "pending: ep12 is done and nothing will run it.
[Queue ep12 now]". Better still, Redo and Retry on a unit that is not queued also place the
`requeue` (one form, two `work_orders.order` rows, both shown on the receipt).

**F2. A hold is invisible except on /floor.** `shell.py` carries no hold state, and `base.html`
has no banner. A studio hold left on means nothing ever runs, and the only signal is "idle — nothing
is running", which reads as healthy. → A persistent amber bar in the shell header on every page: "Studio held
since 19:21: 'checking ep17 grids' · Lift". The GPU card says "Held" instead of "idle".
Data: `db` holds rows with `lifted_at IS NULL` (already read for /floor). It refreshes on the existing
`orders-changed` trigger and the 10 s Needs-you poll.

**F3. Hold copy is wrong in three places, and they disagree.** The runner checks the hold *before
each GPU step* (`run_steps`: `if step.GPU and ctx.held(): _refuse_held`). A held run lets the
current step finish and stops before its **next** GPU step. The wording today:
`actions.EFFECTS['hold']` says "runs stop before the **first** GPU step", floor.html says "stops every
run before its **first** GPU step", and the mockup palette says "before its **next** GPU step" (the only one that is right).
→ One string everywhere: **"The step on the GPU now finishes; then every run stops before its next
GPU step. Nothing new starts until you lift."**

**F4. The mockup's Acknowledge copy and Undo do not match the backend.** `index.html` writes "order **ack** placed ·
pending until a run takes it". `work_orders` says acknowledge "is applied at once and no runner acts
on it", and the kind is `acknowledge`, not `ack`. There is no unacknowledge kind, so "Undo" cannot
be built as drawn. → Copy: "ep12 acknowledged: off Needs you until its flags change." For Undo, use the
**deferred commit** pattern: the card shows "Acknowledged · Undo (5 s)" and the POST fires when
the 5 s expire or the page unloads (`navigator.sendBeacon`). This needs no new order kind, and it is the
Gmail "undo send" model (Raskin, *Never use a warning when you mean undo*,
https://alistapart.com/article/neveruseawarning/ ; NN/g user control and freedom,
https://www.nngroup.com/articles/user-control-and-freedom/).

**F5. Deep links into Architecture are dead.** `department.html` links `/org#{{stage}}`, but
`architecture/index.html:1357` honours only `#future` and `#current`. The `command` tab is never
restored either. → Accept `#future/episode` (tab plus team id from `TEAMS`): scroll to the team, outline it
for 2 s, and keep the hash in sync as tabs change. This is what J7's "one click to the team" needs.

**F6. "Notify me" goes deaf exactly when it is needed.** `progress.js` `poll()` returns at once when
`document.visibilityState !== 'visible'`, so a backgrounded unit tab never sees `done`, `dead` or `refused`,
and the Notification never fires. → While `cc-notify` is on, keep polling while hidden at 30 s
(Chrome throttles hidden timers to about 1/min anyway: https://developer.chrome.com/blog/timer-throttling-in-chrome-88/ ;
Page Visibility: https://developer.mozilla.org/en-US/docs/Web/API/Page_Visibility_API). Move the
watcher into the shell (the GPU card already polls), so the owner gets notified from any page, not only from the unit page.

**F7. Polls eat the owner's feedback.** On home, `#attention` re-polls `every 2s` with no focus or
hover guard. The department rows and the unit head use guards (`[!document.activeElement.closest(...)]`). The
acknowledge receipt lands in the row's `.receipt` and is replaced ≤2 s later, so the owner never reads
it, and a press during a swap can land on a node that is being destroyed. → Add the same guard plus `hx-sync="this:drop"`
(https://htmx.org/attributes/hx-sync/). Show receipts in **one toast region** (`aria-live=polite`)
outside the polled blocks, where they stay 6 s. The success toast carries the order id and the effect sentence.

**F8. A panic hold requires a sentence.** `words(reason)` returns 422 on an empty reason. That is good for the
casebook and bad at 2 a.m. → Offer reason chips that fill the field ("checking output", "GPU needed
elsewhere", "wrong direction: stop") and let Enter submit. The server rule stays unchanged.

**F9. Raw names where the owner thinks in pictures.** On the live Needs you list: "EYE_PANELS ⚑531 · MASTER ⚑3 ·
PLAN ⚑7". 531 reads as a disaster but means "panel faults, best kept". Each row also repeats "shipped with flags,
not acknowledged". Floor and home show a full run id
(`20260827135508__episode__20261005040056`) and "attempt 6". → Gate labels Panels / Takes / Master
/ Plan, as in the mockup. Put a count with its noun in the tooltip ("531 panel faults, kept best of 5"). Say the shared state once,
in the section header. Show runs as "run 6 · 3 h 52". Put the run id behind a copy icon.

**F10. Verbs on buttons.** Some labels are fine ("Acknowledge flags", "Redo 07 board…"). Others are bare
kinds: `retry`, `requeue`, `↑`, `⋯`. GOV.UK guidance is that button text says what will happen
(https://design-system.service.gov.uk/components/button/). → "Retry from 09 shoot", "Queue again",
"Move to front", "Hold this episode". "Requeue" and "retry" are runner words. To the owner both mean
"run it again", so show one verb that picks the right kind (F1).

## 3. Shortcuts (single keys, only when no field has focus; listed under `?`)

The mockup already has ⌘K and the G-chords (`shell.js` CHORDS), plus `a` (ack) and `r` (redo) in dept.js. Proposed additions:
`w` watch the focused unit's master in the Viewer · `h` hold (opens the reason chips) · `.` open the
running unit · `j/k` move between Needs-you cards · `Shift+A` acknowledge all visible (with a
5 s undo). The palette should list **live actions with their current target** ("Retry ep17 from 08 panels",
"Lift studio hold (since 19:21)"), not static pages. NN/g on accelerators:
https://www.nngroup.com/articles/ui-accelerators/.

## 4. How to know each change worked

- F1: on a done unit, Redo → `orders` gets a redo row *and* a requeue row → the unit appears in /queue.
  Test: a `FakeConn` act-route test asserts that both rows exist and that the receipt text contains "queued".
- F2/F3: place a studio hold → every page's header shows the bar. The receipt, floor and palette strings are
  the same constant (grep finds one definition).
- F4: Acknowledge, then Undo within 5 s → no `orders` row is written. Acknowledge and wait → one row.
- F5: `/org#future/episode` loads with the episode team outlined (browse screenshot).
- F6: the unit tab is hidden when the run ends → a Notification fires (Playwright with `visibilityState` overridden).
- F7: press acknowledge → the toast is still readable 5 s later. No receipt lives inside a polled node.

## Proposals (ranked)

| id | page | one-line change | effort | files |
|---|---|---|---|---|
| P10.1 | unit, dept, home | Redo/Retry on a unit that is not queued also queues it; the receipt says who will take the order, or offers "Queue now" | M | actions.py, app.py, _receipt.html, _macros.html, work_orders (no change: two `order` calls), tests |
| P10.2 | shell (all pages) | Held banner and GPU-card "Held" state with Lift; held is never shown as "idle" | S | shell.py, base.html, views.py (holds query), css |
| P10.3 | all | One hold sentence ("current step finishes; stops before its next GPU step"), used by the receipt, floor and palette | S | actions.py EFFECTS, floor.html, shell.js |
| P10.4 | home, shell | One `aria-live` toast region for receipts; polled blocks get focus guards and `hx-sync`; no receipt inside a polled node | S | base.html, _macros.html, home.html, css |
| P10.5 | home, unit | Acknowledge with a 5 s deferred commit (Undo with no new kind); correct copy; Shift+A acknowledges all after a look | S | index/home template, small JS in static/, actions copy |
| P10.6 | shell | Move Notify into the shell watcher; keep polling while hidden (30 s) when notify is on | S | progress.js → static/js/shell watcher, shell.py |
| P10.7 | architecture | `#future/<team>` deep links (scroll + outline), hash kept in sync, `command` tab restored; dept links point to it | S | architecture/index.html, department.html |
| P10.8 | home, dept | Plain gate words and counts with nouns; state said once per section; run id behind copy; "run 6 · 3 h 52" | S | _attention.html, _floor.html, views.py labels |
| P10.9 | all | Verb buttons: "Retry from 09 shoot", "Move to front", "Hold this episode", "Queue again"; one "Run again" picks retry or requeue | S | _macros.html, unit.html, _rows.html |
| P10.10 | shell | Palette lists live, targeted actions; new keys `w h . j k Shift+A` in the `?` sheet | M | shell.js (port), shell.py (action list) |
| P10.11 | home | Poster "Watch" opens the Viewer already playing the master (J6 in 1 click) | S | home cards, viewer.js hook |
| P10.12 | architecture | "Suggest a change" note per team, saved as a dated line under `architecture/inbox/` for Claude to pick up (write path only through a new `/act/` route) | M | architecture/index.html, app.py, new route + test, architecture README |

## I will argue against

1. **Confirmation dialogs on every action ("Are you sure you want to acknowledge?").** Acknowledge,
   bump and requeue are reversible or harmless. A confirm on them trains the owner to click through, and the one confirm that matters
   (Hold studio) then stops protecting anything. Use undo for reversible actions and a reason only for hold. (Raskin, linked above.)
2. **Faster polling, or SSE, "to feel more live".** The ruling (`09_liveness_motion.md`) is pulse + morph, no
   SSE. The owner's pain is not 2 s versus 0.5 s of latency. It is feedback that polls overwrite (F7) and orders that
   never run (F1). Faster polls make F7 worse, and SSE adds a long-lived process to a one-GPU studio for no job gain.
3. **Bulk "select rows + actions bar" on the department grid.** There is one owner and about 30 units per department, and the only real
   bulk job is acknowledging ≤6 shipped episodes, which `Shift+A` covers. A checkbox column takes width away from the step bar and pictures
   for a job that happens about once a week.
