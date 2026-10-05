# V07 — Navigation: inside the viewer, across pages, and Home in the sidebar

Researcher V07, 2026-10-04. Scope: how the owner moves "between images and videos" in the in-page viewer,
what each click on each page opens, deep links + Back, and the sidebar's Home. Read against
`mockups/assets/unit.js` (the shot view `#sv`, `openShot`/`nav`/`wireKeys`, lines 704–805),
`assets/shell.js` (NAV, CHORDS, palette), `book.html`, `books.html`, `index.html`, `dept.js`, and
the real ep12 (655 files) and ep17 trees.

## 1. The brick

A viewer has exactly one state: a **cursor = (sequence, index, depth)**.

- A **sequence** is an ordered list of items of one kind (Shots, Takes, Grids, Masters, Files).
- **← / →** move *across* the sequence (index ± 1). **↑ / ↓** move *into the depth of the same thing*
  (depth ± 1). **1–5** change sequence and keep the subject where it exists (pivot).
- Everything else (counters, filmstrip, hash, Back) is a rendering of that cursor.

Check that it regenerates what nobody stated: "shot 10's third failed take" = (Takes, T10, fail3) —
no new key. "The bank grid before revision r3" = (Grids, bank_2x2, r3) — no new key. "Which master
played shot 05" = press `4` from (Shots, 05) — pivot puts you on v7 at 0:21. The current shot view is
already the special case (Shots, i, stage) with ↑/↓ as stage; we generalise it rather than add modes.

Second brick, for pages: **a click on an entity face (book, unit, character row) navigates; a click on
a media item inside a unit opens the viewer.** Space on any focused face = *peek* (the viewer over the
current page, Linear/Arc peek, research 03 R13).

## 2. Outside evidence

| Product | What it teaches | Source |
|---|---|---|
| Frame.io V4 viewer | `←/→` and `[`/`]` move between assets in the project/collection without leaving the viewer; on **video**, `←/→` frame-step (Shift = 10 frames) and only `[`/`]` move assets. Prev/next controls top-right. `?` lists keys. | https://help.frame.io/en/articles/10535490-move-smoothly-in-the-viewer-with-asset-navigation , https://help.frame.io/en/articles/9105337-keyboard-shortcuts |
| Frame.io version stack | Versions are a stack *on* the asset, not siblings in the folder; `S` splits to compare inside a stack. → our depth axis. | https://help.frame.io/en/articles/4431-version-stacking-and-comparison-mode-legacy |
| Frame.io 2026 nav | "Home now routes to a new All Projects page"; workspace landing pages + breadcrumbs. Home = the top of *your* work, not a dashboard of everything. | https://blog.frame.io/2026/01/08/new-in-frame-io-interactive-zips-access-requests-and-a-faster-way-to-get-around/ |
| Linear | No item called Home: **Inbox** is first, then My issues; `G I` chord. The first sidebar item *is* the home, whatever it is named. | https://linear.app/docs/inbox , https://linear.app/docs/my-issues |
| Vercel (Feb 2026 default) | Tabs moved into a resizable left sidebar; same items at team and project level; mobile gets a floating bottom bar. | https://vercel.com/changelog/dashboard-navigation-redesign-rollout , https://vercel.com/changelog/new-dashboard-navigation-available |
| Next.js photo-modal pattern | An overlay gets a real URL; Back closes it; a cold-opened link has no history, so the close control must not depend on `history.back()`. | https://nextjs.org/docs/app/api-reference/file-conventions/intercepting-routes , https://dev.to/ahmed_mahmoud360/parallel-routes-and-intercepting-routes-in-the-nextjs-app-router-field-notes-on-the-photo-modal-56ko |
| SyncSketch / RV (research 02) | `[`/`]` next item, `,`/`.` frame step, `?` sheet; J/K/L is NLE transport. | research `02_media_review.md` §4.6 |
| Prior ruling | "Lightbox keys ←/→ in the filtered grid order, ↑/↓ across stages, URL hash per item, Back closes, preload neighbours as pictures only." | research `08_media_grids.md` §4.4–4.5 |

## 3. The five sequences (tabs `1 Shots · 2 Takes · 3 Grids · 4 Masters · 5 Files`)

