# V05 — Container pattern: overlay vs drawer vs peek vs stacked panels

Question: the owner wants "a popup on the page, not a new page, which we can close", and it must open
pictures, videos, prompt JSONs and every unit JSON and log. Which container holds that, and how do a
picture and its prompt sit together?
**Answer: one universal Viewer.** It is a single modal `<dialog>` covering the page (inset 12 px),
with a stage on the left and an optional right panel that can be resized. The panel's width is the
mode (Notion's side, center and full peek, collapsed into one draggable seam). JSON is not a separate
drawer: it is either a file kind on the stage or a tab in the panel. There is exactly one viewer, so
there is never a second one to stack.
## 1. What the references do (and what we take)

| Product | Container | What we take |
|---|---|---|
| Linear peek ([docs](https://linear.app/docs/peek)) | Space toggles a preview panel over the list; hold Space for a transient peek | A preview that opens **from the list without leaving it**. Space is ours for play, so `Enter` opens and `Esc` closes. |
| Notion page peek ([release 2022-07-20](https://www.notion.com/releases/2022-07-20), [@NotionHQ](https://x.com/NotionHQ/status/1651271572911718406)) | Side peek / center peek / full page, chosen per database | Three widths of **one** container, not three components. We use them as snap points of the panel seam. |
| VS Code peek definition ([docs](https://code.visualstudio.com/docs/editing/editingevolved#_peek)) | An inline frame embedded in the editor, with a file list on the right; Esc closes; "open" promotes it to a tab | Two exits: **peek, then promote**. The JSON shown in the panel has an "open full" that moves it onto the stage. |
| Figma inspector | A fixed right panel; the canvas is the stage | The panel holds **properties of the thing on stage** (info, prompt, verdict), never a different object. |
| Arc Little Arc ([guide](https://allthings.how/whats-little-arc-in-the-arc-browser-and-how-to-configure-it/)) | A frameless one-page window, no tabs | **One item at a time, no tabs**: no nested viewers and no tab strip of open files. |
| macOS Quick Look ([Apple](https://support.apple.com/guide/mac-help/view-and-edit-files-with-quick-look-mh14119/mac)) | Space previews the selection; arrows walk siblings; the same window renders any type | **Arrows walk the siblings** of the item that opened it. Every file type renders in the same window. |
| Frame.io viewer ([shortcuts](https://help.frame.io/en/articles/9105337-keyboard-shortcuts), [V4 player](https://blog.frame.io/2024/05/28/frame-io-v4-features-player-and-commenting/)) | Media centre, comments panel right, panel toggles, `?` lists keys | **Video + right panel** is the review layout; panel toggle keys; the panel never covers the media. |
| GitHub file preview | Rendered or raw toggle; copy path; line anchors | **Rendered ⇄ Raw** toggle for JSON, `Copy path`, a deep link to a key. |
| Vercel log drawer | A bottom or side drawer streaming logs over the deployment page | **Rejected as a second container**: a log is just a file kind on the stage, tailed. Our *Activity window* stays as it is. |

The platform does most of the work. `dialog.showModal()` puts the dialog in the **top layer**, makes
the rest of the page **inert**, closes on **Esc**, and **returns focus** to the element that opened it
([MDN dialog](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/dialog)). It does
**not** lock page scroll. That takes `html:has(dialog[open]){overflow:hidden}`, plus
`scrollbar-gutter:stable` so the page does not shift sideways, plus `overscroll-behavior:contain`
on the panes ([MDN scrollbar-gutter](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/scrollbar-gutter),
[scroll-locked dialogs](https://blog.master.dev/scroll-locked-dialogs/)). No vendored JS is needed
for the container.
## 2. The options, judged against the owner's request and our constraints

| Option | Verdict |
|---|---|
| A. Full overlay Viewer + optional right panel (resizable) | **Chosen.** One component, one focus trap, one `<video>` slot, closes with Esc / ✕ / backdrop / phone Back. |
| B. Separate JSON drawer beside a picture lightbox | Rejected. Two containers mean two z-levels and two focus traps. The worse problem is that "picture + its prompt" would span two components that each scroll and close on their own. |
| C. Non-modal side peek (page stays live, like Notion side peek) | Rejected as the default. The page underneath re-renders every 5 s (live GPU card, tiles), and on phone there is no room for it. It survives only as the panel's *narrow* snap. |
| D. Stacked panels (VS Code / Finder column style) | Rejected. Nesting depth is a UX tax, and the owner asked for one closable popup. We keep a back stack *inside* the one Viewer instead (§4). |
## 3. Anatomy (one dialog: `<dialog id="vw" class="viewer" aria-labelledby="vw-t">`)

```
.viewer  (fixed inset:12px; radius --r-card; bg --stage #0b0b0c; grid rows: 48px / 1fr / 72px)
├─ header 48px:  [← back]  title (vw-t) · kind chip · path crumb   [i] [{}] [⤢] [↗] [✕ Esc]
├─ body: grid-template-columns: 1fr 6px var(--vw-panel,0px)
│   ├─ .stage    media | JSON tree | log tail | text (prompt .txt)   (tabindex=-1, receives keys)
│   ├─ .seam     role=separator aria-orientation=vertical aria-valuenow=<px>  (drag / ←→ when focused)
│   └─ .panel    tabs: Info · Prompt · Verdict · Raw     (overscroll-behavior:contain; own scroll)
└─ strip 72px:   siblings as 64px thumbs (/thumb/…/160/…), current outlined; "14 / 24"
```

Panel snap points (double-click the seam to cycle; the width is kept in localStorage `vw.panel`, wrapped
in try/catch): **0** (closed) → **360 px** (Info; Figma-like) → **50 %** (side by side) → **stage
collapsed** (JSON alone, which is Notion's "full"). Minimum panel 300 px, minimum stage 360 px. Below
those minimums it snaps to the next point instead of squashing.
## 4. Picture → its JSON → back (the core flow)

1. Click `shot_14.png` in the unit page. The Viewer opens on the stage and the panel shows **Info**
   (360 px) if it was open last time.
2. Press `p` or click `{}`. The panel jumps to **50 %** on the **Prompt** tab. The prompt is the
   *slice* that belongs to this item (for example `plan.json → shots[14]`), not the whole file. A
   header line names the source with a link: `plan.json › shots[14]`.
3. Click "open full" on that line, or `Enter` on a key. **The JSON is promoted onto the stage**, the
   panel closes, the title becomes `plan.json`, and the tree is scrolled to `shots[14]` with that node
   highlighted. That pushes one entry onto the Viewer's **in-dialog back stack**.
4. `Backspace` / `Alt+←` / the header `←` pops back to `shot_14.png` with the panel restored. The
   stack is capped at 8; arrows always walk the siblings of the *current* stage item.
5. `Esc` closes the whole Viewer, whatever the stack depth (one Esc, one closure, which is what the
   owner described). Focus returns to the tile that opened it (native).

### The pairs: which JSON each media file opens (verified on ep12 on disk)

| Stage item (rel. to `episodes/epNN/`) | Panel › Prompt | Panel › Verdict / Info |
|---|---|---|
| `storyboard/shot_NN.png` | `plan.json` shots[NN] (frame, motion, camera) + its grid's `.txt` prompt | `storyboard/panel_content.json`, `panel_dq.json`, `eye_*.json` entries for NN |
| `storyboard/grids/<g>.png` (7 MB, show the 320 thumb, then the original on zoom) | `<g>.txt` (the full grid prompt, 4 KB) | `<g>.json` (shots, seed, plan hash) |
| `takes/r2v/TNN.mp4` | `takes/r2v/prompts.json`[NN] (24 entries: workflow, model, mode, prompt) | `TNN.content.json`, `TNN.dq.json` (40 KB), `TNN.graph.json` under Raw, `eye_*.json` |
| `cut/master_iterN.mp4` | — | `review/eye_*.json`, `qc_r2v.json`, `timing.jsonl` |
| any `*.json` / `*.jsonl` / `*.txt` / log | n/a: the file *is* the stage | Info = size, mtime, path, "copy path" |

Unresolved: what `storyboard/h3/shot_NN.png` pairs with (`takes/r2v/stills.json`?). The data agent
should confirm it before the mapping goes into code. The table should live in **one** JS object
(`PAIRS`) keyed by a path glob, not spread across each page's code.
## 5. Stacking, z-order, focus, scroll

- **Exactly one Viewer.** Opening an item while it is open replaces the stage (Quick Look behaviour).
  It never opens a second dialog.
- **Allowed above it:** only the confirm dialog (redo / ack) and the toast. The top layer orders
  them by `showModal()` call order, so z-index is never needed. The ⌘K palette and the `?` keysheet
  are disabled while the Viewer is open. `shell.js:318` already bails when `dialog[open]` exists;
  extend that guard to Ctrl K.
- **The existing shot view (`#sv`, unit.js:704) stays.** It is the *shot* composite (panel · take ·
  master columns, redo). Clicking one of its frames opens the Viewer **above** it. That is two levels
  at most, and Esc unwinds one at a time. Long term #sv could become a Viewer "shot" mode (see
  disagreements).
- **Activity window:** kept untouched. Clicking a log line in it opens the log file in the Viewer,
  scrolled to that line. The window stays live underneath, inert but still painting.
- **Focus:** on open, focus goes to `.stage` (tabindex −1, `aria-label="shot_14.png, 14 of 24"`),
  so arrow keys work at once. Do not focus ✕, because then Enter would close the Viewer. Tab order:
  header controls → stage → seam → panel tabs → strip. An `aria-live="polite"` node announces
  "14 of 24, shot_14.png" after each move.
- **Scroll:** lock the page as in §1. The stage and the panel scroll on their own. In a JSON
  tree, Page Up/Page Down scroll the pane, not the page.
- **Close:** ✕, Esc, a click on the 12 px backdrop margin (only when pointerdown *and* pointerup land
  on the backdrop, so ending a drag-select there does not close it), and phone Back (below).
## 6. Video in the Viewer (constraints: one `<video>` playing, the server never decodes)

Reuse the page's single `VIDEO` element and its `parkVideo()` (unit.js). On open, move it into
`.stage`. On close or navigation, park it. The poster is the WebP thumb. `src` is `/lib/…mp4`, which
the server delivers with range requests, so the server only serves bytes and never decodes. A master
segment uses a media fragment `#t=t0,t1`, as #sv already does. Keys: `Space` play/pause, `,` and `.`
step a frame, `m` mute. Arrows still walk siblings (Frame.io uses ← → for seeking. We don't, because
walking T00 to T23 is the owner's main motion. `j` and `l` seek ±1 s instead).
## 7. JSON and logs on the stage

The default view is a rendered, collapsible tree: depth 2 open, everything below folded, keys in
`--ink-3`, strings in `--ink`, and a hash or path value becomes a link when it resolves to a library
file. `r` toggles **Raw** (a `<pre>` with line numbers). `/` filters keys. `c` copies the path, and
`Shift+c` copies the JSON pointer of the focused node. JSONL (`learnings.jsonl`, `timing.jsonl`)
renders as one row per line, newest first. Logs fetch the **last 256 KB** with a `Range` header,
follow the tail while the unit is running (htmx later; a 5 s poll in the mockup), and "load
earlier" fetches the previous 256 KB. A file over 2 MB opens in Raw mode only. No JSON library is
needed, because a 40-line renderer over `JSON.parse` is enough.
## 8. Wireframes (desktop 1440 × 900 unless noted)

**W1 — picture + info panel (360 px)**
```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ ←  shot_14.png  PANEL  ep12 › storyboard › shot_14.png           [i]●[{}] [⤢] [↗] [✕ Esc]│
├───────────────────────────────────────────────────────────┬┬─────────────────────────────┤
│                                                           ││ Info● Prompt  Verdict  Raw  │
│                    ┌───────────────────────┐              ││ Shot 14 · bank · WIDE       │
│                    │                       │              ││ 08 board · grid bank_2x2 #2 │
│                    │      picture 1:1      │              ││ ⚑ EYE_PANELS face ×1        │
│                    │   (contain, black)    │              ││ panel_dq  ✓ sharp ✓ exposure│
│                    │                       │              ││ 1024×1024 · 1.6 MB · 09-24  │
│                    └───────────────────────┘              ││ [Copy path] [Open original] │
│  ‹                                                     ›  ││                             │
├───────────────────────────────────────────────────────────┴┴─────────────────────────────┤
│ ▢ ▢ ▢ ▢ ▢ ▢ ▢ ▢ ▢ ▢ ▢ ▢ ▢ ▢[▣]▢ ▢ ▢ ▢ ▢ ▢ ▢ ▢ ▢                              14 / 24  │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```
**W2 — video + info**
```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ ←  T14.mp4  TAKE  ep12 › takes › r2v › T14.mp4                   [i]●[{}] [⤢] [↗] [✕ Esc]│
├───────────────────────────────────────────────────────────┬┬─────────────────────────────┤
│                    ┌───────────────────────┐              ││ Info  Prompt  Verdict  Raw  │
│                    │   <video> (the one)   │              ││ T14 · 6.2 s · try 2 (1 fail)│
│                    │   poster = 320 thumb  │              ││ ✓ EYE_TAKES · content ✓     │
│                    └───────────────────────┘              ││ dq soft: motion_low         │
│   ▶ ━━━━━━━━━━━●━━━━━━━━━━━  00:03.4 / 00:06.2   🔈  ,  . ││ MiniMax-H3 ref2va + 8-step  │
│                                                           ││ in master v7 · 01:12–01:18  │
├───────────────────────────────────────────────────────────┴┴─────────────────────────────┤
│ ▶T00 ▶T01 … [▶T14] … ▶T23                                         Space play · ←→ takes │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```
**W3 — JSON alone (promoted, panel collapsed; the back stack shows its origin)**
```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ ← shot_14.png   plan.json  JSON  ep12 › plan.json  42 KB   [/ filter keys] [Raw r] [✕ Esc]│
├──────────────────────────────────────────────────────────────────────────────────────────┤
│ ▸ number: 12        ▸ title: "…"          ▸ setups {6}        ▸ lines [7]               │
│ ▾ shots [24]                                                                             │
│ ▌ ▾ 14                                                         ← highlighted, scrolled   │
│ ▌   size: "WIDE"   setup: "bank"   section: "flight"                                     │
│ ▌   frame:  "Wide at midday over the gravel bank where the Wey meets …"                  │
│ ▌   motion: "…"   camera: "crane up …"                                                   │
│   ▸ 15 {…}                                                     /shots/14 [copy pointer]  │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```
**W4 — picture + its prompt side by side (panel at 50 %, seam draggable)**
```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ ←  ep12_grid_bank_2x2.png  GRID  ep12 › storyboard › grids       [i] [{}]● [⤢] [↗] [✕ Esc]│
├────────────────────────────────────────────┬┬────────────────────────────────────────────┤
│  ┌───────────┬───────────┐                 ││ Info  Prompt●  Verdict  Raw                │
│  │ panel 1   │ panel 2   │  hover a panel  ││ source: grids/ep12_grid_bank_2x2.txt [full]│
│  │  → 13     │  → 14     │  ⇄ highlights   ││ A storyboard of 4 panels in 2 columns …    │
│  ├───────────┼───────────┤  its PANEL n    ││ ▌PANEL 2 (top-right), WIDE: Wide at midday │
│  │ panel 3   │ panel 4   │  paragraph      ││ ▌over the gravel bank where the Wey …      │
│  │  → 15     │  → 17     │                 ││ PANEL 3 (bottom-left) …                    │
│  └───────────┴───────────┘                 ⇔│ meta: seed 40559 · plan c7aa61c6 · v2      │
├────────────────────────────────────────────┴┴────────────────────────────────────────────┤
│ [bank_2x2] hill_1x1_s02  bank_1x1_s16  bank_1x1_s22 …                            3 / 9   │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```
**W5 — phone (400 × 860): full-screen sheet, panel as a bottom sheet, no side-by-side**
```
┌────────────────────────────┐
│ ✕   shot_14.png    14/24 ⋯ │ 48px, safe-area-top
├────────────────────────────┤
│      picture (contain)     │  swipe ←/→ = siblings
│                            │  pinch = zoom; swipe ↓ on stage = close
├────────────────────────────┤ ← grab handle
│ Info   Prompt   Verdict  { }│ sheet detents: 25% · 60% · 100%
│ Shot 14 · bank · WIDE      │ (100% = JSON alone; picture hides
│ ⚑ EYE_PANELS face ×1       │  behind a "▲ picture" chip)
│ plan.json › shots[14]  [↗] │
└────────────────────────────┘
```
Phone rules: `dialog.viewer` takes `inset:0; width:100vw; height:100dvh; border-radius:0`, with padding
from `env(safe-area-inset-*)`. Opening it does `history.pushState({vw:1})` so the phone's **Back
closes the Viewer**, and `popstate` calls `close()`. The tap targets in the strip are at least 44 px,
and the strip is hidden behind `⋯`.
## 9. Keys (added to the `?` keysheet under "Viewer")
`Esc` close · `←/→` siblings · `Home/End` first/last · `i` info panel · `p` prompt split · `r` raw ·
`/` filter · `Enter` promote JSON slice to stage · `Backspace`/`Alt+←` back · `Space` play ·
`j/l` ±1 s · `,`/`.` frame · `f` toggle panel full (JSON alone) · `c` copy path · `o` open original
in new tab · `[`/`]` seam −/+ 40 px.
## 10. Build notes (mockup now, htmx later)
- One file `assets/viewer.js` (≈ 250 lines) + `viewer.css`. API: `Viewer.open({path, set:[paths],
  pane:'info'|'prompt'|null})`. Any element with `data-view="<rel path>"` opens via a delegated click
  (as `shell.js` does for `[data-order]`), and its siblings are the other `[data-view]` items in the
  same `[data-view-set]`.
- URL: `#v=<rel path>&p=prompt`, updated with `replaceState` while navigating and set once with
  `pushState` on open, so a deep link opens the Viewer on load. Only `production_id` + relative
  path go in the URL, never an absolute path (the architecture invariant).
- htmx later: panel tabs become `hx-get="/view/pane?path=…&tab=…"` into `.panel`; the shell stays static.

## Top 8 recommendations
1. Build **one** modal `<dialog>` Viewer opened with `showModal()`. The native top layer, inert
   page, Esc and focus return replace any hand-rolled trap.
2. Make the right panel **resizable with snap points 0 / 360 / 50 % / full**, so Notion's three
   peeks are one seam, not three components.
3. JSON gets **no separate drawer**. Show the item's *slice* in the panel and **promote** it to the
   stage with an in-dialog back stack (`Backspace` returns to the picture).
4. Keep one `PAIRS` table mapping media → prompt/verdict JSON (§4). It is the spec; confirm the
   `storyboard/h3` row.
5. One Viewer, never nested. Only confirm dialogs and toasts may sit above it. The existing `#sv` shot
   view may open it (max two levels). The Activity window stays and links into it.
6. Lock page scroll (`html:has(dialog[open])`, `scrollbar-gutter:stable`, `overscroll-behavior:contain`).
   Focus goes to the stage, an `aria-live` count announces moves, and the backdrop closes only on a
   full click.
7. Video reuses the single `VIDEO` element via `parkVideo()`, with `/lib` range-served originals and
   WebP posters. Arrows walk takes and `j/l` seek.
8. Phone: a full-screen sheet with a bottom-sheet panel (25 / 60 / 100 %), swipes for siblings, and
   **Back closes it** via `pushState`/`popstate`.
## 2 disagreements I expect
1. **Side-by-side vs tabs for picture + prompt.** A media-review researcher may want the prompt
   as a *tab* only (the picture always full-size, Frame.io-style). I hold that the owner's real task
   is "does this picture match what we asked for", which needs both visible at once. So 50 % split is
   one keystroke (`p`), and on phone it degrades to a tabbed sheet.
2. **Fold `#sv` into the Viewer, or keep two dialogs.** A purist will say two dialog kinds break
   "one popup". I keep `#sv` for now because it is a different object (a *shot* across panel, take
   and master, plus redo), and the Viewer shows a *file*. Merging them as a Viewer "shot" mode is a
   later decision for after the owner has used both. Related: `pushState` on open (so Back closes
   it) vs the current `replaceState` in #sv. I want push on every viewport, and others may want it
   on phone only.
