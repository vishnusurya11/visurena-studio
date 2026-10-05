# 03 — Modern SaaS product craft (Linear, Vercel, Raycast, Plain, Attio, Arc) applied to the board

Researcher 03 · 2026-10-04 · read-only: screenshots in `current/`, `studio/command_center/templates/base.html`,
`unit.html`, `_unit_head.html`, `department.html`. No code touched.

## 0. What the best SaaS tools agree on (with sources)

| # | Rule | Where it comes from |
|---|------|---------------------|
| R1 | **"Structure should be felt not seen."** Fewer dividers, softer borders, fewer and smaller icons, no coloured icon backgrounds. Navigation recedes ("a few notches dimmer"); the work area takes precedence. | Linear, *A calmer interface for a product in motion* (2026) — https://linear.app/now/behind-the-latest-design-refresh |
| R2 | **Few theme inputs, derived surfaces.** Linear went from 98 per-theme variables to 3 (base, accent, contrast) in LCH, which gives a high-contrast theme for free. Display face for headings, text face for body. | Linear, *How we redesigned the Linear UI* — https://linear.app/now/how-we-redesigned-the-linear-ui |
| R3 | **Warm neutrals are in.** Linear's 2026 refresh moved from a cool blue-grey to "a warmer gray". The board's paper palette is already where they ended up. | same as R1 |
| R4 | **One status glyph per object, and it fills as work advances.** Linear: ◌ backlog, ○ todo, ◔ in progress, ◕ in review, ● done; started states are spaced as fractions of the ring. | Linear docs, issue status — https://linear.app/docs/configuring-workflows ; glyph analysis in https://github.com/superset-sh/superset/pull/8076 |
| R5 | **The dot moves only while work runs.** Geist StatusDot "animates while BUILDING or QUEUED and goes static once … terminal". "Don't add a separate spinner alongside it." Don't flash on every poll; repaint only when the state changes. Colour is never the only signal. Pair it with a relative time ("Building · 12s ago"). | Vercel Geist Status Dot — https://vercel.com/geist/status-dot |
| R6 | **Status in the browser tab.** Vercel's redesign put deployment state (queued, building, error, ready) into the tab favicon "for quick project scanning". | https://vercel.com/blog/dashboard-redesign |
| R7 | **Detail = main column + properties panel.** Linear's issue view puts title, description and activity in the main column, with properties in a right panel ("increased and consistent click area"). Attio's record page has highlights, a sidebar of attributes, and main tabs (activity timeline). Plain toggles its sidebar between *thread details* and *customer cards* with ⌘1/⌘2. | https://linear.app/changelog/2024-03-20-new-linear-ui ; https://attio.com/help/academy/introduction/record-pages ; https://www.plain.com/changelog |
| R8 | **⌘K is the one shortcut to remember**, plus the shortcuts it teaches: J/K move, Space peeks, `G` then a letter goes somewhere, `?` lists them all. "Every common action reachable in two keystrokes or fewer." | Linear shortcuts — https://shortcut.fyi/linear-shortcuts , https://linear.app/docs/select-issues |
| R9 | **Primary action on ↵, secondary on ⌘↵, all actions in an Action Panel (⌘K) grouped in sections.** List rows carry right-hand *accessories* (tag, relative date, icon). When the detail split is open, the accessories move into the detail's metadata block. | Raycast API — https://developers.raycast.com/api-reference/user-interface/action-panel , https://developers.raycast.com/api-reference/user-interface/list |
| R10 | **An empty view never shows while the page is loading.** Use one icon, a title and a description. | Raycast List.EmptyView, same URL |
| R11 | **Motion budget.** UI motion stays under 300 ms (180 ms reads faster than 400). Nothing animates on keyboard actions or palette toggles, or on anything seen 100+ times a day. Use ease-out to enter. Press feedback is `scale(.97)`. Tooltips after the first open instantly. | Emil Kowalski — https://emilkowal.ski/ui/7-practical-animation-tips ; https://github.com/emilkowalski/skills/blob/main/skills/review-animations/STANDARDS.md |
| R12 | **Shortcuts need discoverability, memorability and no conflicts.** Show hints in tooltips and in the palette, map keys to verbs, never fire while focus is in a text input, use sequences (`G I`). | Knock — https://knock.app/blog/how-to-design-great-keyboard-shortcuts |
| R13 | **Peek before you commit.** Arc's Peek opens a link as a floating layer over the current window, and the Command Bar (⌘T) searches tabs, history and actions in one place. Plain keeps every action ~100 ms and keyboard-first. | https://blakecrosley.com/guides/design/arc ; https://www.plain.com/blog/plain-vs-zendesk-comparison-2026 |
| R14 | **Group logs by step and point at the failing phase.** Vercel's build logs sit inside the deployment overview, one section per step. "A failure points you straight at the right phase." | https://vercel.com/docs/deployments/logs ; https://vercel.com/changelog/redesigned-deployments-list |

