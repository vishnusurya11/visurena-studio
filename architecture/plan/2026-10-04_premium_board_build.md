# The premium board — build plan (task level)

**Status: IN PROGRESS — owner ruled "looks good go" 2026-10-04.** Decision:
`architecture/decisions/2026-10-04_premium_board.md`. Research, ruling and mockups:
`architecture/decisions/research/2026-10-04_board_design/`. Built in waves of sub-agents; the board
row of `architecture/index.html` (Current tab) moves with the shell, home and unit commits.

## Progress

- [x] P0.1 tiles through /thumb · - [x] P0.2 inbox + acknowledge · - [x] P0.3 --ink-3 + contrast test
- [ ] P0.4 one colour per state · - [ ] P0.5 live notify bugs (with the progress session) · - [x] P0.6 /books, /org back link
- [x] F1 tests pin answers · - [x] F2 CSS out · - [x] F3 fonts · - [x] F4 tokens · - [x] F5 icons · - [ ] F6 macros · - [x] F7 morph · - [x] F8 pulse · - [ ] F9 harness
- [x] G1 shell · - [x] G2 Now · - [x] G3 Queue · - [x] G4 Department · - [x] G5 Unit running · - [x] G6 Unit finished · - [x] G7 Book + Books · - [x] G8 notifications

## Log

- 2026-10-04 — ten reports, the ruling, seven mockups (`3e75901`); owner: "looks good go".
- 2026-10-04 — P0.2: Needs you counts flagged-not-acknowledged done units; `acknowledge` joins `orders.kind` (fresh DDL; an older table keeps its CHECK and `work_orders._insert_order` waives it for that one INSERT -- no rebuild beside a runner); `POST /act/acknowledge`; nav badge `/partials/needs-you-count`. Live: WotW refs/main + ep12–ep16 show.

- 2026-10-04 — Viewer ported (`9641cd3`): one dialog, four renderers, provenance panel; read-only `/json`, `/log`, `/files`, `/viewer/…json`.
- 2026-10-04 — P0.3, F1–F5, G1: Studio black default + Graphite light, CSS out to `static/css/{tokens,components,pages}.css`, self-hosted Plex/Barlow, Lucide sprite, the sidebar shell on every page (Home first, Inbox, Queue, Books, Architecture, departments, pinned, live GPU card, ⌘K); new `/queue`, `/books`, `/architecture` (the org chart inside the board). 1007 board tests green.

- 2026-10-05 — the UX panel's six packages (`PANEL_RULING.md`, all built in parallel, file-disjoint): PKG-1 pulse server (`/api/pulse.json` fingerprints, 204 on an unchanged `?v=`, `/inbox`, async thumbs ≤ 2 at once + 1024 width, `/lib` ETag/304, the error page in the shell, ages, queue ETA "if clean"); PKG-2 shell client (`pulse.js` one 2 s loop, idiomorph morph, heartbeat chip, live title + favicon, announce, held bar, ⌘K over every unit, one key registry, crumbs from Home, the Viewer loaded on every page); PKG-3 style system (motion/type/radius tokens, one looping animation, `.chg` wash, `[data-stale]`, old page overrides removed); PKG-4 lists and Home (pulse + morph everywhere, Needs-you cards, server-SVG GPU chart `viz.py`, department grid by state, `/inbox` page); PKG-5 unit and media (`media.js` one player, every picture/take/grid/file/log opens the Viewer, truthful posters, sibling nav, new-master badge); PKG-6 orders (no double submit, live receipts pending → taken, honest dead letters, Acknowledge with 5 s Undo, verb labels). Lead's ruling: department rows keep their order controls, so the department grid's partial budget is 12 KB (others 6 KB). Open for the owner: a redo on a finished unit has no taker (needs `work_orders`/`tick`, frozen while a drive runs).

- 2026-10-06 — refresh fix (owner: "it is not refreshing"; five agents + referee): the pulse hears the clock (lapsed-lease count in every fp, same-second writes concatenated) `ae843bf`; a dead run lands in Needs you as stale; pulse.js's loop survives its own patch errors `53c6b8d`; unit keys derived + first-pulse 204s `938344d`; every polled section's key cross-checked (caught the never-refreshing Books page), the Today feed hears events, page-as-partial routes answer 204 `25d0304`. Referee: all sections morph +1.2–2 s after a change, no reload.

