# 08 — Media grids, thumbnails and playback in the browser

Researcher 08, 2026-10-04. Scope: how the board shows panels, takes, strips and masters: grids,
hover-scrub, posters, lazy loading, the lightbox, one shot followed through its stages, the
master iteration compare, a master timeline with shot boundaries and fault markers, and a season
wall. Everything below was measured on the real ep12 media (read-only) and on the running board
at 127.0.0.1:8700 (GETs only).

## 1. What is actually on disk (ep12, War of the Worlds)

| Artefact | Count | Pixels | Size | Duration / notes |
|---|---|---|---|---|
| `storyboard/shot_NN.png` (panel) | 24 (+4 in `superseded/`) | 1024×1024 RGB | 1.5–1.9 MB each, **37 MB** total | also `storyboard/h3/shot_NN.png` (24): the picture H3 was actually staged with |
| `storyboard/contact.png` | 1 | 1536×1024 | 2.7 MB | panel contact sheet |
| `takes/r2v/T??.mp4` | 24 | 768×768, h264 High, 24 fps, AAC 32 kHz | 0.55–2.9 MB, **38 MB** total | 3.75–8.71 s; **one keyframe per take** (the whole take is one GOP); `moov` before `mdat` (faststart) |
| `takes/work/guard_T??_{0,1,2}.png` | 72 | 768×768 | ~1.1 MB each | three guard frames per take, written by `assemble.py` |
| `reports/strip_T00_T23.png` | 1 | 960×7680 | **13 MB** | `take_strip.py`: one row per take, three 320 px cells (first third, middle, last third) |
| `cut/master_iter1..7.mp4` + `master_r2v.mp4` | 8 | 1536×1536, h264 12.7 Mb/s, AAC 48 kHz | **~260 MB each, 2.0 GB** | 160.25 s; 25 keyframes (≈6.4 s GOP); faststart |
| `review/contact_faf11c8f.png` | 1 per episode (16 eps) | 1280×1536 | 3.3 MB | the master eye's 30 frames, one every 5 s, 5×6 grid of 256 px |
| `qc_r2v.json` | 1 | — | — | `planned_cuts` (23 boundaries), `seen_cuts` (27: three extra at 111.79/111.88/111.96 inside shot 16), `lines[]` with `heard`/`passed` |

Other facts that change the design:
- **`master_iter5.mp4` and `master_iter7.mp4` are byte-identical** (same md5 `80dc87dd…`;
  `master_r2v.mp4` has the same byte count). Two of seven "iterations" are the same film. An
  iteration compare that does not dedupe by hash will show the owner a no-op as a change.
- All 16 War of the Worlds masters together: **18 GB** in `*/cut/*.mp4`.
- Plan ↔ take ↔ panel join is by index (`plan.shots[11]` ↔ `shot_11.png` ↔ `T11.mp4`), and the
  master segment is `planned_cuts[10]..planned_cuts[11]` = **75.04–79.50 s** for shot 11
  (the take is 5.17 s; the cut uses 4.46 s of it). Shot 0 starts at 0; the last shot ends at
  `planned_seconds` (155.54); the title card runs 155.54–160.25.
- Fault sources with a shot number: the MASTER eye (`review/eye_<sha8>.json`, e.g. `faces`
  evidence `under: [6]`), EYE_PANELS / EYE_TAKES verdicts, `panel_dq.json`, `T??.content.json`,
  `T??.dq.json`; with a time: `qc_r2v.seen_cuts − planned_cuts` (unplanned cuts), `lines[].passed`.

## 2. What the board does today, and what it costs

`studio/command_center/templates/unit.html` already has the right skeleton: 120 px tiles, a
`<dialog id="lightbox">` cloned from per-tile `<template>`s with ←/→/Esc, hover-play takes with
`preload="none"`, and a master `<video preload="metadata">` with iteration links. Measured gaps:

