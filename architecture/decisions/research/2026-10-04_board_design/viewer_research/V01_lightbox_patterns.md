# V01 — Lightbox / media viewer patterns, applied to the unit and book pages

Researcher V01, 2026-10-04. I studied ten viewers: Frame.io, Google Photos, Apple Photos, Lightroom Classic loupe, Figma, Notion/Linear, PhotoSwipe v5, GLightbox, Fancybox and ShotGrid/Flow's Overlay Player. I applied them to the real files of War of the Worlds ep12 (finished) and ep17 (running), and to the v2 mockups (`mockups/unit-finished.html` + `assets/unit.js`, whose `#sv` shot view and `#cmp` compare are already `<dialog>`s).

## 1. The brick

Every viewer I studied rebuilds from one record:

> **viewer = (sequence, index) → renderer[kind](item) + panel(item)**, opened *from* an origin element and
> closed *back to* it; the URL names `(sequence, item)`.

Everything else derives from that record. Arrows and the counter come from `index ± 1` over `sequence`. The filmstrip is the sequence drawn small. Mixed media is `renderer[kind]`. The info panel is `panel(item)`. Return-focus is the origin. A deep link is the URL. The record also tells the board what it needs. The board does not need "a lightbox for pictures", a JSON popup and a log popup. It needs **one dialog with four renderers** (image, video, json, text) and a **sequence the caller hands it**. The rest of this report is the details.

## 2. What the tools do (with sources)

| tool | overlay or page | chrome | navigation | zoom / pan | mixed media | metadata | close | URL |
|---|---|---|---|---|---|---|---|---|
| **Frame.io V4** | page (player route) | file name top bar; right panel comments/props | `⌘⇧←/→` next asset; `←/→` when the asset slider is open | `T` fit, `Y` fill, `+/-` double/halve, `⌘0` / `Shift+click` 100 %, `Shift` hold = loupe, `Z`+drag marquee, `⌘`+scroll fluid | images, video, PDF in one player | Properties panel, status | back to grid; `Esc` leaves fullscreen | own route per asset |
| **Google Photos (web)** | route that renders as a full-window overlay over the grid | thin top bar; actions on hover | `←/→`, hover arrows at edges | `+/-`, click to zoom | photos and videos in one stream; video autoplays | `i` toggles a right info panel (name, size, resolution, device) | `Esc`, ← back arrow | `/photo/<id>`, so Back closes |
| **Apple Photos (Mac)** | in place of the grid (a mode) | toolbar | `←/→` | pinch, `⌘+/-` | photos, videos, Live Photos | `⌘I` Info window | **Space** or Esc closes, **Space** opens | — |
| **Lightroom Classic** | Loupe is a view mode (`E`; `G` returns to grid) | filmstrip toggled with `F6`; `I` cycles the info overlay at top-left | `←/→` along the filmstrip | `Z` toggles fit ⇄ 1:1; `⌘=/-` | stills (video limited) | info overlay + right panels | `G` / `Esc` | — |
| **Figma** | canvas | — | — | the standard: `Shift+1` fit, `Shift+0` 100 %, `Shift+2` selection | — | — | — | — |
| **Notion / Linear** | overlay | close plus download/open-original | arrows step through a block's or issue's attachments | click zoom | images; video plays inline in the doc | none | `Esc`, click outside, ×; Notion: **Space** toggles | none |
| **ShotGrid / Flow Overlay Player** | **overlay on the tracking page** (Screening Room is the full page) | player plus a **Details pane** of the Version's fields | playlist next/prev | — | versions (movies, frames) | Details pane, fields chosen by the site | × / Esc | page URL unchanged |
| **PhotoSwipe v5** (MIT, ESM) | overlay | top bar: counter, zoom, close; caption is DIY | `loop: true`, `arrowKeys: true`, swipe, `preload: [1,2]` | `imageClickAction: 'zoom-or-close'`, `doubleTapAction: 'zoom'`, ctrl+wheel | **images and raw HTML only; no video plugin** ("you can't swipe over iframes") | none | `escKey`, `closeOnVerticalDrag: true`, bg click | via plugin |
| **GLightbox** (MIT, 11 KB gz) | overlay | close / prev / next; description slot | arrows, swipe | zoom-drag on mobile/desktop | YouTube, Vimeo, self-hosted video (through Plyr), inline HTML | description slot | Esc, × , backdrop | none |
| **Fancybox 5** | overlay | toolbar, 3 thumbnail styles, **Sidebar plugin** (two columns) | arrows, thumbs | Panzoom component | images, video, iframe, HTML | sidebar | Esc, overlay click, × | **Hash plugin** |

