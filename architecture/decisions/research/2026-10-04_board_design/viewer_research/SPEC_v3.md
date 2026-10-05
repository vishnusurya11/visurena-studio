# SPEC v3 — the Viewer, Home in the sidebar (ruling over V01–V10)

Owner: "add home to left panel ... click on images inside episode and view them, not a new page ...
navigate between images and videos ... json files of prompts viewable ... popup on the page which we
can close" + keep the Activity window. Implement in the mockups first (work folder), the board after.

## The brick
**One Viewer = a sequence + a position + a renderer per kind, with the recipe beside it.** Every page
hands the Viewer a sequence (shots, takes, grids, masters, files, season, cast); every item is drawn by
one of four renderers (image, video, JSON/document, log/text); the info panel beside it says why the
item looks the way it does (V01, V05, V06). One `<dialog id="viewer">`, injected once by `shell.js`
for every page (V10). No library: Fancybox's licence forbids open source, PhotoSwipe has no video,
GLightbox brings a second player (V01); hand-written `viewer.js` (~300 lines) + `docview.js` (~10 KB).

## Rulings

| point | positions | ruling |
|---|---|---|
| Container | V05 one overlay + resizable panel; V01/V10 same | **One full-window `<dialog>` (12 px inset), dark in both themes** (`--vw-*` tokens): 52 px top bar (title, kind chip, path, `6 / 24`, actions, ✕), stage with 44 px edge arrows, 84 px filmstrip of 64 px thumbs with type icons and `+N` attempt badges (hidden < 700 px), **right panel** snapping 0 / 360 px / 50 % / full (drag seam; `i` toggles). Phone: full-screen `100dvh`, panel as bottom sheet 25/60/100 %. |
| Prompt beside the picture | V05/V07 side by side; tab-only seat | **Side by side.** `P` (or the top-bar switch `Picture · Prompt · JSON …`) opens the item's own prompt in the right panel at 50 %; `Enter`/"open full" moves that JSON onto the stage scrolled to its node; `Backspace` returns. No nested popup, ever. |
| Shot view `#sv` | V01/V10 keep it; V07 it *is* the Shots sequence | **Merged.** The Shots sequence with ↑/↓ across stages (panel → staged → take → master segment) and `R` redo replaces `#sv` — one dialog, one key map, the a11y bugs of `#sv` (V08) die with it. Old `#shot-05` links still open it. |
| Navigation | V07 | ←/→ items (also `J`/`K`), ↑/↓ depth (stage / attempt / revision), Home/End, `1–5` sequence tabs `Shots · Takes · Grids · Masters · Files` with counts (disabled when empty), the same shot kept across tabs. **No wrap at the ends** (review tool, not a gallery). Inside the text pane ←/→ belong to the tree; items move with `J`/`K` there. |
| Close | V08 two-step Esc; V01 click outside | Esc closes the innermost state first (zoom → panel full → viewer); ✕; swipe down; click on bare backdrop only when no text is selected (`closedby="any"` + fallback). Focus returns to the opener. |
| History | V01/V05/V07 push one entry; V08 none | **Push one entry on open, replace while moving, Back closes** — on every screen (the phone's Back gesture closes it too, which was V08's goal). URL `#v=<seq>:<rel path>[@depth][&t=…]`; a cold deep link opens the Viewer over the page. |
| Video | V02 own `<video>`; V01/V05 borrow the page's | **The Viewer owns its own `<video>`** (borrowing throws away the screening player's 259 MB buffer, V02); "one playing at a time" is enforced by a capture-phase `play` listener; opening pauses the page player and closing restores its position without resuming. Custom controls: Space/K, L, J(−1 s), `,`/`.` frame step at 24 fps, `<`/`>` speed, O loop, M sound, T `Take ↔ In master`. Master segment = `qc_r2v.edit.segments` frames/24, stopped exactly with `requestVideoFrameCallback`. `preload=metadata` only; neighbours prefetch posters, never video. |
| Images | V09 progressive | Show the clicked 320 thumb at once, swap in the full picture (board: a new `/thumb` 1024; mockup: `/lib` original) when decoded; a late load never replaces a newer item; `Z`/double-click toggles fit / 1:1 with drag-pan; preload ±1 images (+2 in the direction of travel). |
| JSON / docs | V04 four views | **Read** (default for prompts and verdicts: long strings as wrapped prose, verdict header card, `<Picture n>` chips → `refs[n-1]`), **Table** (default for JSONL, logs, arrays of like objects; group chips e.g. `landmark 520 · framing 9`; level and "refused" chips), **Tree** (lazy children, previews), **Raw** (bytes). Search over parsed data with `n of m`; copy value / jq path / all. **Every value via `textContent` — prompts contain `<Subject 1>`, `<Picture 1>` that `innerHTML` would eat.** Fold arrays > 20 and depth > 2; open at the current item's node. Follow toggle tails a running unit's log. Token colours avoid state colours (strings lavender `#c4b5fd`, numbers rose `#f5a3c7`, keys stage ink, literals grey italic), ≥ 4.5:1. |
| Info panel (provenance) | V06 | Tabs **About · Prompt · Verdict · Raw**. About: a fate line (in the master at 36.54–45.0 s / replaced by a still / not rendered yet), faults on this shot (judge's words, grouped by kind with counts), the plan shot (size, frame, motion). Prompt: the take prompt **as run** (`TNN.graph.json`: model, LoRAs, seed) and **as it would run now** (`prompts.json`), plan-derived phrases underlined per field, and **plan words that never reached the prompt** listed under it. Attempts: reasons and failed renders as two honest ordered lists, never guessed pairs. Every field has a source chip that opens the raw file at that key; missing = "not recorded". Provenance confidence: "source uncertain" when a panel is older than its grid. |
| What opens it | V10 inventory | Shot frames, takes, failed tries, grids, cast sheets, places, posters (Space / the ⤢ chip — the poster's own click keeps navigating), judge stamps and gate chips (their verdict file), the Files section (new, unit page), file names in Activity lines and its **Full log** button. Cursor `zoom-in` + inner ring on hover. Not opened: sidebar faces; the screening player (it already is the master's viewer). |
| Activity | owner: keep | Kept as is; file names in lines become Viewer links; the Viewer's info panel lists the log lines that name the file and jumps back to that line. |
| Home | V07/V10 rename | **"Now" becomes "Home"**: first sidebar item, house icon, `G H` (keep `G N`), page heading, crumbs, phone tab; the live hero keeps "Now" as its own label. |
| Mockup data | V09 | The mockups cannot fetch JSON from :8700 (no CORS) and logs are not served at all → **snapshot** the needed JSON/prompt/log files read-only into `mockups/data/<ep>/…` and point the Viewer there; pictures and video keep coming from `:8700/thumb` and `:8700/lib`. |
| A11y | V08 | `showModal()`, `aria-live` "Shot 06 of 24, take, 6.2 s, ⚑ faces" debounced 250 ms; alt from plan `frame`; captions VTT from `audio/lines/lines.json` + shot starts; two-tone focus ring; reduced motion = hard cuts, no autoplay; `aria-keyshortcuts` on every button; a "still" respect; 44 px touch targets; swipe ←/→, down; never `100vh`. Fix the V08 bug list (keys leaking behind dialogs, focus lost on each move, Tab trap in compare, toast behind backdrop, Esc losing a redo note, T labelled "takes"). |

## For the board later (not the mockup)
`/thumb` 1024 width; `/lib` honours `If-None-Match` (304) and versioned URLs immutable; `/json`
slice (JSON pointer / row range, gzip, ≤ 256 KB); `/log` tail (≤ 64 KB, paging back); a `/logs/`
read-only root; a 1-shot provenance cache. Pipeline asks (separate decision): a `panels.py` sidecar
naming the source grid, a `grids.py` slots map, retired takes keep their graph + reason file.

## Publishable
The Viewer (`viewer.js` + `docview.js`: one sequence, four renderers, provenance panel) as a
standalone MIT package; "prompt lineage" (plan words highlighted in and missing from a prompt) as a
small tool + write-up.
