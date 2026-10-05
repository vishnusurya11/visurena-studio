# P02 — Motion design

Panelist P02, 2026-10-04. Lens: page transitions, state-change animation, Viewer enter/exit,
skeleton vs instant, duration/easing tokens, reduced motion, what must never move.
Builds on report 09 (`architecture/decisions/research/2026-10-04_board_design/09_liveness_motion.md`)
and does not repeat its transport ruling (pulse + morph, no SSE). This report covers the motion layer
that sits on top of it. Read-only. Evidence below was measured with `document.getAnimations()` in the
browse daemon on 8710 (mockups) and 8700 (live board).

## 0. The brick

> **A change animates only if the DOM node that shows it survives the update.**

A CSS transition runs only when a property changes *on an existing element*. Replace the element
(`innerHTML` swap, a full re-render, a new page) and nothing transitions: the new state just appears.
Every live behaviour follows from this:
- A unit flipping running→done crossfades its glyph **only if** the row keeps its id across the
  refresh. htmx already does this for elements with a stable `id`: it copies the old attributes onto
  the new node, then applies the new ones after the settle delay, so a CSS transition fires
  ([htmx docs, CSS transitions](https://htmx.org/docs/#css_transitions)). Idiomorph goes further and
  keeps the node itself ([htmx idiomorph](https://htmx.org/extensions/idiomorph/)).
- Navigation replaces the whole document, so a page change can only animate through a **snapshot**
  (View Transitions), never through CSS on nodes.
- A `<dialog>` closing goes to `display:none`, which is discrete, so it can only animate out with
  `transition-behavior: allow-discrete` plus `overlay`
  ([Chrome, entry/exit animations](https://developer.chrome.com/blog/entry-exit-animations)).

Closure check: it predicts the three gaps found below (no flip animation on the live board, no exit on
the Viewer, no page transition), and it says what to fix in each case: keep the node, take a snapshot,
or make the discrete property animatable.

## 1. What exists (measured)

| Where | Finding | Evidence |
|---|---|---|
| Live board CSS | **Two token sets disagree.** `tokens.css:59` has `--d2:200ms --d3:320ms --d4:600ms --ease-out:(.2,.8,.2,1)`. `pages.css:243` redefines `--d2:240 --d3:480 --d4:900 --ease-out:(.22,1,.36,1)` on `:root` | computed on 8700: `--d2 = 240ms`, ease `(.22,1,.36,1)`. On 8710 the mockups compute `200ms`, `(.2,.8,.2,1)`. The approved design and the board time things differently. |
| Live board CSS | 8 animation/transition durations written as raw numbers instead of tokens (`pulse 1.4s ease-in-out`, `pulse 2s`, `.tile:target pulse 1s ×3`). components.css has 2 more. | grep counts: pages.css 8, components.css 2, viewer.css 4 |
| Live board CSS | Three different "alive" loops: `breathe` 2.4 s (components), `pulse` 1.4 s / 2 s (pages, mostly overridden by `animation:none` at `pages.css:248`), `lv-sheen`/`lv-stripe` (live card). | pages.css 18, 100, 104, 137, 248; components.css 55, 198 |
| Mockup Home `index.html` | **2 infinite loops on screen**: `breathe@.live` (GPU card dot) + `breathe` on the Running chip icon | `getAnimations()` → `["breathe@live","breathe@I"]` |
| Mockup Department | **2 infinite loops**: `.live` dot + `.c.running` (spin 2.4 s in dept.css:153) | `["breathe@live","breathe@running cur"]` |
| Mockup unit-running | 1 loop (rail running step) | `["breathe@"]` |
| Reduced motion | `components.css:24` / `board.css:94`: `*{animation:none!important;transition:none!important}`. `pages.css:352` covers only `.live *`, with a 1 ms duration. | Two rules with different scope. The global one also removes the hover/focus feedback, which is not motion. |
| Viewer (mockup) | Enters with `vw-in` (200 ms, opacity plus `scale(.985)`) and **exits instantly** (`D.close()`, viewer.js:179). It also has an infinite shimmer skeleton, `.vw-skel` 1.2 s. | viewer.css:19, 128 |
| Page transitions | None on either site. The mockup sets `view-transition-name:u-unit` on the unit `h1` (unit.css:14), but no page opts in with `@view-transition`, and no source element carries the matching name. | grep |
| Live card | `.lv-rail i::before` animates `width`; `lv-sweep` animates `width` 0→100 % | pages.css:298, 351: layout properties, not compositor-only |
| Live board now | `/d/episode/…/ep17` returns **500 Internal Server Error** (foundation builder is mid-change) | `shots\panel\P02_live_ep17.png`. Live unit motion could not be measured; it was read from source. |

Screenshots: `D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\9340346d-60b6-4248-b569-c5a6fe035ef8\scratchpad\board_v3\mockups\shots\panel\`
(`P02_m_index.png`, `P02_m_department.png`, `P02_live_ep17.png`).

## 2. One motion token set (the only place durations live)

Use `tokens.css`, since it is the approved design. Delete the `:root` redefinition at `pages.css:243-246`
and keep only the live-card-specific tokens (`--breathe`, `--sheen`, `--stripe`, `--think-glow`,
`--sheen-hi`), moved into tokens.css.

```css
--d0: 0ms;      /* state that must not move */
--d1: 120ms;    /* feedback: hover, press, focus */
--d2: 200ms;    /* state change: glyph/pill colour; page crossfade; viewer enter */
--d3: 320ms;    /* arrival: tile reveal, check draw */
--d4: 600ms;    /* progress fill */
--d-exit: 140ms;/* every exit ≈ 0.7× its enter */
--d-wash: 1600ms;
--ease-out: cubic-bezier(.2,.8,.2,1);   /* enter / arrive */
--ease-in:  cubic-bezier(.4,0,1,1);     /* exit */
--ease-std: cubic-bezier(.4,0,.2,1);    /* in-place change */
```
Why these numbers: functional UI motion sits at 100–500 ms
([NN/g, animation duration](https://www.nngroup.com/articles/animation-duration/)). Exits are shorter
than entries, and an element that leaves accelerates out
([Material 3 tokens](https://m3.material.io/styles/motion/easing-and-duration/tokens-specs)). A tool
used many times a day takes Carbon's "productive" curve, not the "expressive" one
([Carbon motion](https://carbondesignsystem.com/elements/motion/overview/)). The mockup values already
match. The board's 480/900 ms values are expressive-range, which is too slow for a screen opened
80 times a day.

**Still mode is a token flip, not a second stylesheet.** Under
`@media (prefers-reduced-motion: reduce)` and under `:root[data-motion="still"]`, set
`--d2..--d4: 1ms`, keep `--d1` (a colour change on hover is not vestibular motion), set
`--d-wash: 1ms`, and set `animation-iteration-count:1` on the loops. WCAG 2.3.3 targets motion
(translation, scale, parallax), not colour ([W3C 2.3.3](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html));
[web.dev](https://web.dev/articles/prefers-reduced-motion) recommends *reducing*, not deleting. So
replace the blanket `*{transition:none!important}` (components.css:24) with this token flip.

## 3. State change: a unit flips done / failed

Data: the pulse fingerprint (report 09 §3.1) → partial refresh → the row with the same `id="wo-{id}"`
gets a new `data-state` attribute. The motion is plain CSS on that surviving node:

| Transition | Motion (once, never loops) | What reads it |
|---|---|---|
| queued → running | glyph colour `--d2 --ease-std`; the row's status icon becomes **the one loop** on the page (see §6) | `data-state` attr |
| running → done | colour crossfade `--d2`; the check path draws once (`stroke-dashoffset`, `--d3`, already `lv-draw`); row wash `--think 14 %`→0 over `--d-wash` | `.chg` added by pulse.js when `data-v` changed |
| running → failed / dead / refused | colour snaps (`--d1`); the wash uses `--accent`; **then stays still**: ✕ glyph plus a sentence, no blink | same |
| gate flagged | same as failed, with `--qc` | same |
| row inserted (new order) | `.htmx-added` → opacity 0→1 over `--d2` only, with no height or slide | htmx adds the class automatically ([docs](https://htmx.org/docs/#css_transitions)) |
| row removed / re-sorted | **instant**, no exit animation (§6) | |

A one-shot wash for a failure does not contradict report 09's "terminal states never animate". The
*arrival* of an event is an event, and it gets one wash. The *state* is still. What is banned is
looping on an alarm.

Rail progress: animate `transform: scaleX(var(--p))` with `transform-origin:left` instead of
`width`, and do the same for `lv-sweep`. Both currently animate width, which is a layout property; a
transform stays on the compositor ([web.dev, high-performance animations](https://web.dev/articles/animations-guide)).

## 4. Page transitions (View Transitions, cross-document)

- Opt in with `@media (prefers-reduced-motion: no-preference){ @view-transition{navigation:auto} }`
  in tokens.css. Chromium 126+ and Safari 18.2+ animate the navigation; Firefox simply navigates
  ([MDN](https://developer.mozilla.org/en-US/docs/Web/API/View_Transition_API),
  [Chrome cross-document guide](https://developer.chrome.com/docs/web-platform/view-transitions/cross-document)).
- Root crossfade: `::view-transition-old(root),::view-transition-new(root){animation-duration:var(--d2)}`.
  No slide: the pages are siblings in a sidebar, not a stack.
- **What must never move during navigation: the shell.** Give the sidebar `view-transition-name:shell-side`,
  the page header `shell-top` and the GPU card `shell-gpu`, then set
  `::view-transition-group(shell-*){animation:none}`. Without the names they crossfade with the root,
  and the whole frame flickers on every click. That is the most visible problem on an MPA.
- **One morphing element: the unit's name.** The mockup names the destination (`h1` = `u-unit`), but the
  source rows cannot all carry that name, because names must be unique per document. Name the clicked
  link at navigation time instead: in a `pageswap` listener, set `style.viewTransitionName='u-unit'` on
  the activated row's `.uname`. A poster on Home morphs into the unit's player the same way (`u-poster`).
  This is the documented pattern for lists (Chrome guide, "pageswap/pagereveal").
- Never on a poll and never on an htmx swap: no `transition:true`, and `htmx.config.globalViewTransitions`
  stays false. A transition snapshots the page and blocks input for its duration (report 09 §3.5).
- Never on the Back button into a page with a playing video: in `pagereveal`, if
  `navigation.activation.navigationType==='traverse'`, call `skipTransition()`.

## 5. Viewer enter / exit, and loading

- **Enter:** keep the `vw-in` opacity + `scale(.985)` at `--d2 --ease-out`. The backdrop fades
  over the same token.
- **Exit (missing today):** `dialog.vw{transition: opacity var(--d-exit) var(--ease-in), overlay var(--d-exit) allow-discrete, display var(--d-exit) allow-discrete}`,
  with `opacity:0` when the dialog is not `[open]` and `@starting-style` for the entry
  ([Chrome, entry/exit](https://developer.chrome.com/blog/entry-exit-animations)). Browsers without
  `allow-discrete` close instantly, which is what happens today, so nothing regresses.
  `jumpToActivity`'s `setTimeout(fn, 60)` (viewer.js:614) must wait for `transitionend` or
  `--d-exit`, or the scroll starts under a fading dialog.
- **Moving between items inside the Viewer is a hard cut.** No slide, no crossfade. The eye compares
  takes frame to frame (Frame.io and Lightroom cut). The `bump-l/r` 8 px nudge at the sequence ends can
  stay, but only as a one-shot, and it is off in still mode.
- **Loops behind a modal pause:** `body:has(dialog[open]) .live *{animation-play-state:paused}`. The
  owner is looking at a frame, and a breathing dot behind the backdrop competes with the picture.
- **Skeleton vs instant: instant.** Localhost answers in 2–17 ms (report 09). A skeleton helps only for
  waits of roughly 1–10 s and harms faster ones by adding a flash
  ([NN/g, skeleton screens](https://www.nngroup.com/articles/skeleton-screens/)). So remove the
  infinite `.vw-skel` shimmer. Use a **static** `--vw-panel` block shown only after a 300 ms delay
  (`animation: show 0s 300ms forwards`), so a fast load never shows it. Videos show their poster at
  once (`preload=metadata`, SPEC_v3). Fix layout with `aspect-ratio` and `width/height`, so a landing
  thumbnail never pushes content.

## 6. What must never move (the law, testable)

1. **At most one infinite animation in the viewport, and it marks the one thing running on the GPU.**
   Measured violations: mockup Home has 2 and mockup Department has 2 (§1). Rule: the GPU card dot is
   the loop on every page *except* the running unit's own page, where the rail's running step owns it
   and the GPU dot is static. The Running chip icon and `.c.running` become static glyphs in `--st-running`.
2. Digits, clocks, ETAs and counts: no rolling or counting up. They change in place in tabular-nums.
3. Row order: a re-sorted queue jumps. A slide would read as an event that did not happen.
4. Layout size: nothing grows, shrinks or slides open on a poll.
5. Alarm states loop never: failed, dead, refused and flagged get one wash on arrival, then stay still.
6. The shell (sidebar, header, GPU card) never moves during navigation (§4).
7. `.tile:target` today pulses 3× (pages.css:176). Replace that with a static `--qc` outline plus one
   `--d-wash` fade.

WCAG 2.2.2 needs a pause for any motion longer than 5 s
([W3C](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html)). The single loop plus the
`data-motion="still"` toggle (report 09 §4) satisfies it.

**How we know it worked (an automated check, $0):**
- `tests/command_center/test_motion_tokens.py` (pure file read). Fails on any `ms`/`s` duration in
  `static/css/*.css` outside tokens.css, on any `infinite` outside an allowlist of 3 selectors, and on
  a second `:root` that defines `--d[0-9]`.
- A browse check run per page (8700 `/`, `/floor`, `/d/episode`, a running unit, a finished unit):
  `document.getAnimations().filter(a=>a.effect.getTiming().iterations===Infinity).length <= 1`,
  and `== 0` with reduced motion emulated. After a forced `data-state` flip, `getAnimations()` contains
  a `CSSTransition` on `color`, which proves the node survived (the brick).
- Navigation: a 10-frame screenshot burst across `/`→unit shows the sidebar pixels identical across frames.

## Proposals

| id | page | change | effort | files |
|---|---|---|---|---|
| P02.1 | all | One motion token set in tokens.css (`--d0..--d4`, `--d-exit`, `--d-wash`, three easings); delete the pages.css:243 redefinition; tokenise the 10 raw durations | S | static/css/tokens.css, pages.css, components.css |
| P02.2 | all | Still mode as a token flip (reduced-motion + `data-motion="still"`), replacing the blanket `*{transition:none}` | S | tokens.css, components.css:24, pages.css:352, base.html (toggle) |
| P02.3 | home, dept, floor, book | One-loop law: the GPU dot or the running step is the only infinite animation; Running chip and `.c.running` become static | S | components.css:55/198, pages.css:18/100/104/137, mockup dept.css:153, v2.css:111 |
| P02.4 | dept, floor, home, unit | State flips animate on surviving nodes: stable `id="wo-{id}"`, `data-state`, `--d2` colour, one wash (`--think`/`--accent`/`--qc`), check-draw on done, `.htmx-added` fade-in | M | templates/_rows.html, _floor.html, _attention.html, _orders.html, pages.css, (pulse.js from report 09) |
| P02.5 | all | Cross-document View Transition: root crossfade `--d2`, shell named and frozen, `u-unit`/`u-poster` named at `pageswap`, skipped on traverse | M | tokens.css, base.html (one small script), unit.html, _rows.html |
| P02.6 | Viewer | Exit animation (`allow-discrete`, `--d-exit`), `@starting-style` enter, hard cut between items, page loops paused while it is open, `jumpToActivity` waits for close | S | assets/viewer.css, viewer.js (then the board copy) |
| P02.7 | Viewer, tiles | No shimmer skeletons: a static placeholder after a 300 ms delay, poster-first video, `aspect-ratio` on every thumb | S | viewer.css:128, components.css `.pic` |
| P02.8 | unit live card | Rail fill and done sweep on `transform:scaleX` instead of `width` | S | pages.css:298, 351 |
| P02.9 | tests | `test_motion_tokens.py` lint plus a browse loop-count check per page | S | tests/command_center/test_motion_tokens.py, a script in the work folder |
| P02.10 | unit `#tile:target` | Replace the 3× pulse with a static outline plus one wash | S | pages.css:176 |

Publishable: the "surviving-node" motion rules (one-loop law, token flip for still mode, the motion
lint, the `getAnimations()` loop check) could ship as a small `htmx-motion` CSS + checker. It pairs
with report 09's `htmx-pulse`.

## I will argue against

1. **Skeleton shimmer and count-up numbers "to feel premium"** (a visual-polish lens). On localhost a
   skeleton only flashes (NN/g). A rolling digit makes the ETA look as though it changed meaning, and
   each one adds a loop, which breaks the one-loop law. Premium here means *instant and calm*.
2. **`hx-swap="… transition:true"` / `globalViewTransitions` on htmx refreshes** (a "dynamic" lens). A
   View Transition snapshots the whole page and blocks input. At a 2 s pulse it makes the board
   stutter and swallow clicks. View transitions are for navigation only, and polls morph.
3. **Animated re-sorting (FLIP) of the queue, or a pulsing red badge on failures** (an ops/dashboard
   lens). A slide reads as an event that did not happen, and a blinking alarm trains the eye to ignore
   it and fails 2.2.2 once it runs past 5 s. One wash on arrival, then stillness.
