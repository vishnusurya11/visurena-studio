# 10 — Feasibility & engineering audit of the board as it stands

Researcher 10 · 2026-10-04 · read-only audit. Measured on the live board (HEAD `a6133af`) with curl,
the gstack `browse.exe`, and `TestClient` + `sqlite3.set_trace_callback` on the real database.

## 1. What is there today

| Layer | Files | Size |
|---|---|---|
| Routes | `app.py` (375 lines): 6 pages, 9 partials, 4 JSON twins, `/lib`, `/thumb`, 7 `/act/*` POSTs | — |
| View models | `views.py` 506, `unit_view.py` 410, `unit_parse.py` 523, `progress_view.py` 360, `legacy_progress.py` 310, `vitals.py`, `procs.py`, `thumbs.py` | pure functions, dicts out |
| Contract | `models.py` (pydantic, `extra="ignore"`) for every `/api/*.json` | — |
| Templates | 25 files; `base.html` **462 lines / 35 KB, of which ~370 lines are one inline `<style>`**; `unit.html` 217 lines with 3 local macros + 1 inline `<script>` (lightbox, filter, hover-play, redo prefill) | — |
| Macros | `_macros.html` holds only the **action** forms (`btn`, `order`, `hold`, `lift`) | 18 lines |
| JS | `static/htmx.min.js` **2.0.4** (50.9 KB), `static/progress.js` (10.4 KB, the live card), inline theme toggle + `/act/` 4xx swap hook in `base.html`, inline lightbox in `unit.html` | ~62 KB + inline |

The view layer is the healthy part: every page is a projection of dicts that tests already pin
(`views.department`, `unit_view.unit`, `progress_view.progress`). **A redesign is a template + CSS
job; almost no Python has to move.** That is the single most important feasibility fact.

### What the templates repeat (the component library that already exists, unnamed)

The same five visual ideas are hand-written in many places, each with its own CSS class family:

| Idea | Where it is written today (class family) | Count |
|---|---|---|
| **State mark** (glyph + colour) | `.st.X` in `_floor`, `_attention`, `_lanes`, `_today`, `book`, `_unit_head`, `floor`, legend, master QC | 9 templates |
| **State pill** | `.pill.X` (`_rows`, `_unit_head`), `.tpill.X` (dept tally, lightbox filter), `.chip.X` (unused by any template now — dead CSS), `.rung` (live ladder), `.gchip` (gates) | 5 families |
| **Step bar** | `.bar i.X` (lanes), `.minibar i.X` (book group), `.sbar i.X` (dept row), `.ubar .seg.X i` (unit head), `.lv-rail .seg.st-X i` (live card), `.passes .pass.X` (health) | **6 implementations of one idea** |
| **Gate dot** | `.dot.X` in `_rows` + gate chips, `.lv-gate` rungs | 2 |
| **Tile** | `.tile` (unit panels/takes, 120 px), `.lt` (live sheet, 66 px), `.slot` (empty take), `.thumbs img` (unused) | 3 live + 1 dead |
| **Panel/band** | `.strip`, `.band`, `.lane`, `.live`, `.rawpart`, `.pblock` | 6 |

Colour → token mapping is restated in **13 selector families** (`.st`, `.chip`, `.pill`, `.tpill`,
`.dot`, `.bar i`, `.minibar i`, `.sbar i`, `.ubar .seg`, `.pass`, `.badge`, `.lv-rail .st-*`,
`.lt.st-*`). And there are **two state vocabularies**: colour words (`red|blue|green|amber|purple|black|grey`
from `views.COLOURS`) on the old bands, and run words (`st-done|st-fail|st-skip|st-running|st-refused`) on
the live card. Dead/overridden CSS already exists: `.st.blue`, `.sbar i.blue`, `.ubar .seg.blue i`,
`.pill.blue` get `animation:pulse` and then line 310 sets them all to `animation:none`.

## 2. Measurements (live board, warm, localhost)