- 2026-10-07 — accuracy fix (owner: "this is not accurate", ep23 hidden while rendering): liveness is three signals, not a lease stamp — a visible process naming the unit, a book-wide carrier (drive/autopilot) within a 6 h lease window, or the unit's folder still moving within 45 min (`views.carried`, spawn-free; the ctypes walk cannot see another session's processes and the no-spawn guard rightly refused a CIM fallback). The live card's vital reads the same truth (`vitals.files_alive`). ep18 stays stale, ep19 failed, ep23 running. `032afe7` + `d66f0df`, 1662 green.

## Rules for every commit

- Test first; a function does one thing in 10–20 lines; every macro has a test; no test touches the
  GPU, a model or a paid API; the web process stays read-only (writes only `orders`) and never
  decodes video.
- Phase 0 is mechanical: the screenshot diff before/after is ≈ 0, and that is its proof.
- From phase 2 on, a page commit lands only after the owner has looked at its mockup.
- **Collision rule:** the progress-tracker session owns `_live_*.html`, `progress.js` and the
  live card's behaviour. This plan re-tones the live card and moves its CSS; it does not rewrite
  its logic. Before each commit: `git log -5 -- studio/command_center` and rebase on what landed.
- Budgets (checked by the local harness): unit media < 2 MB, ≤ 1,500 DOM nodes on department and
  unit, JS ≤ 80 KB/page, pulse ≤ 1 KB, every route < 50 ms.

## Phase 0 — fix what is broken, change nothing visible (≈ 1 day)

| # | commit | tests first | size |
|---|---|---|---|
| P0.1 | Every panel, take poster and contact tile through `/thumb/…/320/` (B1). ep12 unit page 36.4 MB → ≈ 1.2 MB; blank take tiles fixed. | `test_no_page_loads_a_full_size_picture_for_a_tile.py` (grep templates + render ep12 fixture: no `/lib/…png` in `<img src>`) | ~40 |
| P0.2 | Inbox rule: Needs you counts flagged-not-acknowledged; `acknowledge` joins `orders.kind`; `/act/acknowledge` (B2). | `test_a_flagged_unit_needs_you_until_acknowledged.py`, `test_acknowledge_is_one_orders_row.py` | ~120 |
| P0.3 | **Dark "Studio" palette by default** (owner) replaces the beige on the board; Graphite as the optional light theme; `--ink-3` → #8e9199 dark / #5f6672 light in `architecture/index.html` and the board (B3); the contrast test. | `test_tokens_meet_contrast.py` (WCAG 4.5:1 for every text token on paper/paper-2, both themes) | ~80 |
| P0.4 | One colour per state: `views.COLOURS`, `.live[data-vital]`, `.lv-rail` read one map (B4). | `test_a_state_has_one_colour_everywhere.py` | ~60 |
| P0.5 | Live notify bugs (B6): poll continues hidden at 10 s, `Notification` in try/catch, 2-pulse hysteresis, "board offline" state. **Coordinated with the progress session** (its files). | `test_progress_js_keeps_polling_when_hidden.py` (static JS read), contract tests on the JSON | ~60 |
| P0.6 | `/books` exists (B7); `/org` gets a back link. | `test_every_crumb_resolves.py` | ~60 |

## Phase 1 — the foundation (≈ 2 days; screenshot diff ≈ 0)

