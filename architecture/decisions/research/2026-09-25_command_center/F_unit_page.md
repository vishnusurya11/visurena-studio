# F. The unit page `/d/{stage}/{codex}/{unit}`: redesign spec

Date 2026-09-26. Read-only research on the live board (ep13 running, 24 attempts; ep12 finished,
7 masters). Extends D_ui_design §5d and uses the department page's vocabulary: state pills, the
12-segment step bar, one mark per gate. The fields named here all exist on disk or in
`db/visurena_studio.db` today. Items marked **(new view fn)** are pure reads added to `views.py`.

## 0. What the data says about ep13 (the case the page has to explain)

- `events` holds 170 rows over 29 `run_id`s (one run = one attempt). The last six runs ended on
  `09 failed REFUSED: the takes wait on the panels: panel_dq.json…` (x3),
  `08 failed DEFERRED: EYE_PANELS needs 102 s … share has -247 s`, `02 failed INVALID VERDICT`,
  or are still `08 started`. **The unit is looping on 08→09.** It is not progressing, and the
  current page has no place that shows this.
- `learnings.jsonl` (64 rows): `EYE_PANELS` measured 24 → 20 → 20 → 17 over four passes, so faults
  fall slowly. On every run `PLAN` re-climbs its ladder (improve, fresh_brief, model_tier,
  keep_best), and the plan's title drifts between runs ("The Destruction of Weybridge" against
  "How I Fell in with the Curate"). Both are facts the page should show.
- One `note` field holds up to 11 KB: 61 battery lines joined by `; battery at plan: `, each
  starting with a code (`G-SIZE`, `G-AIM`, `G-LIGHT`, `CONTRACT`, `MOVES/SOURCE`…).
- `storyboard/eye_f3ba61bc.json` `faults[]` has `{kind, where: "shot_NN", note, evidence}` for 17
  faults: framing, posture and missing. The page prints only the count.
- `work_steps.seconds` is 0 for every step. Durations come from `events` started/completed pairs
  per run, or from `timing.jsonl` (151 rows `{stage, started, ended, seconds, ok, note}`).

## 1. Section order: one question per band

| # | band | answers | reads |
|---|---|---|---|
| 1 | **Header** | Which unit is this, where is it now, is it alive? | `work_orders.{unit,state,step_id,progress,attempts,gpu_seconds,cost_usd,started_at,updated_at,lease_until,run_id,flags,hold_reason,blocked_on}`, `plan.json.{number,title,question}`, `step_names(stage)` |
| 2 | **Step bar** | How far through the 12 steps, how long each took, which failed and why | `work_steps.{step_id,state,attempt,terminal,verdict_word,detail}` + durations (new view fn `step_durations`: `events` of the current `run_id`, falling back to `timing.jsonl` summed by stage) |
| 3 | **Health** | Is it looping or improving, and why N attempts? | new view fn `attempts(conn, order)`: `events` grouped by `run_id` → `{run_id, began, last_step, last_event, reason_line}`. New view fn `trend(learnings)`: per gate, the `measured` series |
| 4 | **Gates** | Which gate is holding it, and on which faults | `work_orders.verdicts[gate].{by,sha8,path,faults,terminal,word}` + the verdict file's `faults[]` `{kind,where,note,evidence}` |
| 5 | **Pictures** | What it looks like so far | `storyboard/shot_NN.png`, `plan.shots[i].{index,section,size,setup,frame,motion,camera}`, `takes/r2v/T*.mp4`, `reports/strip_*.png`, `cut/master_iter*.mp4`, `qc_r2v.json`, `youtube.json` |
| 6 | **Actions** | What can I do about it | `orders` rows for this unit (untaken first), `holds`, the `_macros` forms |
| 7 | **Raw** (collapsed) | Full detail when I ask for it | `learnings.jsonl`, newest log (`logs/{codex}/{stage}/{run_id}.log`), `timing.jsonl` |

Bands 1–4 fit in the first 900 px at desktop. Numbers in the wireframes that are not in §0 are illustrative. Note: the live DB row for ep12 now reads `blocked`, attempts 0, verdicts NULL (a backfill reset), so the finished state is drawn from its files. A healthy unit (all green) collapses band 3 to one
line.

## 2. Desktop wireframe: ep13, running and looping

