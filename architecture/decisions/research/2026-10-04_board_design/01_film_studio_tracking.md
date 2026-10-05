# 01 — Film/TV studio production tracking tools, mapped onto the board

Researcher 01 · 2026-10-04 · scope: Autodesk Flow Production Tracking (ShotGrid), ftrack Studio,
Kitsu (CGWire), AYON, Prism, and how Framestore/ILM run tracking. Mapping key used throughout:
**unit = shot**, **department = pipeline-step family**, **book = sequence/show**, **step = task**,
**master_iterN / take = version**, **gate verdict = review note**, **owner = supervisor + coordinator**.

## Sources

1. Kitsu default statuses and hex colours — zou `init_data`: https://raw.githubusercontent.com/cgwire/zou/main/zou/app/utils/commands.py and `tasks_service.py` (Todo `#f5f5f5`)
2. Kitsu status flags (IS DONE, IS RETAKE, IS FEEDBACK REQUEST…): https://kitsu.cg-wire.com/guides/task-configuration/managing-task-statuses/
3. Kitsu status tag component (uppercase short_name, `thin` outlined variant, `!`/`!!`/`!!!` priority): https://raw.githubusercontent.com/cgwire/kitsu/main/src/components/widgets/ValidationTag.vue
4. Kitsu task side panel (comment + status change in one post, checklist, attachments): https://kitsu.cg-wire.com/guides/review-publishing/update-task-progress/
5. Kitsu shot list / shot page (tasks + newsfeed on the right; Casting, Schedule, Preview Files, Timelog tabs): https://kitsu.cg-wire.com/guides/production-structure/manage-shots/
6. Kitsu review (revision history, compare two versions, `@` frame-timestamp in comments): https://kitsu.cg-wire.com/guides/review-publishing/review/
7. Kitsu publish (thumbnail auto-generated from preview; WFA opens the publish tab): https://kitsu.cg-wire.com/guides/review-publishing/publish/
8. Kitsu status automation (upstream done → downstream ready; "copy the latest preview"): https://kitsu.cg-wire.com/guides/task-configuration/status-automation/
9. ftrack — statuses are configurable, **states** are fixed (Not Started / In Progress / Done / Blocked): https://help.ftrack-studio.backlight.co/hc/en-us/articles/13129960855575-Managing-Statuses and http://ftrack.rtd.ftrack.com/en/3.5.19/faq/administering.html
10. ftrack review player (Approve ✓ / Require changes ✗ next to annotation tools; timeline markers coloured by note age: red <3 h, orange 3–24 h, yellow >24 h): https://help.ftrack-studio.backlight.co/hc/en-us/articles/13129839620247-New-Client-Review-Player
11. ftrack versions (a new version takes the first status in its list, so "ready for review" is automatic): https://help.ftrack-studio.backlight.co/hc/en-us/articles/13129804776471-The-Asset-Version-Review-Workflow
12. Flow PT: pipeline-step columns collapsed (status only) vs expanded (assignee, due date) via the double-arrow header: https://help.autodesk.com/cloudhelp/ENU/SG-Tutorials/files/SG_Tutorials_tu_design_reports_html.html (and the Pipeline Steps help topic surfaced in search)
13. Flow PT detail pages: Activity + Info tabs are fixed, Tasks/Versions/Publishes/Notes added per entity: https://help.autodesk.com/cloudhelp/ENU/SG-Administrator/files/ar-get-started/SG_Administrator_ar_get_started_ar_intro_design_html.html
14. Flow PT activity stream (notes, versions submitted, publishes; items need links at creation): https://community.shotgridsoftware.com/t/is-there-some-setting-to-view-in-activity/8932
15. Flow PT "latest Version status on the Shots page" (a common ask; not native): https://community.shotgridsoftware.com/t/can-i-display-the-status-of-the-latest-version-for-each-shot-on-my-shots-page/8555
16. Flow PT task status codes `wtg rdy ip hld omt cbb fin`: https://community.shotgridsoftware.com/t/fetching-entity-level-status-list/4623
17. AYON Task Progress (folders × task cells, ▶ badge when a reviewable exists, Space to preview, details panel): https://help.ayon.app/en/articles/5526719-task-progress-page
18. AYON Tasks home (board/kanban by status + list; cards carry latest-version thumbnail and folder path; details panel = activity feed + versions + attributes): https://help.ayon.app/articles/2408349-tasks-home-page
19. Prism Project Browser (entity → department → task → versions; Media tab of renders/playblasts): https://prism-pipeline.com/docs/latest/general/Project%20Browser/
20. Framestore / ILM run on Flow PT; Framestore coordinators "keep track of shot statuses and targets" and "organise dailies, rounds and meetings" (job posting surfaced via search: https://framestore.recruitee.com/ ; Autodesk customer story https://www.autodesk.com/customer-stories/framestore-story — 403 to the fetcher, cited from search snippet only).

Not verified first-hand (fetch blocked): ShotGrid default status icon colours, the Shotgun Panel
README. Where I describe ShotGrid UI beyond the sources above it is from product familiarity and
marked *(familiarity)*.

## 1. The brick under every one of these tools

All five tools regenerate from one rule:

> **Entity × Step → Task (one status) → Versions (media + notes) → status rolls back up.**

- Base case: a task cell with a status. Recursive rule: a task produces versions; a version is
  reviewed by a note that sets the task's status; statuses roll up to the entity, the entity to the
  sequence, the sequence to the show. Closure: every page in ShotGrid/ftrack/Kitsu/AYON is a view
  of this one table at a different grain — the shots grid (entity × step), the detail page (one
  entity, all its tasks and versions), My Tasks (all tasks filtered to me), the review playlist (all
  versions awaiting a note), the sequence stats (status counts per step column).
- ftrack names the second half of the brick explicitly: **statuses are paint, states are physics**
  [9]. Studios may invent 30 statuses; the software only ever reasons on 4 states.

**This board already has exactly this table**: `work_orders` (book, department, unit) ×
`work_steps` (12 steps) → state; versions = `cut/master_iterN.mp4`, `takes/r2v/T??.mp4`,
`storyboard/*.png`; notes = gate verdict JSONs (`plan.verdict.json`, `review/eye_*.json`) and
`learnings.jsonl`; roll-up = the department's 31-row table and the book grid. So the redesign is
not "adopt a studio look" — it is "draw every page as one grain of the same table", which the
current pages do inconsistently (home cards, dept table, book grid and unit page each invent their
own status drawing).

## 2. Status vocabulary and colour

**What the tools do.**
- Kitsu defaults [1]: Todo `#f5f5f5` (near-paper: not-started recedes), Ready `#fbc02d`,
  WIP `#3273dc`, WFA (waiting for approval) `#ab26ff`, Retake `#ff3860`, Done `#22d160`. The tag
  shows the **uppercase short_name** (`WIP`, `WFA`) on the colour, letter-spacing 1px [3]. A
  `thin` variant (transparent fill, 1px border in the colour) is used for dense contexts [3].
- ShotGrid uses short codes `wtg rdy ip rev fin hld omt cbb` [16] as icon + code.
- ftrack maps every status onto 4 fixed states [9]; Kitsu does the same with flags
  (`is_done`, `is_retake`, `is_feedback_request`) [2].
- Convention across all: grey = not started, blue = working, purple = waiting on a reviewer,
  orange/red = sent back, green = approved. Everyone also pairs colour with a text code.

**What to take.** The board's 11 legend glyphs (queued, blocked, running, done, flagged, deferred,
failed, escalated, held, stale, skipped) are *statuses*. Give each one a fixed **state** and draw
colour from the state, glyph+code from the status:

| state (colour token) | statuses | light / dark from existing tokens |
|---|---|---|
| `--st-idle` | queued, blocked, skipped, stale | `--ink-3` on `--paper-2` |
| `--st-live` | running, deferred | `--think` on `--think-bg` |
| `--st-review` | flagged, escalated, held (needs owner) | `--qc` on `--qc-bg` |
| `--st-done` | done | `--ok` on `--ok-bg` |
| `--st-fail` | failed / refused / killed | `--accent` on paper |

- Use **tinted fill + dark ink**, not Kitsu's saturated fill + white text: `#22d160` with white
  text is ~2:1, fails WCAG; the board's `--ok #2f6b3a` on `--ok-bg #dfeee2` pairs already exist in
  both themes. Glyph + 2–4 letter code always present (not colour alone).
- Kitsu's "Todo is near-paper" is the single most transferable idea: on `/d/episode` 15 of 31
  rows are solid green bars (screenshot `current/dept.png`). Done should be **quiet** (thin variant:
  1px `--ok` outline, no fill) and only live/review/fail get a fill. The eye then lands on the 1
  running and the 5 flagged rows, which is what the owner glances for.
- `--invent` purple is currently a fault colour ("invented ×18"). Do not reuse purple for a state;
  Kitsu's purple = WFA has no analogue here because judges sign automatically.

