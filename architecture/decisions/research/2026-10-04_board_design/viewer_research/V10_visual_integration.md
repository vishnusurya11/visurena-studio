# V10 — Visual design & integration of the in-page viewer (v2 mockups)

Read: `mockups/assets/{v2.css, unit.css, shell.js, unit.js, dept.js}`, all 7 pages live on :8710. Screens (1440 px unless named): `mockups/shots/V10_{index,queue,department,book,books,unit-running,unit-finished,shotview,shotview_phone,activity}.png`. Data checked read-only: ep12 and ep17 folders, `logs/20260827135508/episode/*.log`.

## 0. What already exists (build on it, don't fork it)

- **`dialog.sv` shot view** (ep12 only, `unit.js` openShot/drawShot): 96vw card, `#0f1012`, backdrop `rgb(0 0 0/.72)` + 3 px blur, a header with ← n/24 → and Esc, a panel → take → master triptych, redo. This is a *review* tool. The new viewer is a general *media + file* viewer. They are different jobs.
- **One `<video>` per page** (`VIDEO`, moved by `hoverPlay` / `svPlay` / `parkVideo`). The viewer must borrow this element and give it back. It must not make a second one.
- **Files list in props** (`renderProps`): `<a href=LIB(rel) target=_blank>` with `external-link` icon. This is the thing the owner means by "not a new page".
- **Activity** (`renderActivity`): groups lines by step, uses level chips and search, and `.ln` toggles `.open`. Each line has `id="L<ts*10>"`. The owner said keep it, so it stays as it is. I only add links.
- Stage tokens (`--stage #0e0e0e`, `--stage-ink/-2/-3`) stay dark in every theme. That is the right base for the viewer.
- `icons.svg` lacks `house`, `maximize-2`, `braces`, `file-text`, `scroll`, `copy`, `download`, `info`, `chevron-left`, `zoom-in`. Add their Lucide paths (https://lucide.dev/icons/) to the sprite.

## 1. Overlay chrome (Studio black, and the same in Graphite)

The viewer is a stage, like the screening room. It stays dark in Graphite light too, as Lightroom, Frame.io and Google Photos do. A picture judged on a white surround reads differently from one judged on black.

```
┌ top bar 52px ─────────────────────────────────────────────────────────────────┐
│ [img] shot_05.png  ep12 / storyboard /     Panels · 6 / 24     [Picture|prompt]  ⓘ ⧉ ⤓ ↗  ✕ │
├──────────────────────────────────────────────────────────────┬────────────────┤
│  ‹ (44px round, edge-centred)    STAGE (contain)          ›  │ INFO 360px     │
│                                                              │ (toggle  i)    │
├ filmstrip 84px ──────────────────────────────────────────────┴────────────────┤
│ ▢ ▢ ▢ ▢ ▢ [▣] ▢ ▢ ▢ ▢ ▢ ▢ …  (64px squares, current centred)                    │
└───────────────────────────────────────────────────────────────────────────────┘
```

- **Element**: `<dialog id="viewer" class="vw" aria-labelledby="vw-title">` opened with `showModal()`. It is created once by `shell.js`, so every page has it. Native modal gives an inert background, Esc, and a top layer above `dialog.sv` (it stacks: Esc closes the viewer and returns to the shot view). On close, focus goes back to the invoker (WAI-ARIA APG modal dialog, https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/ ; MDN `<dialog>`, https://developer.mozilla.org/en-US/docs/Web/HTML/Element/dialog).
- **Size**: `inset:0; width:100vw; height:100dvh; max-width:none; max-height:none; margin:0; border-radius:0`. The full screen is for pictures. `dialog.sv` is a card because it is a form.
- **Surfaces** (new tokens, unlayered, `--vw-*`): `--vw-bg:#08090a` (stage area, darker than `--stage` so a 1:1 frame's edge shows); `--vw-bar:rgb(16 17 19/.88)` + `backdrop-filter:blur(12px)` (top bar, filmstrip); `--vw-panel:#16171a` (= `--surface`, the info panel); rules `rgb(255 255 255/.07)`; `::backdrop{background:rgb(0 0 0/.80)}`. The dialog itself is `--vw-bg`, not transparent: the page behind must not show through a letterboxed picture.
- **Top bar** (52 px, `padding:0 12px 0 16px`, grid `auto 1fr auto auto`):
  - title: type icon 16 px + file name in Plex Sans 14/20 600 `--stage-ink`, then the path crumb in Plex Mono 12 `--stage-ink-3`, truncated from the left (`direction:rtl` trick) so `shot_05.png` always shows;
  - counter centred: set name in Plex Sans 12 500 `--stage-ink-3` + `6 / 24` in Plex Mono 12 600;
  - **view switch** (only when the item has siblings): the existing `.segmented` on dark: `Picture | prompt.json | prompt.txt` for a grid, `Video | content | dq | graph` for a take, `Picture` alone for a panel. Key `p` cycles. This is how prompt JSONs open beside their picture.
  - actions: 32 px `.iconbtn`s (`--stage-ink-2`, hover `rgb(255 255 255/.08)`): Info `i`, Copy path `c` (copies `episodes/ep12/storyboard/shot_05.png`, which is relative, never absolute), Download, Open original ↗ (new tab, the `/lib/` URL), and Close `✕` with a `kbd` "Esc" beside it on ≥1100 px.
- **Prev/next**: 44 px round buttons, `rgb(0 0 0/.55)` + 8 px blur, white chevron, centred on the stage edges with a 12 px inset. They fade out after 2 s with no pointer movement (`--d3`) but always show on `:focus-visible`. Keys ← →, plus Home/End. The set wraps, as `nav()` does today.
- **Stage**: the picture is `object-fit:contain` inside 24 px padding. It shows the cached 320 thumb at once, then swaps to the `/lib/` original when that has decoded (`img.decode()`), a blur-up with `filter:blur(6px)` → 0 over `--d2`. Click, or `z`, toggles fit ↔ 1:1 (cursor `zoom-in`/`zoom-out`); at 1:1 you drag to pan. A video uses the page's `VIDEO` with native `controls` and `preload="metadata"`, so the board serves bytes by range and never decodes anything.
- **Filmstrip** (84 px, `--vw-bar`, `overflow-x:auto; scroll-snap-type:x proximity`): 64 px squares from the `/thumb/160/` URLs, 6 px gap, 6 px radius. Unselected thumbs are at `opacity:.55`, 1 on hover. The current thumb gets `outline:2px solid var(--focus); outline-offset:2px`, full opacity, and `scrollIntoView({inline:'center'})`. A video thumb has a 14 px play glyph and its duration (mono 10) bottom-right. A take with a flag gets a 6 px amber dot top-right, the same as `.flagdot`. `f` hides the strip. With one item, there is no strip.
- **Info panel** (360 px, `--vw-panel`, left rule; open by default ≥1280 px, otherwise closed; `i` toggles): sections use `.lbl2` labels:
  1. *File*: path, size, px or duration, modified (studio clock, `hm()`), sha8 when known.
  2. *Gates naming this*: `.chip2.flag` chips (e.g. `EYE_PANELS ⚑ landmark ×19`). A click opens that verdict JSON in the stage, scrolled to the entry.
  3. *Files with this*: the sibling list (`ep12_grid_bank_2x2.json/.txt`, `T05.content/dq/graph.json`, `takes/r2v/attempts/`).
  4. *In the log*: lines that name this file (§5).
  5. *Shot text*: frame / motion / camera from `plan.json`, the same copy as the shot view.
- **Phone ≤640 px**: the top bar is 48 px with the title only; actions fold into a `⋯` menu, but ✕ stays visible. There is no filmstrip or arrows; you swipe horizontally (pointer events, a 40 px threshold). Swipe down closes (≥120 px). Info becomes the existing `.sheet` bottom sheet. `padding: env(safe-area-inset-*)`. Checked against `V10_shotview_phone.png`: the current shot view already crops on 400 px, and the viewer must not copy that.
- Motion: open is opacity 0→1 plus scale .985→1 over `--d2 var(--ease-out)`. The picture does not fly from its thumbnail; FLIP is not worth the code at this size. `prefers-reduced-motion` removes the scale.

## 2. The JSON / text / log panel

The viewer's stage swaps to a code surface. It needs no library: a ~40-line regex tokenizer over `JSON.stringify(obj, null, 2)`.

- **Type**: Plex Mono 12.5/20 px, `tab-size:2`, `font-variant-ligatures:none`. The background is `--vw-bg`. The code column has `max-width:110ch`, centred, with the padding of the picture stage.
- **Line numbers: yes.** They sit in a gutter `min-width:4ch`, right-aligned, `--stage-ink-3` at .6, `user-select:none`, with a 1 px `rgb(255 255 255/.06)` rule. They earn their place because the viewer is deep-linked to lines: a fault, rung or log line opens `plan.json` at `#L214`, and that line gets a `--focus-bg` band plus a 2 px `--focus` left bar that fades to a 1 px rule after 2 s.
- **Token colours** must avoid the four state hues (blue running, green done, amber flagged, red failed), because DIRECTION_v2 says state colours are for state only:

  | token | colour | note |
  |---|---|---|
  | key | `#e6e6e6` 500 | = `--stage-ink`; keys are the structure you scan |
  | string | `#c4b5fd` | lavender, 9.6:1 on #08090a |
  | number | `#f5a3c7` | rose, 8.9:1 |
  | true/false/null | `#9aa4b2` italic | 7.3:1 |
  | punctuation `{}[],:` | `#5d626b` | ≥3:1, decorative (WCAG 1.4.11) |
  | fold summary `… 24 items` | `--stage-ink-3` on `rgb(255 255 255/.05)` pill | |

- **Folding**: every `{`/`[` line gets a 12 px chevron in the gutter. Arrays with more than 20 items open folded (`shots: [ … 24 items ]`). `[`/`]` fold or unfold all. Folding is done with the `hidden` attribute on line ranges, not `<details>`, so the line numbers stay true.
- **Prompts are for reading, not scanning.** When the file holds a prompt (a grid `.txt`; a `prompt`/`text` node in `T??.graph.json`; a `plan.json` shot's `frame/motion/camera`), a **Prompt card** sits above the JSON. It is Plex Sans 14/22 `--stage-ink` in a `--vw-panel` card with 10 px radius, `max-width:72ch`, and has a Copy button. The JSON follows below. Long strings in the JSON wrap with a hanging indent (`white-space:pre-wrap; padding-left` = indent + 2ch).
- **Tools** (a bar over the code, 40 px): Find (`/` or Ctrl F focuses it; `n`/`N` step; hits use the Activity's `mark` style), Copy all, `Raw ↔ Pretty`, Wrap toggle, and the file size.
- **JSONL** (`learnings.jsonl`, `timing.jsonl`, `drive.jsonl`): one row per line, collapsed to a one-line preview (ts · gate · attempt · action, using the gate-thread column grid). The row number replaces the line number. A click expands the row to pretty JSON.
- **`.log`** (JSONL with `ts/level/step_id/msg`): it renders with the **Activity's own `.lines .ln` markup and CSS**: time, level, msg, the WARNING/ERROR left bars, level chips and search. A log read in the viewer looks like the Activity window, so the owner learns one look.
- **Size**: render up to 1.5 MB or 5 000 lines. Beyond that, show the head plus "Open raw ↗". Today's largest is `plan.json` at 42 KB, so this is a guard and nothing more.

## 3. How every clickable picture says "this opens"

There are two kinds of picture, and the affordance must not blur them:

- **View pictures** (the picture *is* the content: shot frames, grids, cast sheets, Up-next stills) open the viewer on a plain click. `cursor:zoom-in` (MDN cursor, https://developer.mozilla.org/en-US/docs/Web/CSS/cursor).
- **Nav pictures** (posters that link to a unit: Needs-you thumbs, the shipped shelf, the season wall, the hero poster) keep their link. `cursor:pointer`. They gain an **expand chip** that opens the viewer without navigating.

The chip `.xp` is a 28 px square, top-right 8 px inset, `rgb(0 0 0/.62)` + 4 px blur, 6 px radius, with a 14 px `maximize-2` icon in `#fff`, and `aria-label="View shot_05.png"`. It shows on `:hover`/`:focus-within` of the picture (opacity 0→1, `--d1`), and its own hover is `rgb(0 0 0/.8)`. On a video item, a second chip bottom-left shows `▶ 0:07`. On `(hover:none)` devices (https://developer.mozilla.org/en-US/docs/Web/CSS/@media/hover) the chip is always visible at .85.

The hover on a view picture adds an inner ring `box-shadow:inset 0 0 0 1px rgb(255 255 255/.18)` and `filter:brightness(1.06)`. There is **no scale**: `.pcard:hover img{scale(1.03)}` stays the "go there" signal for nav cards only. Keyboard: view pictures are `<button>` (or `<a>` with `role=button`), and `:focus-visible` = `--focus` outline plus the chip visible. Enter opens.

**One markup contract** gives one delegated listener in `shell.js`: `data-view="<unit-relative path>" data-unit="ep12" data-set="ep12-panels" [data-kind="video|json|log"]`. The set is every `[data-set=X]` in DOM order, which gives the filmstrip and the arrows. The real board renders the same attributes server-side, so htmx needs nothing extra.

**File links** (props *Files*, gate chips, file names in log lines) stay `<a href="/lib/…">`, so Ctrl-click or middle-click still opens a tab. A plain click calls `preventDefault()` and opens the viewer. The `external-link` icon becomes the type icon (`braces` json, `scroll` jsonl/log, `film` mp4, `image` png), with a 12 px ↗ shown on hover only.

## 4. Home in the sidebar

The owner looked at a sidebar whose first row is "Now" → `index.html` and asked to "add home". Read that literally: the label failed, not the page. Recommendation:

- The first NAV row becomes **Home**, with the `house` icon, `index.html`, chord **G H** (keep G N as an alias). The bottom tab becomes "Home" too. The crumbs go from `Studio › Now` to `Home`. The page H1 "Now" becomes "Home" with the same live subline (`1 running · 5 need you · 92 queued`).
- Change it in `shell.js` `NAV`, `tabsHTML`, `CHORDS`, `PALETTE` (`Pages › Home`) and the keysheet, all in one place. `data-page="now"` can stay as the internal id.
- Do not add Home *above* Now: two rows to the same page is the confusion we are removing.

## 5. Activity ↔ viewer

The Activity window stays as it is. Two links get added:

1. **Activity → viewer.** In `activityEntries` messages, file tokens are linkified by regex `/(?:episodes\/ep\d\d\/)?[\w./-]+\.(json|jsonl|png|mp4|txt|log)\b/`. They render as an inline `<a class="fl" data-view>`: mono, `--focus` colour, dotted underline, no click-through to the `.ln` open toggle (`stopPropagation`). The logs really do contain these: `plan.verdict.json` ×43, `plan.deferred.json` ×30 (often written `episodes/ep15/…`, which the resolver strips to unit-relative when the unit matches), `plan.json`, `storyboard/layout.json`. The queue's refusal lines do too (`qc_r2v.json` ×14, `panel_content.json` ×3, `panel_dq.json`). The Activity header gets one ghost button, **Full log**. It opens this run's `logs/<codex>/episode/<codex>__episode__<run-ts>.log` (the run id already ends in that ts) in the viewer's log renderer, scrolled to the line that was open.
2. **Viewer → Activity.** The *In the log* section lists matching lines as `run #4 · 19:11 · WARNING · msg…`. A click closes the viewer, calls `selectRun(k)`, sets `Q=''`, opens that step's `<details>`, scrolls `#L<ts*10>` into view, and flashes it `--focus-bg` for 2 s. The Activity's own search is untouched.

Build note: logs live outside the library, so the board needs a read-only `GET /logs/<codex>/<stage>/<file>` with a name allowlist (`^\d{14}__\w+__\d{14}\.log$`). Unit-folder logs (`ep17/drive_run0N.log`) are already under `/lib/`.

## 6. Every clickable media and file element, per page

Legend: **V** = view picture (click opens), **C** = nav picture plus expand chip, **F** = file link → viewer. The set is in brackets.

**index.html (Home)**
- C hero poster `ep17/storyboard/anchors/steamer_forward.png` [ep17 anchors + grids]
- C Needs-you thumbs ×5, `ep12…ep16/storyboard/shot_05.png` [that unit's panels]
- V Up-next stills ×4: `ep01/review/work/b2c111e9/f03.png`, `ep02/review/T11_mid.png`, `ep05/storyboard/shot_05.png`, Scarlet `refs/characters/char-john_watson.png` [up next]
- C Shipped-with-flags pcards ×5 (shot_05) plus a **▶ master** chip → `cut/master_iterN.mp4` [shipped masters]
- F "Since 14:02" feed lines: `plan.verdict.json` (02 plan passed), the refusal line's file
- Excluded: sidebar pin faces (24 px), GPU card face (40 px), sparklines. These are navigation only.

**queue.html**
- V row faces ×5 (ep17 shot_04, ep01 f03, ep02 T11_mid, ep05 shot_06, Scarlet sister faces) [queue]
- F refusal history strings: `qc_r2v.json` ×14, `panel_content.json` ×3, `panel_dq.json` ×1 (ep14) → opens that unit's file

**department.html**
- C list faces (36 px, ×17 WotW + Scarlet) [the book's faces]; the chip shows at 20 px here (the face is 36 px), bottom-right
- F gate chips `plan ⚑16`, `panels ⚑531`, `takes ⚑10`, `master ⚑3` → `plan.verdict.json`, `storyboard/eye_*.json`, `takes/r2v/eye_*.json`, `review/eye_*.json`
- F "Gate × unit faults" matrix cells → the same verdict files

**book.html**
- C hero "Newest finished" (ep16 face; the hero background is not clickable)
- C season-wall posters ×17 (contact-sheet scrub stays as the hover; the chip opens `storyboard/contact.png` or the face) [season]
- V cast sheets ×47 `refs/characters/*/sheet.png` [cast · 47], **the most useful set to swipe**
- Matrix cells: not media; no viewer.

**books.html**: no pictures or files today; nothing to wire.

**unit-running.html (ep17)**
- V hero poster (newest grid `storyboard/grids/ep17_grid_steamer_stern_3x1*.png`). Today it is `href="#shots"`; it should open the viewer. [grids]
- V "The look so far" grids ×8 with switch `Picture | .json | .txt` [grids · 8]
- V panels `storyboard/shot_00…11.png` as they land in 08. The folder has 12 now while the mock says "0 of 22", so the build must show them [panels]
- V anchors `steamer_forward.png`, `tillingham_sea.png` [anchors]
- F shot-list rows → `plan.json` at `shots[i]` (line deep-link)
- F gate-thread rung rows → `learnings.jsonl` row; gate name → `plan.verdict.json`
- F props Files: `plan.json`, `plan.verdict.json`, `learnings.jsonl`, `timing.jsonl`, `storyboard/grids/` (a folder opens the grid set)
- F Activity file tokens plus Full log (`drive_run0N.log`, `logs/…`)

**unit-finished.html (ep12)**
- Player poster and master: **not** the viewer. The screening room is the master's viewer.
- V each shot card's **P** frame → `storyboard/shot_NN.png` [panels · 24]; **T** frame → `takes/r2v/TNN.mp4` with `content | dq | graph` [takes · 24]. The card body still opens the existing shot view, so each frame gets its own chip, stopping propagation.
- V shot view's three frames (panel, take, master segment) → chip opens the viewer above `dialog.sv`
- F judge stamps ×4 → `review/eye_faf11c8f.json`, `takes/r2v/eye_20cc84ad.json`|`eye_21227f91.json`, `storyboard/eye_c7e3eb93.json`, `plan.verdict.json`
- F qcline `master_iter7.mp4` → `qc_r2v.json`; versions menu row ⋯ → `cut/master_iterN.mp4` in the viewer
- V `review/contact_faf11c8f.png` (the master contact sheet, not shown today; add it to Files)
- F props Files ×5, Activity tokens, Full log; `.chipnum[data-shot]` keeps opening the shot view

## Top 8 recommendations

1. One `<dialog id="viewer">` injected by `shell.js` on every page, full-bleed, always dark (`--vw-*` tokens). It uses the page's single `<video>`, and `dialog.sv` stays as the review tool underneath it.
2. One contract, `data-view / data-unit / data-set / data-kind`, and one delegated listener. Sets give the filmstrip and the ← → order.
3. Siblings, not a separate file browser: a `Picture | prompt.json | prompt.txt` (and `Video | content | dq | graph`) switch in the top bar answers "prompt JSONs viewable".
4. JSON panel: Plex Mono 12.5/20, line numbers for deep links, state-free token colours (lavender/rose/grey), folding, and a Prose **Prompt card** above any prompt-bearing file.
5. Two affordances: `zoom-in` with an inner ring for view pictures; a 28 px `maximize-2` chip for nav pictures. No hover-scale on view pictures. Chips are always visible on touch.
6. File links keep a real `href` (Ctrl-click = tab) but open the viewer on a plain click, with type icons in place of `external-link`.
7. Rename **Now → Home** (house icon, G H, bottom tab, crumbs, H1), rather than adding a second row.
8. Activity stays as it is, plus linkified file tokens, a **Full log** button that renders `.log` with the Activity's own `.ln` styling, and "In the log" in the info panel that jumps back to `#L<ts>`. Add the read-only `/logs/` route.

## 2 disagreements I expect

1. **Viewer vs the shot view.** Someone will want to merge `dialog.sv` into the viewer, with the triptych as an info layout. I keep them apart. The shot view is a decision surface (redo, faults, stages) and the viewer is for looking. Merging makes the viewer a form and the shot view lose its triptych. Stacking costs nothing with the native top layer.
2. **Line numbers and a dark viewer in Graphite.** A reader-first view would drop the gutter and follow the light theme. I keep both. Deep links to `plan.json:214` and log lines need visible numbers, and pictures must be judged on black whatever the board's chrome is.
