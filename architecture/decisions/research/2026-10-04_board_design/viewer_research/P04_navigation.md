# P04 — Navigation & wayfinding (UX panel, 2026-10-04)

Lens: sidebar, crumbs, ⌘K, keyboard map, deep links, Back, cross-links unit↔book↔department↔Viewer,
the Architecture item, phone tabs. Read-only. Evidence: `studio/command_center/shell.py` (uncommitted,
mid-build), `app.py`, `templates/*.html`, mockup `assets/shell.js`, `SHELL.md`, `SPEC_v3.md`, `V07_navigation.md`.
Screens: `mockups/shots/panel/P04_real_ep12.png` (board :8700, still the v1 beige top bar),
`P04_mock_ep12.png` (mockup at phone width).

## 1. The brick

**Every page is a node with an address, a parent and siblings; every view of it is the address plus
a query.** Navigation means getting to a node's parent, its siblings and its children in one move, and
landing back where you were. Base case: a URL that renders the same thing cold as it does warm.
Rule: crumb = parent chain; `[`/`]` = siblings; the sidebar = the roots; ⌘K = any node by name;
Back = the last *address*, never the last poll. Check that it regenerates things nobody stated: "ep12 → ep13
without going through the book" is sibling navigation; "the flagged filter survives Back" is
query-in-address; "Inbox lights up in the sidebar" needs Inbox to *be* an address, and today it is
not (see D3). "Refresh and updating" belongs to the same brick. A live page may change what is
*at* an address. It must never change the address, the scroll or the focus. That is the line between
the owner's "dynamic" and a page that jumps.

## 2. What is broken or missing today (measured, not guessed)

| # | Where | Finding | Evidence |
|---|---|---|---|
| D1 | sidebar | `shell.py PAGES` links `/queue`, `/books`, `/architecture`: **all three answer 404** on :8700 | `curl` 2026-10-04: `/queue 404 /books 404 /architecture 404`; `app.py` has only `/`, `/floor`, `/d/…`, `/b/…`, `/org` |
| D2 | ⌘K | The real palette indexes only *running* units (`palette()` uses `pins`), so ep12, ep16, every flagged or shipped unit **cannot be found by name** | `shell.py:104-112` |
| D3 | Inbox | Inbox is `/#attention`. `section()` ignores the fragment, so it returns `home`. **Inbox can never show as the current item**, and on the phone the Inbox tab never lights | `shell.py:20,35-46` |
| D4 | crumbs | First crumb reads "Studio". The sidebar's first item is "Home" (SPEC_v3 ruling). "Books" in the book crumb is plain text with no link. The unit crumb is `Studio › episode › book › ep12`, which mixes two parents with no rule for the order | `book.html:4`, `unit.html:6`, `home.html:3` |
| D5 | unit page | No sibling navigation: going from ep12 to ep13 takes 3 clicks (crumb, book, cell) | `unit.html` |
| D6 | Architecture | `/org` serves `architecture/index.html` raw through `FileResponse`. It has **no shell, no sidebar and no way back** except the browser's Back. The mockup also opens it as an external `:8700/org` link | `app.py:150-157`, `shell.js:227` |
| D7 | live refresh | Sidebar counts, dots, pins and the GPU card are rendered once per page load, so they go **stale on any page left open**. Home polls 4 sections at 2 s, 2 s, 10 s and 5 s, each on its own timer | `base.html:617`, `home.html:6-15` |
| D8 | in-page anchors | Gate chips `#gate-PLAN` and shot chips `#shot-05` / `#take-T05` jump under the coming 56 px sticky header, which has no `scroll-margin-top` | `unit.html:111,117` |
| D9 | keys | Mockup chords are hard-coded in `CHORDS`, while the board's `PAGES` carries its own `k` strings. That makes two key maps that will drift, and the `?` sheet is hand-written | `shell.js:41`, `shell.py:20` |
| D10 | Back after a filter | Department filter pills are real links (`?state=flagged`), which is good. The htmx row refresh repeats the query, but the scroll position is lost on every 2 s swap of a long list | `department.html:10-19` |