## 3. The production overview grid (shots × steps)

**What the tools do.** Kitsu's shots page: rows = shots, first column a thumbnail, then one column
per task type holding the status tag; column headers open a stats modal [5]. ShotGrid:
each pipeline step is a column group, **collapsed** to the status only or **expanded** with the
double-arrow to assignee / dates / version [12]. AYON Task Progress: folders × task cells, a ▶
badge in the corner when a reviewable exists, Space previews it [17].

**On this board.**
- **Department page `/d/episode`** = the shots grid. Columns: thumbnail (48×48 square, matches the
  1:1 episodes) · unit · title · 12 step cells · 6 gate cells · moved · gpu · cost. Each step cell
  is a 22×18 tag reading `work_steps.state` with the glyph; a ▶ corner dot when that step left a
  playable artefact (08 panels → `storyboard/contact.png`, 09 shoot → takes, 10 edit → master).
  This replaces today's 12-segment bar, which encodes the same data without the step identity.
- **Collapsed/expanded step families** (ShotGrid): at ≤ 900 px or on the book page, collapse the
  12 steps into 4 families — *prep* (01–03), *sound* (04–05), *picture* (06–09), *finish*
  (10–12) — each cell showing the worst state inside it; a header toggle expands the family.
  Phone (≥400 px): families only.
- **Book page `/b/{codex}`** = the show-level grid that already exists (department × unit).
  Transpose it to match every other tool: **rows = units, columns = departments**, so it reads
  like the dept page and scrolls vertically for 19+ episodes instead of horizontally. The episode
  column expands (ShotGrid double-arrow) into its 4 step families.
- **Column-header stats** (Kitsu): each gate header shows `✓12 ⚑5 ○14` and clicking filters the
  table to that state (htmx `hx-get` with `?gate=MASTER&state=flagged`).

## 4. Thumbnails-first lists

**What the tools do.** Kitsu generates the entity thumbnail from the latest published preview [7]
and can copy it downstream on status change [8]; AYON task cards carry the latest version's
thumbnail [18]; ShotGrid's first column on every entity page is the thumbnail *(familiarity)*;
people explicitly ask ShotGrid to show the latest version's status on the shot row [15].