1. **The panel grid loads the full PNGs.** `tile()` builds `t.url` with `artefact_url` (the
   `/lib/` route), so the ep12 unit page pulls **37 MB of PNG** to draw 24 tiles of 120 px. The
   `/thumb/` route already exists (`thumbs.py`, in-process WebP LRU, 64 MB cap, immutable URL)
   and serves the same panel at 160 px in **5.6 KB** (320 px: 18 KB; cold render 1.8 s, warm
   28 ms). The live card uses it; the unit grid does not. A ×2000 saving, zero new machinery.
2. **Take posters are the panel PNG** (`unit_view.pictures_band`: `poster = panels[index].url`),
   i.e. another 1.8 MB per take and — worse — *not the take*: the panel is a reference input, the
   take may have reframed or changed subject. A poster must be a frame of the take.
3. **The strip (13 MB PNG) is shown as an `<img>` only before takes exist** and a link after.
   It is in fact a ready-made sprite sheet: row *i* = take *i*, three cells. Nobody uses it as one.
4. **The master `<video preload="metadata">` points at a 260 MB file.** On localhost with Range
   (verified: `/lib/` answers `206 Partial Content`, `accept-ranges: bytes`, Starlette 1.6.0)
   this is fine for playback; it is the wrong source for any *preview* (season wall, timeline
   hover, iteration thumbnails).

## 3. The rule that generates the rest (the brick)

**Never decode video to show a still; never create a `<video>` for something the owner is not
watching.** Every grid, hover and timeline preview reads a *picture* (WebP thumb or sprite cell);
exactly **one** `<video>` exists per surface, and it is created/moved on intent (hover dwell,
click, keyboard). The derivations below all follow from it:

- Chrome refuses to create more than a fixed number of `WebMediaPlayer`s per frame (the exact
  cap varies by version and platform; one write-up reports 50 since Chrome 92 — "Blocked attempt
  to create a WebMediaPlayer as there are too many WebMediaPlayers already in existence"), and
  each one is heavy in renderer + GPU memory. A book page with 16 episodes × 24 takes = 384
  `<video>` tags would hit it; the season wall with 16 masters would hold 16 decoders for nothing.
  ([chromium review](https://groups.google.com/a/chromium.org/g/media-dev/c/wEUYR7BvdZI/m/R-8X1EdiBAAJ),
  [MDN preload](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/preload))
- Seeking a take by `currentTime` decodes from frame 0 every time (one GOP per take): cheap for
  one 768² take, wasteful as a hover gesture repeated across 24 tiles. Seeking the master lands
  up to 6.4 s from a keyframe at 1536² — measured in OpenCV: 81 seeks every 2 s took **10.2 s**.
  So scrub previews come from sprites; the `<video>` seeks only when the owner lets go.
- Sprites over many small images: one request, better compression, no per-thumbnail latency —
  the convention every player uses (WebVTT cues with `image.jpg#xywh=x,y,w,h`).
  ([Vidstack loading/thumbnails](https://vidstack.io/docs/player/core-concepts/loading/),
  [Vidstack Thumbnail](https://vidstack.io/docs/player/components/display/thumbnail/),
  [FFmpeg + WebVTT sprite how-to](https://dev.to/masonwritescode/build-scrub-bar-thumbnail-previews-with-ffmpeg-and-a-webvtt-sprite-3ei2),
  [Plyr previewThumbnails](https://www.npmjs.com/package/plyr?activeTab=readme))

## 4. Components

All sizes in CSS px; colours are the existing tokens in `architecture/index.html :root`
(`--paper`, `--ink`, `--rule-2`, `--code`, plus the board's state tokens); no new hues.

### 4.1 `MediaTile` (panel, take, master — one component, three kinds)
- Square, `aspect-ratio:1/1`, grid `repeat(auto-fill, minmax(var(--tile,128px),1fr))`, gap 6.
  Density toggle S/M/L = 96/128/192 (`--tile`), remembered in `localStorage` (try/catch). Phone
  (≥400 px): 3 columns, unchanged from today's rule at `base.html:281`.
- Picture: `<img src="/thumb/{codex}/{w}/…?v={mtime}" width height loading="lazy"
  decoding="async">`, `w = 160` for S/M, `320` for L and for DPR ≥ 2 via `srcset`.
  Explicit `width/height` so the grid never reflows while pictures arrive.
- Overlay (bottom-left, mono 11 px on a 60 % `--ink` scrim): `T11` / `shot 11` · size (`close`) ·
  duration for takes (`5.2 s`, from `cut.json`/probe). Top-right: fault badges, max 3 + `+n`, each
  a glyph **and** a word (`⚑ faces`), never colour alone. Flagged tiles get a 2 px inset outline
  in the gate's flagged token plus the ⚑, so it survives greyscale.
- States: `missing` (dashed `--rule-2` border, label "not drawn"), `waiting` (slot, as today),
  `rendering` (the live card's develop-in filter), `superseded` (40 % opacity, "old" tag),
  `duplicate` (for masters equal by hash: "= iter5").
- Focusable (`tabindex=0`, `role="button"`, `aria-label="take T11, close, 5.2 seconds, flagged
  faces"`); Enter/Space opens the lightbox; arrow keys move focus in the grid (roving tabindex).

### 4.2 Hover-scrub without loading 24 mp4s
Two layers, in this order:
1. **Sprite scrub (instant, zero video):** on `pointermove` over a take tile, pick cell
   `k = floor(x / width × N)` and set `background-position` on a sprite `<div>` above the `<img>`.
   Source: a per-episode **take sprite** — 24 rows × N cells. Today's `strip_T00_T23.png` already
   is N=3 (start/middle/end), which is exactly the "did it freeze, churn, reframe" read the skill
   asks for; served through a new thumb variant (`/sprite/{codex}/{rel}` → 160 px cells, WebP)
   it is **282 KB** for all 24 takes (measured), vs 38 MB of mp4. A 12-cell variant (measured:
   **76 KB per take**, 1.8 MB for 24) gives a smooth scrub. A 2 px progress tick under the tile
   shows `k/N`.
2. **Play on dwell:** after 400 ms of stillness (or focus + Space), the page moves its **single
   shared `<video muted playsinline preload="auto">`** into that tile, sets `src`, seeks to the
   scrubbed time, plays. `pointerleave` pauses and returns it to a hidden parking slot. One
   decoder for the whole grid; `src` swaps are cheap on localhost (a take is ≤ 3 MB).
- `prefers-reduced-motion`: no autoplay on dwell; the sprite scrub still works (it is a still).
- Touch (phone): no hover — tap opens the lightbox; long-press scrubs the sprite.

### 4.3 Posters
- Panel tile: the panel thumb (160/320 WebP).
- Take tile: **the take's own middle frame**, i.e. sprite cell `N/2` (or `guard_T11_1.png`
  thumbed), never the panel. Showing the panel as the take's face is the "gates are not quality"
  trap in UI form: it hides a take that drifted from its panel.
- Master tile: a contact-sheet cell from `review/contact_<sha8>.png` (cell at 30–40 % of the
  runtime, a story frame, not the title card) — already on disk for all 16 episodes.

### 4.4 `Lightbox` (`<dialog>`, no library; extend the existing one)
- Layout ≥ 900 px: media left (square, `min(78vh, 62vw)`), text right 320 px: plan `frame` /
  `motion` / `camera`, faults with source and gate, the path, "redo this shot". < 900 px: stacked.
- Keys: ←/→ previous/next **in the current filtered grid order** (today's behaviour, keep it),
  ↑/↓ **move across stages for the same shot** (panel ⇄ h3 staged ⇄ take ⇄ master segment, see
  4.5), `Space` play/pause, `,`/`.` step one frame (1/24 s) when paused, `F` toggle the flagged
  filter, `C` copy the absolute path, `Esc` close. Show the key legend in the footer (today:
  "← → move · Esc closes"). The URL hash follows (`#take-T11`), so a link reopens the lightbox
  and Back closes it.
- Focus returns to the originating tile on close (the `<dialog>` does it if `showModal()` is
  used; keep it). Preload neighbours as **pictures only** (`new Image()` of the ±1 thumbs at
  1024), never neighbour videos.
- Polls already pause while a dialog has focus (`[!document.activeElement.closest('form,dialog')]`);
  keep that guard on every new partial.

### 4.5 `ShotStrip` — "shot 11 across its stages"
One row, opened from any tile (`↑/↓` in the lightbox or a "stages" tab), four squares:

`[panel shot_11.png] → [staged h3/shot_11.png] → [take T11 5.17 s] → [master 75.04–79.50]`

- Each square shows its verdict glyph (EYE_PANELS, EYE_TAKES, MASTER) and the timestamp it was
  written (mtime), so a re-drawn panel newer than its take shows "panel newer than take ⚠".
- The master square plays the master `<video>` with a media fragment `#t=75.04,79.5` (native,
  no server work; the browser stops at the end time). Reads: `qc_r2v.planned_cuts`.
- Under the row: the plan text and the faults that name shot 11 from every source (§1), grouped by
  gate. This is the single most useful view for "why does shot 11 look wrong": it shows at
  which stage it went wrong.
- Film analogue: ShotGrid/Flow's version history per shot and Kitsu's per-shot task row, where a
  shot is the row and each department's latest version is a column.
  ([Kitsu docs](https://kitsu.cg-wire.com/), [Flow Production Tracking versions](https://help.autodesk.com/view/SGSUB/ENU/))

### 4.6 `MasterTimeline` — scrubbable, with shot boundaries and fault markers
A 48 px band directly under the master player, full width of the player:
- **Shot lane (28 px):** 24 segments from `planned_cuts`, width ∝ duration; each shows its shot
  sprite cell as a background (cover) and the label `11` on hover/focus. The title card is the
  final hatched segment. A 1 px `--paper` gap marks each cut.
- **Marker lane (12 px) above it:** diamonds at fault times — an MASTER-eye fault on shot *n* is
  a marker spanning its segment; unplanned cuts (`seen_cuts − planned_cuts`: 111.79, 111.88,
  111.96, i.e. a flash inside shot 16) are ticks; a failed line (`lines[i].passed == false`) is a
  ▲ at the line's start. Glyph per kind + the word in the tooltip; never colour alone.
- **Hover:** a 160 px preview above the pointer from the master sprite (contact sheet every 5 s
  today; every 1 s if pre-generated, §5), time `01:15.6 · shot 11`. **Click/drag release:** seek
  the one `<video>` there. Arrow keys on the focused band step one shot; Shift+arrow 1 s.
- The playhead line spans both lanes; the current shot's segment gets a 2 px `--ink` underline,
  and the take grid above highlights `T11` while it plays (two-way link: hovering T11 in the grid
  lights segment 11).
- Precedent: Frame.io's comment markers on the scrub bar, NLE timelines with clip thumbnails,
  Vidstack's slider-thumbnail/chapters.
  ([Frame.io player](https://help.frame.io/en/articles/9101068-the-frame-io-player),
  [Vidstack slider chapters](https://vidstack.io/docs/player/components/sliders/slider-chapters/))

### 4.7 `IterationCompare` — master_iter1..7
- Default: a row of iteration cards `iter1 … iter7, r2v` with poster, mtime, duration, size,
  `sha8`, and **a "= iter5" chip on iter7** (dedupe by size then hash; hash computed once and
  cached by (path, mtime, size) — 260 MB md5 is ~0.5 s, never per request).
- Compare mode (pick two): side by side (≥ 1100 px) or a **wipe** (one `<video>` per side is the
  only time two decoders exist; both `muted` except the chosen one; a single shared clock: on
  `timeupdate` of A, if |A−B| > 1/24 s set B.currentTime). Under the pair, a **diff of the
  timelines**: shot segments that changed (different `planned_cuts` span or a different take
  hash) are marked, so "what did iter6 change" is answered by geometry before anyone watches.
- What changed between iterations is better read from data than from frames: if the take hashes
  and the cut list are equal, the card says "audio/mix only" and the wipe is pointless. That
  needs `cut.json` per iteration (today only the latest is kept in `takes/work/cut.json`): see §6.

### 4.8 `SeasonWall` — the masters of a book
- Grid of master tiles, 1:1, `minmax(160px,1fr)`, ordered by episode; tile = poster (§4.3) +
  `ep12` + title + duration + MASTER/RENDER verdict glyphs + published ✓.
- Hover scrubs the contact sheet (30 cells, already on disk for all 16 eps) — **no video on the
  wall at all**. Click opens the unit page at its master, or the lightbox with the one player.
- A "lanes" alternative (one row per episode: 24 shot cells from the take sprite middle frames)
  turns the wall into a season-long continuity check — the camera-variety and unique-look rules in
  memory are judged exactly that way. Offer as a toggle, not default.
- Never `preload` on the wall: 16 × 260 MB = 4 GB of potential `metadata`/buffer requests.

## 5. What has to be pre-generated, and by whom

| Derived picture | Size (measured / est.) | Who makes it | Where |
|---|---|---|---|
| panel / staged thumb 160, 320 WebP | 5.6 / 18 KB | **board, in-process** (`thumbs.py`, exists) | LRU, nothing on disk |
| take sprite from existing strip (3 cells) | 282 KB per episode | **board, in-process** (PIL resize of a 13 MB PNG: 0.29 s) | LRU — a new `/sprite/` variant of `thumbs.py` |
| master hover sprite from `contact_<sha8>.png` | ~120 KB | **board, in-process** | LRU |
| take sprite 12 cells, take middle-frame poster | 76 KB / take | **pipeline step** (`take_strip.py` grows a `--cells 12 --webp` mode) | `reports/sprites/T??.webp` |
| master sprite 1 cell/s + WebVTT | ~160 frames × 160 px ≈ 0.6 MB | **pipeline step** (`qc` or `deliver`) | `cut/master_<sha8>.sprite.webp` + `.vtt` |
| per-iteration `cut.json` + sha8 | < 10 KB | **assemble** at write time | `cut/master_iterN.cut.json` |

Rules: **the web process stays read-only and runs no ffmpeg and no video decode.** Image resizes
of files that already exist are fine in-process (bounded, ≤ 0.3 s, cached, deterministic). Video
decoding is not: 10.2 s of CPU per master sprite, and the GPU box is often busy rendering — a
board request must never compete with H3 for minutes. The pipeline already decodes every take
(`take_strip.py`, `assemble.py` guard frames) and every master (master eye contact), so the
sprites are a by-product of steps that run anyway, written next to their sources under
`library/<book>/…` with relative paths (architecture invariant). If a sprite is missing, the UI
falls back down the chain: 12-cell sprite → 3-cell strip → poster only → label only. Never a
spinner that waits on a file nobody will write.

## 6. Players: native vs Plyr vs Vidstack

| | Native `<video>` + ~150 lines vendored JS | Plyr 3.x | Vidstack (web components) |
|---|---|---|---|
| Vendoring without npm | nothing to vendor | 1 JS + 1 CSS from cdnjs/jsdelivr, ~100 KB | CDN bundle exists, but the docs and theming assume a bundler; larger |
| Sprite/VTT thumbnails on seek bar | write it (§4.6 needs custom lanes anyway) | yes (`previewThumbnails.src`) | yes (`<media-slider-thumbnail>`, chapters) |
| Custom lanes (shots, faults) | yes, it is our markup | fight its DOM | possible via slots, learning curve |
| Theming to the paper tokens | trivial | CSS variables | CSS variables |
| Accessibility of controls | native controls are accessible | good | good |
| Keyboard map of §4.4 | ours | partial, collides | partial |

Recommendation: **native `<video controls>`** for playback, plus one vendored script
`static/media.js` (shared player mover, sprite scrub, timeline lanes, lightbox keys). The
board's distinct value is the shot/fault lanes, which no player gives; a player library would
contribute only a seek-bar thumbnail we must draw anyway. Revisit Plyr only if the owner wants
custom-skinned controls. (Sources: [Plyr](https://github.com/sampotts/plyr),
[Vidstack](https://vidstack.io/), [MDN video](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/video).)

## 7. Performance budget for the ep12 unit page (finished)

| | Today | Proposed |
|---|---|---|
| Panel grid 24 tiles | 37 MB PNG | 24 × 5.6 KB = 135 KB |
| Take posters | same 37 MB (shared URL) | sprite 282 KB (or 1.8 MB for 12-cell) |
| Take videos | 0 until hover; one decoder per hovered tile, never released | 1 shared decoder |
| Master | 260 MB via Range, metadata only until play | same (it is the deliverable), plus a ~0.6 MB sprite |
| Strip | 13 MB PNG when shown | folded into the take sprite |
| `<video>` elements in DOM | 24 + 24 (templates) + 1 | 1–2 |

Caching: thumbs/sprites keep the existing `?v=mtime` + `immutable` scheme; `/lib/` media keep
`no-cache` + ETag (verified present) so a re-rendered take is picked up after an `edit` step.

Source note: Kitsu/Flow/Frame.io/Vidstack-chapters links (§4.5–4.6) are cited from knowledge, not
fetched; Chromium, MDN, Vidstack, Plyr, [Starlette Range→206](https://starlette.dev/responses/) were checked.

## 8. Things the data cannot answer today (flag, do not invent)

- No per-iteration cut list: iteration compare can only diff by hash and duration until assemble
  writes `cut/master_iterN.cut.json`.
- Shot ↔ time mapping for line markers needs the line start times (in `timeline`/plan audio
  data, not in `qc_r2v.lines`); without them, failed lines go to the shot lane, not a time.
- Superseded panels (`storyboard/superseded/`, 4 files) have no link to the shot they replaced
  beyond the filename; the ShotStrip's "history" column would need that link written.

## 9. Publishable note

The "one decoder, sprite-first" media grid + shot-lane/fault-lane timeline for AI-generated
episodes is generalizable: a standalone, dependency-free `media-review.js` (vanilla, ~5 KB) that
reads a JSON of shots, cut times and faults and renders the lanes over a native `<video>` would be
a small public package (npm + jsdelivr), and the sprite-from-pipeline convention (VTT `#xywh`)
plugs into it. Name: e.g. `shotlane`. Flagged as a candidate public artefact.

## Top 10 recommendations for this board

1. Unit page: switch panel tiles from `/lib/` PNG to `/thumb/160|320` WebP (37 MB → 135 KB).
2. Unit page: take posters = the take's own middle frame (sprite cell), never the panel.
3. Unit + book pages: one shared `<video>` element moved on hover-dwell/click; no per-tile video.
4. Unit page: sprite hover-scrub on take tiles from the existing `strip_T00_T23.png` via a new in-process `/sprite/` thumb variant.
5. Unit page: `MasterTimeline` under the player — shot lane from `planned_cuts`, fault lane from eye/QC, sprite hover, seek on release.
6. Unit page: `ShotStrip` (panel → staged → take → master segment via `#t=`) on ↑/↓ in the lightbox.
7. Unit page: iteration cards deduped by hash (iter7 = iter5 today), compare/wipe only for distinct films.
8. Pipeline (not web): `take_strip.py` and qc/deliver write 12-cell take sprites and a 1 s master sprite + VTT; the board never decodes video.
9. Book page `/b/{codex}`: `SeasonWall` of master posters scrubbing the existing contact sheets, zero video on the wall.
10. All pages: lightbox key map (←/→, ↑/↓, Space, `,`/`.`, F, C, Esc), URL hash per open item, glyph+word fault badges, reduced-motion respected.

## 3 disagreements I expect with other researchers

1. **Native `<video>` over Plyr/Vidstack.** A "premium" look researcher will want a skinned
   player; I hold that the board's value is the shot/fault lanes, which no player provides, and
   that a library adds weight and keyboard collisions for a seek-bar thumbnail we draw anyway.
2. **No ffmpeg / video decode in the web process, ever.** An ops/perf researcher may propose
   lazily generating posters/sprites on first request "with a cache"; I argue it competes with the
   GPU renders for CPU for seconds-to-minutes, and the pipeline already decodes every frame it
   needs — sprites belong to the steps, with a fallback chain in the UI.
3. **Takes before panels, and the take's own frame as its face.** A film-tool researcher
   (ShotGrid-style "latest version thumbnail") may want one thumbnail per shot that silently
   becomes the newest stage; I want every stage visible side by side (ShotStrip), because the
   question the owner asks is *where* a shot went wrong, and a single "latest" thumbnail hides it.
