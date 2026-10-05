# P09 — Visual polish & consistency (UX panel, 2026-10-04)

Lens: type scale, spacing rhythm, radii, iconography, empty and error states, microcopy, dark-theme
craft (elevation without shadows), consistency page↔page and mockup↔live board. Read-only.

Evidence (screens, 1440×900, under `mockups\shots\panel\`): `p09_mock_now.png`, `p09_mock_queue.png`,
`p09_mock_dept.png`, `p09_mock_unitrun.png`, `p09_mock_unitrun_light.png`, `p09_live_home.png`,
`p09_live_dept.png`, `p09_live_404.png`. Computed-style census script: `tools\p09_type.js`.

## 0. The headline: the mockups are good, so polish is now *drift control*

The owner already said the mockups are "the direction". What makes a dark tool feel premium after
that is not new ornament. It is that nothing is off by 1 px, one word or one shade between pages.
Linear's 2024 redesign reports the same thing: most of the work was cutting down and aligning
existing elements, not adding new ones (https://linear.app/now/how-we-redesigned-the-linear-ui).
The measurements below show the drift has already started, and the port to the live board is
when it gets locked in.

## 1. Findings, measured

### 1.1 Two real visual bugs that will port straight to the live board
- **The live dot in the sidebar GPU card renders 0 px wide** (computed `width: 0px; height: 6px`
  on Now, Queue and unit-running; 6 px only on Department, where the text is shorter). It shows as a
  grey sliver "▌On the GPU" instead of a breathing blue dot (`p09_mock_now.png`, bottom left).
  Cause: `.gpu-card .t1` is `display:flex` and the empty `.live` span shrinks. Fix: `flex:none`.
  The same rule was copied into `static/css/components.css:198`.
- **A class-name collision in the live CSS:** `pages.css:249` defines a global `.live{padding:14px
  18px 12px;margin:12px 0 16px;border-top:3px solid var(--ink);…}` for the unit live card, and
  `_shell.html:47/54` uses `<span class="live">` for the GPU-card dot. `@layer pages` beats
  `@layer components` whatever the specificity (https://developer.mozilla.org/en-US/docs/Web/CSS/@layer),
  so once the re-skin is served, the sidebar dot will be drawn as a padded, bordered box on every
  page. Rename the dot `.gc-dot`, or scope the page rule to `section.live`.

### 1.2 Type scale: about 33 distinct text styles per page; the target is about 8
Census of rendered text nodes (size × weight × family), mockups:
Now 33 combinations, Queue 22, Department 24, unit-running 35. The sizes used are 9, 10, 11, 12,
13, 13.33, 14, 15, 16, 22, 24, 26, 34, 40, 42, 60 px. In the source, live `pages.css` alone has 22
font sizes, including half-pixel ones (9.5, 10.5, 11.5, 12.5, 13.5). `viewer.css` adds 12.5/13.5.
- Too small to read: unit-running draws 9 px mono ×8 and 10 px mono ×70 (the step-rail
  "01 cached" sub-labels and the dock). At 9–10 px, Plex Mono on #16171a reads as grey fuzz, even
  where the contrast passes.
- Mono is everywhere. DIRECTION_v2 says "mono only for ids, timestamps, numbers", but about 45% of
  the text nodes on Now, and about 60% on unit-running, are Plex Mono (for example "published ▲ ·
  not acked" and "Last words").
- `13.33px Arial` appears once on every page: a `<button>`/`<input>` that does not inherit the font
  (form controls default to the UA font). Add `button,input,select,textarea{font:inherit}` in base.
- Best practice: a named, token-driven scale with roles instead of raw px values (Material 3 type
  tokens https://m3.material.io/styles/typography/type-scale-tokens; Radix Themes 9-step scale
  https://www.radix-ui.com/themes/docs/theme/typography). Proposed roles, all already used somewhere:
  `--t-micro 11/14` (floor; nothing below 11), `--t-label 12/16 500`, `--t-body 13/18`,
  `--t-lead 14/20`, `--t-title 16/20 600 Barlow`, `--t-h2 24/28 Barlow`, `--t-h1 34/38 Barlow`,
  `--t-hero 60/60 Barlow`. Mono keeps exactly two sizes (11, 12) and `tabular-nums` (already set in
  live `components.css:11`, missing in 4 of the 6 mockup sheets).

### 1.3 Radii: 10 values in use; the tokens define 4
Rendered border-radius on Now: 6px×111, 4×51, 8×49, 3×16, 999×14, 10×14, 7×12, 5×8, 2×3, 50%×10.
`unit.css` alone writes 20 different radius literals, and `viewer.css` writes 15. The tokens are
`--r-ctl 6`, `--r-pic 8`, `--r-card 10`, `--r-pill` (plus `--r-1 2`, `--r-2 4` for bars and kbd).
3, 5 and 7 px are drift. Nested radii should follow outer = inner + padding: a 10 px card holding
an 8 px picture at 10 px padding should be 18 px, or the picture 0 px. In the hero, the 8 px
poster sits 12 px inside a 10 px card, so the corners do not line up concentrically. Either use
`--r-pic: calc(var(--r-card) - 2px)` with tight padding, or accept the mismatch and keep only
these 4 radii. Lint it: stylelint `declaration-property-value-allowed-list` for `border-radius`
→ `var(--r-*)|0|50%` (https://stylelint.io/user-guide/rules/declaration-property-value-allowed-list/).

### 1.4 Colour: hard-coded values that skip the theme
- `unit.css`: `#e9b44c`×13, `#fff`×16, `#86cf95`×4, `inset 2px 0 0 #c8952a/#5aa76a`. These are the
  dark-theme state colours written as literals, so in Graphite they stay dark-theme amber and green
  (the light theme's `--st-flagged` is `#8a5a00`). The Graphite screenshot looks fine only because
  the page shows no flagged chip there.
- `viewer.css` brings in Tailwind-palette literals for the JSON/prompt viewer: `#c4b5fd #f5a3c7
  #67e8f9 #fdba74`. These are a fifth and sixth hue family that appear nowhere else on the board.
  Map them to `--viz-*`/`--st-*` tints or define `--syn-*` tokens with light variants.
- In live `components.css` the header says "no colour is written here that tokens.css does not
  name", but the `.sb-mark` gradient `#2a2d33→#15171a` does exactly that. Small, but it is the rule.

### 1.5 Elevation on dark: mostly right, keep it that way
Material's dark-theme guidance: express elevation with lighter surfaces, not shadows
(https://m2.material.io/design/color/dark-theme.html#properties); Atlassian's elevation tokens
pair each surface with one shadow (https://atlassian.design/foundations/elevation). In the
mockups, `unit.css`/`dept.css` box-shadows are almost all `inset 0 0 0 1px` rings or 2–3 px inset
state bars, which is correct. Two drifts to fix: `--e-2` is a drop shadow (`0 2px 6px rgb(0 0 0/.3)`)
that does nothing on #0f1012, and `--e-3` means a 1 px ring in dark but a 28 px blur in light, so
one token means two different things. Define elevation as surface + ring: `--e-1 = surface`,
`--e-2 = surface-2 + ring rule-2`, `--e-3 = overlay + shadow-pop` (only floating things like the
palette, menus, toast and viewer get a real shadow).

### 1.6 Microcopy: one thing, four names
- The owner-attention bucket is called **Inbox** (sidebar), **Needs you** (Now section title,
  department filter, live nav), **flagged** (state pill) and **shipped with flags, not acknowledged**
  (sub-line). The counts also differ: 5 on the mockups, 6 on the live board. Choose one noun for
  the place ("Needs you") and one for the state ("flagged"), and rename the sidebar to match.
- The home page is called "Now" in DIRECTION_v2, "Home" in the sidebar and h1, "Studio home" in
  the live h1, and the 404 link says "Studio home". Choose one.
- Breadcrumb roots vary between pages: Now "Studio › Home"; Queue "Queue" (no root); Department
  "Studio › Departments › Episode"; unit "Episode › The War of the Worlds › ep17" (no Studio, and
  "Episode" here links to the department). Rule: the crumbs always start at the sidebar section,
  and the page h1 never repeats the last crumb.
- The header chip says "live · 19:21" on unit-running, while the hero on the same page says
  "snapshot 19:34 · not live". These are two clocks that contradict each other. The chip must come
  from the same vital as the hero (live / stale Ns / snapshot).
- Data leaks into the copy: the ep17 question renders as "Today, can the brother (grey eyes, Brown
  herringbone Norfolk jacket grey with road dust and salt spray) get the women aboard…". A
  description of a character's look has been interpolated into the logline (likely the brief's
  name-expansion rule). The board should show the plan's raw question or strip parentheticals.
  Flag this to the episode owner as well.
- Case: DIRECTION_v2 says sentence case, but the live empty-state strings are lowercase fragments
  ("nothing needs you", "idle — nothing is running", "none yet"). Sentence case with a reason and
  a next step works better (NN/g on empty states: https://www.nngroup.com/articles/empty-state-interface-design/).
  For example, "Nothing needs you. The last flag was cleared 2 h ago." and "The GPU is idle. Next
  in the queue: ep01, about 2 h 38."
- "Last words super().__init__(loader)" puts a raw Python line in hero position. Keep it, because
  the owner reads logs, but give it a muted mono 12 line with a "log ›" link, not a framed card at
  hero weight.

### 1.7 Empty, loading and error states
- **404 and 500 are off-brand:** `templates/404.html` hard-codes the retired beige
  (`#f6f3ec`/`#1d1a16`) in an inline `<style>` and does not extend `base.html`. After the re-skin,
  it is the only beige page left (`p09_live_404.png`). It should be the shell with a body card:
  the code, a plain sentence, what was asked (`/d/episode/…/ep99`), and links to Now and the
  nearest parent (NN/g error guidelines: https://www.nngroup.com/articles/error-message-guidelines/).
- **Lazy sections flash empty:** on the first screenshot of unit-running, "Panels on disk now" was
  a heading over blank space, and the strip filled in later. Queued rows on the department page
  show an empty grey square where the face goes. Reserve the space with aspect-ratio skeleton
  tiles (`--surface-2` with a 1.2 s shimmer, disabled under reduced-motion), and use a clapperboard
  glyph for "no picture yet" (https://www.nngroup.com/articles/skeleton-screens/).
- **The live ep17 page took more than 15 s to reach DOMContentLoaded** (the browse goto timed out).
  Whatever the perf panel decides, the polish fix is the same: serve the shell and the hero first,
  and stream the heavy parts in with skeletons, so the page never shows a blank white or black
  screen.
- **A tab strip wraps at 1440 px:** the unit dock tabs "Now · Shots · Gates · Runs · Files" push
  "Activity" onto a second line (`p09_mock_unitrun.png`, right column). Use a segmented control
  that scrolls horizontally, or move Activity behind an overflow ⋯.

### 1.8 Iconography
Lucide is the set, at 16 px with a 1.75 stroke in the sidebar. `unit.css` sets `stroke-width` 11
times with different values, and the flag glyph appears as a Lucide icon, the Unicode ⚑ (live and
mockup chips "Panels ⚑531") and a coloured square. Rule from Lucide's own guide: one stroke width
per size step (https://lucide.dev/guide/design/icon-design-guide). Use 16/1.75 in UI and 14/2 in
chips, from the sprite (`static/icons.svg` exists now), and never use Unicode glyphs for state.

### 1.9 Spacing rhythm
The tokens give a 4/8 scale (`--sp-1..8`: 2,4,8,12,16,24,32,48). The mockups mostly follow it.
The live `pages.css` still carries v1 paddings (`14px 18px 12px`, and 10/14 px), which are off
the scale. Card internals should be 16 (dense) or 24 (hero), section gaps 32, and the page gutter
24, set by tokens only.

### 1.10 Mockup ↔ live: two theming switches
The mockups switch theme with `data-palette="studio|graphite|white|slate"` (v2.css still keys off
the three retired palettes). The live board uses `data-theme="light"`. Anything ported literally
from v2.css under `[data-palette=…]` will silently never apply. Standardise on `data-theme`, and
delete the retired palette selectors from the mockup sheets before they are copied again.

## 2. How to know polish is holding (the closure test)
1. **The census as a test.** Run `tools\p09_type.js` (or a pytest+Playwright twin) against each live
   page and assert: at most 10 text-style combinations, no font-size below 11 px, no non-token
   radius, no `Arial`. This makes "consistent" a number that can regress, not a feeling.
2. **Visual snapshots.** Playwright `toHaveScreenshot` per page × theme at 1440 and 390, with masks
   over clocks and ETAs (https://playwright.dev/docs/test-snapshots). The mockup screenshots are
   the first baselines, and a diff above 2% fails.
3. **A token lint.** stylelint allowed-lists for `color`, `border-radius`, `font-size` and
   `box-shadow` in `static/css/*`: values must come from `var(--…)`. `tokens.css` is the only
   exemption. This is free, runs in CI and spends no credits.

## Proposals (ranked)

| id | page | change | effort | files |
|---|---|---|---|---|
| P09.1 | every page (shell) | Rename the GPU-card dot to `.gc-dot` + `flex:none`; fixes the 0 px sliver and the `.live` layer collision | S | `templates/_shell.html`, `static/css/components.css`, mockup `assets/v2.css` |
| P09.2 | every page | Type-role tokens (`--t-micro…--t-hero`, 8 roles, 11 px floor, mono only for ids/numbers/times) and replace raw px | M | `static/css/tokens.css`, `components.css`, `pages.css`, mockup `unit.css`/`viewer.css` |
| P09.3 | all | One vocabulary: "Needs you" (place), "flagged" (state), "Now" or "Home" (one), breadcrumbs rooted at the sidebar section; one string table in `shell.py` `PAGES` | S | `shell.py`, `templates/_shell.html`, `_attention.html`, `home.html`, `unit.html` |
| P09.4 | 404/500 | Error pages extend `base.html`: shell, card, the path asked for, links to Now and its parent; retire the beige inline style | S | `templates/404.html`, `app.py` (error handler context) |
| P09.5 | unit, dept, home | Skeleton tiles with reserved aspect-ratio for lazy picture strips; a clapperboard glyph for "no picture yet"; a shell-first render for the slow unit page | M | `templates/unit.html`, `_unit_live.html`, `components.css`, `static/progress.js` |
| P09.6 | unit, viewer | Remove hard-coded colours (`#e9b44c`, `#fff`, Tailwind `#c4b5fd…`) in favour of `--st-*`/`--viz-*`/new `--syn-*` tokens with Graphite values | S | mockup `unit.css`, `viewer.css` → their live ports; `tokens.css` |
| P09.7 | all | Radius allowed-list: `--r-1/2/ctl/pic/card/pill`, 50%, 0; drop 3/5/7/9/13/14 px | S | all CSS + stylelint config |
| P09.8 | header chip | The "live · HH:MM" chip reads the same vital as the hero (live / stale Ns / snapshot) so the two clocks never disagree | S | `templates/_shell.html`, `shell.py`, `vitals.py` |
| P09.9 | empty states | Sentence-case empty states with reason + next step ("The GPU is idle. Next: ep01 ~2 h 38.") | S | `_attention.html`, `_floor.html`, `_today.html`, `_tails.html`, `unit.html` |
| P09.10 | tests | Style census + Playwright screenshot baselines + stylelint token lint, all free and offline | M | `tests/command_center/test_style_census.py`, `tools/p09_type.js` (port), `package.json`/`.stylelintrc` |
| P09.11 | elevation | Redefine `--e-1..3` as surface + ring; real shadow only on floating layers; one meaning per token in both themes | S | `tokens.css`, `components.css` |
| P09.12 | unit dock | The dock tabs stop wrapping: a scrollable segmented control, or Activity behind ⋯ | S | mockup `unit.css` → live `pages.css`, `unit.html` |
| P09.13 | unit hero | Logline shows the plan's question without interpolated appearance text; "Last words" demoted to a muted log line | S | `unit_view.py`, `unit.html` |
| P09.14 | theming | One switch: `data-theme`; delete `[data-palette=graphite|white|slate]` selectors before porting | S | mockup `v2.css`, `shell.js` → live `tokens.css` |

## I will argue against

1. **"More motion makes it feel alive" (a liveness/motion lens likely proposes animated counters,
   rolling digits, shimmering progress bars and per-row pulses).** SPEC 09 already ruled one animation
   per viewport. The mockups already have three things breathing at once on Now (the hero spinner,
   the sidebar GPU dot and the rail's active segment). In a tool opened many times a day, motion
   that is always on becomes noise the eye learns to ignore, which removes the one signal that
   matters (something changed). Animate change, and only change: a 600 ms morph when a value
   updates, then stillness (https://m3.material.io/styles/motion/overview).
2. **"Add drop shadows / glass / gradients for depth" (a visual-hierarchy or 'premium feel' lens).**
   On #0f1012 a drop shadow is invisible, and glass blurs text that sits over posters. Elevation on
   dark is surface lightness plus a 1 px ring (Material dark theme; Linear dark). The sb-mark
   gradient is the only decoration the design needs.
3. **"Toasts for every update" (a notifications lens).** The owner is one person watching one GPU.
   A toast every time a step ticks over trains them to dismiss toasts. Keep toasts for receipts of
   the owner's own actions (hold, acknowledge, redo). State changes belong in place (the morph) and
   in the Since-14:02 feed. Only the SPEC 09 notification table (a unit finished, failed or needs
   you) is allowed to interrupt.