## 1. What the current board does against those rules (from the screenshots)

**Unit page (`current/unit_ep17.png`, `unit_ep12.png`, `unit_ep17_phone.png`)**
- **The identity block appears twice.** The live card says `ep17 · The Thunder Child · QUIET 02 PLAN`, and directly under it
  the h1 says `ep17 The Thunder Child · ● running · 02 plan`. The step rail also appears twice: the card's proportional rail,
  then the 12-segment `.ubar`. That breaks R1 and R7. On a 400 px phone the title appears before the fold twice and the
  takes appear 3 screens down.
- **The largest number answers the wrong question.** `11:44 IN PLAN` (elapsed) is set at about 64 px. The owner's question is
  "when does it end"; `done around 21:40` is set at about 22 px. Linear and Vercel set durations small and states/outcomes large.
- **Several things move at once.** `base.html` animates `.pill.blue`, `.st.blue`, `.sbar i.blue`, `.ubar .seg.blue i`
  (`pulse 1.4s/2s infinite`) as well as the live card's `.vdot.beat` and the rail sheen, so up to 4 things pulse on ep17.
  That breaks R5 (one dot, no second spinner). The `_unit_live.html` comment already says "Only one thing moves".
  The older pulses contradict it.
- **Boxes everywhere.** Every shot number is a bordered chip (`00 01 02 04 08 …` ×18), every run is a bordered chip with a
  coloured left edge, every gate is a pill, and every unshot take is a dashed 120 px tile (`T00…T21` on ep17: 22 dashed boxes
  that say nothing). That breaks R1.
- **Some glyphs collide.** The legend shows `○ queued` and `○ blocked` as near-identical rings. Flagged is `⚑` in gates but
  `⚑4 flagged` in a pill elsewhere. Escalated is an emoji (`✋`) inside a mono set.
- **Actions sit at the bottom.** `redo 02 ▾` and `…` are at y≈1090 px of 1280, under every section. Linear and Raycast put the
  primary action where the eye already is, and on ↵.

**Department page (`current/dept.png`)**
- **Six gate columns, mostly `○`.** For the 15 done units, PLAN, LAYOUT, PANELS, TAKES, MASTER and RENDER are almost all `○`:
  6×31 cells of noise. The flagged counts (`⚑531`) are the only signal.
- **No title in rows.** The row says `ep12`, not `ep12 Weybridge and Shepperton`. Linear never shows an ID without its title.
- **The state pill is 92 px wide** (`✓ done`), and the steps bar repeats the same fact.
- **The `…` action column floats outside the table's right rule.** It is visibly detached.
- **Repeated text.** Seven blocked rows each print `· waiting on refs/04`. That is a group fact, not a row fact.
- **Done rows dominate.** 22 of 31 rows are finished and sort above nothing. Linear groups by status and folds Done.

## 2. Type scale and density (tokens, not taste)

Keep the three faces the page already uses, since they come from the org chart and the test holds the tokens. Cut the
sizes down to **six steps** and make every number tabular:

| token | face / weight | size / line | used for |
|---|---|---|---|
| `--t-label` | Plex Mono 500, caps, +.10em | 11 / 14 | eyebrows, column heads, property keys |
| `--t-meta` | Plex Sans 400, `--ink-3` | 12.5 / 18 | relative times, run ids, secondary lines |
| `--t-body` | Plex Sans 400 | 13.5 / 20 | rows, property values, findings |
| `--t-lede` | Plex Sans 400, `--ink-2` | 15 / 22 | the episode question, the "now" sentence |
| `--t-title` | Barlow Condensed 700 | 28 / 32 (phone 24) | page title only (one per page) |
| `--t-hero` | Plex Mono 600, `tabular-nums` | 44 / 44 (phone 36) | the one hero number on a running unit |