| # | commit | tests first |
|---|---|---|
| F1 | Tests pin answers, not markup: ~25 class/CSS-text assertions → words, roles, `data-testid`. | the converted tests themselves |
| F2 | CSS out of `base.html` into cached `static/css/{tokens,components,pages}.css` with `@layer`, byte-for-byte; `?v=<mtime>`. Baseline screenshots taken. | `test_the_board_css_is_served_and_cached.py` |
| F3 | Self-hosted fonts (Barlow Condensed, Plex Sans, Plex Mono; OFL) under `static/fonts/`. | `test_no_page_loads_a_remote_font.py` |
| F4 | Token system per SPEC: state tokens `--st-*` (06 table), type roles, space/radius/elevation, `--viz-1..4`, `--stage*`; the core byte-equal test kept for the shared core, a board-only state block, `test_every_var_is_defined`. | three token tests |
| F5 | `icons.svg` (Lucide subset, ISC) + `icon()` macro; glyphs become an icon-name map; Unicode kept for plain text (B9). | `test_every_state_has_an_icon_and_a_word.py` |
| F6 | `components/` macros: `mark`, `pill`, `step_bar` (one, with patterns), `gate_cell`, `frame`, `tile`, `sparkline`, `run_matrix` shell; pages switched with zero visual change except the patterns (B5). | one test per macro |
| F7 | Vendor idiomorph; morph swaps on `#rows`, `#floor`, `#attention`, `#head`, `#orders`; inline JS → `static/board.js` (B8). | `test_polled_regions_morph.py` |
| F8 | `/api/pulse.json` + `pulse.js`: fingerprints, events since cursor, ≤ 1 KB, 2 s / 10 s hidden; partials answer 204 when unchanged; title + favicon owner. | `test_pulse_is_small_and_changes_only_when_the_ledger_does.py`, `test_an_unchanged_partial_is_204.py` |
| F9 | Local harness `@pytest.mark.local`: browse.exe screenshots at 1440/400 × light/dark, axe, budgets. | the harness |

## Phase 2 — the pages, on the components (≈ 4–5 days; each after its mockup is approved)

| # | commit | mockup |
|---|---|---|
| G1 | **Shell**: top bar, GPU pill on every page, inbox badge, ⌘K palette (navigate + this page's actions via confirm), keyboard map + `?` sheet, phone bottom tabs. Architecture page Current tab: the board's shell. | `index.html` (shell) |
| G2 | **Now** (`/`): GPU lane card, Needs you, Up next, Where the GPU went · 7 days, shipped with flags, since-you-looked strip. | `index.html` |
| G3 | **Queue** (`/queue`, `/floor` redirects): GPU lane timeline with now line, ghost queued bars + queue ETA, idle strip; grouped queue, actions behind ⋯. | `queue.html` |
| G4 | **Department**: book → status groups, done/blocked collapsed, shared reason on the header, faces where a poster exists, gates cell, unit titles, count filters, gate × unit fault matrix. | `department.html` |
| G5 | **Unit — running**: one header, finish-time hero with p50/p90 range, properties sidebar, run matrix + loop brackets, run waterfall, verdict threads, shot strip empty states, activity (log grouped by step). Live card re-toned with the progress session. | `unit-running.html` |
| G6 | **Unit — finished**: screening room (player on stage, version stack deduped by hash, compare, shots/faults/lines lanes, judges' stamps), shot strip, shot view lightbox with redo. | `unit-finished.html` |
| G7 | **Book + Books**: season wall, season matrix, refs/cast strip; `/books` shelf. | `book.html`, `books.html` |
| G8 | Notifications table (09 §6) + "still" toggle + one view transition. | — |

## Phase 3 — URLs and the pipeline asks (separate decisions)

| # | item | note |
|---|---|---|
| U1 | Book-first canonical URLs with slugs, `/d/…` 301s; deep links `/…/shot/NN`, `/take/TNN`, `/gate/G`, `/run/<id>` rendered server-side. | board only |
| A1 | `poster.jpg` per unit; take sprites; master 1 s sprite + VTT; `cut/master_iterN.cut.json`; `timing.jsonl` carries `step` + UTC; `work_steps.seconds` written; learnings keep `faults` as a list. | **architecture changes** — pipeline steps, each with a decision line and the Future tab of `architecture/index.html` |

## Sizes

Phase 0 ≈ 420 lines, 6 commits. Phase 1 ≈ 1,600 lines, 9 commits. Phase 2 ≈ 3,000 lines,
8 commits. ~23 commits, ~60 new tests, ~8–9 working days with sub-agents in waves (phase 0 can
start the moment the owner says so; it changes nothing he would see except fixes).

## Publishable (EB-1)

`htmx-pulse` (F8), `<review-player>` (G6), `css-token-contrast` (P0.3/F4), the tone-based Jinja
component set + screenshot/axe harness (F6/F9) — each built so it can be lifted into its own repo.
- 2026-10-04 — owner: the beige is retired ("the bg is shit colour"); four neutral palettes mocked live; owner picked **Graphite** (#f4f5f7). P0.3 carries it.
- 2026-10-04 — owner, after picking Graphite: "need dark colour". Default palette = **Studio dark** (#0f1012); Graphite is the light option.
