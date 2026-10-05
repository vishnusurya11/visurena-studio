# 07 — Information architecture & navigation

Researcher 07, 2026-10-04. Scope: the page set, global navigation, breadcrumbs, cross-links,
URL design, deep links, search, the landing page, the first viewport of every page, the phone.
Evidence: the live board at http://127.0.0.1:8700 (read-only, GET only), `studio/command_center/app.py`
(6 pages, 9 partials, 4 JSON twins, `/lib`, `/thumb`, `/act/*`), `templates/base.html`, the
eight screenshots in `current/`, and the 2026-09-25 spec `D_ui_design.md`.

## 1. What the board has today (measured, not remembered)

| route | template | what the owner sees first (1440×900) | finding |
|---|---|---|---|
| `/` | home.html | "On the floor" line, "Needs you (0)", 5 department cards, orders, today | **Needs you says 0 while ep12–ep16 are flagged with 4/20/26/27/37 faults and published (`▲ file` on the book page).** `views.attention` reads `v_attention` = failed, deferred, escalated, stale. Flagged is not in it. The landing page says "nothing" at exactly the moment the memory *"a terminal is not a pass"* (ep12 shipped over keep_best/flag) says it should say something. |
| `/floor` | floor.html | "Call sheet", then a 92-row table | 92 rows, each with its own `why hold?` input and `hold` button: that's 92 forms. Rows 4–92 are 89 untouched `refs/screenplay/trailer` units at priority 0. The page reads as a phone book. |
| `/d/{stage}` | department.html | filter pills, then one table per book | `/d/refs` shows 30 near-identical blocks for 1 flagged + 2 started units (refs.png is 4521 px tall). |
| `/d/{stage}/{codex}/{unit}` | unit.html | live card (episode only), header, step strip, health, gates | This is the best page. Anchors already exist (`#take-T05`, `#panel-…`, `#gate-PLAN`, `#master`, `#health`, `#gates`, `#raw`), **but nothing links to them**: a fault chip `05` under `PLAN ⚑7 invented` doesn't jump to shot 05, and a `#take-T05` URL does not open the lightbox. |
| `/b/{codex}` | book.html | department × unit matrix | The H1 shows the raw codex id `20260827135508`. The breadcrumb `Studio › Books › …` has an unlinked "Books" because **`/b` returns 404**: there's no book index. 30 books are reachable only through department pages. No picture of any episode. |
| `/org` | architecture/index.html served raw | "Visurena Story Department" | **No link back to the board.** It's a dead end with its own chrome. |
| — | — | — | `/search`, `/d`, `/b` → 404. No search, no ⌘K, no keyboard shortcuts besides the lightbox arrows. |

Global nav today: a top bar in `base.html` reading `Home · Floor · analysis · screenplay ·
trailer · refs · episode · Org chart` with the theme toggle on the right. On the phone
(unit_ep17_phone.png) the bar wraps to 2 lines plus a third line for ◐, so **~165 px of a
400×860 screen goes to chrome before the breadcrumb**.

The board's three questions (BRIEF): *what is running and when does it end*, *what is stuck and
why*, *what does it look like so far*, *what do I do*. Today the first one has an answer on every
page only on the unit page (live card). The second has no answer on the landing page, because
of the flagged gap. The third has no answer above unit level.

## 2. How the reference tools structure navigation, and the part this board takes

- **Linear**: a left sidebar with *Inbox* and *My issues* above the workspace's teams. **⌘K** is
  the universal command menu, plus `G` then `I` / `G` then `V` go-to chords. Issue URLs are
  `linear.app/<ws>/issue/ENG-123/<slug>`: the stable short ID is the key and the slug is cosmetic.
  Sources: https://linear.app/docs/inbox · https://linear.app/docs/conceptual-model ·
  https://linear.app/docs/keyboard-shortcuts. **We take** the Inbox as a first-class page, ⌘K,
  the go-to chords, and "stable id + cosmetic slug" URLs. **We don't take** the sidebar: Linear
  needs it for N teams × M views, and this board has 5 departments and 1 user.
