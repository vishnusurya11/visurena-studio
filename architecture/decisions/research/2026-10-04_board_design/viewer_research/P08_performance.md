# P08 — Performance and perceived speed (panelist P08, 2026-10-04)

Lens: TTFB, bytes per page, DOM size, image weight, cache headers, idle cost of polling, and how
fast a click feels. Measured on :8700 and in-process against the same code, DB and library.
Nothing was changed. Scripts: `research\p08_prof.py`, `p08_html.py`, `p08_lib2.py`, `p08_thumb.py`, `p08_mp4.py`.

## 0. A caveat about the live server
The first pass hit live :8700 with curl, twice per page. Partway through, the live process
started answering **500 on every templated page**. The cause: the old `app.py` is still loaded
(no reload), but the new templates on disk call `static_url`, which that process does not define
(`scratchpad\cc8700.log`: `UndefinedError: 'static_url' is undefined`). Every number after that
comes from the current tree, driven in-process with Starlette's `TestClient` against the real DB
and library. The board needs a restart after the re-skin lands.

## 1. What I measured

### Live :8700 (curl, cold then warm)
| Page | TTFB cold | TTFB warm | HTML |
|---|---|---|---|
| `/` | 8 ms | 6 ms | 52 KB |
| `/floor` | 10 ms | 6 ms | 140 KB |
| `/d/episode` | 18 ms | 9 ms | 115 KB |
| `/d/episode/…/ep17` (running) | **63 173 ms** | **4 879 ms** | 127 KB |
| `/d/episode/…/ep12` (finished) | 39 ms | 49 ms | 174 KB |
| `/b/20260827135508` | **2 516 ms** | 489 ms | 45 KB |

### The same routes in-process (current tree, 3 calls each)
| Route | Status | Bytes | Call 1 / 2 / 3 |
|---|---|---|---|
| `/` | 200 | 39 KB | 168 / 17 / 13 ms |
| `/floor` | 200 | 150 KB | 25 / 14 / 12 ms |
| `/d/episode` | 200 | 109 KB | 44 / 13 / 12 ms |
| ep17 unit | 200 | 114 KB | **687 / 25 / 25 ms** |
| ep12 unit | 200 | 161 KB | 500 / 34 / 35 ms |
| `/b/…` | 200 | 32 KB | 44 / 9 / 8 ms |
| partials floor / attention / orders / lanes | 200 | 0.6 / 4.7 / 0.8 / 9.2 KB | 2–4 ms |
| `/partials/d/episode` | 200 | **85 KB** | 6–18 ms |
| ep17 `tails` / `head` / `live` / `orders` | 200 | 25.6 / 4.1 / 13.2 / 0.1 KB | 14–18 ms |
| `/api/progress/…/ep17.json` | 200 | 3.7 KB | 6–7 ms |

Building the page itself is fast: 25 ms warm, under 700 ms cold. So the 63 s and 4.9 s live
TTFBs on ep17 are time spent **waiting in a queue**, not building the page. That queue is the
next finding.

### Cold thumbnails are the bottleneck
- ep17 references 48 `/thumb/…/320/…` WebPs. Fetching all 48 from a cold cache took **39 230 ms
  in-process** (390 KB total). Warm, the same 48 took **146 ms**.
- One render measured on its own: decode 15 ms, resize 5 ms, WebP `method=4` encode 29 ms
  (`method=0`: 2 ms, 40 % larger). That is about 30–50 ms, but **up to about 800 ms** while the
  GPU sits at 100 % and the render pipeline is writing to the same disk. The same PNG through a
  JPEG path took 529 ms in that state.