## 3. Outside practice

| Practice | Lesson for us | Source |
|---|---|---|
| Linear: `G` chords (G I inbox, G M my issues), `⌘K` for everything, `?` sheet generated from the command registry, `J/K` list walk | One command registry feeds ⌘K, the key sheet and the tooltips (D9) | https://linear.app/docs/conceptual-model , https://linear.app/docs/keyboard-shortcuts |
| GitHub: `g i` and `g p` chords; `?` lists keys **for the current page** | The key sheet is per page plus global | https://docs.github.com/en/get-started/accessibility/keyboard-shortcuts |
| Gmail: `u` returns to the list, `j/k` move between threads *inside* an open thread | `u` = up one level; `[`/`]` = sibling units on the unit page | https://support.google.com/mail/answer/6594 |
| NN/g breadcrumbs: show location in the hierarchy, not history; every crumb except the last is a link | Fix D4; the crumb is the parent chain | https://www.nngroup.com/articles/breadcrumbs/ |
| W3C WAI breadcrumb pattern: `nav aria-label="Breadcrumb"`, `aria-current="page"` on the last crumb | Markup for the crumb and the sidebar | https://www.w3.org/WAI/ARIA/apg/patterns/breadcrumb/ |
| Vercel 2026 nav: a resizable sidebar holding the same items at every level; a phone bottom bar | Sidebar items stable across pages; phone tabs are the sidebar's top 4 | https://vercel.com/changelog/dashboard-navigation-redesign-rollout |
| Material 3 navigation bar: 3–5 destinations, each a top-level page with a stable URL, plus a badge | Phone tabs must be pages, not fragments (D3) | https://m3.material.io/components/navigation-bar/guidelines |
| htmx `hx-push-url` / `hx-replace-url`; `hx-preserve`; idiomorph `hx-swap="morph"` keeps focus and scroll | Live refresh without stealing scroll or focus; filters write the address | https://htmx.org/attributes/hx-push-url/ , https://htmx.org/attributes/hx-replace-url/ , https://github.com/bigskysoftware/idiomorph |
| htmx out-of-band swaps: one response updates several regions | One poll feeds sidebar + header chip + page (D7) | https://htmx.org/attributes/hx-swap-oob/ |
| Page Visibility API | Slow or stop polling in a hidden tab, refresh at once on return | https://developer.mozilla.org/en-US/docs/Web/API/Page_Visibility_API |
| Next.js intercepting routes (photo modal): an overlay has a URL; a cold link must close without `history.back()` | Already ruled for the Viewer (SPEC_v3); the same applies to the palette, which must not push | https://nextjs.org/docs/app/api-reference/file-conventions/intercepting-routes |
| `document.title` as wayfinding: browser tabs and history menus show it | Title = `ep17 · 07 board · ~21:35 — Visurena`; history entries become readable | https://developer.mozilla.org/en-US/docs/Web/API/Document/title |

## 4. The proposals in detail

**Addresses (fix D1, D3, D6).** Make every sidebar item a real route. `/queue` serves today's `floor.html`
(keep `/floor` as a 308 to it). `/books` is the shelf. `/inbox` serves the attention list as its own page
(keep `/#attention` working with a tiny redirect script on Home). `/architecture` renders the org page
*inside* the shell; `/org` stays the bare standalone file for the claude.ai copy. Test: a route test asserts
every `href` in `PAGES` returns 200, and `section('/inbox') == 'inbox'`. This kills the whole class of
"sidebar links to nowhere".

**Crumbs (D4).** One function, `crumbs(path) -> [(label, href)]`, built from the address and not
hand-written per template: `Home › Books › The War of the Worlds › episode › ep12`. Book comes
before department because the owner thinks in books, and the book page already holds the department matrix.
The department stays one click away through a chip in the unit header (`episode ▸`). The last crumb is not a link.
On the unit crumb, a ▾ on the unit name opens the sibling list (all episodes of this book, state
glyph each). That is the "switch unit" menu Frame.io and Linear put on the title. Test: each page's crumbs
come from one helper; a unit test per route shape.