| Page | HTML bytes | gzip | TTFB | SQL queries | DOM nodes | forms | media on load |
|---|---|---|---|---|---|---|---|
| `/` home | 47.7 KB | 10.1 KB | 6 ms | 11 | 417 | 0 | 0 |
| `/floor` | **139.8 KB** (163 KB writable) | 13.2 KB | 6 ms | 6 | **2,681** | **185** | 0 |
| `/d/episode` | **114.4 KB** | 11.9 KB | 6–20 ms | 4 | 1,804 | 63 | 0 |
| `/d/episode/…/ep17` (running, live card) | 93.7 KB | 17.5 KB | 14–30 ms | 8 | 1,432 | 4 | 22 thumbs |
| `/d/episode/…/ep12` (finished) | **176.4 KB** | 28.5 KB | 30 ms | 8 | — | 4 | **36.4 MB, load 954 ms** |
| `/b/20260827135508` | 45.2 KB | 9.4 KB | 4 ms | **23** | 360 | 1 | 0 |
| `/org` | 149 KB (static file) | — | 1.5 ms | 0 | — | — | — |
| `/api/progress/…/ep17.json` | 2.1 KB | — | 4 ms | 2 | — | — | — |
| `/partials/d/episode` (10 s poll) | 77.5–85 KB | — | 6 ms | 4 | — | — | — |

Findings, each with its cause:

1. **The server is not the problem.** Every page answers in ≤ 31 ms and ≤ 23 queries. No N+1 worth
   fixing (the book page's 23 are one per stage×lookup, 4 ms total). A redesign can add data
   without a performance project.
2. **~34 KB of every page is the inline `<style>`**, re-sent and re-parsed on every navigation
   (home is 47.7 KB of which ~34 KB is CSS). Served as a static file it is fetched once.
3. **The finished unit page pulls 36 MB.** `unit.html`'s `tiles_grid` sets `poster=` on 24 take
   `<video>`s to the full-size storyboard PNG (`/lib/…/storyboard/shot_NN.png`, 1.5 MB each) and posters
   are not lazy; the 24 panel `<img>` are lazy but also full PNGs. The `/thumb/{codex}/{160|320}/…`
   route (WebP, in-process LRU, `immutable`) already exists and only the live card uses it.
   Switching both to `/thumb/…/320/` is ≈ 48 × 25 KB ≈ 1.2 MB. **Biggest single win on the board.**
4. **`/floor` is 2,681 DOM nodes because every queued row carries two inline forms** (`bump` + `hold`
   with a text input) — 185 forms. `/d/episode` carries a `<details>` menu with 2 forms per row and
   **683 `title=` attributes**: the step bar's per-segment meaning lives only in tooltips, which a
   phone and a screen reader never see.
5. **The department partial re-sends 77–85 KB every 10 s** (`hx-swap="innerHTML"` of the whole table),
   which also resets any open `<details>` menu and scroll-anchoring inside it.
6. **Contrast:** `--ink-3` (#7d7566) on `--paper` is **4.11:1** and on `--paper-2` **3.77:1** in light —
   below AA 4.5 for the 11–12.5 px text it is used for (`.eyebrow`, `th`, `.muted`, legend; 19 uses in
   `base.html`). `--line` text (`.dot` unsigned gate) is 2.75:1. The live card already bans `--ink-3`
   (`test_the_card_never_sets_text_in_ink_3`); the rest of the board does not. Dark theme passes (5.08).
7. **External font dependency:** fonts come from `fonts.googleapis.com` (test-pinned equal to the org
   chart's link). Offline, the board falls back to system fonts, and screenshot tests become
   non-deterministic.
8. Phone (400 px): no horizontal page scroll on any page (tables scroll inside `.tbl-wrap`); `/floor` is
   6,806 px tall at 400 px.

## 3. Restructure into a component library (Jinja macros)

Jinja `import` + `macro` + `call`/`caller()` is the whole mechanism; no new dependency
(https://jinja.palletsprojects.com/en/stable/templates/#macros, #call). Proposed tree:

```
templates/
  base.html                 # <head>, nav, theme, <link> to css, htmx; no <style> body
  components/
    state.html   mark(state, flags=0) · pill(state, label=None, size='md') · tone(state)  # one map
    bar.html     step_bar(steps, cur=None, variant='row'|'head'|'mini'|'lane', label=True)
    gate.html    gate_dot(chip) · gate_chips(gates) · rung(r)
    tile.html    tile(item, kind, size=120, thumb=320, lb=True) · slot(label, reason)
    panel.html   {% call panel('Gates', count=…, id='gates', fold=False) %}…{% endcall %}
    chart.html   sparkline(points) · trend(series) · trace(p)       # server-drawn SVG
    table.html   unit_table(rows, gates) · empty(text)
    actions.html (today's _macros.html, renamed; same forms, same hx-post)
  pages/  home.html floor.html department.html unit.html book.html
  partials/ _floor.html _rows.html … (kept at their current names until the routes move)
```

Rules that make it safe:

- **One state → tone map.** Python already owns it (`views.COLOURS`, `GLYPHS`). Emit one attribute,
  `data-tone="run|ok|warn|fault|owner|next|idle"`, and let CSS read
  `[data-tone=run]{--tone:var(--think);--tone-bg:var(--think-bg)}` once. Every component uses
  `var(--tone)`. This deletes the 13 colour families and unifies the two vocabularies; the glyph stays
  next to the colour so state is never colour-only.
- **A macro takes the view dict as-is** (`r`, `s`, `g`, `t` from the existing views), never a
  re-shaped one, so `models.py` and the JSON twins do not move.
- **Keep the hooks other code and tests read**: `id="live"`, `id="head"`, `id="orders"`, `id="rows"`,
  `data-k=*`, `data-clock=*`, `.seg[data-id]`, `.lt[data-id]` + `st-*`, `.lv-rail`, `data-lb`, `.lb-redo`,
  `data-step/artefact/note`, the hidden section words (`ON THE FLOOR`, `NEEDS YOU`, `STEPS`, `VERDICTS`,
  `TIMING`), `role="progressbar"` + `aria-valuetext`. `progress.js` writes markup by string
  (`'<span class="of">/'`, `'done around <b>'`, `.lv-why`) — that is a second copy of `_live_hero.html`
  that must change in the same commit as the template.
- **Macro unit tests** render a macro alone with `templates.env.from_string('{% import … %}{{ c.pill("running") }}')`
  and assert the glyph, the word, `data-tone`, and `aria-label` — a test per component, as the repo
  rule demands (one function, one test).

## 4. CSS architecture

Today: one inline `<style>` in `base.html`, the token block byte-equal to `architecture/index.html`
(enforced), a second `:root` block of motion tokens (enforced to sit after `*{box-sizing`), live-card
CSS between `/* live card` … `/* /live card */` (enforced by slice in `test_progress_card_page.py`).

Proposal — three static files, cascade layers, cache-busted by mtime:

```
static/css/tokens.css      @layer tokens  — the org chart's :root + both dark blocks (byte copy),
                                             motion tokens, + board-only additions (--tone map, spacing, radii)
static/css/components.css  @layer components — pill, bar, dot, tile, panel, table, live card
static/css/pages.css       @layer pages   — page grids only (home grid, unit bands, floor)
```

- `@layer tokens, base, components, pages;` declared first in `base.html`
  (https://developer.mozilla.org/en-US/docs/Web/CSS/@layer) so a page rule can never be out-ranked by
  source order — today's `.pill.blue{animation:none}` override bug is a source-order bug.
- Serve with `?v={{ mtime }}` and `Cache-Control: public,max-age=31536000,immutable` (the `/thumb`
  route already does exactly this); Starlette's `StaticFiles` gives ETag/Last-Modified for free.
- **Tests that must move with it:** `test_the_board_copies_the_org_charts_tokens.py` reads `BASE`;
  `test_progress_card_page.py` reads `BASE` four ways (live slice, `:root{--ease-out` position, the
  reduced-motion line, contrast tokens). Point both at a tiny helper `board_css()` that concatenates the
  served files, in the extraction commit. The byte-equal token rule survives unchanged (tokens.css
  contains the block).
- **Contrast fix without breaking the byte-copy rule:** add a board-only `--ink-3` override in
  `tokens.css` *after* the copied block (light ≥ #6f6759 ≈ 4.9:1 on paper) — or, better, change the org
  chart's token too in the same commit (CLAUDE.md: the design language flows org chart → board). Then
  extend the live card's 4.5:1 contrast test to every text pair in `components.css`.
- **Fonts:** vendor Barlow Condensed + IBM Plex Sans/Mono woff2 (OFL) into `static/fonts/` with a local
  `@font-face`; relax the font test from "same `<link>`" to "same families". Needed for deterministic
  screenshots and for working offline. (Disagreement risk — see §11.)

## 5. JS budget and where to vendor from

| Piece | Status | Size (min) | Source to vendor from |
|---|---|---|---|
| htmx 2.0.4 | in use | 50.9 KB | already vendored; bump only deliberately (https://htmx.org) |
| **idiomorph** (morph swaps) | add | small (measure at vendoring) | `cdn.jsdelivr.net/npm/idiomorph@<pin>/dist/idiomorph-ext.min.js`, https://github.com/bigskysoftware/idiomorph |
| board.js (theme, lightbox, hover-play, filters, act-swap hook) | extract from inline | ~4 KB | ours |
| progress.js | in use | 10.4 KB | ours |
| Chart library | **don't add** | 0 | charts are server-drawn SVG macros (sparkline/trend/trace already work this way via `trace_points`) |
| Video helper | **don't add** | 0 | native `<video preload=none>` + `/thumb` posters + `<dialog>`; a sprite scrubber is a later progress-tracker item |
| axe-core | tests only, never served | ~550 KB | `cdn.jsdelivr.net/npm/axe-core@<pin>/axe.min.js`, https://github.com/dequelabs/axe-core |

Budget: **≤ 80 KB of JS served per page, uncompressed**, all from `/static`, no CDN at runtime.
Morph is the one addition that pays for itself: `hx-swap="morph"` on `#rows` (dept), `#floor`,
`#attention`, `#head` keeps open `<details>` menus, focus and running CSS animations across the 2–10 s
polls, which is the reason `progress.js` hand-patches today. Only if a chart must be interactive
(zoom a GPU-hours series) is uPlot (~50 KB, https://github.com/leeoniya/uPlot) the smallest credible
choice — not needed for any page in the brief.

## 6. Testing strategy for visual work

Three layers, all free, none touches a paid API:

Baseline at `a6133af`: the full board suite is **247 passed in 10 min 29 s** (6 core files alone: 95 in 5 min 46 s),
too slow to run on every redesign commit; split fast macro tests from the page-level TestClient tests.
1. **Keep the TestClient content tests** (they pin *answers*: "3 of the last 3 runs ended at 09 refused",
   `<option value="08" selected>`, the `/act/` contract). Before the redesign, convert the ones that pin
   *markup* (`class="pass "` count, `class="slot"` count, `'data-k="big">1<span class="of">/3'`, the CSS
   slices) to pin a `data-testid`/role/word instead — one commit, no visual change.
2. **Macro tests** per component (§3) + a **page smoke** per route at both widths that asserts no
   `title=`-only information for state (every state glyph has a visible word or `aria-label`).
3. **Screenshots with the gstack binary**, `@pytest.mark.local` (excluded from the default run):
   `scripts/command_center/shoot_board.py` starts `make_app` on the frozen fixture library
   (`command_center_fixtures.make_library` + `seed`, plus a finished and a running episode) on a free port,
   then drives `C:\Users\vishn\.claude\skills\gstack\browse\dist\browse.exe`:
   `viewport 1440x900` / `400x900` × `js "document.documentElement.dataset.theme='dark'"` × each route →
   `screenshot <path>`; compare against `tests/fixtures/board_shots/*.png` with Pillow `ImageChops`
   (threshold, not byte-equal). Verified today: `goto`, `wait --load`, `js`, `perf`, `viewport`,
   `screenshot` all work against the live board. Determinism needs: (a) local fonts, (b) a frozen
   `now` (the views call `datetime.now()` for "12m ago" — inject a clock or mask `[data-clock]`),
   (c) animations off via an injected `*{animation:none!important}`.
4. **a11y:** `browse eval axe.js` then `js "axe.run().then(r=>JSON.stringify(r.violations))"`, failing on
   any `serious|critical`; plus the existing token-contrast test widened to all components.
   `browse accessibility` dumps the tree for a manual landmarks check (nav, main, one h1 per page).

## 7. Performance budgets (per page, at today's data, localhost)

| Budget | Home | Floor | Dept | Unit (running) | Unit (finished) | Book |
|---|---|---|---|---|---|---|
| TTFB p95 | 30 ms | 30 ms | 30 ms | 50 ms | 50 ms | 30 ms |
| HTML (no CSS) | 25 KB | 40 KB | 50 KB | 60 KB | 80 KB | 30 KB |
| DOM nodes | 600 | 1,200 | 1,500 | 1,500 | 2,000 | 600 |
| Media on load | 0 | 0 | ≤ 300 KB (row thumbs) | ≤ 1 MB | **≤ 2 MB** (now 36 MB) | ≤ 500 KB |
| Poll traffic | ≤ 1 req/s, ≤ 5 KB/s | same | ≤ 0.2 req/s | progress JSON ≤ 6 KB / 2 s (spec) | none once done | none |

CSS ≤ 45 KB total cached; JS ≤ 80 KB. Enforce the byte/DOM/media budgets in the local screenshot run
(`perf` + `performance.getEntriesByType('resource')`) and the HTML-byte budget in TestClient tests
(`test_the_unit_page_answers…` already asserts < 400 KB — tighten it).

## 8. Who else is editing the board — collision map

`git log -20 -- studio/command_center`: ten commits, **six of them today (10-04, 18:01–18:27)**, all from
the progress-tracker build (spec `docs/audit/2026-10-04_progress_tracker_spec.md` §8). Its open items:
W1–W6 pipeline write sites (not board files), commit 7 **ComfyUI bridge** (`comfy_tap.py`, `app.py`
startup, `models.Progress.sampler`), the `/browse` visual pass with `replay_progress.py`, and "later":
posters/3 s loops, the lifeline, a master sprite scrubber — all inside `_live_*.html`, `progress.js`,
the live block of `base.html`, `unit.html`. Their tests pin `base.html` text.

Rules to avoid collisions (one checkout on `master`, no worktrees, per CLAUDE.md):

- **Freeze order:** the redesign does not start until the progress session's commit 7 lands or is
  parked; ask the owner which session owns `base.html` that day.
- **Commit 1 is a pure move** (CSS out of `base.html` byte-for-byte, tests repointed) — small, fast, and
  rebased by nobody. After it, the live card's CSS lives in `components.css` under `/* live card */`
  markers so the progress session keeps a stable slice.
- **Leave `_live_*.html` and `progress.js` to their owner;** the redesign only re-tones them through
  tokens. Touch them only in a commit agreed with that session.
- Each redesign commit touches ≤ 1 page template + its components, runs the whole board suite
  (`tests/test_command_center_* test_the_* test_a_* test_progress_card_* test_unit_parse.py`) and
  re-checks `git log -1 -- studio/command_center` right before committing.

## 9. Risks

| Risk | Why it is real here | Mitigation |
|---|---|---|
| Markup-pinned tests break en masse | ~25 assertions match class names / CSS text | commit 0 converts them to words/roles/testids first |
| `progress.js` duplicates template markup | `innerHTML` strings for hero/finish | morph-swap the partial, or a `<template>` the JS clones |
| Polls clobber state | `innerHTML` swaps of `#rows`, `#head` reset menus, focus | idiomorph; keep the `[!document.activeElement.closest(...)]` guards |
| Org chart drift | tokens are a byte copy; CLAUDE.md says flow is org → board | token changes land in `architecture/index.html` in the same commit + republish |
| Live drive interrupted | the board is read-only; but a restart of `command_center.py` during a run is harmless — **editing step scripts is not** | redesign touches nothing under `scripts/` or `studio/` outside `command_center/` |
| Screenshot flake | Google Fonts, clocks, animations | local fonts, frozen now, animations off |
| Scope creep into the view layer | "premium" pages want new data (ETAs per row, thumbs per row) | new data = a new view function with its own test and a `models.py` field, in its own commit |
| Heavy media on new pages | dept/book "filmstrips" would repeat the 36 MB mistake | every `<img>`/poster through `/thumb`; a test greps templates for `/lib/…png` in `src=`/`poster=` |
| a11y regressions from colour-led design | the brief wants richer colour | glyph+word stay; contrast test covers every pair |

## 10. Commit-by-commit build sequence (whole-board redesign)

Each commit: failing test first, all board tests green. None of these is an architecture change
(no stage, step, runner or owner gate moves), so the org-chart rule applies only where a token edit
touches `architecture/index.html` as the design source.

0. **Tests pin answers, not markup.** Replace class/CSS-text assertions with words/roles/`data-testid`. No template change.
1. **CSS out of `base.html`** into `static/css/{tokens,components,pages}.css`, byte-for-byte, with `@layer`;
   `?v=mtime` + immutable cache; tests read `board_css()`. Visual diff must be zero (first screenshot baseline taken here).
2. **Local fonts** + font test relaxed to families. Baseline screenshots re-taken.
3. **`--tone` map**: `data-tone` on every state element via `components/state.html`; delete the 13 colour families; contrast test widened; `--ink-3` fixed (org chart too).
4. **`components/` macros**: `mark`, `pill`, `gate_dot`, `step_bar` (4 variants), `tile`, `panel`, `sparkline` — each with its macro test; pages switched to them with zero visual change (screenshot diff ≈ 0).
5. **Media through `/thumb`** for every panel/poster (unit page, then any new filmstrip) + the template grep test. ep12 page 36 MB → ~1–2 MB.
6. **Vendor idiomorph**; `hx-swap="morph"` on `#rows`, `#floor`, `#attention`, `#head`, `#orders`; extract inline JS to `static/board.js`.
7. **Shell**: new `base.html` nav/header, page grid, keyboard shortcuts (if the plan adopts them) — one commit.
8. **Home** redesign (the "what is running / stuck / next" answer) on the components.
9. **Floor** redesign — actions collapsed to one per-row menu (185 forms → ≤ 20).
10. **Department** redesign — table rows on `step_bar`/`gate_dot`, tooltips replaced by visible words at ≥ 760 px.
11. **Unit** redesign — bands as `panel`s; live card re-toned only (agreed with the progress session).
12. **Book** redesign — the grid on `mark`, filmstrip on `/thumb`.
13. **`/org` link-in**: the org page keeps its own file; the board shell links to it (it is a static page, not a template).
14. **Screenshot + axe suite** `@pytest.mark.local` and the budget checks; README of the board updated.

15 commits, each ≤ ~400 lines diff; 0–6 are mechanical (screenshot diff ≈ 0 is the proof); 7–12 each
need the owner's eye on the mockup first. **Publishable:** the `--tone` + Jinja component set for htmx
boards plus the browse-driven screenshot/axe harness is a small standalone package.

## Top 10 recommendations for this board

1. Route every panel and poster through `/thumb/…/320/` — unit page (ep12: 36 MB → ~1.2 MB).
2. Move the 34 KB inline `<style>` to cached `static/css/*.css` with `@layer` — all pages.
3. One `data-tone` state map replacing 13 colour class families and two vocabularies — all pages.
4. Build `components/` Jinja macros (mark, pill, step_bar, gate_dot, tile, panel, sparkline) before any visual change — all pages.
5. Convert markup-pinned tests to answer-pinned tests as commit 0 — board test suite.
6. Vendor idiomorph and morph-swap the polled regions so menus, focus and animations survive polls — home, floor, dept, unit.
7. Fix `--ink-3` contrast (4.11:1 light) in tokens and extend the 4.5:1 test to every component — all pages.
8. Collapse per-row inline forms into one action menu per row (185 forms, 2,681 nodes) — floor, dept.
9. Self-host the fonts for offline use and deterministic screenshots — all pages.
10. Add the `@pytest.mark.local` browse.exe screenshot + axe + budget harness at both widths and themes — all pages.

## 3 disagreements I expect with other researchers

1. **No chart library.** Others will want a chart lib for GPU-hours, ETAs, run histories; I say server-drawn
   SVG macros cover every chart in the brief and keep JS ≤ 80 KB.
2. **Morph over client patching.** The progress-tracker design patches nodes by hand in `progress.js` to keep
   animations alive; I'd rather morph the server partial and delete the duplicated markup in JS — the progress
   session may disagree about animation continuity.
3. **Self-hosted fonts and a board-side token override.** The token/font tests treat the org chart as the single
   source byte-for-byte; a design researcher may want new tokens or fonts freely, and the org-chart purist will
   refuse any divergence. I propose: tokens may grow on the board only *after* the copied block; contrast fixes
   go to the org chart itself.