- Add `font-variant-numeric: tabular-nums` to `.mono`, `td`, `.lv-*` and every time, cost and GPU value so polling
  updates don't jitter. Today `9.8 h` and `34.0 h` misalign in the GPU column.
- **Density:** department rows at 36 px (currently ~38–46 px with pills). Sidebar property rows at 28 px. Hit area stays
  at least 28 px tall even where the text is 13.5, following Linear's "increased and consistent click area" for properties.
- **Hierarchy comes from weight and ink, not boxes.** Three inks (`--ink`, `--ink-2`, `--ink-3`) plus one rule
  (`--rule`). A section is an eyebrow followed by 12 px of space, with no border. Keep the one 3 px `--ink` rule under the
  header as the editorial signature.

## 3. Status iconography: one glyph family, 14 px inline SVG, `currentColor`

Replace the mixed text glyphs (`○ ● ✓ ⚑ ↩ ✕ ✋ ⏸ ~ –`) with one sprite (`static/glyphs.svg`, `<symbol>` ids, about 2 KB,
no build step). It follows Linear's filling-ring idea and Geist's "shape + label, never colour alone".
The board has a fact Linear lacks: **a running unit's ring fills by step n/12.** That is real progress, not a guess.

| state | shape (14×14, 1.5 px stroke) | colour token | reads field |
|---|---|---|---|
| queued | dashed ring | `--ink-3` | `work_orders.state` |
| blocked | ring with a horizontal bar through it | `--ink-3` | state, plus `blocked_on` shown as a tooltip |
| running | ring + pie wedge = `step_index/12` | `--think` | `work_steps` current index |
| done | filled disc + knocked-out check | `--ok` | state |
| flagged | filled disc + knocked-out `!` | `--qc` | any gate verdict `flagged` |
| deferred | ring + small return arrow | `--invent` | last run outcome |
| failed / refused | filled disc + knocked-out × | `--accent` | last run outcome |
| escalated | filled square + knocked-out `!` (square = needs you) | `--accent` | `holds`/gate ESCALATE |
| held | ring + two pause bars | `--ink-2` | `holds` |
| stale | dotted ring | `--ink-3` | lease expired |
| skipped | ring + diagonal | `--ink-3` | step skipped |

- **Gates use the same family at 12 px:** pass is a filled check, flagged is `!` plus a count, unsigned is a dashed ring,
  and a skipped gate is not drawn at all.
- **Motion:** only the *running* glyph animates, and only the glyph of the one running unit on screen. Its wedge
  advances when the step changes, over 240 ms ease-out. No pulse, no spinner (R5). Under `prefers-reduced-motion` it is
  static.
- The legend footer becomes a `?` popover (R8). The glyphs carry `<title>` text and the row carries the word in
  `aria-label`. A shape that colour-blind users can't tell apart from another one is a bug.

## 4. Unit page: one header, main column + properties sidebar

```
crumbs  episode › The War of the Worlds › ep17                          [⌘K]  ◐
◔ ep17  The Thunder Child                                  [Redo 02 ↵] [⋯ ⌘.]
"Today, can the brother … escape the Martians?"            (t-lede, 2 lines max)
┌ main (min 0, 1fr) ──────────────────────────────┐  ┌ properties (264 px) ─────┐
│ NOW  (only when running; no box, 3px --think    │  │ State     ◔ running      │
│      left rule)                                 │  │ Step      02 plan · r2   │
│  done around 21:40          ← t-hero            │  │ Elapsed   11m in step    │
│  02 plan · round 2 · improve   11m in step      │  │ Range     20:25–22:55    │
│  rail ▕██▒▒▒│░│░│░│░│░░░░░░│░░░░░░░░│░│        │  │ Attempt   3              │
│  last words  "plan_check refused: G-STORY …"    │  │ GPU       18 m           │
│ ─────────────────────────────────────────────── │  │ Cost      $0.35          │
│ LOOK SO FAR   master ▸ / takes grid / panels    │  │ Started   05 Oct 00:21   │
│ GATES & FINDINGS (only non-pass gates expanded) │  │ Moved     11m ago        │
│ HISTORY  runs grouped by step, failing step     │  │ Lease     ok → 02:10     │
│          open (Vercel-style log sections)       │  │ ── Gates ─────────────── │
└─────────────────────────────────────────────────┘  │ ! PLAN 18  ○ LAYOUT …    │
                                                     │ ── Files ─────────────── │
                                                     │ plan.json · learnings 14 │
                                                     │ ── Orders ── none        │
                                                     └──────────────────────────┘
```

