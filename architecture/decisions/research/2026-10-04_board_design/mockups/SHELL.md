# The shell — paste this into every mockup page

Owner of `assets/shell.css` + `assets/shell.js`: the Now/Queue builder. Other builders paste the
three blocks below unchanged, then set `aria-current="page"` on their own nav/ribbon/tab link.
Do not fork board.css; page-only CSS goes in a `<style>` in the page.

What the shell gives every page, with no extra code:
- top bar: brand, nav `Now · Queue · Books · Departments ▾ · Org`, ⌘K search box, GPU pill
  (`● ep17 07 board · ~21:35`, the live value at capture time 19:21 PDT; links `unit-running.html`),
  inbox badge (needs-you count **5** = ep12–ep16 shipped with flags, not acknowledged), theme toggle;
- phone (≤ 640 px): one-line bar (brand · GPU pill) + fixed bottom tabs `Now · Inbox · Books · Search`;
- the ⌘K palette (`<dialog>`, injected by shell.js): opens on Ctrl/⌘ K, `/`, or any `[data-palette]`;
  ↑/↓ + ↵ navigate to the mockup pages; entries live in `PALETTE` at the top of shell.js;
- the `?` keyboard sheet (also holds the state legend — it replaces the old legend footer);
- `g` chords: `g n` Now · `g i` inbox · `g q` Queue · `g b` Books · `g r` running unit · `g e` episode dept;
  `t` theme; `j/k` walks any element with `data-row` (give rows `tabindex="0"`);
- `<button data-order="redo ep16 09">` anywhere → closes its ⋯ menu and shows the receipt toast
  (the mockups never post); `window.board.toast("…")` for your own receipts;
- `<details class="rowmenu"><summary>⋯</summary><div class="pop">…</div></details>` = the row ⋯ menu;
- theme persists in localStorage `cc-theme` (wrapped in try/catch).

Canonical numbers (captured 2026-10-04 19:21 PDT, read-only): ep17 *The Thunder Child* at 07 board,
panel 00/22, run 3 started 18:55, done around **21:35** (range 20:20–22:40, 31 runs measured).

## 1 · `<head>` (change only the `<title>` page name)

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>(5) ● ep17 07 board · ~21:35 · Now — Visurena</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Ccircle cx='16' cy='16' r='11' fill='none' stroke='%23d6cfc0' stroke-width='5'/%3E%3Cpath d='M16 5a11 11 0 0 1 11 11' fill='none' stroke='%231f5a86' stroke-width='5'/%3E%3Ccircle cx='26.5' cy='5.5' r='5' fill='%23b07a12'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<link rel="stylesheet" href="assets/board.css">
<link rel="stylesheet" href="assets/shell.css">
<script src="assets/shell.js"></script>
<style>/* page-only CSS here */</style>
</head>
```

## 2 · first thing in `<body>` (ribbon is mockup-only; mark your page with aria-current)

```html
<body>
<div class="mock-ribbon"><div class="wrap"><b>Mockups</b>
  <a href="index.html">Now</a><a href="queue.html">Queue</a><a href="unit-running.html">Unit · running</a>
  <a href="unit-finished.html">Unit · finished</a><a href="department.html">Department</a>
  <a href="book.html">Book</a><a href="books.html">Books</a>
  <span class="spacer"></span><a href="#" data-keys>? keys</a>
</div></div>
<header class="topbar"><div class="wrap">
  <a class="brand" href="index.html">Visurena<span class="b-sub"> Studio</span></a>
  <nav class="nav" aria-label="Board">
    <a href="index.html">Now</a>
    <a href="queue.html">Queue</a>
    <a href="books.html">Books</a>
    <details class="menu"><summary>Departments <svg class="i"><use href="assets/icons.svg#chevron-down"/></svg></summary>
      <div class="pop">
        <a href="department.html?stage=analysis">analysis <span class="muted">30 done</span></a>
        <a href="department.html?stage=screenplay">screenplay <span class="muted">30 queued</span></a>
        <a href="department.html?stage=trailer">trailer <span class="muted">30 queued</span></a>
        <a href="department.html?stage=refs">refs <span class="muted">29 queued</span></a>
        <a href="department.html?stage=episode">episode <span class="muted">1 running</span></a>
      </div></details>
    <a href="http://127.0.0.1:8700/org">Org</a>
  </nav>
  <span class="spacer"></span>
  <button class="cmdk" type="button" data-palette aria-label="Search (Ctrl K)"><svg class="i"><use href="assets/icons.svg#search"/></svg>Search or jump to…<span class="kbd">Ctrl K</span></button>
  <a class="gpu-pill" href="unit-running.html" title="GPU: episode ep17 The Thunder Child, step 07 board, done around 21:35 (20:20–22:40)"><span class="dot"></span><b class="gp-unit">ep17</b> 07 board · ~21:35</a>
  <a class="inbox" href="index.html#needs" title="Needs you: 5"><svg class="i"><use href="assets/icons.svg#inbox"/></svg><span class="badge">5</span><span class="vh">need you</span></a>
  <button class="iconbtn theme-btn" type="button" data-theme-toggle aria-label="Toggle theme (T)"><svg class="i"><use href="assets/icons.svg#sun-moon"/></svg></button>
</div></header>
```

## 3 · last thing before `</body>` (phone tabs)

```html
<nav class="tabs" aria-label="Phone">
  <a href="index.html"><svg class="i"><use href="assets/icons.svg#gauge"/></svg>Now</a>
  <a href="index.html#needs"><svg class="i"><use href="assets/icons.svg#inbox"/></svg>Inbox<span class="badge">5</span></a>
  <a href="books.html"><svg class="i"><use href="assets/icons.svg#book-open"/></svg>Books</a>
  <a href="#" data-palette><svg class="i"><use href="assets/icons.svg#search"/></svg>Search</a>
</nav>
</body>
</html>
```

`aria-current="page"` goes on: your ribbon link, your nav link (unit/department pages: none, or the
`summary` of Departments), and your tab (unit/department pages: none).
