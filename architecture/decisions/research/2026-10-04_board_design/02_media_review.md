# 02 — Media review and approval tools, applied to the board

Researcher 02, 2026-10-04. I studied Frame.io V4, SyncSketch, Flow Capture (formerly Moxion), ShotGrid / Flow
Production Tracking Review with RV / OpenRV, Vimeo Review, Filestage and Krock.io. I applied them to the unit
page, using the real files of War of the Worlds ep12 (finished, flagged) and ep17 (mid-plan).
All sizes and frame numbers below were measured from `library/20260827135508_the-war-of-the-worlds/episodes/ep12/`.

## 1. The brick under every review tool

All seven tools build their UI from one record:

> **note = (asset, version, time range, author) → text + verdict**; a **version stack** is an ordered list of
> versions of one asset; **compare** = two versions on one shared clock.

That record produces every surface I studied. The player is one asset at one version. Timeline markers are
notes plotted by time range. A version dropdown is the stack. A status badge is the verdict of the latest
version. Compare is two players sharing one clock. The approval stamp is a verdict with an author and a time.
Every surface on the board should come from the same record. The board already stores it, but under other names:

| review-tool term | this board's file / field |
|---|---|
| asset | a **shot** (index 0–23): panel `storyboard/shot_NN.png`, take `takes/r2v/TNN.mp4`, its window in the master |
| version | panel: `storyboard/superseded/r1..r3/` + current; take: `takes/r2v/attempts/T10_fail1..3.mp4` + `T10.mp4`; master: `cut/master_iter1..7.mp4` (`master_r2v.mp4` = iter7, same 259,457,105 bytes) |
| time range | `qc_r2v.json → edit.segments[i].start / n` in frames at 24 fps (3846 frames = 160.25 s); `planned_cuts` in seconds |
| note + author | gate verdicts: `review/eye_faf11c8f.json` (judge:master_eye@1), `takes/r2v/eye_20cc84ad.json` (judge:take_eye@1), `storyboard/eye_c7e3eb93.json`, `plan.verdict.json` |
| reason a version died | `learnings.jsonl` rows: `{gate:"EYE_TAKES", action:"move_type", attempt:2, note:"rotation at T10: 7.6deg turned, no roll planned"}` |
| status | gate `pass` / `flagged`; per take `T05.dq.json gates[].ok`, `T05.content.json passed` |
| approve / reject | `/act/redo` (order + casebook note); owner verdict files |

So the redesign does not need a data model, only a review surface. Every component below states the field it reads.

## 2. What the tools do (with sources)