**On this board.** One rule, "**the unit's face is its newest picture**":
`cut/master_iterN` poster → newest `takes/r2v/T??` frame → `storyboard/contact.png` → places
output → book cover → glyph placeholder. Use it on the dept rows, home cards (episode card shows
the running unit's face), book grid rows, and the unit header.
- Data gap: the web process makes no thumbnails (D_ui_design line 86, no ffmpeg). Proposal: the
  `edit` and `shoot` step scripts write `poster.jpg` next to each mp4 (the pipeline already runs
  ffmpeg); the board only reads files. The thumbnail cache in process (commit `8b276f0`) serves
  them.
- ep12's takes grid (screenshot `current/unit_ep12.png`) shows 18 of 24 cells as empty beige —
  that is a missing-poster problem, not a layout one; the Kitsu/AYON pattern only works if every
  version has a face.

## 5. The shot (unit) detail page

**What the tools do.** ShotGrid detail page: header strip (thumbnail, name, status, key fields),
then tabs where **Activity** and **Info** are fixed and Tasks / Versions / Notes / Publishes are
added [13]. Kitsu's shot page: task list with statuses on the left, **status newsfeed on the
right**, with tabs Casting / Schedule / Preview Files / Timelog [5]. AYON: the same entity opens a
details panel = activity feed + versions + attributes [18]. Prism: entity → department → task →
versions table [19].

**On this board** (unit page is today a 2,000-px single scroll mixing live card, steps, health,
gates, panels, takes, master, actions, raw):
- **Header strip (sticky, 72 px)**: face thumbnail 64×64 · `ep12 Weybridge and Shepperton` ·
  state pill · step rail (the existing 12-step rail, now tags) · `attempt 31 · 9.8 h gpu · $0`.
  The live "now" card (ep17 screenshot) sits under it only while `state = running`.
- **Two columns ≥ 1100 px** (Kitsu): left = media and tasks, right 340 px = **Activity**. Phone:
  Activity becomes a tab.
- **Tabs, left column** (anchored sections or `hx-get` partials, no JS framework):
  `Overview` (steps + gates summary) · `Versions` (masters, §6) · `Takes` (24-cell grid) ·
  `Panels` · `Plan` · `Raw` (learnings, log, timing). Default tab follows state: running →
  Overview; finished → Versions.
- **Activity column** = one chronological stream merged from `events` (runs started/ended/refused),
  verdict files (gate signed pass/flagged), `orders` (owner redo/hold), `learnings.jsonl`
  (one line each). Each item: time · actor (`judge:master_eye@1`, `runner`, `owner`) · verb ·
  object chip. This is ShotGrid's Activity stream [14] and replaces the separate HEALTH,
  ORDERS FOR EP12 and RAW blocks.

## 6. Version history and review

**What the tools do.** Versions are numbered, each with its own status; a new version auto-takes
the "pending review" status [11]; Kitsu keeps every revision in the comment panel and compares two
side by side [6]; ftrack's player puts **Approve ✓ / Require changes ✗** beside the annotation
tools [10].

**On this board.**
- `Versions` tab lists `master_iter1 … master_iter7`, newest first, each row: poster · `iter7` ·
  duration (`160.2 s, plan 155.5`) · LUFS/peak ticks · MASTER verdict tag for that iteration
  (`⚑3 identity×2 faces×1`) · created time. The row marked "delivered" carries a ▲ published chip
  linking `youtube.json`. Today the iterations are bare links (`iter1 · iter2 …`).
- **Compare** (Kitsu): tick two rows → two `<video>` elements side by side with one shared
  play/scrub (≈30 lines vendored JS). Answers "did iter7 fix what iter6 was flagged for?".
- Takes: each `T??` cell shows its EYE_TAKES result as a corner tag (✓ / ⚑) and the shot size
  label it already has; hover plays (existing), click opens a take sheet with that take's
  `T??.content.json` / `T??.dq.json` findings as notes.
- No Approve/Reject buttons: judges sign, the owner audits (memory: judges replace the eye).
  The owner's equivalent of ftrack's ✗ is the existing `redo NN` order — put it in the version
  row's `…` menu so the action sits on the object it judges.

## 7. Notes and feedback threads

**What the tools do.** Kitsu posts comment + status change + attachment in one act [4], and an
`@` in a comment stamps the current frame, clickable to seek [6]. ftrack colours timeline markers
by note age [10]. ShotGrid notes link to a version and a task and thread replies *(familiarity)*.

**On this board.** Gate verdicts are notes; render them as threads, not tables:
- Thread per gate per round: `PLAN round 2 · judge:plan@1 · ⚑18` → fault lines
  (`invented ×18` with shot chips) → owner order (`redo 02`) → `round 3 · ⚑16` …
  The PLAN `2 ▸ 31 ▸ 18 ▸ 30 → stuck` trend line already exists; the thread gives it its reasons.
- **Frame-stamped faults on the master** (Kitsu `@` + ftrack markers): every fault that names a
  shot (`landmark ×520` on shots 00–23, `identity ×2`) becomes a marker on the master player's
  scrub bar at that shot's start from `timeline` / `timing.jsonl`; marker colour by state
  (`--st-review`), click seeks. The owner then *sees* where the flagged shots are in the cut.
- Shot chips (`00 01 05 08 22`) everywhere link to the same shot: panel, take, timeline position.

## 8. "My tasks" = "Needs you"

**What the tools do.** AYON's home is the user's tasks as a kanban grouped by status, with
thumbnail and folder path per card [18]; ShotGrid/Prism have a My Tasks tab [19]; Framestore
coordinators track "shot statuses and targets" and run dailies and rounds [20].

**On this board** (one user): "my tasks" is everything in state `--st-review` plus pending orders
and holds. The home page's `NEEDS YOU (0)` becomes a short **3-lane board** — *Needs you* ·
*Running* · *Up next* — each card = face thumbnail + `book › ep` + reason line (the fault or
the block reason, e.g. "waiting on refs/04"). Five flagged-and-shipped episodes (ep12–16) are not
"needs you" unless an audit is open; put them in a collapsed *Shipped with flags* lane so they
neither nag nor disappear (memory: a terminal is not a pass).

## 9. Dependencies and dailies

- Kitsu status automation (done upstream → ready downstream) [8] is what `blocked · waiting on
  refs/04` already expresses. Keep the reason text inline in the step cell's title and in the
  card; ShotGrid hides it in a field nobody reads.
- **Dailies** (Framestore rounds [20], Kitsu playlists [6]): a `/floor` sub-view "Today" =
  every version produced since 00:00 across units, as a thumbnail strip with hover-play. This is
  "what does it look like so far" for the whole studio in one row; `events` + file mtimes suffice.

## 10. What not to copy

- Design Mode / per-project configurable pages, custom fields, status lists per project [13]:
  a single-user local board wants one fixed vocabulary.
- Assignment, bids, timelogs, quotas, Gantt (Kitsu Schedule [5]): one GPU, one owner; the ETA
  line on the live card replaces the schedule.
- Client review portals, notifications, @mentions of people: no second user.
- Saturated full-fill status cells on every cell (Kitsu/ShotGrid default): reads as a heatmap of
  "done" and hides the one row that matters.
- ShotGrid's density without hierarchy (20+ columns of equal weight): keep the paper editorial
  headings and rules; the grids live inside them.

## Top 10 recommendations for this board

1. Map the 11 statuses onto 5 fixed states and draw all colour from the state tokens (`--st-*`) — **all pages**.
2. Done is quiet (thin outline), only live/review/fail get fill; glyph + code always present — **all pages**.
3. Replace the 12-segment bar with 12 named step tags + ▶ artefact dot per row — **department `/d/{stage}`**.
4. "The unit's face is its newest picture": a 48 px square thumbnail first in every unit row and card; step scripts write `poster.jpg` — **dept, home, book, unit**.
5. Sticky unit header (face, title, state, step rail, attempt/gpu/cost) + two columns with an Activity stream merged from events, verdicts, orders, learnings — **unit**.
6. A Versions tab listing master_iter1…N with per-iteration MASTER verdict, LUFS, duration, and a two-up synced compare — **unit**.
7. Gate verdicts rendered as round-by-round threads, and shot-naming faults as markers on the master scrub bar — **unit**.
8. Transpose the book grid to rows = units, columns = departments, with the episode column expandable into 4 step families — **book `/b/{codex}`**.
9. Home "Needs you" as a 3-lane card board (Needs you / Running / Up next) plus a collapsed "Shipped with flags" lane — **home `/`**.
10. A "Today" dailies strip of every version produced since midnight — **floor `/floor`**.

## 3 disagreements I expect with other researchers

1. **Saturated vs quiet status colour.** The ops-monitor (Grafana/Dagster) and Kitsu camp will
   want solid green/red fills for scan speed; I argue done must recede because 15/31 rows are done
   and a wall of green is noise. The test: can the owner find the 1 running + 5 flagged rows in
   under a second on `current/dept.png`?
2. **Tabs vs one long scroll on the unit page.** The editorial "paper" researcher will defend the
   single scrolling document; I argue the studio tools all split Activity from media, because the
   unit page is now 2,000 px and the ep17 live card pushes the gates below the fold.
3. **Thumbnails everywhere vs text density.** SaaS researchers (Linear/Vercel) will favour dense
   text rows without images; every film tracker puts the picture first because the product *is*
   the picture. I would hold this one hardest — but it depends on the poster-writing pipeline
   change, and without it empty beige cells are worse than none.