- **Vercel**: the breadcrumb *is* the navigation. `Team ▾ / Project ▾ / Deployment` is a chain of
  switchers, each segment a dropdown of its siblings, and the project page opens on the
  latest production deployment with a screenshot. Source: https://vercel.com/docs/dashboard-features ·
  https://vercel.com/docs/deployments/managing-deployments. **We take** the switcher breadcrumb
  (`The War of the Worlds ▾ › episode ▾ › ep17 ▾`) and "open on the latest artefact's picture".
- **Dagster**: the left nav is Overview, Runs, Assets, Jobs, Automation, Deployment. *Overview →
  Timeline* draws every run as a bar on a time axis, one row per job, which shows at a glance
  what ran when and what overlapped. A run page has a stable `/runs/<run_id>` URL. Assets and
  runs cross-link both ways. Source: https://docs.dagster.io/guides/operate/webserver ·
  https://docs.dagster.io/guides/monitor/logging. **We take** the Timeline as its own page
  (one GPU = one lane, so it's simpler than Dagster's) and the run_id as an addressable thing.
- **ShotGrid / Flow Production Tracking**: Project → entity pages (Shots, Assets, Tasks, Media).
  An entity's detail page has tabs (Tasks, Versions, Notes), and a global *My Tasks* / *Inbox*
  sits outside any project. Shot URLs are `/detail/Shot/1234`. The *project overview* is a grid
  of shot thumbnails with status pills. Source:
  https://help.autodesk.com/view/SGDOCS/ENU/?guid=SG_Tutorials_tu_navigating_the_interface_html ·
  Kitsu's production → episode → shot grid with thumbnails, https://kitsu.cg-wire.com/.
  **We take** book-first hierarchy (book = project, episode = shot/sequence, department =
  pipeline step) and the **season grid of thumbnails** as the book page's first viewport.

These four tools agree on one rule. **The object hierarchy is project → unit, and the pipeline
step is an attribute or a filter, not the parent.** The board has it the other way round
(`/d/{stage}/{codex}/{unit}`, breadcrumb `Studio › episode › book › ep17`). For the owner,
"ep17" is an episode *of The War of the Worlds* first, and a row in the episode department second.

## 3. Sitemap (proposed)

```
/                         NOW          — landing: GPU lane, needs-you, next, today        (replaces home)
/inbox                    NEEDS YOU    — every item the owner must look at, oldest first   (new)
/queue                    QUEUE        — the call sheet, grouped & collapsed               (was /floor)
/timeline                 TIMELINE     — the one GPU's runs on a time axis, 24 h / 7 d     (new)
/books                    BOOKS        — the shelf: book × department grid, 30 rows        (new; fixes /b 404)
/b/{book}                 BOOK         — season grid of episode posters + department matrix
/b/{book}/{stage}/{unit}  UNIT         — the unit page (canonical)
    …/{unit}/take/T05     · unit page with the T05 lightbox open
    …/{unit}/shot/07      · unit page scrolled to shot 07 (panel + take + its faults)
    …/{unit}/gate/PLAN    · unit page scrolled to the PLAN verdict, faults expanded
    …/{unit}/run/{run_id} · that attempt's health row expanded with its log tail
/d/{stage}                DEPARTMENT   — kept: one department across books, active books first
/org                      ORG CHART    — kept, wrapped with the board's top bar
/search?q=                SEARCH       — the ⌘K results as a page (no-JS fallback, phone)
/api/index.json           the palette's index (books, units, gates, runs; ~20 KB)
legacy: /floor → 301 /queue · /d/{stage}/{codex}/{unit}[#x] → 301 canonical · /b/{codex} → 301 /b/{slug}
```

Merge or keep decisions:
- **home + floor's "on the floor" → `/` Now.** Both pages open on the same "On the floor" line
  today. The floor's 92-row table becomes `/queue`; the floor stops being a landing candidate.
- **Inbox is a page, not a strip.** It's the only page whose count changes the owner's next
  action, so it gets a nav badge (`Inbox 5`).
- **Timeline is new and cheap.** `work_steps` already has started/finished per step and
  `events` has the run boundaries. One lane, because there is one GPU, plus a thin CPU lane
  for non-GPU steps (record, timeline, edit). That answers "what did the GPU do overnight"
  better than the today strip's 5 links.