```
Studio › episode › The War of the Worlds › ep13                                 [◐]
ep13  How I Fell in with the Curate                         (● running) 08 panels 2/12
"Is there any hope left against them?"
attempt 24 · 5.4 h gpu · $0.51 · started 25 Sep 17:40 · moved 2m ago · lease ok to 04:30
[■■■■■■■▣□□□□]  ⚑11
 01  02  03  04  05  06  07  08  09  10  11  12
 –   ✓   –   –   –   ✓   ✓   ●   ✕   ○   ○   ○
 skip <s>  skip skip skip <s> <s> 18m… ref.   (durations: §1 row 2)
 click 09 → "REFUSED: the takes wait on the panels: panel_dq.json: panels failed…"
───────────────────────────────────────────────────────────────────────────────────
HEALTH   ⟳ LOOPING: last 4 runs ended at 08/09 on the panel gate             [why ▾]
 runs  ┊ 20:29 02✕invalid ┊ 20:39 08● ┊ 21:13 09✕refused ┊ 22:55 08↩budget ┊
       ┊ 00:27 09✕refused ┊ 02:25 09✕refused ┊ 04:02 08● now                    ┊
 trend  EYE_PANELS  24 ▸ 20 ▸ 20 ▸ 17   ↘ improving, 3 per pass        (learnings)
        PLAN        re-climbed on 6 of 6 runs · title changed 2×      ⚠ drift
 ended on    09 refused ×3 · 08 deferred ×1 · 02 invalid ×1 · 08 running ×1
───────────────────────────────────────────────────────────────────────────────────
GATES          PLAN ⚑1   LAYOUT ○   PANELS ⚑17   TAKES ○   MASTER ○   RENDER ○
 PANELS ⚑17  judge:panel_eye@1 · f3ba61bc · keep_best · 04:00          [file] [▾]
   framing  ×7  [03] [11] [12] [15] [17] [18] [22] [24]
   posture  ×9  [09] [11] [15] [16] [17] [19] [21] [22]
   missing  ×1  [04]
 PLAN ⚑1  judge:plan@1 · 86195b5f · APPROVE
   invented ×1  [02] place 'the crater rim' not in the chapter (0.74 < 0.85)
───────────────────────────────────────────────────────────────────────────────────
PANELS 25 · 17 flagged        [all] [flagged] [by section]           contact.png ▸
 ┌00────┐┌01────┐┌02──⚑─┐┌03──⚑─┐┌04──⚑─┐┌05────┐┌06────┐┌07────┐┌08────┐
 │ img  ││ img  ││ img  ││ img  ││ ░░░░ ││ img  ││ img  ││ img  ││ img  │
 │close ││wide  ││full  ││insert││missing│ …                 hook·hook·…
 └──────┘└──────┘└──────┘└──────┘└──────┘└──────┘└──────┘└──────┘└──────┘
 … 3 rows of 9 at 120 px; a flagged tile has an amber corner and ⚑ with the kind
TAKES   not shot · waits on the panel gate (09 refused 02:25)
 [T00 ○][T01 ○][T02 ○] … [T24 ○]    one grey slot per planned shot
MASTER  none yet · 12 deliver not reached
───────────────────────────────────────────────────────────────────────────────────
ACTIONS                                         │ ORDERS for ep13
 [redo 08 panels ▾]  (suggested: the gate that  │  none pending
   holds it · shots prefilled from ⚑17)         │  last: requeue 26 Sep 09:48 ✓ taken
 [retry] [requeue] [bump ↑]   [hold … reason]   │
───────────────────────────────────────────────────────────────────────────────────
▸ Learnings  64 rows · PLAN 53 · EYE_PANELS 10 · budget 1 · newest 04:11 keep_best
▸ Log  …040215.log · 9 warnings · newest 04:47 panel_check: faults found
▸ Timing  151 rows · grids 41m · panel_content 2h33 · panels 3m · …   (by stage)
```

## 3. Desktop wireframe: ep12, finished (only the bands that change)

```
ep12  Weybridge and Shepperton                               (⚑ flagged) 12 deliver
"Can the guns stop them?"
attempt 5 · 3.6 h gpu · done <finished_at> · master_r2v.mp4 · on YouTube ▸
[■■■■■■■■■■■■]  ⚑ PLAN 7 · PANELS 1 · TAKES 5 · MASTER 3
HEALTH   ✓ finished in 5 runs · no loop                                     [why ▾]
───────────────────────────────────────────────────────────────────────────────────
MASTER  ┌────────────────────────┐  master_r2v.mp4 · 160.3 s (plan 155.5)
        │   ▶  <video 1:1>       │  LUFS -14.15 ✓  peak -1.51 ✓  cuts 23/23 ✓
        │                        │  longest gap 5.8 s · lines heard 23/23
        └────────────────────────┘  iterations: iter1 … iter7 · r2v  (links)
 MASTER ⚑3 master_eye@1 faf11c8f · flag
   faces ×1 [master]   identity ×2 [artilleryman] [narrator]
GATES      PLAN ⚑7  LAYOUT ✓  PANELS ⚑1  TAKES ⚑5  MASTER ⚑3  RENDER ✓
 TAKES ⚑5  take_eye@1 21227f91 · still
   face-at-end [T16]  lag [T16]  cut [T19]  jump [T19]  cut-vote [T19]
TAKES 24 · strip_T00_T23.png
 [T00▶][T01▶]…[T16⚑][T17▶][T18▶][T19⚑]…[T23▶]   hover plays, click → lightbox
PANELS 24 (collapsed to one row with ▸ all, because the takes supersede them)
```

