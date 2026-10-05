# The premium board — build plan (task level)

**Status: PROPOSED 2026-10-04 — waits for the owner's review of `SPEC.md` and `mockups/`.**
Nothing is built. When the owner rules, this file moves to `architecture/plan/` as the tracker, the
decision gets its dated file in `architecture/decisions/` and its line in `docs/DECISIONS.md`, and
the board row of `architecture/index.html` (Current tab) moves with the shell, home and unit commits.

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
| P0.3 | `--ink-3` → #6f6759 / #9a9282 in `architecture/index.html` and the board (B3); the contrast test. | `test_tokens_meet_contrast.py` (WCAG 4.5:1 for every text token on paper/paper-2, both themes) | ~80 |
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