- **Books index is new.** It fills the breadcrumb hole and serves as the season overview of
  the whole shelf.
- **Not added:** a separate "artefacts" browser (artefacts belong to their unit, ShotGrid's
  Media page is for teams of reviewers); a "runs" list page (runs live under the unit, plus the
  timeline); a settings page.

## 4. Global navigation

**A top bar, kept and restructured. No sidebar.** The arguments: 1 user, 6 destinations,
`max-width:1180px` content that would lose 220 px to a sidebar, and the org chart's
editorial look is a top-ruled page (the 3 px `--ink` rule under the header is its signature).
A sidebar earns its width only when the destination list is long or user-specific (Linear,
ShotGrid). Here it is neither.

```
Visurena Studio   Now  Inbox ⑤  Queue  Timeline  Books  Departments ▾  Org      [⌘K search]  ● ep17 02 plan · ~21:40  ◐
```
- **The GPU pill** (right side, every page): `● {stage} {unit} {step_id} {step_name} · ~{eta}`
  from `/api/floor.json running[0]` plus progress `eta`, polled with the existing 10 s
  `hx-trigger`. Idle: `○ GPU idle · next ep01`. Held: `⏸ studio held`. Clicking it opens the
  running unit. This answers question 1 on every page, the way Vercel's build-status dot does.
  The state is carried by glyph and word as well as colour.
- **Inbox badge**: the count from §5, using `--accent` background and `--accent-ink` text. It's
  hidden at 0, so "0" never claims anything.
- **Departments ▾**: the five department links move into one disclosure (`<details>`, no JS).
  On desktop ≥ 1100 px they may stay inline after a hairline. Their order follows
  stages.yaml (analysis → screenplay → trailer → refs → episode).
- **⌘K / Ctrl+K and `/`** open the palette (a `<dialog>` and about 60 lines of vendored JS, no
  library). It runs a fuzzy match over `/api/index.json`, which lists books by title and slug,
  units as `wotw ep17 The Thunder Child`, gates as `ep12 PLAN ⚑7`, takes as `ep12 T05`, and
  pages. **The palette navigates only in v1.** Orders (hold, redo) stay on their pages behind
  their forms, because a mistyped palette command that spends GPU hours is the wrong failure.
- **Go-to chords** (Linear): `g n` Now, `g i` Inbox, `g q` Queue, `g t` Timeline, `g b` Books,
  `g r` the running unit. On the unit page: `[` / `]` previous/next unit in the book, `j/k`
  next/previous fault, `t` to the takes. `?` lists them. They're ignored while an input has focus.

## 5. Needs you: one definition, used by the inbox, the badge and the Now page

An item needs the owner when any of these is true:
1. `v_attention` (failed, deferred, escalated, stale): today's rule, kept.
2. **flagged and not acknowledged**: `shown == "flagged"` with no owner order or audit note
   newer than the verdict's mtime. This is the gap that shows 0 today. ep12–ep16 would show
   here as `⚑4 ep12 MASTER ⚑3 · published 8d ago`.
3. an open **hold** older than 24 h (a forgotten hold blocks the studio silently).
4. a **refused** order receipt (`/act/*` 409/405) in the last 24 h.
5. the running unit is **looping**: health band `loop` (same step refused ≥ 3 runs).

Each inbox row looks like this: `glyph · book short · unit · what · why (detail, 1 line) · age ·
[open ›]`. The row's link is a **deep link to the fault** (`…/ep12/gate/MASTER`), not to the
top of the unit. Sorting puts kind 5, then 1, then 2, then 3, then 4 first, and oldest first
within a kind. "Acknowledge" is an order (`kind=ack`, note optional), so it lands in the ledger
like every other owner act. The acknowledge order is a dependency for item 2. If it's deferred,
item 2 falls back to "flagged and published", and the owner clears it through redo or note.

## 6. URL design

- **Book slugs.** `/b/war-of-the-worlds`, derived once from the book title (lowercase ASCII,
  hyphens, leading "The" kept so it stays unambiguous) and stored on the books row.
  The 14-digit codex stays accepted everywhere and 301s to the slug. Like Linear's
  `ENG-123/slug`, the id resolves and the slug reads. Ambiguous short slugs get the
  codex appended. The H1 never shows the codex. It moves to a `--ink-3` mono meta line.
