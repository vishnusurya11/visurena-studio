# P03 — Information hierarchy & scannability

Lens: what the eye hits first, density, grouping, what to remove, which numbers matter, and the
5-second test for Home, department and unit. Read-only pass, 2026-10-04.

Evidence: screenshots at 1440x900 and 390x844, in
`D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\9340346d-60b6-4248-b569-c5a6fe035ef8\scratchpad\board_v3\mockups\shots\panel\`
(`P03_index.png`, `P03_index_full.png`, `P03_index_phone.png`, `P03_dept.png`, `P03_urun.png`,
`P03_ufin.png`, `P03_live_home.png`, `P03_live_dept.png`). The live ep17 unit page timed out in the
browser (B1 weight), so I judged the unit pages from the 8710 mockups.

## The brick for this lens

**One page answers one question, and each answer has one owner element.** You have hierarchy when
each owner question maps to exactly one element that is the biggest, highest-contrast thing in its
region, and every other copy of that fact is either removed or visibly secondary. You can test this
mechanically. For each page, list the questions, list the elements that answer each one, and count
them. More than one equal-weight answer means a duplicate to demote. An element that answers no
question is noise to remove. (NN/g visual hierarchy: https://www.nngroup.com/articles/visual-hierarchy-ux-definition/;
Few, *Common Pitfalls in Dashboard Design*: https://www.perceptualedge.com/articles/Whitepapers/Common_Pitfalls.pdf)

For a board that refreshes itself, this adds a second rule. **Slots are stable and only changed
facts earn salience.** If the layout re-sorts or re-weights on every pulse, the owner has to
re-scan the whole page each time. This agrees with 09's "one animation per viewport".

## 5-second tests (questions the owner must answer in 5 s)

| page | Q1 | Q2 | Q3 |
|---|---|---|---|
| Home | Is the GPU working, and when is it free? | Does anything need **me**? | Is anything going wrong (burning, looping, stalled)? |
| Department | Which units need me? | What is running and how far along? | How far along is each book? |
| Unit (running) | When will it be done? | Is it healthy right now (heartbeat, attempt)? | What is it making now (the newest picture)? |
| Unit (finished) | Watch it. | Is it good (verdict, flags)? | What do I do about it (ack, redo)? |

### Home mockup (8710 `index.html`): scores Q1 4/5, Q2 2/5, Q3 1/5
- **Too many focal points above the fold.** I count six display-size elements: the 360 px poster,
  the 40 px title, "21:35" at 56 px, and three KPI hero numbers (1.5, ~05:29, 5). With six equal
  claims, the eye lands on the poster, which is the one element that answers none of the three
  questions.
- **Q2 is spread out and partly below the fold.** "Need you" appears four times: the header tally
  "5 need you", the sidebar Inbox badge, KPI tile 3, and the section at y≈700, which is below the
  fold. On the phone (`P03_index_phone.png`), not one needs-you card is visible. The only signal is
  the small amber "5" in the tally.
- **The counts disagree.** The sidebar shows refs ●1 + episode ●5 = 6 attention items, but the
  Inbox says 5. The live board says "Needs you (6)" and includes `refs › main`. If two numbers for
  the same fact can disagree, the owner learns to trust neither. One function should produce the
  inbox count, and every surface should read it.
- **Q3 sits at the bottom of the page.** "34 of 75 GPU-hours burned" and the callout "09 shoot is
  the lever: 55 % … ended in a refusal" are the most consequential facts on the page, and they sit
  at y≈1600 of 2445. Above the fold, Q3 gets "0.5 burned" in grey 13 px next to "1.5 h".
- **Noise in the hero card.** It carries eight same-weight micro-facts (`07 board · panel 00 of 22 ·
  attempt 1 · run 26 min · step 10 min · p50 9 · run 3 today · last log 8 s ago`), plus a raw log
  line (`ep17_grid_steamer_forward_3x1_a: shots [13, 14,…`). The step rail prints "cached" four
  times. The timeline beside 21:35 uses axis text of about 7 px, which nobody can read at a glance.
- **Repeated information.** The "Shipped with flags" shelf shows the same five units (ep12–ep16) as
  "Needs you". The sidebar GPU card and Pinned ep17 repeat the hero on the one page where the hero
  is already shown. "Everything else is clear" spends 7 rows on zeros.
- **Sidebar counts that do not matter:** 30 / 30 / 30 / 30 / 31 per department, and Books 30. These
  are constant totals at the same weight as the attention dots, which do change.

### Department mockup (`department.html`): the best of the set, Q1 5/5, Q2 4/5, Q3 3/5
- Grouping by status (Running / Needs you / Queued / Done) works, and the group header carries the
  reason.
- Row text repeats the group header. "published ▲ · not acked" appears in every Needs-you row,
  under a header that already says "shipped with flags · not acknowledged".
- Constants appear in the title tally: "12 steps · 6 gates". Remove them.
- The segmented filter (Running 1 / Needs you 5 / Queued 3 …) repeats the group headers directly
  below it. Keep one: the headers, plus a filter that only collapses groups.
- Queued rows show **empty 36 px face boxes**. The SPEC says "never an empty box".
- Done (8) is expanded in the mockup, but the SPEC says it is collapsed. Done rows must recede.
- Gate chips use raw fault counts with no shared scale (`panels ⚑531` beside `master ⚑3`). The 531
  catches the eye but says less than the 3 on master. Order the chips by gate severity
  (master > takes > panels > plan), and cap the number display at "99+".
- The book header's stacked state bar sits at the far right, away from the numbers it summarises.
  Put it directly under the book title.

### Unit running (`unit-running.html`): Q1 5/5, Q2 2/5, Q3 2/5
- **Three finish times disagree.** The hero says 21:38, while the sidebar card and Home both say
  ~21:35. Separately, the hero card says "snapshot 19:34 · not live" while the top bar says
  "live · 19:21". Any refresh design has to fix this first.
- The question line under the title includes the plan's character expansion ("grey eyes, Brown
  herringbone Norfolk jacket…"). That is pipeline text leaking into a display string. Show the
  question only.
- Q2 has no owner element. "heartbeat 6m ago" is grey 13 px in a row with five peers. A stale
  heartbeat is the one fact that should change weight (P03.6).
- Q3 has no picture. The poster is the "newest grid", but the Shots section opens with an
  empty-state paragraph, and "0 of 22 so far" contradicts "22/22 panels cut".
- The properties panel has a tab row (Now / Shots / Gates / Runs / Files / Activity). The SPEC ruled
  "no tabs: a glance must not need a click".

### Unit finished (`unit-finished.html`): Q1 5/5, Q2 4/5, Q3 4/5
- Media first is right.
- The prime spot above the player is filled with file-identity jargon
  (`master_iter7.mp4 = iter5 = master_r2v · faf11c8f`) and five all-pass QC chips. Collapse them to
  one `QC 5/5 ✓` chip that expands, show failures only, and move the hash to properties.
- The judges card mixes verbs. "Plan · approve ⚑7" reads as both a pass and a flag. Use one word
  per gate state from the 11-state vocabulary.
- Faults on the master (by time, click to seek) is the best scannable list on the board. Keep it.

### Live board (8700, old skin): for the re-skin builder
- Needs-you rows wrap ("acknowledge" falls onto a new line) and the ISO timestamps are the
  longest token in each row. Show ages ("9 d") instead.
- The department table has 6 gate columns that are mostly `○`, which is wasted ink. The SPEC's
  single "gates" cell is right.

## Density, numbers, removal: the rules I would enforce in code

1. **One display-size number per region.** Barlow 40+ px goes to the answer of that region's Q1
   only. Everything else is at most 15 px Plex. Data-ink: https://www.edwardtufte.com/notebooks/
2. **Show what changed, not what is constant.** Totals that never move (30 units, 12 steps, 6
   gates, Books 30) lose their slot. Counts that move (attention, queue, burn) keep it.
3. **Zero means silence.** A group or tile with nothing to report collapses to one line
   ("Nothing failed, stale, looping or held"). NN/g progressive disclosure:
   https://www.nngroup.com/articles/progressive-disclosure/
4. **Ages, not timestamps, in lists.** Absolute times go in a `title` tooltip and in properties.
5. **One count source.** Each count (needs-you, queue, finish p50) comes from one server function,
   and every surface (title, favicon, sidebar, tally, tile, section) reads that one value from the
   pulse. The test: a snapshot of the page asserts that all copies are equal.
6. **Stable slots under refresh.** Morph in place. Never re-order rows during a pulse; new items
   join their group at the end. A changed value gets one 1.2 s highlight (background fade), never
   a size change. (Carbon status pattern:
   https://carbondesignsystem.com/patterns/status-indicator-pattern/)
7. **Scan line first in tables.** Face, then unit id + title, then state, then the non-pass gate,
   then age, in that order and left-aligned. Numbers are right-aligned and tabular. NN/g data
   tables: https://www.nngroup.com/articles/data-tables/

## Proposals (ranked)

| id | page | change | effort | files |
|---|---|---|---|---|
| P03.1 | all | **One count source.** `inbox_count()`, `queue_count()` and `finish_p50()` live in one module, are emitted in `pulse.json`, and every copy carries `data-count="needs"` and is set from the pulse. A test asserts that the title, sidebar, tally and section agree (this fixes the 5 vs 6 and 21:35 vs 21:38 disagreements). | M | `studio/command_center/views.py`, `progress_view.py`, `templates/_shell.html`, `home.html`, `static/progress.js`, tests |
| P03.2 | Home | **Re-rank the page.** The order becomes: hero (finish time is the single display number, poster shrunk to 200 px), then **Needs you** directly under it at full width, then a **burn line** ("34 of 75 GPU-h burned this week · lever: 09 shoot 55 %"), then Up next, then the chart. Needs you must be above the fold at 1440x900 and be the first card under the hero on the phone. | M | `templates/home.html`, `_live_hero.html`, `_attention.html`, `static/css/pages.css` |
| P03.3 | Home | **Remove the duplicates.** Drop the "Shipped with flags" shelf (it equals Needs you). Hide the sidebar GPU card and Pinned row for the unit that is the current hero. Collapse "Everything else is clear" to one line, and expand it only for a non-zero item. Drop KPI tile 3 (Needs you), since the section owns that answer. | S | `home.html`, `_shell.html`, `_today.html` |
| P03.4 | Home | **Hero diet.** Keep: state, title, the question, Done around + the p50–p90 line, step N of 12 + name, run elapsed, and attempt. Move the log line, `last log`, `p50 9` and `run 3 today` to the unit page. The step rail labels only the current step and failed steps; done steps become plain bars with no "cached" text. | S | `_live_hero.html`, `_live_rail.html` |
| P03.5 | Department | **Remove repeated row text.** Drop the per-row "not acked" text (the group header says it). Drop "12 steps · 6 gates". Collapse Done by default. Show no face box when no poster exists. Order gate chips by severity and cap at 99+. Put the book state bar under the book title. | S | `templates/department.html`, `_rows.html`, `_macros.html` |
| P03.6 | Unit running | **Give Q2 an owner element.** A health line beside the finish time ("heartbeat 8 s · attempt 1 · on p50") stays quiet while healthy. Past 2 pulses with no heartbeat it becomes amber at the same size, and past p90 it says "late". It is the only element that changes weight on this page. | S | `_unit_live.html`, `_live_vital.html`, `progress_view.py` |
| P03.7 | Unit running | **Give Q3 a picture.** The Shots section opens on the newest panels or takes as tiles (from `/thumb/`) and drops the empty-state paragraph whenever ≥1 exists. Strip the plan's character expansion from the display question. Remove the properties tab row (SPEC: no tabs). | M | `unit.html`, `unit_view.py`, `_unit_head.html` |
| P03.8 | Unit finished | **Clear the player's crown.** Replace the five pass chips with `QC 5/5 ✓` (failures listed in full), and move the file/hash line to properties. The judges card uses one state word per gate. | S | `unit.html`, `_receipt.html`, `unit_view.py` |
| P03.9 | Sidebar | **Show only counts that move.** Remove the department totals (30 / 30 / 31) and Books 30. Keep only the state dots with their non-zero counts, and Queue. | S | `templates/_shell.html`, `shell.py` |
| P03.10 | all | **Changed-value highlight.** On a morph, an element whose `data-count` or state changed gets a single 1.2 s background fade (suppressed under reduced motion). Rows never re-sort during a pulse. | S | `static/progress.js` (or `board.js`), `static/css/components.css` |
| P03.11 | all lists | Ages instead of ISO timestamps in rows, with the timestamp in a `title` attribute and in properties. | S | `_attention.html`, `_rows.html`, `_macros.html` |

How to know it worked. Run a 5-second check with the screenshot harness at 1440x900 and 390x844.
Every Q in the table above must be answered by an element above the fold with the largest type in
its region. The DOM must contain exactly one element at display size per region (a lint over
computed font-size). A pytest must assert that all `data-count` copies are equal on every route.

## I will argue against

1. **"More live widgets on Home"** (likely from the liveness/dynamic lens): rolling counters, a live
   log tail, an animated GPU trace in the hero. Each one adds a focal point that competes with the
   finish time and Needs you. Liveness belongs in *what changed* (P03.10) and the heartbeat line
   (P03.6), not in more moving elements. A log tail answers no 5-second question.
2. **"Bigger posters and more shelves"** (likely from the visual or media lens): the poster is
   already the first thing the eye hits on Home, and it answers nothing. A second poster shelf of
   the same units as Needs you doubles the page height for no information. Pictures lead on the
   *unit* and *book* pages, where watching is the task. On Home they are thumbnails that serve the
   decision.
3. **"KPI tiles with sparklines and deltas"** (likely from the dataviz or SaaS-craft lens): the SPEC
   already rules no deltas until ≥4 comparable weeks. An unlabeled sparkline beside "1.5 h" cannot
   be read in 5 s. The one GPU number that drives action is *burned share + the lever step*, which
   is a sentence and not a trend line.