**Siblings (D5).** On the unit page, add `‹ ep11 · ep13 ›` in the header, keys `[` and `]`, and `u` = up to
the book. Order comes from the book's unit order (`views.book`). Prefetch the neighbour HTML on
hover/idle (`<link rel=prefetch>`), so the flip feels instant. Test: ep12's header links to ep11/ep13;
ep01 has no "prev".

**⌘K that knows everything (D2).** Index *all* units (≈150 rows across 5 departments; tiny), each
with its state glyph and book. Rank in this order: running, then needs-you, then recently visited, then the rest. Add
**Recent** (last 8 addresses visited, `localStorage`, try/catch, per viewer). Add verbs that already
exist as orders (`Acknowledge ep16 flags…`, `Hold studio…`, `Redo 08 on ep12…`) behind a confirm, exactly
as the mockup lists them. Make the palette live: refetch `/api/palette.json` when it opens if older than 10 s,
so a unit that started a minute ago is findable. Selecting a result is a normal navigation (push).

**One key registry (D9).** Keep `PAGES` plus a `KEYS` table in `shell.py` as the single source. Render the
`?` sheet, the `title=` tooltips, `aria-keyshortcuts` and the JS chord map from it (serialize it into
the page as JSON). Global keys: `g h/i/q/b/a/e`, `⌘K` or `/`, `?`, `t`, `j/k`, `u`. Unit keys: `[ ]`, `v` (open
the Viewer on the master), `1–5` reserved for the Viewer only. The Viewer suspends the shell keys
(already true in the mockup, `shell.js:335`). Test: a template test that every chord in the sheet is
in the JS map, and the reverse.

**Live shell (D7, D10). This is the owner's "dynamic".** One `GET /partials/shell` every 5 s (paused when
`document.hidden`, fired at once on `visibilitychange` and on `orders-changed`) returns the
sidebar counts, dots, pins, the GPU card, the phone header chip, the Inbox badge and `document.title` as **OOB
swaps** with `hx-swap="morph"`. The page body keeps its own section polls but goes through morph, so scroll and
focus survive and open `<details>` stay open. Add a change cue that fits ruling 09 (pulse, no SSE,
one animation per viewport): when a pin's state changes, its dot pulses once. When a new unit
appears in Needs you, the Inbox badge ticks with one 240 ms count-up. Nothing moves the page.
How to know it worked: leave `/d/episode` open while ep17 advances a step. The sidebar dot, GPU card
and tab title change within 5 s, `window.scrollY` is unchanged, and the network panel shows one request
every 5 s instead of four.

**Architecture item (D6).** `/architecture` = the shell around the org page. Either render the
page's `<main>` into the shell, or use a same-origin iframe sized to the content. Add one line under
the crumb: "Standalone ↗ /org". Cross-link both ways: the department page's "org chart ▸" deep-links
`/architecture#episode`, and each department box on the org page links back to `/d/<stage>`.

**Anchors (D8).** `:target, [id^=gate-], [id^=shot-], [id^=take-] {scroll-margin-top: 72px}` and a
1 s outline pulse on arrival (already styled `.tile:target`). Test: Playwright/browse click on
`#gate-PLAN` and check the header does not cover the heading.

**Phone tabs.** Keep Home · Inbox · Queue · Books · More (Material: 3–5). Add two things. (1) The header GPU
chip (exists in the mockup) is the one-tap route to the running unit. (2) More opens the sidebar sheet with
departments and pins *first*, mockup links last. Every tab is a route (after P04.1), so the phone's
Back works. Tab badges come from the same `/partials/shell` poll.

**Back.** Rule: polls never push; filters `replaceState` (`hx-replace-url`) when changed on a page, and push
only on a pill click from another page. The Viewer pushes once (SPEC_v3). The palette never pushes. Restore
scroll on Back for htmx-swapped lists: `htmx.config.scrollIntoViewOnBoost=false` plus
`history.scrollRestoration='auto'`, and no morph on the first paint after `pageshow`.