- **Unit canonical** `/b/{book}/{stage}/{unit}`, so the breadcrumb and the URL read the same:
  `Studio › The War of the Worlds ▾ › episode ▾ › ep17 ▾`. The old
  `/d/{stage}/{codex}/{unit}` 301s, keeping the fragment, so links already pasted in Telegram
  keep working. Partials and JSON keep their current paths. They're internal, and
  renaming them is churn with no reader.
- **Deep-link sub-paths** (`/take/T05`, `/shot/07`, `/gate/PLAN`, `/run/{run_id}`) render the
  same unit page with a `focus` context. The server marks the target (`aria-current`, open
  `<details>`, `<dialog open>` for a take), so the link works without JS, on the phone, and
  when pasted into Telegram from `notify_bench.py`. The fragment forms (`#take-T05`) keep working
  for in-page jumps. A small script turns a hash into the same focus.
- **Filters are query params** that a URL can carry: `/d/episode?book=war-of-the-worlds&state=flagged`
  (today `?book=<codex>`), `/queue?stage=episode`, `/timeline?range=7d`. Every filter state is
  a link, so the inbox, palette and Telegram can point at a filtered view.
- **Artefacts** keep `/lib/{codex}/{path}` and `/thumb/...` (immutable, cache-forever). They're
  files, not pages, and the codex form is the safest key for the path guard.

## 7. Cross-links: every noun is a link, in both directions

| from | to | where it appears |
|---|---|---|
| unit | book | breadcrumb segment and `[` `]` siblings; the book page's season grid highlights it |
| unit | department | breadcrumb `episode ▾` lists the 5 departments' units *for this book* (`/b/wotw/refs/main`) |
| unit → upstream | the unit it waits on | "waiting on refs/04" (dept table) becomes a link to the upstream unit at that step: `/b/{book}/refs/main#step-04` |
| fault chip | shot | every `00 01 05` chip under a verdict links `…/shot/05`; the shot focus shows panel, take, and all faults on that shot across gates |
| take tile | gate | a flagged tile's corner `⚑` links the gate row that flagged it |
| health chip | run | `06:26 08 error` links `…/run/{run_id}`, with its log tail |
| book | department | matrix row headers link `/d/{stage}?book=` |
| department | book | each book block's title links `/b/{book}` |
| timeline bar | unit/run | each bar links `…/run/{run_id}` |
| org chart | board | the wrapped `/org` gets the top bar; each department node links `/d/{stage}` (the TEAMS table already names them) |
| order row | its target | `episode › ep14 · step 09` links `…/ep14/run/…` or the step |

## 8. First-viewport spec, per page (1440×900 desktop; what must be visible without scrolling)

**`/` Now.** It answers "is the GPU earning, does anything need me, what's next".
1. **Lane card** (full width, ~220 px). This is the unit page's live card at half height: poster
   (latest panel or take thumb `/thumb/…/320/`), `ep17 · The Thunder Child · The War of the Worlds`,
   big `02 PLAN`, `done around 21:40`, range, the 12-step rail, last words (1 line). Idle state:
   `GPU idle since 01:55 · next: episode ep01 [open]`.
2. **Needs you** (left 2/3): the top 5 inbox rows from §5 and `all 7 ›`. At 0 it reads `Nothing
   needs you · last checked 10 s ago`, honest because §5 includes flagged.
3. **Next on the GPU** (right 1/3): the next 3 queue rows and `queue ›`.
4. **Last 24 h** (one line): a mini timeline strip, 24 h wide, the bars coloured by outcome
   with glyphs on hover/focus, linking to `/timeline`.
Below the fold: department cards (kept, but each shows counts plus its 3 most recently moved
units, not 6 alphabetical books), recent orders.

**`/inbox` Needs you.** The first viewport is the list itself, up to 12 rows at 40 px, grouped
under kind headings (`Looping`, `Failed`, `Flagged, not acknowledged`, `Holds > 24 h`,
`Refused orders`). Each row has its open › deep link and an `ack` form. `j/k` moves, `Enter` opens.