| tool | what matters for this board | source |
|---|---|---|
| **Frame.io V4** | Version stack under one thumbnail; the player opens on the **newest version**; the **version number at the top of the player** opens the reorderable list. | [Versioning](https://help.frame.io/en/articles/9101068-versioning-in-frame-io) |
| | Comparison Viewer: **linked playback and zoom**; side-by-side, Overlay (draggable **slider wipe**, for stills), **Pixel Difference** (right side greyscale, changes lit; long-press toggles), Unlink. | [Comparison Viewer](https://help.frame.io/en/articles/9952618-comparison-viewer) |
| | Comments: single-frame, **range** (bracket handles; a line on the timeline; playback loops the range), **anchored** pins. Coloured dots on the timeline show the comment on hover. | [Commenting](https://help.frame.io/en/articles/9105251-commenting-on-your-media), [panel](https://help.frame.io/en/articles/9105278-comments-panel-overview) |
| | Keys: `Space`/`K` play, `J`/`L` multi-speed, `←/→` one frame, `I`/`O`, `M`, `F`, `[ ]` previous/next asset, `C` comment, `X` checkbox, `?` sheet. | [Shortcuts](https://help.frame.io/en/articles/9105337-keyboard-shortcuts) |
| | Speed 0.25–1.75x, Loop, frame guides with a mask, "Set Frame as Thumb", status Needs Review / In Progress / Approved (customisable). | [Player page](https://help.frame.io/en/articles/9105311-player-page-features) |
| | Frame-accurate **hover scrub** in the grid; **status badges on grid cards**; the "Vapor" design system is built in LCH for perceptual uniformity, in light and dark; the user picks the metadata shown on each card. | [V4 beta](https://blog.frame.io/2024/04/09/frame-io-version-4-beta-is-here-v4-announcement/), [V4 design](https://blog.frame.io/2024/05/21/frame-io-v4-web-app-beta-feature-focus-new-design-smooth-navigation/) |
| **SyncSketch** | Every note puts a **marker at its frame**; `↑/↓` jump from note to note; All Notes sorts **by frame**; `J/K/L`, `←/→`, `Home/End`, `Shift+?`. Compare is side-by-side or an **A/B toggle** with linked scrub. Users have asked for a **"ghost mode" of previous versions' notes** on the current timeline, which is exactly "iter1 vs iter7 faults". | [Timeline](https://support.syncsketch.com/hc/en-us/articles/32393850754196-Timeline-Navigation-and-Playback-Controls), [Keys](https://support.syncsketch.com/hc/en-us/articles/32393851909012-Keyboard-shortcuts), [Compare](https://support.syncsketch.com/hc/en-us/articles/32393992531092-Compare-Items), [ghost request](https://feedback.syncsketch.com/feature-requests/p/ghost-mode-of-previous-notes-on-timeline) |
| **ShotGrid / Flow Review + RV** | Right panel with **Notes \| Versions** tabs; "Compare with Current" puts two versions in a grid; `t` toggles compare. RV's heads-up timeline shows the frame count, fps and **marks**; `Alt+arrows` jump to **source boundaries** (cut-to-cut, which a 24-shot master wants); `F6` toggles wipe (drag an edge, or the centre to move it); Stack, Layout and difference matte. | [Collaborative review](https://knowledge.autodesk.com/support/shotgrid/getting-started/caas/CloudHelp/cloudhelp/ENU/SG-Tutorials/files/SG-Tutorials-tu-collaborative-review-html-html.html), [Review 0.227.12](https://community.shotgridsoftware.com/t/review-v0-227-12-released/20943), [OpenRV ch.4](https://aswf-openrv.readthedocs.io/en/latest/rv-manuals/rv-user-manual/rv-user-manual-chapter-four.html), [openrv-web](https://github.com/lifeart/openrv-web) |
| **Flow Capture (Moxion)** | **One-click Approve / Decline** in the Information panel and the Player; counts are tallied; "View details" shows who decided and when; bulk approve on a multi-selection; a hidden batch acts as an approval step before release. | [Asset status](https://help.moxion.io/article/641-asset-status), [Jul 2025 release](https://help.moxion.io/article/665-2025-07-late-july-release), [Playlists](https://help.moxion.io/article/603-playlist-beta) |
| **Vimeo Review** | A **version menu** keeps each iteration *with its own time-coded notes*, upload time and size; Approve stamps the version with a timestamp. | [Version history](https://vimeo.com/blog/post/video-version-history), [Review page](https://help.vimeo.com/hc/en-us/articles/12426192100113-Video-review-page-) |
| **Filestage** | Statuses In review / Needs changes / Approved; **who decided and when** for each version; compare puts two versions side by side *with both comment sets*; the comment list works as a to-do to check that feedback was met. | [Versions](https://help.filestage.io/en/articles/7872784-chapter-3-managing-versions), [Feedback met](https://help.filestage.io/en/articles/9113215-how-to-verify-that-everyone-s-feedback-has-been-met) |
| **Krock.io** | A version sits *inside a production stage*, so history, comments and status move together; an overlay line; an **auto-compare that detects and highlights visual differences**; comments pinned to the waveform. | [Krock vs Frame](https://krock.io/blog/krock-vs-frame/), [Proofing](https://krock.io/video-proofing/) |

**What all seven share:** (1) media is the hero, with metadata in a side panel; (2) the version number is on the media and opens the stack; (3) notes are plotted on the timeline and navigated with keys; (4) compare has 2–4 modes on one linked clock; (5) status is a closed vocabulary stamped with who and when; (6) J/K/L, `←/→`, I/O and `?` are the keyboard standard.

## 3. What the board does today (read from `current/unit_ep12.png`, `unit_ep17.png`, `templates/unit.html`)

1. **The master is a 300 px player** on the left of a band, below Health, with a black first frame (`unit_ep12.png`
   y≈480–780). The 2.5-minute film the whole unit exists for is smaller than the take grid.
2. **The iterations are bare links**: `iter1 · iter2 … iter7` (unit.html:68). There is no stack, no compare and no
   badge showing which one is current, and `master_r2v.mp4` is byte-identical to iter7 without the page saying so.
3. **18 of 24 take tiles render as empty paper** in the screenshot. Tiles use `<video preload="none"
   poster="…shot_NN.png">` (unit.html:15, unit_view.py:258–259), and each poster is a **full 1024² PNG of ~1.6 MB**.
   That is 24 × 1.6 MB ≈ 38 MB before one take plays. `/thumb/{codex}/320/` already exists (thumbs.py) but the
   tiles do not use it.
4. **Faults sit apart from the media they accuse.** "faces ×1 master" is a chip (unit.html:69). The fact behind it is
   in `eye_faf11c8f.json → rubric.faces.evidence.under = [6]`. Shot 6 occupies frames 1080–1213, so the fault is at
   **45.00–50.58 s** of the master, yet nothing on the player shows it.
5. **Dead versions are invisible.** T10 went through 3 failed attempts (`attempts/T10_fail1..3.mp4`), each with a
   reason in `learnings.jsonl` ("rotation at T10: 7.6deg turned"). The page shows only the survivor.
6. **The lightbox and the redo prefill are good** (unit.html:19–29, 187–191): the plan text, faults and "redo this
   shot" with the step, artefact and note filled in. They are the seed of the shot review below. Keep both.
7. **Hover play loads the whole mp4** (unit.html:208). That is acceptable at 1–3 MB per take, but there is no scrub,
   and the first hover after the page opens waits on the network.

## 4. The proposal — five components, each tied to the files

### 4.1 Screening room (master as hero) — unit page, finished or with a master

Layout at ≥1100 px: a two-column grid, `minmax(0,1fr) 340px`. The player column is square (all output is 1:1) and is
**640 px tall at most, 100 vw minus 32 px on phone**. The right column holds tabs **Faults | Versions | Lines**.
Placement: the screening room goes directly under the unit head once the master exists. Health moves below it.

Under the player sit **three lanes in one SVG**, all sharing the x-scale `frames → px` (3846 frames across the width):

| lane | height | reads | draws |
|---|---|---|---|
| shots | 18 px | `qc_r2v.json edit.segments[i].start,n` | 24 abutting cells labelled `06`, fill `--paper-2`, rule `--rule-2`. Hover shows the shot's poster from `/thumb/…/160/storyboard/shot_06.png` and its `plan.shots[6].section` |
| faults | 14 px | gate verdicts mapped to shots (below) | range bars in `--accent` with a ⚑ glyph at the start, MASTER faults on top, EYE_TAKES faults beneath. Never colour alone: glyph plus `title` text |
| lines | 10 px | `qc.lines[i]` + line start times | ticks: ✓ `--ok` when `passed`; ✕ `--accent` when `error_rate>0` |

A playhead (2 px `--ink`) and a timecode `00:45:00 · f1080 · shot 06` sit in tabular mono.

**How faults map to time.** Each step is deterministic and has a test:
- When a fault names shots (`faces.evidence.under:[6]`, PLAN `invented [0,1,5,8,22]`), each shot maps to `segments[shot]`
  as `[start/24, (start+n)/24]`.
- When a fault names characters (MASTER `identity ×2: artilleryman, unnamed_first_person_narrator`), map it through
  `plan.shots[i].faces` to every shot showing that face. Draw these as a thinner bar so that "character-wide" reads as
  different from "this shot".
- When a fault is take-level (`T05.dq.json gates[]` with `ok:false`), put it on that take's segment.
- Panel faults (EYE_PANELS `landmark ×520`) **do not go on the master**. They belong to the panel stack (4.3).
  Putting 520 marks on the timeline would turn it into noise.

**Fault list (right tab)**: grouped by gate, sorted by time (SyncSketch's "by frame"); a row reads `⚑ faces · shot 06 · 0:45–0:50 · h 0.102 < wall 0.12` (numbers from `evidence.closes[]`); click seeks and loops the range (Frame.io); `↑/↓` move between rows.

**Header strip above the player** — one line in mono:
`master_r2v.mp4 = iter7 · faf11c8f · 160.25 s (plan 155.54) · LUFS −14.15 ✓ · peak −1.51 ✓ · cuts 23/23 · lines 23/23`.
Every field is already in `qc_r2v.json`.

**Approval stamp** — a bordered box in the top-right corner of the player:
`MASTER ⚑ FLAGGED · judge:master_eye@1 · 26 Sep 02:14 · faces n`. The word is printed (`FLAGGED`/`PASSED`) and so is
the glyph; the border is `--accent` or `--ok`. This combines the Moxion, Filestage and Vimeo stamps: who, when and
verdict, never colour alone. The stamp must read the verdict file. It must never be written by the page; the owner's
hand stays `/act/*` only (memory: "never sign verdict files by hand").

**Poster.** Do not show a black frame zero (ep12 opens on a title fade). Use a frame from
`review/contact_faf11c8f.png` or `/thumb/…/320/storyboard/shot_00.png`.

### 4.2 Version stack and compare — master iterations, takes, panels

**Version badge.** It sits on the media's top-left, the way Frame.io puts the number on the player: `v7 ▾` for the
master and `T10 · try 4 ▾` for a take. Opening it lists the stack newest first:

```
v7  iter7   18:49  faf11c8f  ⚑ faces            ← current (= master_r2v)
v6  iter6   18:22  —         no verdict kept
…
v1  iter1   07:31  —
```
For a take: `try 4 T10.mp4 ✓ pass · try 3 T10_fail3 ✕ "rotation 7.6deg" (move_type) · try 2 … · try 1 …`. The reasons
and actions come from `learnings.jsonl` rows where `gate=EYE_TAKES` and `note` contains `T10`, matched by attempt.

**Compare** opens on `C` or the ⇄ button. It has three modes on one clock:
1. **Side by side.** The default. Two square players, each 50 % of the width, linked by one `requestAnimationFrame` loop
   that sets `b.currentTime = a.currentTime` whenever the gap exceeds half a frame (1/48 s). Each side keeps its own
   lanes, so the iter1 faults sit above the iter7 faults (SyncSketch's requested "ghost mode").
2. **Wipe.** Stacked players, with the top one clipped by `clip-path: inset(0 0 0 X%)`. The handle is a 2 px `--ink`
   bar, dragged or moved with `,` and `.`. Use this for "did the face get bigger": it is the RV / Frame.io overlay.
3. **Flip (A/B).** `Tab` swaps which player is visible, and the same frame stays shown. This is the best mode for
   noticing a change in place.

Pixel difference only for **stills** (panel r1 vs current), via a canvas `difference` composite, because a canvas
diff of a playing video is costly and adds little.

**Picking the pair.** Defaults: master current vs previous; take survivor vs last failure; panel current vs `superseded/r3`. `Shift+click` in the stack picks any other A or B.

**Which shots changed.** "iter1 vs iter7" is mostly a question of *which shots changed*. Today only the latest
`qc_r2v.json` survives, so the board **cannot** answer it. Recommendation (to the episode step, not the board): the
`edit` step writes `cut/master_iterN.cut.json` with that iteration's `cut_manifest` (rel_path, bytes per take).
Comparing two of those manifests names the changed shots, which can then be tinted on the shot lane. This is the
cheap, exact version of Krock's "auto-compare highlights differences".

**Cost.** Masters are **~259 MB each** (`cut/master_iter*.mp4`). Two of them over `127.0.0.1` with HTTP Range work,
because Starlette's `FileResponse` serves ranges. Always use `preload="metadata"`. Proxies are not needed.

### 4.3 Shot strip — the 24 shots as a contact sheet, one column per shot

This replaces the separate Panels and Takes grids. There is **one row of shot cards**, and each card is a mini stack:

```
┌ 06 ──────── medium_close ┐
│ [take poster 160px]      │   ← hover = scrub (4.4); click = shot review (4.5)
│ panel ▫ take ▫ in master │   three dots: ✓ / ⚑ / ○ per stage, glyph not colour
│ try 2 · ⚑ faces          │   latest version + worst fault
└──────────────────────────┘
```

- **Grid.** `repeat(auto-fill, minmax(148px,1fr))`, gap 8 px. That gives 6 per row at 1000 px and **2 per row at
  400 px** (phone). The card's status border is 2 px: `--accent` when flagged, otherwise `--rule`.
- **Filters**, which already exist as `data-filter`, become `all · ⚑ flagged · retried · changed since vN`.
- **Running units** (ep17) show slots for shots not shot yet (as today, dashed `--rule-2`). A slot fills in as
  `panels/` and `takes/` land. This is the live contact sheet the owner wants: "what it looks like so far".
- The **strip PNG** (`reports/strip_T00_T23.png`, 960×7680) and the contact sheet become links in the band head.
  They are not the primary view.

### 4.4 Hover scrub without loading the video

Frame.io-style scrub: the pointer's x across the card picks a frame. The source is a **sprite**, not the mp4:
- **Now, at no cost:** `takes/work/content/TNN_0..2.png` (three frames per take, 768²) already exist. Through
  `/thumb/…/160/`, three frames make a coarse first/mid/last scrub, which is enough to see a freeze or a drift.
- **Better:** add width-160 **8-frame sprite** rendering to `thumbs.py`. Run `ffmpeg -vf fps=…,scale=160:-1,tile=8x1`
  in process; ffmpeg is at `C:\Users\vishn\bin\ffmpeg`. Use the same LRU and immutable URL keyed by mtime. That is
  about 25 KB per take as WebP against 1–3 MB of mp4.
- Click or Space plays the real take (the current behaviour). On touch devices there is no hover, so a tap opens the
  shot review.
- Replace the posters with `/thumb/{codex}/320/storyboard/shot_NN.png`, which fixes item 3 of §3 (38 MB → ~0.5 MB).

### 4.5 Shot review (the lightbox, grown) and "redo this shot"

Keep the `<dialog>` (unit.html:174). Make it a three-column review at ≥1000 px, stacked on phone:

| panel (current; ⇄ r3) | take (survivor; stack ▾) | the shot in the master (seek to segment, loop) |
|---|---|---|

Below the three columns go the plan text that exists today (`frame`, `motion`, `camera`) and the fault rows, each
with its evidence numbers. Last comes **one primary button: `Redo shot 06 ▸`** (`R`).

Redo flow. It keeps today's prefill and adds the review-tool pieces:
1. `R` opens an inline note box above the button. It is prefilled from the fault rows, as today
   (`data-note`), and the step is picked from the medium: panel → step 08, take → step 09.
2. `Enter` posts `/act/redo` (unchanged endpoint, unchanged casebook row).
3. The stack shows a **ghost version at once**: `try 3 · queued · your note "…"`, in a dashed `--rule-2` border.
   The receipt is the order id. This is the Frame.io placeholder pattern: the redo is *visible where the next version
   will land*, not only in the Orders column.
4. **Multi-select.** `X` marks a shot card (the Frame.io checkbox key). A sticky bar then appears:
   `3 shots marked · Redo 06, 11, 16 ▸`. This feeds the existing `.picks` shot checkboxes (unit.html:148) and is
   Moxion's bulk approve, turned to its use here.

No approve button. Judges sign, and the owner audits (memory: judges replace the eye). The board's "approve" is
therefore **not redoing**; the stamp in 4.1 shows the judge's verdict.

### 4.6 Keyboard map (shown by `?`, a modal using the existing `<dialog>` styling)

| key | action | precedent |
|---|---|---|
| `Space` / `K` | play / pause | Frame.io, SyncSketch |
| `J` / `L` | back / forward, ×1 ×2 ×4 | NLE standard |
| `←` / `→` | one frame (1/24 s); `Shift` = 1 s | all |
| `Alt+←/→` or `,`/`.` with no compare open | previous / next **cut** (segment boundary) | RV `Alt+arrows` |
| `↑` / `↓` | previous / next **fault** marker | SyncSketch |
| `[` / `]` | previous / next shot card or lightbox item | Frame.io |
| `1`…`7` | jump to master version vN | (new; 7 iterations fit) |
| `C` | compare open / close; `Tab` flip A/B; `W` wipe mode | Flow `t`, RV `F6` |
| `I` / `O` | loop in / out; `\` clears | Frame.io, RV |
| `R` | redo this shot (note box) | — |
| `X` | mark shot for batch redo | Frame.io checkbox |
| `F` | fullscreen; `M` mute | all |
| `?` | this sheet | Frame.io, SyncSketch |

Keys are ignored while focus is in a `form`, `textarea` or `dialog` input. This is the same guard the htmx polls
already use (unit.html:162).

**Frame accuracy.** `currentTime` stepping is not frame-exact in browsers. Step with
`currentTime = (f + 0.5)/24`, and read the shown frame with `requestVideoFrameCallback` (`metadata.mediaTime`;
[MDN](https://developer.mozilla.org/en-US/docs/Web/API/HTMLVideoElement/requestVideoFrameCallback)) so that the
timecode reads `f1080` and not a rounded guess.

## 5. Per page

- **Unit, finished (ep12).** Screening room (4.1) at the top → shot strip (4.3) → Gates (as text, now each row linked
  to markers) → Health → Actions. Panels fold into the shot cards; there is no separate panel grid.
- **Unit, running (ep17).** The live card stays at the top. Below it, the shot strip shows slots filling (4.3). The
  master section shows `none yet`, as now. Before panels exist (ep17 is in `02 plan`), the strip shows **plan cards**:
  `shot 06 · medium_close · artilleryman`, taken from `plan.shots`. The owner then sees the shot list being written.
- **Department / book.** Each episode row gets a 48 px poster (`/thumb/…/160/`, shot_00 or the master's
  contact frame), a `v7` badge and the MASTER stamp glyph. That is the Frame.io grid-card metadata, chosen per card.
- **Floor / home.** A "latest picture" thumbnail on a running unit's row (newest file in `storyboard/` or
  `takes/r2v/` by mtime) answers "what it looks like so far" at a glance.

## 6. Tokens and states (all from `architecture/index.html :root`; no new colours)

| state | glyph | border / fill | text |
|---|---|---|---|
| pass | ✓ | `--ok` / `--ok-bg` | PASSED |
| flagged | ⚑ | `--accent` / `--paper` | FLAGGED |
| failed version | ✕ | `--rule-2` dashed, picture at 60 % opacity | try 3 ✕ + reason |
| queued redo | ↻ | `--rule-2` dashed | queued |
| not yet | ○ | `--rule` | — |
| QC numeric | — | `--qc` / `--qc-bg` | LUFS, peak |
| invented (PLAN) | ⚑ | `--invent` / `--invent-bg` | invented |

- **The player well.** The player sits on a dark surface in both themes: `--lead` with the ink colour `--lead-ink`
  in light, which is already a token. Every review tool uses dark around the picture, because a light surround
  distorts how the frame's contrast is read. The rest of the page stays paper. This is the one place where the
  film-tool look overrides the paper look, and the reason is perceptual, not taste.
- **Lane text** is 11 px mono, `--ink-2`, and meets 4.5:1 contrast on `--paper-2` (both themes are already used that
  way by `.shotchip`).

## 7. Publishable artefact (standing goal)

The pieces in 4.1, 4.2 and 4.4 together make a **dependency-free `<review-player>` web component**. It would provide
the square or any-aspect player, the shot, fault and line lanes from a JSON of ranges, linked compare with
side-by-side, wipe and flip, a frame-exact timecode via `requestVideoFrameCallback`, sprite hover-scrub, and a J/K/L
keymap. All of that fits in one vendored JS file under 15 KB and works with htmx.

Nothing equivalent ships as a small open-source drop-in. Frame.io and SyncSketch are hosted products; openrv-web is
a whole application. The component would be useful to anyone reviewing AI-generated video against automated judges.
Name: `judge-lanes` or `review-player`; ship it on GitHub and npm (it can still be consumed vendored, without a build
step). Build it in its own repository and vendor it in, rather than writing it into `templates/unit.html`.

## Top 10 recommendations for this board

1. Unit: make the master the hero. Square player up to 640 px, dark well, header strip from `qc_r2v.json`, placed above Health.
2. Unit: draw a shots lane from `edit.segments`, and a faults lane mapped shot→frames, under the master; `↑/↓` jump between faults.
3. Unit: turn `iter1…iter7` into a version stack with a `v7 ▾` badge; say `master_r2v = iter7`.
4. Unit: add compare (side by side, wipe, flip on one clock) for master iterations, take tries and panel revisions.
5. Unit: merge the Panels and Takes grids into one 24-card shot strip with per-stage ✓/⚑/○ and a try count.
6. Unit: fix the blank take tiles. Posters come from `/thumb/…/320/` (≈38 MB → ≈0.5 MB on ep12).
7. Unit: hover-scrub from 3 existing content frames now; an 8-frame ffmpeg sprite in `thumbs.py` later.
8. Unit: grow the lightbox into a panel | take | in-master shot review, with `R` redo, a ghost "queued" version, and `X` batch.
9. Unit/dept/book: approval stamp = judge verdict + who + when + glyph + word. It is read-only and never signs.
10. Episode step (data, not UI): write `cut/master_iterN.cut.json` per iteration, so "iter1 vs iter7" can name the changed shots.

## 3 disagreements I expect with other researchers

1. **Media before status.** Ops and SaaS researchers will want the live card, the health band and the step rail on
   top. I put the screening room above Health on any unit with a master. A finished unit's question is "is it good",
   and the answer is a picture; running units keep the live card on top.
2. **A dark well inside a paper page.** The editorial/paper researcher will want one surface. I hold that the player
   (only the player) sits on `--lead`, because of how contrast is perceived around a frame, and every review tool
   studied does this.
3. **No approve button.** Review-tool convention (Moxion, Filestage, Vimeo) says the owner gets Approve/Decline. On
   this board the judges sign and the owner's only hand is redo / hold / bump, so I propose stamps that report and do
   not decide. Someone will argue for an owner "accept" verdict; that is an owner decision for `docs/DECISIONS.md`,
   not a UI choice.