Real counts from ep12 (finished) / ep17 (running, 07 board, 22 panels, no takes yet).

| # | Sequence | ← / → over | ↑ / ↓ depth | ep12 items | Files it opens |
|---|---|---|---|---|---|
| 1 | **Shots** | shot 00 → 23 (plan order) | stage: panel → staged → take → master segment | 24 × 4 | `storyboard/shot_NN.png`, `storyboard/h3/shot_NN.png`, `takes/r2v/TNN.mp4`, `cut/master_iter7.mp4#t=t0,t1` (segments from `qc_r2v.json`) |
| 2 | **Takes** | T00 → T23, kept takes | attempts: kept → fail1 → … failN (newest first) | 24 kept + 11 fails (T10 has 3) | `takes/r2v/TNN.mp4`, `takes/r2v/attempts/TNN_failK.mp4` |
| 3 | **Grids** | `layout.json` order (hill 2x1 → … → water 1x1 s20) | revision: current → `superseded/r3` → `r2` → `r1` → `hand_layout`, matched by setup | 12 current + ~21 superseded | `storyboard/grids/*.png` (+ its `.json`/`.txt` in the side panel) |
| 4 | **Masters** | v7 → v1, **deduped by hash** (iter7 = iter5 = master_r2v shows once, chip "= iter5") | none (iterations *are* this sequence) | 6 distinct of 8 files | `cut/master_iter*.mp4`, `review/contact_faf11c8f.png` as poster |
| 5 | **Files** | pipeline order: plan → plan.verdict → layout → panel_dq → panel_content → `storyboard/eye_*` → `takes/r2v/prompts.json` → shots/stills → `takes/r2v/eye_*` → `qc_r2v.json` → `review/eye_*` → learnings/timing → run logs | none; `n`/`N` jump between search hits inside a file | ~20 unit files + this unit's run logs | the JSON/JSONL pretty-printed; logs from `logs/<codex>/episode/<codex>__episode__<ts>.log` matched to the unit's runs |

Rules:
- **Pivot on switch.** `2` from (Shots, 05, panel) → (Takes, T05, kept). `3` → the grid whose
  `shots` include 5 (`layout.json`). `4` → v7 seeked to shot 05's `t0`. `5` → `prompts.json` scrolled
  to `"index": 5`. No match → index 0 of the new sequence, toast "no grid holds shot 05".
- **Per-item JSON is not in Files.** Files lists unit-level files. A media item's own JSON
  (`TNN.content.json`, `TNN.dq.json`, `TNN.graph.json`, its `prompts.json` entry, the grid's `.json`
  + `.txt` prompt, the plan shot) lives in the item's **side panel**, toggled with `P` ("prompt").
  This answers "json files of prompts viewable" in 1 key from the picture, without leaving it.