**`/queue` Queue.** It opens with a studio-hold control (kept), then the GPU now line, then the
**next 10 rows**, each showing stage, book, unit, step, waits-on, and the `↑` bump. Below that
are **collapsed groups** (`refs · 29 books queued, none started ›`, `screenplay · 30 ›`,
`trailer · 30 ›`). Per-row hold forms move behind a row `⋯` menu, so the page carries 0
text inputs per row instead of 92. Holds come next.

**`/timeline` Timeline.** The axis covers the last 24 h, with "now" at the right edge and a
ruled `--accent` hairline. Lane 1 is the GPU: bars per step-run, labelled `ep17 02` when the
width is ≥ 40 px, and fill encodes outcome (done `--ok`, refused/failed `--accent` with
hatching, killed `--ink-3`), never colour alone, since each bar's end carries the glyph.
Lane 2 is the CPU steps. Above the lanes sit the totals `GPU busy 19h12 / 24h · 43 runs ·
7 refused`. Range pills: `24h 3d 7d`.

**`/books` Books (the shelf).** It's a table with 30 rows: book (title, author in `--ink-3`) and
one cell per department (analysis ✓, screenplay ○, trailer ○, refs ⚑1, episode as a
mini-bar `13/17` plus `▲16 published`), then GPU h and last moved. It sorts by last moved, so
the two live books are on top. The first viewport is ~18 rows, so every book with activity is
visible.