## Proposals

| id | page | change (one line) | effort | files |
|---|---|---|---|---|
| P04.1 | shell / all | Make every sidebar item a real route: `/queue` (308 from `/floor`), `/books`, `/inbox`, `/architecture`; route test that every `PAGES` href is 200 | S | `app.py`, `shell.py`, new `templates/books.html`, `inbox.html`, `architecture.html`, `tests/` |
| P04.2 | shell / all | One `/partials/shell` poll (5 s, paused when hidden) that OOB-morphs sidebar counts, dots, pins, GPU card, Inbox badge, phone chip and `document.title` | M | `app.py`, `shell.py`, `templates/base.html` (shell partial), `static/js/shell.js` |
| P04.3 | ⌘K | Index every unit (state glyph, book), rank running › needs-you › recent › rest, add Recent (localStorage), refetch `/api/palette.json` on open | M | `shell.py`, `app.py`, `static/js/shell.js` |
| P04.4 | unit | Sibling nav `‹ ep11 · ep13 ›` + `[`/`]` + `u` up + unit-name ▾ switcher; prefetch neighbours | S | `unit_view.py`, `templates/_unit_head.html`, `static/js/shell.js` |
| P04.5 | all | Crumbs from one `crumbs(path)` helper: `Home › Books › <book> › <stage> › <unit>`, all links but the last, ARIA breadcrumb markup | S | `shell.py`, `templates/*.html` (crumb block) |
| P04.6 | shell | One `KEYS` registry renders the `?` sheet, tooltips, `aria-keyshortcuts` and the JS chord map; test that both directions match | S | `shell.py`, `templates/base.html`, `static/js/shell.js` |
| P04.7 | Architecture | `/architecture` renders the org page inside the shell, with a "Standalone ↗" link; department ↔ org boxes cross-linked both ways | M | `app.py`, `templates/architecture.html`, `architecture/index.html` (links only) |
| P04.8 | all lists | Section polls swap with idiomorph so scroll, focus and open `<details>` survive; filters `hx-replace-url` | S | `templates/home.html`, `department.html`, `floor.html`, `static/` (idiomorph ext) |
| P04.9 | unit | `scroll-margin-top` on gate, shot and take anchors under the sticky header, plus the arrival pulse | S | `static/css/*.css` |
| P04.10 | phone | More sheet lists departments + pins first; tab badges from P04.2; GPU chip in the header kept as the running-unit route | S | `templates/base.html`, `static/css/*.css` |
| P04.11 | all | Live `document.title` (`ep17 · 07 board · ~21:35`), plus a favicon dot for running / needs-you state, so the browser tab itself is a status | S | `templates/base.html`, `static/js/shell.js` |

Each one is test-first per the repo rules. P04.1, P04.5 and P04.6 are pure-function tests. P04.2 and P04.8 are
verified with browse: scroll position unchanged across a poll, one request per 5 s.

## I will argue against

1. **A client-side SPA router or `hx-boost` on everything "to feel dynamic".** It breaks the brick
   (a cold URL must render the same page). It also makes Back, focus and scroll the app's problem instead of
   the browser's. The board is a dozen pages on localhost, where full loads take ~50 ms. Liveness belongs in the
   *content* (P04.2, P04.8), not in routing. Boost only the sidebar links later, and only if a
   measurement says a load feels slow.
2. **SSE or WebSocket push for the sidebar.** Ruling 09 already chose pulse polling with no SSE. One owner,
   one tab, a 5 s OOB poll that pauses when the tab is hidden costs nothing. Push adds reconnect, ordering and
   proxy bugs for a gain of under 5 s. Revisit only if a gate must interrupt the owner.
3. **Dropping crumbs because "the sidebar already says where you are", or a second Home
   ("studio overview") beside Now.** The sidebar shows the *root*, not the chain
   (book › stage › unit). The owner jumps in from ⌘K and Telegram links, and lands deep. Two homes split
   "needs you" (V07 already argued this). Keep one Home and real crumbs.
