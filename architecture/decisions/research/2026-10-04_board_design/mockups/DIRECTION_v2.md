# Mockups v2 — direction (owner, 2026-10-04)

Owner after the palette change: "studio black" ... "tabs are not good in the 8710 version ..
better home page and other tabs". v1 was the paper design with inverted colours: a thin row of
text tabs (plus a second mockup ribbon), monospace everywhere, flat 1-px rules, small pictures.
v2 is a dark studio tool built for dark, in the craft of Frame.io / Linear dark / DaVinci Resolve.

## Navigation: a left sidebar replaces the tab row

- Fixed left sidebar, 232 px (collapses to 64 px icon rail ≤ 1100 px; phone: bottom tabs + a
  sheet). Surface `--side` #0b0c0e, right border `--rule`.
- Top: brand mark "Visurena" (Barlow 22 px) + studio switcher look.
- Primary items with Lucide icons and live counts, 36 px rows, 8 px radius, active row = raised
  surface + 2 px left accent bar: **Now**, **Inbox** (badge 5), **Queue** (92), **Books** (30).
- Section "Departments": analysis · screenplay · trailer · refs · episode, each with a tiny state
  tally dot (running blue / flagged amber) and count.
- Section "Pinned": the units being watched (ep17, ep16) with a 24 px face.
- Bottom: the **live GPU card** (face 40 px, `ep17 · 07 board`, a thin progress line, "~21:35"),
  then search (⌘K), theme, keys.
- Remove the mockup ribbon; put "mockup pages" as a small sidebar footer section instead.
- The page header becomes a slim 56 px bar inside the content area: crumbs on the left,
  page actions on the right — no full-width 2 px white rule.

## Surfaces, type, shape (dark-first)

- Layers: page `--paper` #0f1012 → card `--surface` #16171a → raised `--surface-2` #1d1f23 →
  overlay #24262b. Borders 1 px `--rule` #26282d; **radius 10 px on cards, 6 px on controls,
  pill only for state**. No hard white rules; section separation by spacing + card edges.
- Text: Plex Sans for UI text (not mono); mono only for ids, timestamps, numbers in tables.
  Barlow Condensed for page titles and the hero numbers. Labels: Plex Sans 12 px, 500,
  `--ink-3`, sentence case (no letter-spaced uppercase mono everywhere).
- Hierarchy by size and weight, not by boxes and caps.
- Pictures large and first: posters on stage black, 8 px radius inside cards.
- One accent for interactive focus/selection: a cool blue `--focus` #5b8def; state colours stay
  for state only.

## Home ("Now") v2

1. **Hero row** — a wide live card for the running unit: big poster/frame (left, ~360 px square),
   title + question, "Done around 21:35" (Barlow 56 px) with the p50–p90 band and a now-line,
   the 12-step rail with names, last words, Open / Notify. Next to it a narrow column of
   **3 KPI tiles** (GPU today h, queue ETA, needs-you count) each with a sparkline.
2. **Needs you** as cards (poster thumb, title, the 2–3 non-pass gates as chips, age, Acknowledge
   / Open) in a 2-up grid — not a table.
3. **Up next** as a horizontal strip of poster cards with start times.
4. **Where the GPU went** — the stacked chart in a card, burned in hatched red, with the
   "burned by step" bars beside it.
5. **Recently finished / shipped with flags** — a poster shelf (like a streaming row).
6. "Since 14:02" becomes a compact activity feed card in the right column, not a banner.

## Other pages

Same shell; tables become dark data grids inside cards (row hover `--surface-2`, 44 px rows,
poster faces 36 px with 6 px radius); filters as a segmented control; the book page leads with
a big season wall; the unit pages keep their content but adopt the surfaces, sidebar and type.
