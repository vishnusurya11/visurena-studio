# V08 — Accessibility, keyboard and phone for the viewer overlay and JSON panel

V08 · 2026-10-04 · read shell.js, unit.js, unit/v2/shell.css, unit-finished.html, ep12 data; sources inline.

## 0. What already exists, and what is broken in it (from the code, not guessed)

The finished-unit page already has two native modals: `<dialog id="sv" aria-label="Shot view">`
(the shot lightbox, `unit.js` 704–762) and `<dialog id="cmp">` (compare, 637–657). The new viewer
should be the generalisation of `#sv`, so its faults are the starting list:

| # | Where | Fault | Fix |
|---|---|---|---|
| F1 | `unit.js` 766–778 `wireKeys` | Only `#sv` / `#cmp` are checked. With any other modal open (keysheet `?`, the new viewer, the phone `#sheet`), **Space plays the master behind the backdrop** and **`C` opens Compare on top**. | Guard on `document.querySelector('dialog[open]')`, then route to the open dialog's own handler. |
| F2 | `unit.js` 734, 762 `drawShot`/`nav` | Every ←/→ rebuilds `d.innerHTML`, destroying the focused button; focus drops to `<body>`, SR users lose their place, and the next Tab restarts at the top. | Build the chrome (header, prev/next, close, tabs) once; re-render only the stage + text regions. |
| F3 | `unit.js` 737 | Close button's accessible name is "Esc"; prev/next named only by an arrow glyph label. | `aria-label="Close"`, `aria-keyshortcuts="Escape"`; "Previous shot"/"Next shot" + `aria-keyshortcuts="ArrowLeft"`. |
| F4 | `unit-finished.html` 38 | `aria-label="Shot view"` never changes; the dialog has no name tied to its content. | `aria-labelledby` → the `<h2>` ("Shot 05"), plus a live region (§4). |
| F5 | `unit.js` 655 | Compare's "Flip A/B" **hijacks Tab** — a keyboard trap inside a modal (WCAG 2.1.2). | Flip on `X` (Photoshop's swap) and a button; Tab stays Tab. |
| F6 | `unit.js` 752 → `shell.js` 153 | The redo toast is a `position:fixed` div **outside** the dialog: modal content makes it inert *and* it renders **under the `::backdrop`** (not in the top layer). Neither seen nor announced. | Each dialog owns a `role="status"` slot; or make the toast `popover="manual"` and `showPopover()` it after the dialog, which stacks it above in the top layer. |
| F7 | `unit.js` 750, 744 | Esc while typing the redo note closes the whole viewer and drops the draft (`wireKeys` returns on textarea, so native cancel runs). | `cancel` listener: if the note is dirty, `preventDefault()` and ask "Discard note?" inline. |
| F8 | `unit.css` 474 | Phone modal is `height:100vh` → on iOS Safari the bottom bar hides behind the toolbar. | `100dvh` + `env(safe-area-inset-*)` padding. |
| F9 | `shell.js` 76 vs 323 | The keysheet advertises **T = takes** on a unit page while the global handler binds **T = toggle theme**. | Unit section keys must not reuse `T`; see §3. |
| F10 | `#sv` | No backdrop-click close (the palette and keysheet have one, `shell.js` 292). | `closedby="any"` + the same `ev.target === dlg` fallback for Safari. |

## 1. The container: native `<dialog>` + `showModal()` — keep it, add four things