- `thumb()` is a sync route, so every render runs in AnyIO's shared threadpool (40 tokens by
  default, [anyio threads](https://anyio.readthedocs.io/en/stable/threads.html)) while holding
  the GIL for PIL work. A cold unit page, plus ten panelists opening ep17 at once, puts the page
  HTML behind hundreds of renders. That is the most likely cause of the 63 s TTFB.
- The LRU lives in process memory (`thumbs.Lru`, 64 MB), so **every board restart empties it**.
  The board restarts many times a day while it is being re-skinned.
- Tiles are laid out at `width=120` but use the 320 px variant. That is 2.7× the pixels at DPR 1.

### Page weight and DOM size
Element counts from the rendered HTML:

| Page | Elements | HTML |
|---|---|---|
| `/` | 797 | 39 KB |
| `/floor` | **3 001** | 150 KB |
| `/d/episode` | **2 125** | 108 KB |
| ep17 | **2 046** | 114 KB |
| ep12 | **2 539** | 160 KB |
| `/b/…` | 680 | 32 KB |

Lighthouse warns above 800 elements and flags above 1 400
([dom-size](https://developer.chrome.com/docs/lighthouse/performance/dom-size)). Four of six pages
are over the flag.

### Media that is already right
- The full-size lightbox PNGs (ep17: 22 files, 34.4 MB; ep12: 24 files, 38.1 MB) sit inside
  inert `<template>`s, so none of them load until a tile is opened.
- The 24 take `<video>`s are `preload="none"` with a 320 px poster.
- The mp4s are faststart: `ftyp, moov, free, mdat` on the master (253 MB) and on the takes
  (1.4–2.0 MB).

Each lightbox open still pulls one 1.2–1.6 MB PNG, served `Cache-Control: no-cache` (a
revalidation round trip every time).

### Static assets
The builder's `CachedStatic` plus `static_url(?v=)` is already in the tree: a versioned file or a
font gets `immutable` for a year. That fixes the old state I saw live (no `Cache-Control` at all,
only ETag). Two gaps remain:
- The fonts go out as `application/octet-stream`.
- Nothing preloads the two text fonts.

No response is compressed (no `content-encoding`). For scale: `/org` is 149 KB raw and 43 KB
gzipped, htmx is 51 KB raw and 16 KB gzipped. On 127.0.0.1 that buys no time; over the LAN or
phone it would.

### What polling costs while the owner just watches
- **ep17:** progress JSON every 2 s, `head` every 3 s, `tails` every 5 s (only while open),
  `orders` every 10 s, `needs` every 10 s and `eta` every 30 s (board.js). That is about
  **30 MB/hour of mostly identical HTML**: 6.7 MB JSON, 5.0 MB head, 18.4 MB tails. It costs
  about 38 s of server CPU per hour, and the `head` section is rebuilt with `outerHTML` every 3 s.
- **`/`:** four timers (2 s, 2 s, 5 s, 10 s) send about 9.5 MB/hour.
- **Hidden tabs:** htmx 2.0.4 has no visibility check (`visibilityState` appears 0 times in
  `htmx.min.js`), so a background tab keeps polling. Chrome only throttles it to once a minute
  after 5 minutes hidden
  ([timer throttling](https://developer.chrome.com/blog/timer-throttling-in-chrome-88)).
  `progress.js` does gate on visibility.

### How a click feels
- **Orders:** `/act/*` forms (`_macros.html`, `unit.html:146`) have no `hx-disabled-elt`, no
  `.htmx-request` style and no `:active` press state. A click shows nothing until the receipt
  arrives, and a second click sends a second order.
- **Navigation:** every link is a full page load. Warm, that is 10–35 ms server time plus
  re-parsing 51 KB of htmx and 65 KB of CSS from cache. Nothing is prefetched on hover.

Benchmarks:
- Response times: 100 ms feels instant, 1 s keeps the flow
  ([NN/g](https://www.nngroup.com/articles/response-times-3-important-limits/)).
- INP should be ≤ 200 ms ([web.dev INP](https://web.dev/articles/inp)).
- TTFB should be ≤ 800 ms ([web.dev TTFB](https://web.dev/articles/ttfb)). Cold ep17 misses it
  by about 80×.

## 2. Reasoning
The board's warm path is already fast: every page builds in under 35 ms. Perceived slowness
comes from three things that are not that path:
1. **The cold thumbnail path**, which starves the threadpool.
2. **Churn:** whole sections re-sent and re-built when nothing changed.
3. **Silent clicks.**

Fixing those three makes the board feel instant. Adding skeletons, push transports or animation
would only cover a delay that should not exist.

## 3. Best practice cited
- Immutable versioned assets:
  [MDN Cache-Control](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control).
- Document prefetch on hover with Speculation Rules, eagerness `moderate` (fires about 200 ms
  into a hover): [Chrome prerender/prefetch](https://developer.chrome.com/docs/web-platform/prerender-pages).
- `content-visibility: auto` skips layout and paint for offscreen rows:
  [web.dev](https://web.dev/articles/content-visibility).
- Back/forward cache. It works today because no page sends `no-store`; keep it that way:
  [web.dev bfcache](https://web.dev/articles/bfcache).
- Pause on hidden: [Page Visibility API](https://developer.mozilla.org/en-US/docs/Web/API/Page_Visibility_API).
- Disable while in flight: [hx-disabled-elt](https://htmx.org/attributes/hx-disabled-elt/).
- 204 means no swap: [htmx response handling](https://htmx.org/docs/#response-handling).
- Compression: [Starlette GZipMiddleware](https://www.starlette.io/middleware/#gzipmiddleware).
  It compresses every type unless told otherwise, so restrict it to text types; never compress
  mp4 or Range responses.
- Preload critical fonts: [web.dev](https://web.dev/articles/preload-critical-assets).

## Proposals (ranked)

| id | Page | Change (one line) | Effort | Files |
|---|---|---|---|---|
| **P08.1** | unit pages, every tile | Make the thumbnail cache survive restarts and stop it starving the pages: write each WebP to a disk cache under `library/<book>/.thumbs/<w>/<rel>.<mtime>.webp` (relative path only), cap renders at 2 at a time (a semaphore), encode with `method=2`, and warm the running unit's thumbs in the background at startup. Done when cold ep17 TTFB is ≤ 300 ms with 48 cold thumbs, and the page HTML never waits behind a render. | M | `thumbs.py`, `app.py` (thumb route, startup), `tests/…/test_thumbs.py` |
| **P08.2** | every polled section | Endorse the 09 pulse ruling and add numbers: one fingerprint poll per tab; a partial whose `v` matches returns **204**; `morph` swaps. Target: ep17 idle traffic goes from about 30 MB/h to under 1 MB/h, and `head`'s every-3 s `outerHTML` rebuild ends. | M | new `static/pulse.js`, `app.py` (`/api/pulse`, 204 path), `home.html`, `floor.html`, `department.html`, `unit.html`, `_unit_head.html`, `progress.js` |
| **P08.3** | all | Pulse owns the visibility gate. Visible: 2 s. Hidden: 30 s, so a dead or stalled run still notifies, as 09 issue 1 requires. On `visibilitychange` to visible: pulse at once. Fold board.js's `needs` and `eta` timers into the pulse. | S | `pulse.js`, `board.js` |
| **P08.4** | every `/act/` form | Instant feedback: `hx-disabled-elt="find button"`, a `:active` scale(.98), the receipt shows "sending…" at 0 ms, and the spinner appears only after 400 ms. Done when a double click sends exactly one order (test the macro output) and press-to-visible-change is ≤ 100 ms. | S | `_macros.html`, `unit.html`, `components.css` |
| **P08.5** | nav, rows, tiles | Hover prefetch: one `<script type="speculationrules">` in `base.html`, **prefetch** (not prerender) at `moderate` eagerness for `/d/*`, `/b/*` and unit links. Prerender would run htmx timers in a hidden page. Done when `PerformanceNavigationTiming.deliveryType` is a prefetch hit and click to first paint is under 100 ms. | S | `base.html` |
| **P08.6** | `/floor`, `/d/episode`, ep12 | DOM budget of 1 400 elements: `content-visibility:auto; contain-intrinsic-size` on table bodies and tile grids below the fold; `/floor` (3 001 elements) gets a collapsed "done" group. | S–M | `pages.css`, `_floor.html`, `_rows.html` |
| **P08.7** | lightbox | Serve a 1 024 px WebP variant through the thumb route (`WIDTHS` adds 1024, immutable), not the 1.2–1.6 MB PNG with `no-cache`. When a tile opens, preload its neighbours so the arrow keys are instant. Keep a "full PNG" link. | S | `thumbs.py`, `unit.html`, viewer js |
| **P08.8** | tiles | Use the 160 px variant with `srcset="…160 1x, …320 2x"` for 120 px tiles. That cuts bytes and decode work about 2.5× on DPR 1. | S | `unit.html`, `_live_sheet.html`, `_macros.html` |
| **P08.9** | all | A free, offline perf-budget pytest over every page with `TestClient`, where every test's input is built from the contract. Checks: warm ≤ 50 ms; HTML ≤ 120 KB; ≤ 1 400 elements; every `<img>` outside a `<template>` has `width`, `height` and `loading=lazy`; no `<video>` outside a template without `preload`; each partial ≤ 6 KB; unchanged `v` answers 204. | M | `tests/command_center/test_budgets.py` |
| **P08.10** | static | Serve fonts as `font/woff2`, preload Plex Sans and Barlow 600, and gzip `text/*` and JSON only, in a small middleware (it pays off only off-localhost). | S | `app.py`, `base.html` |

## I will argue against
1. **SSE or WebSocket push "to make it dynamic".** Runners and `drive.py` write the truth into
   SQLite and the log folder; nothing notifies the web process. A stream would still poll, just
   inside the server, one loop per open tab. It would also hold threadpool slots, which is the
   resource P08.1 shows is already scarce, and it delays a `--reload`. The pulse plus 204
   delivers the same liveness at about 1 KB per tick.
2. **Skeleton screens and loading shimmer.** Warm pages answer in 8–35 ms, so a skeleton would
   only flash. The one slow path, cold thumbs, needs the cache fixed (P08.1), not a placeholder
   painted over it. Tiles already reserve their box with `width` and `height`, so nothing
   shifts.
3. **`hx-boost` or SPA-style navigation, and View Transitions on poll swaps.** Body swaps keep
   `board.js`'s `setInterval(needs)` and `progress.js`'s `setInterval(tick)` and poll loop alive
   across pages, so timers pile up and pages double-poll. A full load already costs 10–35 ms,
   and P08.5's prefetch makes it instant without that leak. `startViewTransition` blocks input
   while it runs, so it must never wrap a 2 s swap (09 agrees).