- **One header.** The status glyph, unit id and title, with primary and secondary actions on the right of the same row
  (R9). `redo 02` moves up from y≈1090. It still posts through the existing `act.*` forms with a confirm `<dialog>`.
  Credit-spending actions keep the ESCALATE default; the palette never skips the confirm.
- **The hero is the finish time**, not elapsed time. Elapsed moves to the sidebar `Elapsed` row and to `--t-meta`. When
  a step is past every measured run, the hero reads `running long` in `--qc` (the field already exists, `e.long`).
- **Delete the second rail.** Keep the live card's proportional rail (honest durations). Show the 12-segment `.ubar` only
  when the unit is not running (done, queued). Never show both.
- **The sidebar owns every scalar.** It takes the fields that today sit in the dotted meta line (`attempt 3 · 18 m gpu ·
  $0.35 · started … · moved … · lease … · run 01:55`) plus the gate summary. Each value is one `<dl>` row, and the keys
  read `--t-label`. It is sticky at `top: 16px` on wide screens. At **< 900 px** it renders as a 2-column `<dl>` grid
  directly under the header (Linear mobile and Attio both collapse this way), so the phone sees state and finish in the
  first 400 px.
- **Main column order follows the owner's questions:** *when it ends* (NOW), *what it looks like* (master, then takes,
  then panels, newest material first), *why it's stuck* (non-pass gates with findings), *history*.
- **Findings without chips.** `invented ×18  00 01 02 04 08 09 10 11 14 …` renders as mono numbers separated by
  `0.4em`, with no borders. Each number is still a link to its tile (`#T08`). Only a number that has a tile gets the
  underline.
- **Runs as a Vercel-style step log.** `HEALTH 4 runs · no loop` becomes a list grouped by step:
  `02 plan — killed 00:21 · deferred 00:43 · running 01:55` and `06 prompts — refused 01:18 ▸ scripts/episode/takes_r2v.py exit 1`.
  A step with a failure is expanded; the rest are collapsed (R14). The colour-edged chips go.
- **Empty states (R10):** an unreached section is one line in `--ink-3` that says *when* it arrives, not a grid of
  placeholders:
  `Takes · 22 planned · arrive at 09 shoot (not before ~21:40)`. The 22 dashed tiles render only once step 08 has
  started, and then as real `<figure>` slots filling in. `ORDERS no orders for this unit` becomes the sidebar row
  `Orders —`. `PANELS 0 / no panels yet` (two lines saying the same thing) becomes one line.
- **Peek (R13, Linear Space):** in the takes grid, Space on a focused tile opens the existing lightbox `<dialog>`. ←/→
  already work. Add `r` = prefill redo for this shot (the `.lb-redo` path exists).

## 5. Department page: a Linear list grouped by book, then by status

```
Episode   31 units · 2 books          [filter /]  [book ▾]   ◔1  !5  ○3  ⊘7  ●15
The War of the Worlds  13/17 ▕████▒▒▒██████▏
  RUNNING 1
  ◔ ep17  The Thunder Child       ▕██▒▒▒░░░░░░░▏ 02 plan · done ~21:40   !18      11m   18m  $0.35  ⋯
  FLAGGED 5
  ! ep16  …title…                 ▕████████████▏ deliver                !6 !23 !21 !5  1h  2.7h $2.69 ⋯
  QUEUED 3 · DONE 6 ▸   (collapsed; click or →)
A Study in Scarlet  7/14
  BLOCKED 7 · all waiting on refs/04 ▸
  DONE 7 ▸
```

- **Group by status inside each book**, in the order *running, escalated, flagged, failed, queued, blocked, done*. Done
  and blocked start collapsed, and their state is remembered per viewer in `localStorage` (wrapped in try/catch). The
  page goes from 31 rows to about 9 visible rows. The existing filter pills become counts in the toolbar (glyph + number).
