# The shell (v2) — how a mockup page adopts it

Owner of `assets/v2.css` + `assets/shell.js` (+ `shell.css` for dialogs, menus, toast): the Now
builder. Brief: `DIRECTION_v2.md`. Do not fork board.css or v2.css; page-only CSS goes in a
`<style>` in the page.

## Adopt it in 3 lines

```html
<link rel="stylesheet" href="assets/board.css"><link rel="stylesheet" href="assets/shell.css"><link rel="stylesheet" href="assets/v2.css"><script src="assets/shell.js"></script>
<body data-page="now|inbox|queue|books|book|department|unit" [data-unit="ep17"]>
<aside id="side"></aside>   <!-- optional: shell.js creates it when missing -->
```

That is all. On DOMContentLoaded `shell.js` renders, from one place (`NAV`, `DEPTS`, `PINS`, `GPU`,
`MOCKS` at the top of its v2 block):

- the **sidebar** (232 px; icon rail ≤ 1100 px): brand, Home · Inbox (badge 5) · Queue 92 · Books 30 · Architecture (architecture.html, the live :8700/org framed);
  Departments with counts and state dots (running blue / flagged amber / all-done green); Pinned
  units with 24 px faces; a collapsed "Mockup pages" footer; the **live GPU card** (ep17 · 07 board,
  progress line, ~21:35); search (Ctrl K), theme, keys, org;
- the **slim 56 px content header**: if the page has no `<header class="ph">`, the shell builds one
  and *moves the page's first `<nav class="crumbs">` into it*; put page actions in any element with
  `data-ph-actions` and they move to the right side (default: a "live · 19:21" chip);
- **phone (≤ 640 px)**: sidebar hidden, bottom tabs Home · Inbox · Queue · Books · More; More opens a
  sheet holding the whole sidebar; the header gains a GPU chip;
- the ⌘K palette, `?` keyboard sheet, `g` chords, `j/k` rows, `t` theme, `[data-order]` receipts —
  all delegated, so injected controls work too.

The active item comes from `data-page` (book → Books; department → `?stage=`; unit → its pin, else
episode). Theme: Studio black is the default; `t` / the sun button switches to Graphite light and
persists in localStorage `palette` (try/catch). The v1 ribbon, top bar and `nav.tabs` are removed
by the shell if a page still has them.

## What v2.css gives a page

Tokens `--side --surface --surface-2 --overlay --focus --r-card(10) --r-ctl(6) --r-pic(8)`, and
components: `.page` (content container), `.panel/.panel-h/.panel-b` (card), `.sh` (section
heading), `.kpi` (KPI tile + sparkline svg), `.chip2` (gate chip; pills stay for state only),
`.dgrid` (dark data grid, 44 px rows, 36 px faces), `.segmented` (filter control), `.pic` (picture
on stage black), `.pcard` + `.shelf2` (poster card / streaming shelf), `.btn.sm/.ghost`, `.count`.
Controls (`.btn`, `.kbd`, dialogs, menus, toast) are restyled inside `@layer components`, so a
page's own CSS still wins; shell and new components are unlayered but namespaced.

Canonical numbers (captured 2026-10-04 19:21 PDT, read-only): ep17 *The Thunder Child* at 07 board,
panel 00/22, run 3 started 18:55, done around **21:35** (range 20:20–22:40, 31 runs measured).
Thumbnails: `http://127.0.0.1:8700/thumb/<codex>/<160|320>/<path>` (only 160 and 320 exist).