**`/b/{book}` Book (the season).** Header: title, `19 units · 16 published · 73.5 h GPU`,
hold-book. The **first viewport is the season grid**: 17 episode poster cards (160×160 square
thumb of the master's middle frame, or the last panel, or a hatched placeholder), each with
`ep12 · Weybridge and Shepperton`, a state pill, gate dots `PLAN LAYOUT PANELS TAKES MASTER
RENDER` as ✓/⚑n/○, and `▲` when published. That's 6 per row at 1180 px, so 2 rows fit and all
17 fit in about 1.4 viewports. This is the ShotGrid/Kitsu project overview and the only place
the owner sees *what the season looks like*. Below it: the department matrix (today's page,
kept), then cast & refs (sheets from the refs unit).

**`/d/{stage}` Department.** Filter pills (kept), then **active books first**: books with a
running, flagged, failed or started unit get full tables. Books whose units are all queued or
all done collapse to one line each under `27 books: all queued ›`. `/d/refs` drops from
4521 px to under 900 px.

**`/b/{book}/{stage}/{unit}` Unit.** Running: the live card (kept, it's the spec'd hero), then
the header and step strip. Finished: header, step strip, **the master player plus gate
summary side by side**. The verdict counts (`MASTER ⚑3`) sit next to the picture they judge,
which is the Frame.io review stance. A **fault rail** goes in the header's right column:
`⚑ 38 faults · next ›`, which `j` walks. Takes, panels, health and raw stay below, unchanged in
order. The 900 px fold should land just below the step strip plus the first gate line.

**`/org` Org chart.** The board's top bar (thin variant), then the page unchanged. Department
nodes link to `/d/{stage}`.

**`/search`** shows results grouped Books / Units / Gates / Takes / Pages, 8 per group. It's
the palette's no-JS fallback and the phone's search.

## 9. The phone (≥ 400 px)

The phone use case is "glance from the couch": is it running, did it break, show me the take.
- **Top bar collapses to one 48 px line**: `Visurena ▾ · ● 02 plan ~21:40 · ◐`. The brand
  is a `<details>` that drops the full nav list. The GPU pill stays, since it's the answer.
- **A bottom tab bar** (fixed, 56 px, `env(safe-area-inset-bottom)`) with
  `Now · Inbox ⑤ · Books · Search`. These are the four phone destinations. Queue and Timeline
  are desk pages and stay reachable via the brand menu.
- **Now on phone**: the lane card (poster 96 px left, text right), then the needs-you rows as
  full-width 56 px tap rows, then next. No department cards.
- **Unit on phone**: the live card compact (the clock and the ETA on one line, the 12-step rail
  as 12 equal ticks without labels, labels on tap), then the **fault rail as a sticky chip**
  `⚑38 ›`, then takes in a 4-column grid of 88 px tiles. Gates, health and raw become collapsed
  `<details>`. Tap targets are ≥ 44 px. The fault chips `00 01 02 …` grow from 22 px to 32 px
  on `pointer:coarse`.
- **Book on phone**: the season grid in 3 columns of 120 px posters. The matrix scrolls
  horizontally inside its own box (sticky first column), and the page never does.
- Telegram is the real phone entry point: every link `notify_bench.py` sends should be a
  canonical deep link (`…/ep12/gate/MASTER`), which works without JS.

## 10. What this costs to build (for the planner, not a commitment)

All server-rendered Jinja + htmx. No new dependency. New view functions, each 10–20 lines
and test-first: `needs_you()` (the §5 rules, one function per rule), `timeline(range)`,
`shelf()`, `season(book)`, `slug_for(codex)`/`codex_for(slug)`, `index_json()`, and a
`focus` resolver for the four sub-paths. One schema touch: `books.slug` (or a computed map
if the books table is not to change). One palette script (~60 lines) next to `htmx.min.js`.
Redirect routes for the legacy URLs. `architecture/index.html` gains board links on its
department nodes. That's an architecture-page change, so it lands in the same commit per CLAUDE.md.

## Top 10 recommendations for this board

1. **Count flagged-not-acknowledged in Needs you.** It shows 0 today while 5 published episodes
   carry 4–37 faults. (`/`, `/inbox`, nav badge)
2. **Put a GPU pill (`● ep17 02 plan · ~21:40`) in the top bar of every page**, linking to the
   running unit. (all pages)
3. **Make `/` a "Now" page**: lane card, needs-you top 5, next 3, 24 h strip. Retire the floor as
   a landing candidate. (`/`)
4. **Make fault chips and health chips deep links** (`…/shot/05`, `…/gate/PLAN`, `…/run/{id}`,
   `…/take/T05` opening the lightbox server-side). The anchors already exist and nothing
   uses them. (unit)
5. **Open the book page on a season grid of episode posters with gate dots.** Keep the matrix
   below. (`/b/{book}`)
6. **Add `/books`** (the shelf grid). It fixes the `/b` 404 behind the "Books" breadcrumb. (`/books`)
7. **Use book-first canonical URLs with slugs** (`/b/war-of-the-worlds/episode/ep17`). The codex
   form 301s, and the H1 never shows the 14-digit id. (unit, book)
8. **Collapse idle books on department and queue pages** (`27 books: all queued ›`). Move
   per-row hold forms behind `⋯`. `/d/refs` goes from 4521 px to under 900 px and `/queue`
   from 92 inputs to 0. (`/d/{stage}`, `/queue`)
9. **Add ⌘K / `/` palette (navigate-only) plus `g`-chords and `j/k` fault walking**, from a
   ~20 KB `/api/index.json`. `/search` is the no-JS and phone fallback. (all pages)
10. **Phone: one-line top bar plus bottom tabs `Now · Inbox · Books · Search`**, compact live
   card, sticky fault chip. Wrap `/org` in the board's top bar so it stops being a dead end.
   (phone, `/org`)

## 3 disagreements I expect with other researchers

1. **Top bar vs sidebar.** Whoever studies ShotGrid/Linear/Dagster visuals will likely propose a
   left sidebar. I hold that 6 destinations, 1 user and a 1180 px editorial column don't pay
   for 220 px of permanent chrome. The switcher breadcrumb plus ⌘K does the sidebar's job.
2. **Book-first URLs and breadcrumbs.** The 2026-09-25 spec chose `/d/{stage}/…`, and the
   org-chart framing (departments as the company) argues for department-first. I argue that
   the owner's object is "ep17 of The War of the Worlds" and the department is a filter. Every
   film tool studied agrees. The old URLs survive as redirects.
3. **The landing page.** An ops/monitor researcher may want the call sheet (queue) or a Grafana
   wall as `/`. A film-tools researcher may want the season grid. I put the *one GPU lane +
   needs-you* first, because the BRIEF's four questions are about now, not about the shelf.
   The season grid lives one click away on the book page.