The finished page puts MASTER directly under the header. Takes come before panels. Panels
collapse to one row.

## 4. Phone (≤ 420 px)

```
ep13 · How I Fell in with the Curate          ep12 · Weybridge and Shepperton
(● running) 08 panels 2/12                    (⚑ flagged) 12 deliver
att 24 · 5.4 h · moved 2m                     att 5 · 3.6 h · YouTube ▸
[■■■■■■■▣□□□□]                                [■■■■■■■■■■■■]
08 panels ● 18m… · 09 ✕ refused               ┌──────────────┐
⟳ LOOPING · 4 runs end 08/09  ▸               │ ▶ master 1:1 │
PANELS ⚑17  24▸20▸20▸17 ↘                     └──────────────┘
PLAN ⚑1 · others ○                            160 s · -14.1 LUFS ✓ · 23/23
▸ framing ×7   ▸ posture ×9                   MASTER ⚑3 ▸  TAKES ⚑5 ▸
▸ missing ×1                                  PANELS ⚑1 ▸  PLAN ⚑7 ▸
[00][01][02⚑]                                 [T00][T01][T02]
[03⚑][04⚑][05]   3-up grid, ⚑ filter on       [T03]…  3-up
…                                             …
[redo 08 ▾]  [retry]  [⋯]                     [redo ▾]  [⋯]
▸ learnings · ▸ log · ▸ timing                ▸ learnings · ▸ log · ▸ timing
```

On a phone the step bar is the bar only; tapping a segment opens its row. Gates render as one
line per gate with `<details>` for the fault kinds. Actions become a sticky bottom bar with the
suggested action and `⋯` (hold, bump, requeue).

## 5. Taming long texts (the 11,700 px problem)

One rule: **no text node over 160 characters is rendered open.** Each long field becomes a
`<details>` whose `<summary>` is a one-line digest built in Python, not in the template.

- **new view fn `split_note(note) -> list[{code, text}]`**: split on `; battery at plan: `, `; `
  and `\n`. Tag each line with the first `\b(G-[A-Z]+|CONTRACT|[A-Z/ ]{3,}(?=\s*:))` match, else `—`.
  Rendered as one row per line: `[G-SIZE] shot 11: a close whose at_rest names no head fraction…`
  (the row is ellipsised at one line, and a click expands it).
- **new view fn `count_codes(lines) -> {code: n}`**: the digest. Summary of the 11 KB row:
  `04:11 PLAN model_tier #4 · 61 → refused · G-SIZE 12 · G-FIRSTFRAME 4 · G-AIM 4 · G-SYNC 2 · +9`.
- Learnings render as a **table**, not a `<pre>`: `time · step · gate · action · #attempt ·
  measured/threshold · terminal · note digest ▸`. Default: the newest 8 rows, with a "show all 64"
  link. Consecutive rows with the same `(gate, action)` merge into one row with `×n`.
- **Log**: WARNING+ rows only, `msg` first line only, a `▸` to see the rest. The multi-line
  `plan_check refused:` message goes through `split_note` like above.
- **Verdict notes** (`eye_*.json.note`, 1–2 KB) are never printed. The page renders `faults[]`
  grouped by `kind` → `where` chips (§2). Evidence (`{planned, keypoints, read}`) appears on hover
  and in the lightbox.
- **Timing**: 151 rows fold to one row per `stage` (`count, total seconds, last ok`). The rows
  themselves sit behind `▸`.
- CSS backstop: `.tail, td.note { overflow-wrap:anywhere; max-height: 12lh; overflow:auto }`.

## 6. Panel grid

- Source: `thumbnails(kind="panels")` joined to `plan.shots` by `NN == shot.index` (new view fn
  `shot_tiles(home, plan, verdicts)` → `{index, url, section, size, setup, faults:[{gate,kind,note}], superseded:n}`).
- Tile: 120 px square (1:1 like the episode). Shot number `03` sits top-left on a paper chip. The
  planned `size` sits bottom-left in small mono. A fault badge `⚑ framing` sits top-right in amber
  (red `✕` for `missing`), with one badge per gate that names the shot (PANELS, and later TAKES).
  A missing file shows a hatched tile with the number.
- Filters: `all · flagged · by section` (hook/…); the `section` headers come from
  `plan.shots[].section`. A fault chip in GATES (`[11]`) scrolls to its tile and pulses it.