Sources: [Frame.io image viewer](https://help.frame.io/en/articles/9105322-image-viewer-in-frame-io), [Frame.io shortcuts](https://help.frame.io/en/articles/9105337-keyboard-shortcuts), [Frame.io player](https://help.frame.io/en/articles/9105311-player-page-features), [Google Photos shortcuts](https://www.guidingtech.com/google-photos-keyboard-shortcuts/) / [DefKey](https://defkey.com/google-photos-2026-shortcuts), [Apple Photos keys](https://support.apple.com/guide/photos/keyboard-shortcuts-and-gestures-pht9b4411b24/mac), [Lightroom Classic keys](https://helpx.adobe.com/lightroom-classic/help/keyboard-shortcuts.html), [Figma zoom](https://help.figma.com/hc/en-us/articles/360041065034-Adjust-your-zoom-and-view-options), [Notion images](https://www.notion.com/help/images-files-and-media), [Notion keys](https://www.notion.com/help/keyboard-shortcuts), [Flow Overlay Player details pane](https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/How-to-configure-which-fields-are-shown-in-Overlay-Player-Details-Pane-in-Flow-Production-Tracking.html), [PhotoSwipe getting started](https://photoswipe.com/getting-started/), [options](https://photoswipe.com/options/), [click actions](https://photoswipe.com/click-and-tap-actions/), [custom content](https://photoswipe.com/custom-content/), [GLightbox](https://biati-digital.github.io/glightbox/), [Fancybox](https://fancyapps.com/fancybox/), [Fancybox license](https://fancyapps.com/license/), [MDN `<dialog>`](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/dialog).

**What they agree on:** (1) the media is on black and fills the window; (2) `←/→` move and a counter shows
`n / N`; (3) **Esc and ×** always close, and so does a backdrop click everywhere except the pro tools, where there is no backdrop; (4) info is a **toggled right panel** (`i` in Google Photos, `I` in Lightroom, `⌘I` in Apple, Details in Flow); (5) zoom is **fit ⇄ 1:1** on one key or a double-click, with ctrl/⌘+wheel for fluid zoom; (6) neighbours preload as **pictures, never videos**.

**Where they split:** a page (Frame.io, Lightroom) or an overlay (Google Photos, Flow Overlay Player, Notion). The owner asked for "popup on the page but not a new page", so the overlay wins. Google Photos shows how an overlay can still be linkable: it owns a URL and Back closes it.

## 3. Libraries: verdict — build it, borrow PhotoSwipe's defaults as the spec

- **Fancybox is out.** Its licence is proprietary and paid, and "you may not use the Software in Open Source projects". That conflicts with the standing goal of shipping this board publicly.
- **PhotoSwipe** is the best image engine, but it **requires width/height up front** and **has no video**. Half of our items are mp4s or JSON.
- **GLightbox** does video by pulling in **Plyr**, a second library with its own controls. That breaks the board's single-`<video>` mover (`VIDEO` / `parkVideo()` in `unit.js:692–702`).
- **The board already has 80 % of it.** `#sv` and `#cmp` are `<dialog>`s opened with `showModal()`. That gives inert background, Esc → `cancel`, `::backdrop` and focus return for free (MDN). The page already moves one `<video>` around.

So I recommend a **vendored, ~250-line `viewer.js`** with no dependency. It would adopt PhotoSwipe's defaults as the written spec: `loop`, `escKey`, `arrowKeys`, `returnFocus`, `trapFocus`, `preload [1,2]`,
`closeOnVerticalDrag`, `imageClickAction: zoom-or-close`, `doubleTapAction: zoom`, `wheelToZoom` behind ctrl. That fits the "no npm, vendored small JS" rule. It is also the generalisable piece, which §8 flags.

## 4. The component — `<dialog id="mv" class="mv">`, one for every page

### 4.1 Layout (Studio black always, both palettes, because media is judged on black)

```
┌ top bar 48px ─────────────────────────────────────────────────────────────────────┐
│ ‹ T06 (crumb, only when drilled in) · takes/r2v/T06.mp4 · [video] 5.2s  7 / 24  ⓘ ⎘ ↗ ✕│
├──────────────────────────────────────────────────────────────┬────────────────────┤
│ ‹                         STAGE (black)                     › │ INFO 360px (I)     │
│        image: fit; video: native controls; json: tree;       │ tabs: About|Prompt │
│        text/log: mono lines                                   │ |Verdict|Raw       │
├──────────────────────────────────────────────────────────────┴────────────────────┤
│ filmstrip 64px: ▢▢▢▣▢▢▢… (thumbs /thumb/160, videos get a ▶ corner, json a {} tile)│
└───────────────────────────────────────────────────────────────────────────────────┘
```

- **Size**: `width:100vw;height:100dvh;max-width:none;margin:0`. This is a viewer, not a card; the existing `#sv` takes 96vw × 94vh. Stage = `grid-template-columns: minmax(0,1fr) var(--mv-info, 360px)`. Info hidden → `0`.
- **Top bar** (left → right): the drill crumb (§4.6); the **rel path** in mono, middle-truncated (`takes/r2v/T06.mp4`), never an absolute path, per the invariant; a kind chip with its key fact (`video 5.2 s`, `png 1024²`, `json 88 KB · 24 rows`, `log 18 KB`); the counter `7 / 24` (`aria-live="polite"`); then the buttons **ⓘ info (I)**, **⎘ copy path (C)**, **↗ open original** (`/lib/…` in a new tab), **✕ close (Esc)**. Every button is 32 px with an `aria-label` and `title` naming its key.
- **Edge arrows**: 48 × 96 px hit zones on the stage edges, visible on hover/focus, always on touch-less pointer:fine. Hidden when `N = 1`.
- **Filmstrip** (Lightroom `F6`, Fancybox thumbs): 64 px tall, `/thumb/160/` images, current item outlined 2 px `--focus`, `scrollIntoView({inline:'center'})` on every move. Toggle with `T`. **Hidden under 700 px** and for sequences of 1.
- **Info panel**: 360 px. Its open state persists in `localStorage['mv.info']` (try/catch, per-viewer convenience only). Under 700 px it becomes a bottom sheet at 45 dvh with a drag handle.

### 4.2 Renderers — exactly what each file opens as

| kind | items on ep12 (measured) | renders as | load strategy |
|---|---|---|---|
| **image** | panels `storyboard/shot_00..23.png` (1024², ~1.7 MB); grids `storyboard/grids/*.png` (13; 2048² up to **7.2 MB**, `woods_3x1` 3072×1024); staged `storyboard/h3/shot_NN.png`; contact `review/contact_faf11c8f.png` (1280×1536, 3.3 MB); cast `refs/characters/*/sheet.png` (**3072×2048, 5.8 MB**) | `<img>` fit-contain, `decoding="async"` | show `/thumb/320/<rel>` **instantly**, scaled up as a placeholder (PhotoSwipe's `msrc`), then swap to `/lib/<rel>` on `load`. Preload ±1 originals with `new Image()` (never ±2: 7 MB grids) |
| **video** | takes `takes/r2v/T00..23.mp4` (~1 MB), failed tries `takes/r2v/attempts/T10_fail1..3.mp4` (11 files), masters `cut/master_iter1..7.mp4` (**259 MB**) | the page's **one** `VIDEO`, moved into the stage; `controls`, `preload="metadata"`, `poster` = `/thumb/320/takes/work/content/TNN_1.png` (masters: `review/contact_<sha>.png` crop) | never preload a neighbour video; pause on every move; master opens with `#t=` when it came from a shot. Range requests already served by `/lib/` |
| **json** | `takes/r2v/prompts.json` (88 KB, 24 rows), `takes/r2v/shots.json`, `storyboard/grids/*.json` (275 B), `plan.json` (43 KB), `plan.verdict.json`, `eye_*.json`, `qc_r2v.json`, `TNN.{dq,content,graph}.json`, `panel_content.json` | collapsible tree built from `<details>`/`<summary>`, depth-2 open, key in `--stage-ink-2`, strings wrapped, long `prompt` strings shown as paragraphs; a **`/` search box** that filters keys/values; **Raw** toggle = `<pre>` | `fetch('/lib/<rel>')`, `JSON.parse`; files > 1 MB render Raw only |
| **text / log** | grid prompts `storyboard/grids/*.txt`, `learnings.jsonl` (28 KB), `timing.jsonl`, `drive_run0N.log`, `logs/<codex>/episode/*.log` (4–18 KB) | mono `<pre>`, line numbers, **`.jsonl` one row per line with the row's `gate`/`action` as a gutter chip**; level colouring (`ERROR`, `WARN`) with glyph + word, never colour alone | fetch whole file (< 1 MB on disk today); "tail" button jumps to end; for ep17 (running) a ↻ reload, no polling inside the dialog |

`viewer.js` dispatches on extension: `png|jpg|webp → image`, `mp4|webm → video`, `json → json`,
`jsonl|log|txt → text`. These kinds are a closed vocabulary, and a test asserts the mapping.

### 4.3 Navigation

- `←/→` previous/next **in the sequence the caller passed**, i.e. the visible (filtered) grid order, as `#sv` does today. `Home/End` go to first/last. **Wrap on** (PhotoSwipe `loop:true`, and the `nav()` of today's shot view). On wrap the counter flashes, so the jump is not silent.
- On a video, arrow keys **still navigate**: the dialog's keydown handler runs before the native control's seek. `Shift+←/→` seeks ±1 s, and `,` / `.` step one frame (1/24 s) while paused (Frame.io/RV). `Space` plays and pauses. `J/K/L` are deliberately **not** bound. They would collide with the board's `j/k` list keys (SPEC) and add nothing for 5 s takes.
- Swipe left/right on touch (pointer events, 48 px threshold, cancelled when zoomed). **Swipe down closes** (PhotoSwipe `closeOnVerticalDrag`).
- `?` shows the key sheet. The footer legend matches today's `#sv` ".keys" row.

### 4.4 Zoom and pan (images only)

- Default **fit**. **`Z` or a double-click toggles fit ⇄ 1:1** (Lightroom `Z`, PhotoSwipe double-tap). It zooms about the pointer. `0` = fit and `1` = 100 % (the Figma `Shift+0/1` idea without the Shift, since there is no canvas). `+/-` double and halve (Frame.io). **ctrl/⌘+wheel** zooms fluidly (PhotoSwipe default); a plain wheel does nothing, so page scroll never hijacks.
- At more than fit, drag pans (pointer capture) and arrows pan by 10 % instead of navigating. This is the Linear/Notion convention: "while zoomed, arrow keys pan, clamped". Esc resets the zoom first, then closes on the second press.
- Why zoom matters here: a 1024² panel shows at about 700 px on a laptop, so 1:1 is a 1.46× look at the face the EYE_PANELS gate flagged. A 2048² grid at fit shows each cell at about 350 px, and 1:1 is the only way to read a cell. Implementation: one `transform: translate() scale()` on the `<img>`, about 60 lines, and no canvas.
- Zoom is reset on every item change. Each item opens at its own fit, so Lightroom's carry-over of zoom between photos is not copied.

### 4.5 The info panel — four tabs, every field from a file

| tab | for a panel `shot_06.png` | for a take `T06.mp4` | for a grid `ep12_grid_bank_2x2.png` | for a cast sheet |
|---|---|---|---|---|
| **About** | 1024² · 1.7 MB · mtime · plan `shots[6]` frame/size/setup/faces | 5.2 s · 1.1 MB · try 1 (or `try 4 · 3 failed` → attempts listed) | cols×rows, `shots:[13,14,15,17]`, seed 40559 | `refs.json` row: description, colours, dress |
| **Prompt** | the **grid that drew it**: the grid JSON whose `shots` contains 6, plus its `.txt` paragraph for that cell | `prompts.json[6]`: workflow, model, mode, seed, steps, frames, **refs as clickable links**, prompt text | the `.txt`, whole | the sheet prompt row (`refs.json`) |
| **Verdict** | `storyboard/eye_*.json` faults naming shot 6 (glyph + word) | `T06.dq.json gates[]`, `T06.content.json passed`, EYE_TAKES entry, `learnings.jsonl` rows naming T06 | EYE_PANELS per cell | refs verdict |
| **Raw** | `{}` opens the source JSON *in the viewer* (§4.6) | same | same | same |

A **prompt is never shown without its file path.** Every tab footer shows the rel path, ⎘ copies it, and
`{}` opens it. This answers the owner's request that "json files of prompts" be viewable, without a second popup.

### 4.6 Drill-in instead of a second dialog

A ref link in the Prompt tab (`episodes/ep12/storyboard/h3/shot_00.png`, a cast sheet) and every `{}` button
**push** a one-item frame onto a small stack inside the same dialog. The top bar shows `‹ T06` as a crumb.
`Backspace` or the crumb pops back to the take at the same index. `←/→` inside a drilled frame move within that frame's sequence (all of `prompts.json`'s refs, say), not the parent's. Depth is capped at 3. The tools never stack modal on modal, and `<dialog>`s stacked on each other confuse focus return.

### 4.7 Closing, focus, a11y

- **Esc** (native `cancel`; it is intercepted only to reset zoom or clear the JSON search first), **✕**, **swipe down**, and a **click on the bare black stage outside the media box** (PhotoSwipe `bgClickAction`). Implement the click as `e.target === stageEl`, not with `closedby="any"`, because that attribute is newer than `<dialog>` itself and our click target is the stage, not the backdrop. **No close on outside click while text is selected** in a JSON or log, so selecting a prompt to copy never closes the viewer.
- `showModal()` makes the page inert and returns focus to the origin tile on close. Keep `returnFocus` explicit as well (`origin.focus()`), because the origin can be re-rendered by a poll. Re-find it by `data-mv-key`.
- `aria-label` = `"Viewer: takes/r2v/T06.mp4, 7 of 24"`, updated on every move. Stage `role="img"` with `aria-label` from the plan `frame` text for pictures. Videos keep native controls. Reduced motion: no zoom tween and no slide.
- **One video**: opening the viewer calls `parkVideo()` first, so a hover-play in the grid stops. Closing parks the video back. This keeps the "one `<video>` at a time" rule.
- Polls stay paused while the dialog is open (the existing guard `!document.activeElement.closest('form,dialog')`).

### 4.8 URL state

- The hash is `#v=<set>:<rel path>`, for example `#v=takes:takes/r2v/T06.mp4` or `#v=cast:refs/characters/artilleryman/sheet.png`. It holds book-relative paths only, never absolute ones.
- **Open = `history.pushState`** once, **move = `replaceState`**, **`popstate` closes**. With this, Back closes the viewer, as in Google Photos, instead of walking through 24 items or leaving the page. Today's `#sv` uses `replaceState` only, so Back leaves the unit page entirely. Fix that in the same pass.
- On load, a `#v=` hash opens the viewer on that item. A missing file opens the viewer with "not on disk" and the path, rather than failing silently. A link pasted into Telegram reopens the exact take.

## 5. Applied: what opens what, page by page

**Unit page, finished (ep12, `unit-finished.html`):**

| click on | opens viewer with sequence | starts at |
|---|---|---|
| a panel `P` frame in a shot card | `panels` = 24 `storyboard/shot_NN.png` in filter order | that shot |
| a take `T` frame | `takes` = 24 `takes/r2v/TNN.mp4` | that take, paused at poster |
| `try 4` chip | `tries:T10` = `attempts/T10_fail1..3.mp4` + `T10.mp4` | the survivor |
| master version stack row | `masters` = `cut/master_iter1..7.mp4` (newest first, like the stack) | that iteration |
| a stamp / fault row's `{}` | that verdict JSON (`review/eye_faf11c8f.json` …) | — |
| a new **Files** section (collapsed, under Runs) | `files` = every `*.json`, `*.jsonl`, `*.txt`, `*.log` of the unit, grouped (plan, storyboard, takes, review, logs) | that file |
| grids row (new strip in Shots: 13 grid thumbs) | `grids` = `storyboard/grids/*.png` | that grid |

The **shot view (`#sv`) stays** as the approved "one shot across stages" page. Each of its three frames gets ⤢ (and a click on the frame while it is already current) to open the viewer **on that item inside its stage sequence**. Its plan/faults stay where they are. The viewer is the "look closely" layer; the shot view is the "why is shot 6 wrong" layer.

**Unit page, running (ep17):** the same sequences, but only for files that exist. While step 08 runs, panels come from the `storyboard/shot_NN.png` written so far (12 today) and the counter reads `7 / 12 so far`. The sequence is frozen at open; a ↻ in the top bar refetches it. It never grows under the user.

**Book page (`book.html`):** a poster **click still navigates** to the unit. Posters are nav cards.
`Space` on a focused poster (Apple Photos / Quick Look) or its ⤢ corner opens the viewer on `posters` = each episode's face image (`review/contact_<sha>.png` where it exists), with the info panel showing that unit's gate chips and a "Open ep12 →" link. **Cast**: a click on a character card opens `cast` = every
`refs/characters/*/sheet.png`. The About tab shows the `refs.json` row, and Versions shows `sheet_v1.png …` as a version list (Frame.io's stack). Locations get the same treatment via `refs/locations/*/`.

**Data needed (board, later; nothing in the mockup):** add `1024` to `thumbs.py WIDTHS` (today `{160, 320}`) so 7 MB grids and 6 MB sheets arrive as ~300 KB WebP and the original loads only on 1:1. Add a
`GET /ls/<codex>/<unit rel dir>` listing (name, bytes, mtime) so the Files section is not hand-coded.

## 6. Mockup implementation notes and risks

- `assets/viewer.js` (about 250 lines, 10–20-line functions: `kindOf`, `renderImage|Video|Json|Text`, `renderInfo`, `move`, `zoomTo`, `pan`, `pushFrame`, `popFrame`, `syncHash`, `onKey`) plus `assets/viewer.css` (about 120 lines, `.mv*`). One delegated listener: any element with `data-mv-set` + `data-mv-rel` opens its set. The htmx board can render the same markup later.
- Risks: `shots.json` (91 KB) has about 2,000 nodes, so render JSON children only when a `<details>` opens. A poll re-render can stale the origin, so re-find it by `data-mv-key`.

## 7. Publishable artifact (standing goal)

The viewer is **generalisable beyond this repo**: a zero-dependency, MIT, `<dialog>`-based media + JSON + log viewer with one-`<video>` discipline, a drill-in stack and hash state. No MIT library covers image + video + JSON tree + text in one sequence. PhotoSwipe has no video, GLightbox needs Plyr, and Fancybox is proprietary. Ship it as a standalone package (`dialog-viewer`, on GitHub + npm/jsDelivr) once the board adopts it.

## Top 8 recommendations

1. **One viewer, four renderers** (image, video, json, text), `<dialog id="mv">`, full-window, Studio black. Do not make a separate JSON popup or log popup.
2. **Build it; don't vendor a lightbox.** Fancybox's licence forbids open source, PhotoSwipe has no video and GLightbox drags in Plyr. Write PhotoSwipe's defaults down as the spec.
3. **The caller passes the sequence** (`data-mv-set`), in visible filter order. `←/→`, `Home/End`, wrap on, counter `n / N` in an aria-live region.
4. **Info panel toggled by `I`**, 360 px right (bottom sheet under 700 px), with tabs About | Prompt | Verdict | Raw. The Prompt tab resolves the *right* source: the grid JSON+txt for a panel and `prompts.json[i]` for a take.
5. **Drill-in stack, not stacked modals.** Refs and `{}` push a frame, and the `‹ T06` crumb or Backspace pops it.
6. **Zoom = fit ⇄ 1:1 on `Z` and double-click**, ctrl+wheel fluid, drag to pan. While zoomed the arrows pan, and Esc resets the zoom first. Thumb-first loading, then the original.
7. **Close = Esc, ✕, swipe-down, click on the bare stage** (never while text is selected). Focus returns to the origin, re-found after polls. One `<video>`: park on open and on close.
8. **`#v=<set>:<rel>` hash, pushState on open, replaceState on move, popstate closes.** Fix `#sv` to match, so Back closes the viewer instead of leaving the page.

## 2 disagreements I expect

1. **Merge the shot view into the viewer, or keep both?** A minimalist will say one dialog is enough: make "stages" a fifth sequence and delete `#sv`. I keep both. The shot view answers *why* (three stages + faults + redo), and the viewer answers *look closely* (zoom, prompt, raw). Merging them would load the viewer with redo forms and fault lists. The risk is two dialogs with near-identical keys, so the keymaps must be identical where they overlap.
2. **Wrap at the ends, and close on backdrop click.** Pro tools (Frame.io, Lightroom) stop at the ends and have no backdrop to click; consumer viewers wrap and close on a click outside. I chose wrap with a counter flash, and a close on a click on the bare stage, because the owner asked for a popup "which we can close". A reviewer stepping through 24 takes may prefer a hard stop at 24 and no accidental close. The decision is whether the board is a review tool or a gallery. Note that the existing `#sv` already wraps.