- **Row anatomy** (36 px, left to right): 14 px state glyph, then `ep17` in mono, then the **title in `--t-body`**
  (from `plan.json` / the unit's title field, ellipsis at 1 line), then the steps bar at 120 px fixed, then a *now* cell
  (`02 plan · done ~21:40` for running, the blocking reason for blocked, empty for done), then **one gates cell** that
  shows only non-pass gates as `!n` (Raycast accessories, R9), then moved, GPU and cost (right-aligned, tabular), then
  `⋯` *inside* the row.
- **The six gate columns are gone.** Their column heads become the tooltip of each `!n`
  (`PANELS flagged 23 · judge:panel_eye@1`).
- **Group facts on the group header.** `BLOCKED 7 · all waiting on refs/04` appears once. If the reasons differ, the
  header shows the most common reason plus `+2 other`.
- **Inline actions:** on hover or focus a row shows two 24 px icon buttons before `⋯` (`open ↵`, `redo last step`), and
  `⋯` opens a menu with the rest. On touch (`@media (hover:none)`) only `⋯` shows, always visible. Right-click on a
  row opens the same menu.
- **Polling:** keep `hx-trigger="every 10s"`, but have the partial carry a hash. Swap only rows whose hash changed
  (`hx-swap-oob` per row id) so the list never re-flows under the cursor (R5: "only refresh when state changes").

## 6. Command palette (⌘K / Ctrl K) without a build step

- **Markup:** a `<dialog id="palette">` in `base.html` with one input and a `<ul role="listbox">`. About 150 lines of
  vendored JS in `static/palette.js`, no dependency.
- **Data:** fetch `GET /palette.json` once on first open (and after `orders-changed`), about 100 entries. The client
  does a subsequence filter, so typing costs 0 ms of network (Plain's 100 ms bar, R13). Entries have the form
  `{kind, label, sub, href | act, keys}`:
  - *Go to:* every unit (`ep17 The Thunder Child — episode · WotW · running 02 plan`), department, book, Floor, Org chart.
  - *This page:* the current unit's actions (`Redo 02 plan`, `Notify me`, `Hold`), its files (`plan.json`,
    `manifest.json`, `master_iter7.mp4`), and its sections (`Jump to takes`).
  - *Recent:* the last 5 pages, from `localStorage`.
- **Behaviour:** ↑/↓ or Ctrl-N/P to move, ↵ to run the primary action, ⌘↵ to open in a new tab. Rows show their
  shortcut on the right (`G E`), which is how the shortcuts get learned (R12). An `act` entry never posts directly. It
  opens the same confirm dialog the button opens.
- **No open/close animation** (R11: palette toggles are 100+/day).

## 7. Keyboard map (ignored while focus is in input/textarea/select/contenteditable or a dialog form)

| keys | does | page |
|---|---|---|
| ⌘K / Ctrl K | palette | all |
| `?` | shortcuts sheet (replaces the legend footer) | all |
| `G H` · `G F` · `G O` · `G B` | home · floor · org · current book | all |
| `G A` `G S` `G T` `G R` `G E` | analysis · screenplay · trailer · refs · episode | all |
| `J` / `K` | move row focus (visible 2 px `--accent` focus ring, `aria-current`) | dept, book, home lanes |
| ↵ | open focused unit | dept |
| Space | peek: unit header + sidebar in a side `<dialog>` via `hx-get …/head` | dept |
| `/` | focus the filter | dept |
| `[` / `]` | previous / next unit in this book | unit |
| `T` · `M` · `L` | jump to takes · master · log | unit |
| `.` | open the row/unit action menu (the `⋯`) | dept, unit |
| Esc | close dialog, clear the filter, clear focus | all |

## 8. Live "in progress" (reconciling with the live card already built)

- **One moving thing per viewport:** the running glyph's wedge, plus the live card's `vdot.beat` heartbeat when a
  sign or log line lands. Delete the `pulse` keyframe uses on `.pill.blue`, `.st.blue`, `.sbar i.blue` and
  `.ubar .seg.blue i` (base.html lines ~72, 157, 161, 194).
- **Favicon and title (R6):** `progress.js` already polls. On a state change, draw a 32 px canvas favicon with the
  same ring and wedge (running), `!` (flagged or escalated) or × (failed), and set
  `document.title = "◔ 02 plan · ep17 · ~21:40"`. The owner works next to a terminal, so the tab strip *is* the glance.
- **Relative times** (`moved 11m ago`) re-render client-side once a minute from an ISO `datetime` attribute on `<time>`.
  The server doesn't need a repaint for that.
- **Patch, don't re-flow:** keep `_unit_live`'s in-place node patching. Extend it to `_unit_head`, which today does an
  `outerHTML` swap every 3 s while running and loses hover and focus. Patch only nodes whose `data-k` value changed.

## 9. Motion budget (fits the existing `--d1…--d4` tokens)

| interaction | duration | easing | note |
|---|---|---|---|
| hover colour, focus ring | 0 ms | — | seen hundreds of times |
| button press | 80 ms `scale(.97)` | ease-out | R11 |
| menu / tooltip enter | 120 ms (`--d1`), opacity + 4 px | `--ease-out` | 2nd tooltip 0 ms |
| side peek / lightbox | 200 ms | `--ease-out` | from 0.96 scale, never 0 |
| glyph wedge / step tick | 240 ms (`--d2`) | `--ease-out` | only on change |
| new take tile reveal | 480 ms (`--d3`) | `--ease-out` | rare event, earns it |
| rail width interpolation | 900 ms (`--d4`) | `--ease-out` | data motion, not UI response, so it's exempt |
| anything keyboard-triggered, palette | 0 ms | — | R11 |

All of it sits under `@media (prefers-reduced-motion: no-preference)`, as `base.html` already does for the live card.

## 10. Reconciling with "paper"

SaaS craft doesn't need cool grey. Linear just moved *toward* warm grey (R3). Keep `--paper`, `--ink`, `--rule` and the
Barlow page title. What SaaS adds is subtraction: fewer borders, one title, one moving thing, properties in a column, and
a keyboard. Following R2, the six status hues (`--think --qc --invent --ok --accent --ink-3`) stay the whole palette. A
high-contrast theme is `--ink-3 → --ink-2` and `--rule → --rule-2`, a two-line override.

## Top 10 recommendations for this board

1. **Unit:** merge the live card and the h1 into one header (glyph · id · title · actions top right), and delete the duplicate rail.
2. **Unit:** make the finish time (`done around 21:40` / `running long`) the hero number. Elapsed becomes a sidebar row.
3. **Unit:** add a 264 px sticky properties sidebar (state, step, attempt, GPU, cost, times, lease, gates, files, orders) that collapses to a 2-column `<dl>` under the header below 900 px.
4. **All pages:** one 14 px SVG status-glyph family with a running ring that fills by step n/12. It replaces the colliding `○` queued/blocked and the `✋` emoji.
5. **All pages:** exactly one animated element per viewport. Remove the four `pulse` loops, and repaint only on state change.
6. **Department:** group rows by status within each book, with Done and Blocked collapsed and the shared blocking reason on the group header.
7. **Department:** replace the six mostly-`○` gate columns with one accessory cell showing only non-pass gates as `!n`, and add the unit title to every row.
8. **All pages:** a ⌘K palette (`<dialog>` + `/palette.json`, about 150 lines of vendored JS) covering units, departments, books, this page's actions (through the confirm dialog) and files.
9. **All pages:** a keyboard map (`G`-sequences, `J/K`, ↵, Space peek, `[ ]`, `?` sheet replacing the legend footer), inert inside inputs.
10. **Unit / all tabs:** a state favicon and `document.title` (`◔ 02 plan · ep17 · ~21:40`), plus one-line "arrives at step NN" empty states instead of 22 dashed placeholder tiles.

## 3 disagreements I expect with other researchers

1. **Film-studio researchers (ShotGrid/ftrack/Kitsu)** will want a thumbnail on every department row. I'd keep list rows
   text-dense and put pictures in Space-peek and the unit page, with one exception: a 36 px poster on the *running* row.
   Thirty-one thumbnails of mostly-finished units are noise to someone glancing.
2. **Ops-monitor researchers (Grafana/Dagster)** will want more live graphics: sparklines per row, GPU gauges, animated
   DAGs. I'd allow one moving element per viewport (Geist's rule). Every additional pulse lowers the signal of the one
   that matters.
3. **The editorial/paper researcher (and the live-card spec)** will want to keep the big elapsed clock and the boxed live
   card as the page's signature. I'd make the *finish time* the hero and remove the box (a left rule only), because the
   owner's first question is "when does it end", not "how long has it run".