Native modal gives, for free: top-layer stacking over the sidebar and the phone `.btabs`, the rest
of the page made **inert** (no focus, no clicks, removed from the a11y tree and from find-in-page),
implicit `aria-modal="true"`, a `::backdrop`, Esc → `cancel` → close, initial focus on the first
focusable (or `autofocus`), and focus **returned to the opener** on close
([MDN dialog](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/dialog)). That
covers everything the WAI-ARIA APG modal pattern asks for
([APG dialog-modal](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)): trap, Esc, return,
labelled — with zero vendored JS. PhotoSwipe's own a11y options are exactly this list
(`trapFocus`, `returnFocus`, `escKey`, `arrowKeys`, `closeTitle`, `arrowPrevTitle`,
`indexIndicatorSep`; [PhotoSwipe options](https://photoswipe.com/options/)) — we get them natively.

What native does **not** do, so we add it:

1. **Scroll lock.** `showModal()` does not stop the page scrolling under it (wheel/touch on the
   backdrop chains through). CSS only: `html:has(dialog[open]){overflow:hidden;scrollbar-gutter:stable}`
   and `dialog{overscroll-behavior:contain}`. The `scrollbar-gutter` stops the page jumping 15 px on
   Windows when the scrollbar vanishes.
2. **Light dismiss.** `closedby="any"` (Chrome/Edge 134, Firefox 141; Safari 26 not yet, in
   Technology Preview — [caniuse](https://caniuse.com/mdn-html_elements_dialog_closedby),
   [features explorer](https://web-platform-dx.github.io/web-features-explorer/features/dialog-closedby/)).
   Keep the shell's click-on-`dlg` fallback until Safari ships.
3. **Layered Esc.** Esc should first leave an inner state (1:1 zoom, the JSON find box, a dirty
   note), then close. Do it in the `cancel` event with `preventDefault()`. Caveat: browsers ignore a
   *repeated* cancellable close request with no user activation in between (the close-watcher
   anti-abuse rule, [HTML §close requests](https://html.spec.whatwg.org/multipage/interaction.html#close-requests-and-close-watchers)),
   so never rely on two cancels in a row — one inner layer, then close.
4. **Android back / swipe-back** sends a close request to an open modal (same close-watcher
   mechanism; [Judis on mobile close requests](https://www.stefanjudis.com/blog/risky-mobile-close-requests/)).
   That is what a phone user expects of a full-screen viewer, so: **never `pushState` on open** —
   keep `unit.js`'s `replaceState('#shot-NN')` deep link, and back closes the viewer without
   leaving the unit page.

## 2. Focus

- **Initial focus:** `autofocus` on the **stage** (`<div class="vw-stage" tabindex="-1">`), not on
  Close. Focus on Close makes Space/Enter one keystroke from dismissal; focus on the stage lets ←/→
  and Space work immediately and the SR reads the dialog name + the live line.
- **Stable chrome (F2):** prev/next/close/tabs survive navigation, so a user who pressed "Next
  shot" with the mouse or Tab keeps focus on "Next shot".
- **Return:** native returns focus to the opener (the `.shot` card button / chip). If the user
  navigated to item 9 while opened from item 5, move focus to card 9 on `close` (and
  `scrollIntoView({block:'nearest'})`) — the grid then matches where the user is. PhotoSwipe does the
  same with its thumbnail-bounds return.
- **Focus rings in Studio black.** The token exists: `--focus:#5b8def` (v2.css 12) on stage
  `#0f1012` ≈ 5.6:1, Graphite `#2f6fdb` on white ≈ 4.9:1 — both clear the 3:1 of WCAG 1.4.11.
  The failure case is a ring drawn **over a picture** (panel/take thumbnails are mid-tone): use a
  two-tone ring for anything on media,
  `outline:2px solid var(--focus);outline-offset:2px;box-shadow:0 0 0 4px #000` — readable on any
  frame (WCAG 2.4.13 focus appearance). Sticky viewer header: give stage children
  `scroll-margin-top: 56px` so the focused item is never hidden under it (WCAG 2.4.11).

## 3. Keyboard map, and its conflicts with the board

The shell's global handler (`shell.js` 314) already returns early when **any** `dialog[open]`
exists, *except* Ctrl/⌘K which is tested first. So inside the viewer, `g`-chords, `t`, `j/k`, `/`,
`?` are already dead — the viewer owns the single-letter space. WCAG 2.1.4 (character key
shortcuts) is satisfied for the viewer because its keys are active only while it has focus.

| Key | In the viewer | Conflict checked | Ruling |
|---|---|---|---|
| ← / → | previous / next item in the set (shots, or files in a folder) | native `<video controls>` seeks on arrows; `<pre>` scrolls horizontally | Ignore when `e.target.closest('video,pre,[role=region],input,textarea')` |
| Home / End | first / last item | — | add |
| ↑ / ↓ | stage: panel → take → master (existing `#sv`) | vertical scroll of the JSON/log pane | same target guard as ←/→ |
| Space | play/pause the current take or segment | a focused button also fires on Space | Only when focus is the stage or the video; never `preventDefault` a button's Space |
| `I` | toggle the **JSON / info** pane for this item (Google Photos and Lightroom both use `i` for info) | shell `g i` (Needs you) — dead in dialogs | adopt |
| `Z` / double-click | fit ↔ 1:1 original | — | adopt |
| `X` | flip A/B in Compare (replaces Tab, F5) | — | adopt |
| `R` | redo this shot (existing) | — | keep |
| `C` | inside viewer: **copy** the JSON shown | page-level `C` = Compare (`unit.js` 785) | page `C` only when no dialog open (F1) |
| `?` | toggle the viewer's own key strip (the `.keys` row already in `#sv`) | shell `?` keysheet — dead in dialogs | adopt; do not stack the keysheet over the viewer |
| Ctrl/⌘K | palette **stacks on top** of the viewer (top layer orders correctly); Esc returns to the viewer | `shell.js` 316 fires before the dialog guard | acceptable; leave it |
| `J` / `K` | aliases of → / ← | shell `j/k` row walk — dead in dialogs | optional; costs nothing, matches the list idiom |
| Esc | layered: inner state → close (§1.3) | video fullscreen eats the first Esc natively | fine |
| Tab | normal order: header → stage → pane → footer | — | never hijacked |

Board-wide, outside this viewer's scope but found: the page-level `t`, `j`, `k`, `g`, `/`, `c` are
single-character shortcuts active page-wide; WCAG 2.1.4 wants them remappable or switchable off.
Cheap fix: a "Single-key shortcuts" toggle in the keysheet, stored per viewer in `localStorage`.
And fix the keysheet's "T M L — takes · master · log" (F9): nothing implements it and `T` is
taken by theme; drop the row (the unit page's `#jump` links already cover those sections).

Every visible button carries `aria-keyshortcuts` so SRs announce the key with the control.
## 4. Screen reader: names, announcements, alt text, captions

**Markup** (one viewer, one `<video>` — the page's existing `VIDEO` is moved in, `unit.js` 758):

```html
<dialog id="vw" class="vw" aria-labelledby="vw-t" closedby="any">
  <header class="vw-h">
    <button class="vw-x" aria-label="Close" aria-keyshortcuts="Escape" data-close>…</button>
    <h2 id="vw-t">Shot 05 · take</h2><span class="vw-n" aria-hidden="true">6 / 24</span>
    <div role="tablist" aria-label="View">  <!-- Picture | JSON  ·  panel | take | master -->
  </header>
  <div class="vw-stage" tabindex="-1" autofocus>
    <img alt="Medium through the pine stems on a Sunday morning at three hussars on horseback …">
  </div>
  <section class="vw-pane" aria-label="takes/r2v/prompts.json, item 5">…</section>
  <nav class="vw-f" aria-label="Shots">
    <button aria-label="Previous shot" aria-keyshortcuts="ArrowLeft">…</button>
    <button aria-label="Next shot" aria-keyshortcuts="ArrowRight">…</button></nav>
  <p class="sr-only" role="status" aria-live="polite" id="vw-live"></p>
</dialog>
```

- **"Image 5 of 24".** Do **not** move focus on navigation; write one line to `#vw-live`,
  debounced 250 ms so a held arrow key announces only where it lands:
  `"Shot 06 of 24, take, 6.2 seconds. ⚑ master: faces."` The visual counter is `aria-hidden` so it is
  not read twice. Live region lives **inside** the dialog (an outside one is inert — F6).
- **Alt text comes from the plan, not from filenames.** `plan.json` shot `frame` is a written
  picture description (ep12 shot 05: 143 characters — the right length for alt). Panel `img alt` =
  `frame`; take poster `alt` = `frame` + ` Motion: ` + `motion`; grid sheets = `"Storyboard grid,
  <setup>, shots 02 05 06"` (already done for running grids, `unit.js` 199). Today `#sv` says
  "panel 5" / "take 5" — replace. Thumbnails inside a labelled card button keep `alt=""` (correct now).
- **Video.** In the viewer use native `controls` (keyboard- and SR-operable for free) plus the
  custom Space binding; `aria-label="Take T05, 6.2 s"` and `aria-describedby` → the motion text.
  No autoplay with sound on open; Space or tap starts it.
- **Captions (WCAG 1.2.2).** Masters carry narration. `audio/lines/lines.json` holds every line's
  `text`, `shot` and `seconds` (ep12: 23 lines); with each shot's segment start (already computed as
  `SH[i].t0`) the board can emit `cut/master_iterN.vtt` as a plain text route — the web process
  writes text, never decodes video, so the constraint holds. `<track kind="captions" default>`.
  Mockup: hand-build ep12's VTT once to show it.
- **Status not by colour alone** (1.4.1): keep the ⚑/✓ glyph + word of the `.fl`/`.ok` spans.

## 5. The JSON / log pane

Sizes on disk (ep12): `plan.json` 43 KB, `qc_r2v.json` 18 KB, `takes/r2v/prompts.json` 24
entries, `T??.dq.json` 20–41 KB, the biggest `storyboard/eye_c7e3eb93.json` 138 KB; episode logs
≤ 47 KB (`logs/20260827135508/episode/`). All fit plain DOM — no virtualisation, which matters
because virtualised text breaks find-in-page and SR reading.

- A scrollable `<pre>` must be focusable or keyboard users cannot scroll it
  ([axe scrollable-region-focusable](https://dequeuniversity.com/rules/axe/4.10/scrollable-region-focusable)):
  `<pre tabindex="0" role="region" aria-label="plan.json · 43 KB · 1,214 lines">`.
- **Wrap, never scroll sideways**: `white-space:pre-wrap; overflow-wrap:anywhere`. Horizontal
  scrolling at 400 px fails 1.4.10 reflow and steals the swipe gesture.
- **Collapsing**: native `<details>/<summary>` per object/array over ~12 lines — keyboard and SR
  work with no ARIA tree widget (the APG tree pattern is a large, error-prone build). Prompt-sized
  strings (the `mode`/prompt text in `prompts.json`) render as wrapped prose blocks, not escaped
  one-liners.
- **Search = the browser's Ctrl+F.** Dialog content is searchable (only the inert page behind is
  not); Chromium auto-opens closed `<details>` on a find hit. No custom search box to build and get
  wrong. A small "Copy" and "Open raw ↗" (the `/lib/` URL) pair; Copy confirms via `#vw-live`
  ("Copied plan.json").
- Syntax colours each ≥ 4.5:1 on `#0f1012` and on Graphite white.
- Logs: one line per row, level as text not colour only; reuse the Activity `.ln` styles.

## 6. Phone (≥ 400 px)

**Layout under 640 px**: the viewer is full-bleed — `width:100vw;height:100dvh;max-height:100dvh;
margin:0;border-radius:0`, padding `env(safe-area-inset-top/bottom)`; no visible backdrop.
Header 48 px: Close at the **left** (Apple Photos / Material full-screen dialog put dismiss top-left;
[Material dialogs](https://m3.material.io/components/dialogs/guidelines)), title, counter.
Media fills the middle. Bottom bar 56 px + safe area: ‹ prev · Picture | JSON · next ›.
The three-stage strip already collapses to one stage (`unit.css` 471–472); keep that, with the
stage as a segmented control. JSON opens as the second tab, full height — not a half sheet, which
would leave 200 px of text at 400 px wide.

**Targets**: 44×44 px minimum (Apple HIG 44 pt; Material 48 dp; WCAG 2.5.8 floor is 24 px —
[HIG accessibility](https://developer.apple.com/design/human-interface-guidelines/accessibility)).
Current `.btn.icon` arrows in `#sv` are smaller — enlarge on phone.

**Gestures** (each has a button equivalent — WCAG 2.5.1 pointer gestures, 2.5.7 dragging):

| Gesture | Does | How, without a library |
|---|---|---|
| Swipe ← / → | next / previous | Pointer events on `.vw-stage`; commit at 25 % of width or 0.4 px/ms; ignore if it starts in the bottom 64 px (video scrubber) or in the JSON pane |
| Swipe ↓ | close | Same handler, vertical; > 120 px or fast flick. Backdrop/stage opacity follows the finger (PhotoSwipe `closeOnVerticalDrag`) |
| Pinch | zoom | **Native.** Viewport meta already allows it (`width=device-width,initial-scale=1`, no `user-scalable=no` — keep it so). Stage `touch-action: pinch-zoom` so JS gets one-finger pans and the browser keeps pinch. Disable swipes while `visualViewport.scale > 1` |
| Double-tap / double-click / `Z` | fit ↔ 1:1 | 1:1 swaps the `/thumb/320` for the `/lib/` original inside an `overflow:auto` box with `touch-action:auto`: **panning is native scroll**, momentum and all. Swipes off while 1:1; Esc or double-tap returns to fit |
| Tap | nothing hidden | **No auto-hiding chrome.** Hidden controls are invisible to SR users and to someone who doesn't know to tap |
| Back gesture | close (close watcher, §1.4) | free |

Vendored JS stays at zero (~60 lines of pointer code); PhotoSwipe v5 (MIT) is the fallback for
rubber-band pan-zoom, but it brings its own DOM and would replace `<dialog>`, not sit in it.

**One video**: swipe away from a playing take pauses it and moves the element (existing
`parkVideo`). A take never autoplays on swipe-arrival.

## 7. Reduced motion

`board.css` 94 already kills all animation/transition under `prefers-reduced-motion: reduce`.
For the viewer that means: no open/close zoom-from-thumbnail, no slide between items (cut), no
crossfade, swipe-down dismiss follows the finger (direct manipulation is the user's own motion,
WCAG 2.3.3) but **settles instantly**; no looping hover-play (already gated, `unit.js` 688); takes
never autoplay. Default (motion allowed): ≤ 150 ms opacity fade only — the palette set the house
rule of no open/close animation (`shell.css` 57), so the viewer should not out-animate it.

## 8. Test plan that costs nothing

Keyboard-only pass on `unit-finished.html#shot-05` (every §3 key, Esc layering, focus on card 9
after 5→9 + close); NVDA/Firefox and Narrator/Edge (name on open, one live line per landing, alt =
frame); `/browse` at 400×860 with touch emulation (no sideways scroll, safe area, swipes); axe-core
in both palettes; DevTools reduced-motion emulation.

## Top 8 recommendations

1. **Generalise `#sv` into one native `<dialog>` viewer** with `showModal()`, `closedby="any"` +
   the click fallback, `html:has(dialog[open]){overflow:hidden}` and `overscroll-behavior:contain`.
   No library.
2. **Fix the dialog-blind key handler (F1)**: `unit.js` page keys bail on any `dialog[open]`;
   each dialog handles its own keys. Today Space plays the master behind the keysheet.
3. **Build the chrome once, re-render only the stage (F2)**, so focus and SR position survive
   ←/→; on close, send focus to the card of the item last viewed.
4. **Keyboard map of §3**: ←/→ Home/End items, ↑/↓ stages, Space play, `I` JSON pane, `Z` 1:1,
   `X` flip (Tab is never hijacked — F5), layered Esc; `aria-keyshortcuts` on every button.
5. **Announce by one debounced polite line inside the dialog** ("Shot 06 of 24, take, 6.2 s,
   ⚑ faces"); move the toast into the top layer or the dialog (F6).
6. **Alt text = `plan.json` `frame`** (+ `motion` for takes); captions for masters as a VTT built
   from `lines.json` text + segment starts.
7. **JSON pane = focusable wrapped `<pre>` + native `<details>` + browser Ctrl+F**; no custom tree,
   no custom search, no horizontal scroll.
8. **Phone: `100dvh` full-bleed with safe-area padding, 44 px targets, swipe ←/→/↓ in ~60 lines of
   pointer events, native pinch, double-tap = 1:1 as a native scroll box, no auto-hiding chrome,
   back gesture closes.** Reduced motion: cuts, no settle animation, no autoplay.

## 2 disagreements I expect

1. **Gesture library vs hand-rolled.** A media-UX researcher will want PhotoSwipe for its
   pan-zoom physics and thumbnail zoom-in. My position: it replaces the native dialog (losing
   free inert/close-watcher/focus return), and the board's stills are ≤ 1 MP panels where native
   pinch + a scroll-box 1:1 is enough. Revisit only if the owner asks for smooth deep zoom.
2. **Initial focus on the stage, not on Close.** APG's guidance and many checkers favour the first
   interactive control or Close. I put it on the stage because arrows and Space are the viewer's
   main job and Close-first makes an accidental Enter dismiss it; the dialog name and live line
   still give SR users their bearings. Expect an a11y reviewer to push back; both are conformant.