- **Filter inherits.** If the page's shot grid is filtered (`⚑ Master 4`), Shots opens with the same
  filter as a removable chip `⚑ Master · 4 of 24`; ←/→ walk only those (as today's ruling says).
- **No wrap.** ←/→ stop at the ends with a 120 ms bump (today's `nav()` wraps modulo 24 — change it:
  wrapping silently in a 24-list loses place). Home / End jump to first / last.
- **Running unit.** Items not yet made (ep17 shot 22, every take) show as dashed slots in the
  filmstrip, are skipped by ←/→, and a new arrival never moves the cursor: a pill "shot 22 drawn ·
  End" appears instead.

## 4. Keys (inside the viewer; inert in inputs; the shell's `g`-chords and `j/k` are suspended)

| Key | Action |
|---|---|
| `←` `→` · `[` `]` · `k` `j` | previous / next item (all items, **video included**) |
| `↑` `↓` | depth: stage / attempt / revision |
| `Home` `End` | first / last item of the sequence |
| `1`–`5` | switch sequence (pivot) |
| `Space` | play / pause the one video |
| `,` `.` | one frame back / forward when paused (1/24 s); `Shift+,`/`.` = 1 s |
| `P` | side panel: this item's prompt + JSON (toggle) |
| `O` | open the original in a new tab (`/lib/<codex>/<rel>`) |
| `C` | copy the relative path (`episodes/ep12/takes/r2v/T10.mp4`; never an absolute path in the page) |
| `R` | redo this shot (kept from today) |
| `F` | fullscreen the media pane |
| `/` | search inside a Files item; `n`/`N` next/previous hit |
| `?` | key sheet for the viewer |
| `Esc` | close the innermost layer (search → side panel → viewer) |

Where this departs from Frame.io: arrows move items even on a video. Our videos are 2–8 s takes and
segments the owner flips through; frame stepping is a QC act, rarer, so it gets `,`/`.`.

## 5. Chrome: counter, tabs, filmstrip

```
┌ Shots 1 · Takes 2 · Grids 3 · Masters 4 · Files 5 ─────────── ← 6/24 → ── P  O  ✕ Esc ┐
│ Shot 05 · take · try 1 of 1 · EYE_TAKES ✓                    panel ○ staged ○ take ● master ○ │
│                         [ media, square, min(74vh, 62vw) ]       │ side panel 320 px (P) │
│ ▸ ▣ ▣ ▣ ▣ ▣ [▶] ▣ ▣ ▣ … ▣  filmstrip, 56 px, current ringed --focus, type icon bottom-left │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

- **Counter grammar**: `<subject> · <depth word> · <depth position>` then the gate state, and the
  sequence position `i / n` beside the arrows.
  - Shots: `Shot 05 · master · 0:21.4–0:25.9 · MASTER ⚑ faces` — depth dots `panel ○ staged ○ take ○ master ●`.
  - Takes: `T10 · fail2 · try 2 of 4` / `T10 · kept · try 4 of 4`.
  - Grids: `bank 2x2 · shots 13 14 15 17 · rev r3 of 2 earlier · superseded`.
  - Masters: `v7 · iter7 = iter5 · 2:40.25 · 25 Sep 18:49 · MASTER ⚑ 3`.
  - Files: `takes/r2v/prompts.json · 24 entries · 9 / 21`.
- **Filmstrip**: thumbnails at 160 (`/thumb/<codex>/160/<rel>`), 56 px squares, 4 px gap, horizontally
  scrolled to keep the cursor centred; type icon (image · film · braces · scroll-text for logs);
  a depth badge `+3` on items with attempts/revisions; flag dot amber. Files tab shows a 32 px-row list
  instead of thumbs. Click = jump; it is a `role="listbox"` with `aria-activedescendant`.
- **Tabs** show counts (`Takes 24 ·11 fails`), `role="tablist"`; disabled when empty (ep17 Takes 0, Masters 0).
- **Phone (≥ 400 px)**: full-screen sheet; swipe ←/→ = items, swipe ↑/↓ on the media = depth, pull
  down from the header = close; filmstrip 44 px; tabs become a segmented control that scrolls.
- **One video**: the viewer borrows the page's single `VIDEO` (`parkVideo()` already does this);
  opening pauses the Screen player, closing returns it. Neighbours preload as pictures only.

## 6. What each click opens

| Page | Element | Click | Space (peek) |
|---|---|---|---|
| Unit · finished (ep12) | shot card, take half | Shots · NN · take | — |
| | shot card, panel half | Shots · NN · panel | — |
| | fault list row / lane marker under Screen | Shots · NN · master | — |
| | version badge `v7 ▾` | Masters · v7 (stack menu stays for compare) | — |
| | Props → Files links (today `target=_blank`) | Files · that file | — |
| | gate chip (`EYE_PANELS ⚑`) | Files · that verdict JSON (`storyboard/eye_c7e3eb93.json`) | — |
| | run in the matrix / Activity log line | Files · that run's log, scrolled to the line | — |
| Unit · running (ep17) | hero "newest grid" poster (today links `#shots`) | Grids · newest | — |
| | panel tile in the running strip | Shots · NN · panel | — |
| Book (season wall) | poster | unit page | viewer, sequence **Season**: posters ep01…ep17, ↑/↓ = that unit's masters; header button "Open ep12 ↗" |
| | season matrix cell | unit page `#runs` | — |
| Book (cast shelf) | character card | viewer, sequence **Cast** (shelf order, `refs/characters/*/sheet.png`), ↑/↓ = sheet versions; side panel = the `refs.json` row + "used in" episodes | same |
| Now | hero poster / Needs-you card / Up-next / shipped shelf poster | unit page | viewer on that unit's newest media (master or newest grid) |
| | Needs-you flag chip (`MASTER ⚑ 3`) | unit page with `#view=shots/NN@master` of the first flagged shot | — |
| Department | 36 px face / row | unit page | viewer on the face's media |
| Books | live-book mosaic tile | book page | viewer, Season of that book |

Cross-unit sequences (Season, Cast) use the same viewer with tabs hidden; they are the only ones
on non-unit pages. The board is still pages for entities and an overlay for media.

## 7. URL hash and Back

- Grammar: `#view=<seq>/<id>[@<depth>][&t=<sec>][&p=1]` — ids are stable names, not indices:
  `#view=shots/05@master&t=21.4`, `#view=takes/T10@fail2`, `#view=grids/ep12_grid_bank_2x2@r3`,
  `#view=masters/iter7`, `#view=files/takes/r2v/prompts.json&L=120`, `#view=cast/ogilvy`.
  Old `#shot-05` maps to `#view=shots/05@take` (keep inbound links working).
- **Open = `pushState`** (one entry). **Moves inside = `replaceState`**, so one Back closes the viewer
  instead of rewinding 24 shots. **`popstate` with no `view=` closes** it. Esc / ✕ close by
  `history.back()` only if the viewer pushed the entry itself; on a cold deep link (no entry to go
  back to) they `replaceState` to the bare page — the Next.js caveat.
- Page sections keep their own hashes (`#gates`, `#runs`); `view=` is parsed as a key in the hash so
  `#runs&view=…` is impossible to confuse.
- In the htmx build: hash only, no server route; the server renders the page, `media.js` opens the
  viewer from the hash. Files are fetched from `/lib/<codex>/<rel>` (GET, ranges), never decoded.

## 8. Home vs Now in the sidebar

Decision: **rename "Now" to "Home"; same page (`index.html`), first item, `house` icon.**

- The page already *is* home: the brand mark links to it (`sb-mark href="index.html"`), SPEC.md
  names the zooms "studio (home) → book → …", research 03 has `G H home`. The owner did not see it
  as home because it is labelled with a time word. A second page would split "what needs me" in two.
- Linear's first item is Inbox, Frame.io's Home is "your projects", Vercel's first item is the
  team overview: in all three, **the first sidebar item is home and there is one of it**.
- Changes: NAV `{id:'home', ic:'house', l:'Home', h:'index.html', k:'G H'}`; keep `G N` as an alias;
  page title "Home", the live hero keeps the word "Now" as its section label ("Now · on the GPU");
  phone bottom tab `Home`; palette entry "Home — the GPU, needs you, up next"; `data-page="home"`
  (accept `now`). Inbox stays second (`index.html#needs` today; its own page later).

## Top 8 recommendations

1. Build the viewer as one cursor `(sequence, index, depth)`; ←/→ across, ↑/↓ depth, 1–5 pivot.
2. Five unit sequences — Shots, Takes, Grids, Masters (hash-deduped), Files — plus Season and Cast off the unit page.
3. Arrows (and `[ ]`, `j k`) always move items, including on video; frame step on `,`/`.`.
4. `P` opens the item's own prompt + JSON beside the picture; Files holds only unit-level files and logs.
5. Counter grammar `subject · depth · position` + `i / n`; filmstrip of 160 thumbs with type icons and `+N` depth badges.
6. Click an entity → its page; click media → the viewer; Space on any face → peek.
7. `#view=seq/id@depth`: pushState on open, replaceState inside, popstate closes, cold links close by replaceState; `#shot-NN` aliased.
8. Sidebar: rename Now → Home (same page, first item, `G H`), keep "Now" as the hero's label.

## 2 disagreements I expect

1. **Arrows on video.** The media-review camp (02, Frame.io) wants ←/→ to frame-step a video and only
   `[ ]` to change item. I chose items everywhere, because the owner asked to "navigate between
   images and videos" and our clips are seconds long; QC frame-stepping moves to `,`/`.`.
2. **Home as a rename.** The IA camp will argue for a new studio-level Home (books, departments,
   totals) with Now as a separate live page. I hold that two homes split "needs you" and that the
   owner's "add home" is about the label and the first slot, not a missing page; revisit if he
   then asks for a studio overview.