- Click → a **lightbox** (`<dialog>`, no library): the picture large on the left; on the right
  the shot's `frame`, `motion` and `camera` text from `plan.json`, then the faults on this shot
  with their evidence, then `storyboard/superseded/` earlier draws when present, then a
  `[redo this shot]` button that pre-fills the redo form (step 08, `artefact=storyboard/shot_11.png`,
  note seeded with the fault notes). `←/→` move between shots and `Esc` closes.
- Takes use the same grid: `T{NN}` (for ep12, `plan.shots` index = take number), with
  `<video preload="metadata">` that plays on hover. The fault badge comes from the takes eye
  file (`takes/r2v/eye_*.json`, the newest by `signed_at`). Before 09 runs, there is one grey
  slot per planned shot with the reason (`waits on the panel gate`), so the section never
  disappears.

## 7. Attempts and history ("why 24 attempts?")

- **new view fn `attempts(conn, codex, stage, unit)`** groups `events` by `run_id` in order,
  and gives each run `{began, ended, steps_done: [ids], last_step, last_event, reason: first
  line of detail, gpu_s}`. Each run is **one segment on a timeline**, coloured by how it ended
  (green completed, red failed/refused, purple deferred, blue running) and labelled with
  `last_step` and one word (`refused`, `budget`, `invalid`). Hovering shows the reason. A click
  filters the log and learnings to that `run_id`.
- **Classify** the reason by its first word, `REFUSED|DEFERRED|INVALID VERDICT|<exception>`. The
  health line reports `ended on` counts across the last 10 runs.
- **Loop detector** (pure fn, tested on fixtures): if the last 3 finished runs share
  `(last_step, reason class)`, show `⟳ LOOPING`. If the gate's `measured` series (from learnings
  rows of the holding gate, last value per run) went down on the last pass, add `↘ improving`,
  otherwise `→ stuck`. Also, if `plan.json.title` differs between `learnings` notes (`CONTRACT OK:
  <title>`), show `⚠ plan drift`.
- `[why ▾]` expands the full table: `run · began · reached · ended · reason · gpu`.

## 8. Actions panel

One block, labelled, with the state-appropriate primary first (same `/act/*` POSTs and
`orders` rows as today; nothing new on the server):

| state | primary | secondary (behind `⋯` on phone) |
|---|---|---|
| running, looping | `redo <holding step> ▾` prefilled from the gate faults | hold, bump |
| failed / deferred | `retry` | redo ▾, requeue, hold |
| held | `lift` (the hold id) | — |
| done / flagged | `redo ▾` (step + note, artefact picker of flagged shots) | requeue |

- Redo becomes a full-width drawer, not an inline `<details>`: a step `<select>` (defaulting to
  the holding step), a shot multi-pick (the flagged shots are checked), a note (required), and
  the receipt.
- Beside it: **Orders for this unit**, from `orders WHERE codex_id=? AND stage=? AND unit=?` newest
  5, with `pending` or `taken <ts> by <run>`. A click that has not been taken yet stays visible.
- The hold reason input moves inside the hold button's popover (it currently takes up the header
  row).

## 9. Live polling

| part | while running | when terminal |
|---|---|---|
| header + step bar partial (`/partials/unit/…/head`) | every 3 s | once, then stop (server omits `hx-trigger`) |
| health (attempts + trend) | on `run_id` or `attempts` change: head emits `HX-Trigger: unit-run-changed` | static |
| gates | on `verdicts` change (head emits `unit-verdict-changed`) | static |
| panel/take grid | on `progress` change or a new eye sha8 (event), cache-busted by file mtime | static |
| raw tails (learnings, log) | every 5 s, only while their `<details>` is open | static |
| orders | on `orders-changed from:body` + every 10 s | same |

All polls pause while focus is in a form or the lightbox is open (the guard
`[!document.activeElement.closest('form,dialog')]`, the same one the department page uses).
The lease check: if `lease_until` is older than now, the header pill turns `~ stale lease`.
A crashed runner then looks different from a live one.

## 10. What is removed or demoted

- The **Deliverable** box (folded into the header + MASTER); the **`<pre>` learnings/log dumps**
  (tables with digests, §5); the flat **151-row timing table** (per stage behind `▸`).
- The **`file` link as the only way to see faults**: it stays as a small `[file]`.
- The **inline hold input** in the header (moves to actions); the full `run_id` in the header
  (shows `04:02`, full id in `title=`). Keep the hidden `STEPS`/`VERDICTS` test markers.

## 11. Build order (test-first, each its own commit)

1. `split_note` + `count_codes` (fixtures: the 11 KB learnings row, the log `plan_check refused`).
2. `attempts` + `loop_state` + `trend` (fixture: ep13's 29 runs). 3. `step_durations`.
4. `shot_tiles` + lightbox partial. 5. Bands 1–7 + head partial. 6. Phone CSS, `/browse` at 390 px.
No stage, step or runner changes, so `architecture/index.html` is untouched.
