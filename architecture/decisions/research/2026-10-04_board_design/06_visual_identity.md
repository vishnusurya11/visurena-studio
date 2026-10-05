# 06 — Visual identity & design system

Researcher 06, 2026-10-04. The question: blend four looks (film-studio dark tools, modern SaaS,
ops monitors, the warm "paper" editorial org chart) into **one** identity, with a token table,
a state colour system with measured contrast, icons, imagery, and a ruling on the token test.

Evidence read: `current/*.png` (home, dept, unit_ep17, unit_ep12), `studio/command_center/templates/base.html`
(419 lines of CSS), `studio/command_center/views.py` (`GLYPHS`, `COLOURS`), `architecture/index.html`
`:root`, `tests/test_the_board_copies_the_org_charts_tokens.py`, `../2026-09-25_command_center/D_ui_design.md` §2.
Every contrast number below was computed with the WCAG 2.x relative-luminance formula
(script: scratchpad `cr.py`, not committed), not estimated.

## 1. The brick: what the four looks each contribute (and what they don't)

The four references are not four styles; each one solves a different *surface*:

| Look | What it actually solves | Source | What we take | What we refuse |
|---|---|---|---|---|
| Film-studio tools (Frame.io V4, Resolve) | **Judging pictures.** Media must sit in a neutral, dark surround so the eye is not colour-biased. Resolve is dark "because grading is done in a darkened room"; the bias-light rule is a *neutral grey*, not a warm one. Frame.io V4 (Vapor) tunes surfaces in LCH "to make media look vivid and luminous". | [Resolve forum](https://forum.blackmagicdesign.com/viewtopic.php?f=21&t=65628), [Cubie: mid-grey](https://www.cubiecolor.com/post/what-is-mid-grey-and-the-importance-of-18-midtone-grey-in-color-grading), [Frame.io V4 design](https://blog.frame.io/2024/05/21/frame-io-v4-web-app-beta-feature-focus-new-design-smooth-navigation/) | a neutral **stage** surface for every frame, take, panel and master | making the whole board dark: the board is mostly reading, not grading |
| Modern SaaS (Linear, Vercel Geist) | **A token system that is generated, not hand-picked.** Linear went from 98 variables per theme to 3 inputs (base, accent, contrast) in LCH and *reduced chrome colour*; Geist gives every hue a 10-step scale with fixed jobs (100–300 fills, 400–600 borders, 700–800 solids, 900–1000 text). | [Linear redesign](https://linear.app/now/how-we-redesigned-the-linear-ui), [Geist colors](https://vercel.com/geist/colors) | role-named tokens (fill / border / solid / text per state), quiet chrome so state colour is the only colour | Inter, purple-gradient SaaS chrome, 8px-radius cards everywhere |
| Ops monitors (Carbon status, Grafana, Dagster) | **State legibility at a glance and colour-blind.** Carbon: a status indicator uses "at least two of colour, shape, symbol", with "at least 3:1 between the indicator and the page background". | [Carbon status pattern](https://carbondesignsystem.com/patterns/status-indicator-pattern/), [WCAG 1.4.11](https://www.w3.org/WAI/WCAG21/Understanding/non-text-contrast.html) | glyph + word + colour on every state; a contrast test | traffic-light row fills (already rejected in D_ui_design §2) |
| Editorial paper (the org chart; Criterion, Kinfolk, A24) | **Hierarchy by type and rule, not by boxes.** Heavy 3 px ink rules, condensed display heads, mono eyebrows, generous measure. Teenage Engineering shows the same discipline in hardware: chrome is "black, white and three greys", radius 0, no shadows, colour reserved for meaning. | [Criterion redesign](https://www.criterion.com/current/posts/5617-welcome-to-our-new-site), [TE: constraints as aesthetic](https://blakecrosley.com/guides/design/teenage-engineering) | paper/ink, Barlow + Plex, 3 px ink rules, 0–2 px radii, flat | serif body text, decorative imagery, pull quotes |

**The reconciliation rule (one sentence):** *paper is the office, stage is the screening room,
ink is the voice, and colour means state — nothing else gets colour.*

- **Paper** (warm, light or dark) carries everything you *read*: tables, ladders, verdicts, logs, the org chart.
- **Stage** (neutral, always dark, chroma 0) carries everything you *look at*: thumbnails, take tiles, the
  live sheet, the master player, the lightbox. It is dark in both themes — a picture is judged against
  the same surround whether the page is light or dark.
- **Ink** (Barlow display + Plex) carries hierarchy; no coloured headings, no coloured links.
- **State colour** is the only chroma on the page outside the stage. The brand accent stays on the org
  chart (owner node, agent stripes) and the focus ring; on the board, red means *failed* and nothing else.

This is how a premium studio tool actually behaves: Frame.io's chrome is near-monochrome so media
reads; Linear's is near-monochrome so status reads. Our paper does both jobs at once.

## 2. When paper, when dark

| Surface | Light theme | Dark theme ("screening room") | Why |
|---|---|---|---|
| page, tables, cards | `--paper` #f6f3ec | `--paper` #181613 (warm graphite, unchanged) | the org chart's identity; warm dark is calmer next to a terminal than #000 |
| raised (lane, sheet tray, row hover) | `--paper-2` #eee9df | `--paper-2` #211e1a | elevation by tone, not shadow |
| **media well** (`.frame`, `.tile`, `.lt`, `video`, lightbox body) | `--stage` #121212 | `--stage` #0e0e0e | neutral surround for judging; currently thumbs sit on `--code` beige and the master on `#000` — two different surrounds |
| missing picture | `--stage-2` #1b1b1b + 1 px dashed `--stage-line` | same | today an unshot take is a beige box (`unit_ep12.png` T02–T23) indistinguishable from a beige frame |
| overlays (menu, lightbox, dialog) | `--paper` + `--e3` shadow | `--paper-2` + 1 px `--rule-2` border, no shadow | shadows vanish on dark; lighten instead (Geist/Material practice) |

**A dark mode that is a true studio dark?** No new theme. The existing dark theme becomes the
"screening room": same warm hue, ink-3 lifted to pass AA, and the stage drops one step darker so
media still pops. A third "full Resolve grey" theme was considered and rejected: the owner glances
next to a terminal, three themes triple the contrast test, and the stage already gives the neutral
surround where it matters.

Phone (≥ 400 px): the stage goes edge-to-edge (negative 16 px inline margin) for the master and
the live sheet — the media becomes the page, as in Frame.io's mobile viewer.

## 3. State colour system

Current problems found (each verified in code or screenshots):
1. `--ink-3` #7d7566 is used for `.muted`, `th`, `.eyebrow`, timestamps — **4.11:1 on paper, 3.77:1 on
   paper-2: fails AA text** (4.5:1). Most of the board's secondary text is below the line.
2. `--qc` #5f4b1c, the "amber" flagged colour, is a dark olive-brown. In `dept.png` the flagged minibar
   segments read as brown and merge with the dark green done segments.
3. **The same state has three colours.** `deferred` is purple in `views.COLOURS`, blue (`--think`) in
   `.live[data-vital="deferred"]`, and amber (`--qc`) in `.lv-rail .st-deferred`. `stale` is red in
   `COLOURS`/`.tpill.stale` but "hollow green, dashed" in the D_ui_design spec.
4. **Bar segments are separated by hue only.** Measured luminance contrast between adjacent state
   fills in light theme: done↔failed **1.01**, done↔flagged 1.08, running↔deferred 1.09. To a
   deuteranope, done and failed segments in `.sbar`/`.minibar` are the same bar. No choice of five
   hues inside the AA range fixes this (tried; the best flagged/done split is 1.72), so **pattern must
   carry the attention states** (see "bar" column).
5. `✋` (escalated) renders as a yellow colour emoji on Windows (visible in every legend screenshot);
   `○` queued and `◌` blocked are indistinguishable at 12 px.

**The system:** each state has four role tokens, Geist-style: `fg` (text, glyph, border),
`bg` (tint fill behind a pill/chip), `bar` (segment fill), plus a mandatory icon and word.
The one-glance rule from D_ui_design stands: red = needs a developer, ink = needs the owner,
amber = audit later, purple = next pass, blue = moving.

| state | icon (Lucide) | fg light | fg dark | bg light / dark | bar treatment | contrast fg vs paper / paper-2 — light | — dark | on stage |
|---|---|---|---|---|---|---|---|---|
| running | `loader` ring, pulses | `#1f5a86` | `#7db6e3` | `#e1ebf4` / `#16283a` | solid fg + moving sheen (exists) | 6.61 / 6.06 | 8.32 / 7.64 | 8.63 |
| done | `check` | `#2f6b3a` (=`--ok`) | `#86cf95` | `#dfeee2` / `#18301d` | solid fg | 5.77 / 5.28 | 9.78 / 8.99 | 10.15 |
| flagged | `flag` + count | `#8a5a00` (true amber) | `#e9b44c` | `#f6e7c4` / `#36280c` | solid **`#b07a12`** (lighter tier, 1.72 vs done) | 5.35 / 4.90 | 9.54 / 8.77 | 9.90 |
| deferred | `corner-up-left` | `#6a3b8f` (=`--invent`) | `#c7a3e3` | `#ece3f3` / `#2c2035` | fg at 100% with 2 px **dotted** top edge | 7.19 / 6.59 | 8.41 / 7.73 | 8.72 |
| failed | `x` | `#b42d1a` | `#f2735a` | `#f8e1db` / `#3d1a13` | fg with **45° hatch** (paper 2 px / fg 4 px) | 5.69 / 5.21 | 6.34 / 5.83 | 6.58 |
| escalated | `hand` (SVG, not emoji) | `--ink` | `--ink` | solid ink, paper text (15.64) | solid ink + 2 px ink outline | 15.64 / 14.33 | 14.64 / 13.46 | 15.19 |
| held | `pause` | `#6b6457` | `#a39b8b` | none | **neutral hatch** (`--rule-2`/paper) | 5.28 / 4.84 | 6.55 / 6.02 | 6.80 |
| stale | `history` | done fg | done fg | none; **dashed** border | done hue at 40% + dashed outline | 5.77 / 5.28 | 9.78 / 8.99 | 10.15 |
| queued | `circle` | `--ink-3` | `--ink-3` | none | `--rule` empty | 5.04 / 4.62 | 5.85 / 5.38 | 6.07 |
| blocked | `circle-dashed` | `--ink-3` | `--ink-3` | none | `--rule` + dashed outline | same | same | same |
| skipped | `minus` | `--ink-3` | `--ink-3` | none | 40% done tint (exists) | same | same | same |

Every fg passes 4.5:1 (text) against paper, paper-2 *and* its own tint in both themes (lowest:
flagged-light on its tint 4.84). Solid pills: white on failed-light 6.30; paper-dark on failed-dark 6.46.
On the stage the state tokens always resolve to their **dark** values (a tile badge in light theme
sits on #121212), so badges are written `.on-stage{ --st-*: <dark values> }`.

The brand accent is split from failed: `--accent` stays #a4341f/#e0664c for the org chart and the
2 px focus ring (6.13:1 on paper); the board's failed is `--st-failed` (#b42d1a), cooler and redder.
Stale changes from red to the D_ui_design spec (dashed done hue): stale is "was good, now old", not broken.

## 4. Proposed token table

Naming: `--<role>` for neutrals, `--st-<state>[-bg|-bar]` for states, `--sp-n`, `--r-n`, `--e-n`,
`--t-<role>`. Shared core = the org chart's names (unchanged where unchanged, so the org chart keeps working).

### 4.1 Neutrals (shared core)

| token | light | dark | job | change |
|---|---|---|---|---|
| `--paper` | #f6f3ec | #181613 | page | — |
| `--paper-2` | #eee9df | #211e1a | raised surface, row hover | — |
| `--ink` | #1d1a16 | #ece7dc | text, display, 3 px rules, escalated | — |
| `--ink-2` | #4d473d | #c3bbab | secondary text (7.60 / 8.81 on paper-2) | — |
| `--ink-3` | **#6f6759** | **#9a9282** | tertiary text, eyebrows, th (5.04 / 5.85) | darkened/lifted to pass AA |
| `--rule` | #d6cfc0 | #3a352d | hairlines, empty segment | — |
| `--rule-2` | #bfb6a3 | #4d473d | control borders | — |
| `--line` | #9c937f | #6a6254 | tree connectors (non-text, 2.75 / 3.00) | — |
| `--code` / `--code-ink` | #e9e4d7 / #3b352c | #2a2621 / #d8d1c2 | inline code | no longer a thumbnail background |
| `--accent` / `--accent-ink` | #a4341f / #fff | #e0664c / #1d1a16 | org-chart owner + agent stripe, focus ring | board stops using it for state |
| `--stage` | #121212 | #0e0e0e | media well | **new** |
| `--stage-2` | #1b1b1b | #171717 | missing frame, tray behind tiles | **new** |
| `--stage-line` | #3a3a3a | #2e2e2e | frame hairline, dashed placeholder | **new** |
| `--stage-ink` / `--stage-ink-2` / `--stage-ink-3` | #e6e6e6 / #a8a8a8 / #8a8a8a | same | text on stage (15.0 / 7.24 / 5.43) | **new** |
| `--scrim` | rgba(0,0,0,.62) | same | label backing on a picture | **new** (replaces `.tile .size` inline rgba) |

### 4.2 Space, radius, elevation, motion

| token | value | used for |
|---|---|---|
| `--sp-1 … --sp-8` | 2, 4, 8, 12, 16, 24, 32, 48 px | 4 px base (Carbon/Geist both 4/8). Today's paddings `1px 5px`, `2px 7px`, `3px 9px`, `3px 10px`, `2px 9px 2px 7px` collapse to `--sp-1/--sp-3` (chip) and `--sp-2/--sp-4` (button) |
| `--gutter` | 16 px (phone) / 24 px (≥ 960) | page inline padding |
| `--r-0` | 0 | frames, stage, tables, rules (TE/Criterion straight cut) |
| `--r-1` | 2 px | chips, tiles, segments, badges |
| `--r-2` | 4 px | buttons, inputs, menus |
| `--r-pill` | 999 px | **state pills only** (so a rounded shape *means* state) |
| `--e-0` | none | default; paper is flat |
| `--e-1` | `inset 0 -1px 0 var(--rule)` | row separation |
| `--e-2` | `0 1px 0 var(--rule-2), 0 2px 6px rgb(29 26 22 / .06)` | sticky action bar, live card |
| `--e-3` | `0 8px 28px rgb(29 26 22 / .18)` light; dark: none + `--rule-2` border | menu, lightbox |
| motion | keep `--d1..d4`, `--ease-out`, `--ease-std`, `--breathe` | **move into the core block** (today a second `:root` dodges the byte test) |

Radii today: 1, 2, 3, 50%, 999 px across 25 rules → four values with jobs.

### 4.3 Type scale

Today `base.html` uses **23 distinct font sizes, 11 of them under 14 px** (9, 9.5, 10, 10.5, 11, 11.5,
12, 12.5, 13, 13.5 …). The proposal keeps the three faces and their jobs and cuts to nine roles, anchored
on Carbon's productive set (14/20 body, 12/16 label) — the IBM Plex family's own native scale
([Carbon type sets](https://carbondesignsystem.com/elements/typography/type-sets/)).

| token | face | size / line-height | weight | tracking | used for |
|---|---|---|---|---|---|
| `--t-hero` | Barlow Condensed | 72/62 (phone 44/40) | 700 | −0.01em | live card countdown `11:44` |
| `--t-h1` | Barlow Condensed | 36/38 (phone 30) | 700 | .01em | page title, `ep17` |
| `--t-h2` | Barlow Condensed | 24/28 | 700 | .01em | book group, unit subtitle, `lv-sentence` |
| `--t-h3` | Barlow Condensed | 18/22 | 600 | .02em | department card, step name (uppercase allowed) |
| `--t-body` | Plex Sans | 14/20 | 400; 600 for emphasis | 0 | prose, table cells |
| `--t-small` | Plex Sans | 13/18 | 400 | 0 | meta lines, notes, reasons |
| `--t-mono` | Plex Mono | 12/16 | 400/500 | 0 | ids (`ep17`, `T05`), timestamps, paths, pills |
| `--t-label` | Plex Mono | 11/16 | 500 | .12em, uppercase | eyebrow, `th`, legend |
| `--t-micro` | Plex Mono | 10/12 | 500 | .02em | tile ids, rail labels, badges — **floor; nothing below 10** |

All numbers `font-variant-numeric: tabular-nums` (already on tables; extend to `.live`, `.ubar`, pills).
Barlow is display only; it never sets a sentence longer than one line except `lv-sentence`.

## 5. Iconography

**Recommendation: a vendored Lucide subset as one SVG sprite**, `studio/command_center/static/icons.svg`,
~24 symbols, ~6 KB, used as `<svg class="i"><use href="/static/icons.svg#flag"/></svg>` through one
Jinja macro `icon(name)`; `stroke: currentColor`, so the state fg colours it.

Why Lucide over Phosphor ([comparison](https://dev.to/svgicons/lucide-vs-tabler-vs-phosphor-which-free-icon-set-fits-your-ui-4ocl)):
Lucide is a single 24-grid, 2 px-stroke outline style (ISC licence) whose line weight sits with IBM Plex
Mono; Phosphor's value is six weights (thin…duotone) we don't need, and filled 256-grid shapes read heavier
than our hairline rules. Lucide has every glyph we need: `circle`, `circle-dashed`, `loader`, `check`, `flag`,
`corner-up-left`, `x`, `hand`, `pause`, `history`, `minus`, plus `play`, `film`, `image`, `clapperboard`,
`gauge`, `cpu`, `bell`, `external-link`, `chevron-right`, `more-horizontal`, `sun-moon`.

Sizes: 12 px inline in mono text (stroke-width 2.25 so it survives the scale-down), 16 px in pills and
buttons (stroke 1.75), 20 px in the live card vital. No icon without its word, except inside the
`.sbar`/`.ubar` labels where the step id is the word.

Unicode stays where it is *typographic*, not semantic: `·` separators, `›` crumbs, `→` in ladders,
`×18` counts. `GLYPHS` in `views.py` becomes the icon-name map; the Unicode glyph survives only as the
`aria-hidden` text fallback for plain-text contexts (tooltips, Telegram, logs). Sprite file is vendored
(no npm), licence text in a comment at its top. Fixes problem 5 (colour emoji ✋, ⏸; ○/◌ confusion).

## 6. Imagery treatment

Episodes are square 1:1; trailer and refs pictures may be 16:9 or portrait sheets. One component, `.frame`:

- `aspect-ratio` from the asset's own ratio (thumbs.py knows it), `object-fit: contain` on `--stage`:
  **letterbox/pillarbox bars are stage black, never paper.** `cover` only for contact-sheet tiles
  ≤ 66 px (`.lt`) where recognition beats composition, and the lightbox always shows `contain`.
- Edge: `--r-0`, 1 px `--stage-line` inside (`box-shadow: inset 0 0 0 1px`), so a dark frame on dark
  paper still has an edge. No drop shadows, no rounded thumbnails (Criterion/TE straight cut).
- Overlays on a `--scrim`, Plex Mono `--t-micro`, `--stage-ink`: **id top-left** (`T05`), **state icon
  top-right** in the state's dark fg, **shot size bottom-left** (`medium_close`), **timecode/duration
  bottom-right** for video. Max four corners, nothing in the centre — the picture is the content.
- States on a frame: flagged = 2 px inset `--st-flagged` border + flag icon; failed = 3 px inset
  `--st-failed` + `x`; rendering = the existing develop/conic ring (keep — it is good); waiting =
  `--stage-2` with dashed `--stage-line` and the shot size word centred in `--stage-ink-3`.
- Hover-plays a take (exists); the master player gets the stage well with the QC column on paper beside it.
- Grid rhythm: tiles at 120 px desktop / 3-up phone, gap `--sp-2`, tray `--stage-2` with `--sp-2` padding,
  so a contact sheet reads as one dark strip of film on the paper page — the blend in one picture.

## 7. Should the byte-equal token test stay?

**Keep the invariant, change its shape.** What the test protects is real: the design language flows
from the org chart to the board, never back (decision 2026-09-25). What it costs is also real: the board
already needs tokens the org chart doesn't (motion), and works around the test with a second `:root`
block at line 256 of `base.html` — the test is being dodged, which means it no longer describes the system.

Proposal (three tests, all free, all test-first):
1. **Core byte-equal (kept):** the `:root` + two dark blocks in `architecture/index.html` hold the
   *shared core* (§4.1 neutrals, §4.2 space/radius/elevation/motion, §4.3 type) and the board copies them
   byte for byte. The org chart gains the new core tokens (unused ones cost nothing; it is a reference sheet).
2. **State tokens live only on the board**, in a second, named block `/* state tokens */`, with a test
   that the org chart's block contains no `--st-` token and the board's state block uses only core
   tokens or literals (direction of flow preserved).
3. **New: `test_tokens_meet_contrast`** — parse both themes' tokens and assert the §3 table: every
   `--st-*` and `--ink-*` ≥ 4.5 vs paper, paper-2 and its tint; `--line`/bars ≥ 3.0 vs paper; stage inks
   vs stage. Plus `test_every_var_is_defined` (every `var(--x)` in templates resolves). This catches
   problem 1 forever, which the byte test never could.

Rejected alternative: a shared `tokens.css` file linked by both. The org chart must stay one
self-contained HTML (CLAUDE.md, and the claude.ai published copy), so the inline copy + byte test is the
cheapest correct sync.

**Publishable artifact flag:** test 3 — a stdlib-only pytest helper that reads CSS custom properties
from HTML, resolves both `prefers-color-scheme` and `[data-theme]` blocks, and asserts WCAG pairs from
a small table — is generalizable beyond this repo (`css-token-contrast` on PyPI). Worth extracting once
it exists here.

## 8. What the blend looks like, page by page

- **Home `/`**: paper; department cards flat (`--r-0`, `--paper-2`, 3 px ink top rule like the org chart's
  section blocks); "on the floor" line gets a 72 px stage strip of the running unit's latest frame.
- **Floor**: ops-monitor density; state pills and bars only colour; GPU trace stays a single hairline.
- **Department / book**: editorial table, 3 px ink rule per book, patterned bars (§3), pills `--r-pill`.
- **Unit**: paper page, two stage wells (live sheet, takes/master), lightbox stage full-bleed.
- **Org chart**: unchanged look; gains the core tokens; keeps `--accent` for owner and agents.

## Top 10 recommendations for this board

1. Fix `--ink-3` to #6f6759 / #9a9282 — every page (muted text, th, eyebrows fail AA today at 4.11/3.77).
2. Introduce `--stage` neutral dark wells for every picture and video in both themes — unit, home, lightbox.
3. Collapse each state to one colour everywhere (deferred purple, stale dashed-green) via `--st-*` tokens — unit live card, dept, floor.
4. Pattern the attention states in bars (failed hatch, deferred dotted, held neutral hatch, flagged lighter tier) — dept `.sbar`, book `.minibar`, unit `.ubar`/`.lv-rail`.
5. Replace Unicode state glyphs with a vendored 24-symbol Lucide sprite + `icon()` macro — legend and every page.
6. Make flagged a true amber (#8a5a00 text, #b07a12 bar) instead of olive-brown #5f4b1c — dept, book, unit.
7. Add `test_tokens_meet_contrast` + `test_every_var_is_defined`; keep the core byte-equal test — tests.
8. Cut 23 font sizes to the 9-role type scale with a 10 px floor — every template.
9. One `.frame` component: contain on stage, four-corner scrim labels, dashed stage placeholder for unshot takes — unit takes/panels, live sheet.
10. Four radii with jobs (0 frames, 2 chips, 4 controls, pill = state only) and flat elevation, shadow only on overlays — every page.

## 3 disagreements I expect with other researchers

1. **"Make the board dark by default like Frame.io/Resolve."** I disagree: the board is 80 % reading
   (tables, verdicts, logs) glanced at beside a terminal; only the pictures need a dark surround, and the
   stage gives them that in *both* themes. A dark-first board also throws away the org chart identity the
   owner asked to keep.
2. **"Drop Barlow Condensed / adopt Inter or Geist Sans for a modern SaaS feel."** I disagree: Barlow is
   what makes this read as a studio slate rather than a generic dashboard; the SaaS lesson worth taking is
   the *token discipline* (Linear's 3 inputs, Geist's role steps), not the typeface.
3. **"Colour the whole row / card by state for faster scanning (Grafana, ShotGrid status columns)."**
   I disagree: measured adjacent-state luminance is 1.01–1.34, so fills don't scan for colour-blind eyes
   anyway; state belongs in one pill + a patterned bar, with paper left quiet so the one red thing is seen.
