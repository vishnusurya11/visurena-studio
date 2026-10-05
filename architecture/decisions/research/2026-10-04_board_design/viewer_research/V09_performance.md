# V09 — Performance and loading for the in-page viewer

Researcher V09, 2026-10-04. Measured read-only against the live board `http://127.0.0.1:8700`
(uvicorn, Starlette 1.6.0, FastAPI 0.141.1, bound to 127.0.0.1 only) and the library on disk
(`library/20260827135508_the-war-of-the-worlds/episodes/ep12`, `ep17`, plus ep13–ep15 for the worst
JSON). Server code read: `studio/command_center/app.py` (`/lib`, `/thumb`), `thumbs.py`, `library_paths.py`.

## 1. What the files weigh (measured)

| Kind | Example | Pixels | On disk | Notes |
|---|---|---|---|---|
| Panel | `storyboard/shot_NN.png` | 1024×1024 RGB | 1.52–1.59 MB avg (ep17/ep12) | 22–24 per unit |
| Grid | `storyboard/grids/*_2x2.png` | 2048×2048 RGBA | 3.9–4.6 MB avg, **7.76 MB max** | 1x1 grids are 1024² |
| Cast sheet | `refs/characters/albin/sheet.png` | 3072×2048 RGB | 5.8–6.7 MB | 245 PNGs under `refs/` |
| Contact | `storyboard/contact.png` | 1536×1024 | — | |
| Take | `takes/r2v/T03.mp4` | 768², 24 fps, 2.2 Mb/s, 8.7 s | 1.6 MB avg, 2.9 MB max | `moov` at byte 32 (faststart) |
| Master | `cut/master_iter7.mp4` | 1536², 12.9 Mb/s, 160 s | **259 MB** (8 iters ≈ 2 GB) | `moov` at byte 32, 112 KB |
| JSON (worst) | `ep14/takes/r2v/T05.dq.json` | — | 255 KB, 10,609 pretty lines | mostly numeric arrays (`segments`, `energy_q`) |
| JSON (prompts) | `ep17/takes/r2v/prompts.json` | — | 111 KB, list of 22 | `ep12/storyboard/eye_*.json` 138 KB |
| JSONL (worst) | `ep15/learnings.jsonl` | — | 263 KB, 98 rows, **longest row 10.9 KB** | ep14: 172 KB / 123 rows |
| Log (worst) | `logs/20260822113400/analysis/…050535.log` | — | 400 KB, 782 lines, **longest line 203 KB** | episode logs ≤ 47 KB, but 12 lines → ~4 KB lines |

Every `ep*` folder holds ~126 JSON files (ep12); the library holds 10,894.

## 2. What the server does today (measured with curl, loopback)

| Request | Size | TTFB / total | Headers |
|---|---|---|---|
| `/thumb/…/160/…shot_NN.png` cold | 3–6 KB | 25–72 ms | `public,max-age=31536000,immutable` |
| `/thumb/…/320/…shot_NN.png` cold | 11–20 KB | 92–118 ms | same |
| `/thumb/…/320/…grid_2x2.png` cold | 18 KB | 119 ms (160: **677 ms** — first decode of the 7.7 MB PNG) | same |
| `/thumb/…/320/refs/characters/*/sheet.png` cold | 9–12 KB | **400–530 ms** | same |
| any `/thumb` warm (process LRU, 64 MB) | — | 1.8–2.6 ms | same |
| `/thumb/…/1024/…` | 404 | — | `WIDTHS = {160, 320}` only |
| `/lib/…/shot_05.png` | 1.61 MB | 2.6 / 6.4 ms | `no-cache`, ETag, Last-Modified, `accept-ranges` |
| `/lib/…/grid_weybridge_2x2.png` | 7.76 MB | 2.5 / 21 ms | same |
| `/lib/…/albin/sheet.png` | 6.73 MB | 2.5 / 25 ms | same |
| `/lib/…/T03.mp4` Range `0-` | 206 | 2.0 ms TTFB | `content-range` correct |
| `/lib/…/master_iter7.mp4` Range at 200 MB, 1 MB | 206 | 2.1 / 4.6 ms | seek is free |
| `/lib/…/prompts.json`, `eye_*.json`, ep14 `learnings.jsonl` | 88 / 138 / 172 KB | ≤ 4 ms | `no-cache`, **not compressed** |

Four facts the design has to answer:

1. **Revalidation is broken on `/lib`.** `no-cache` makes the browser revalidate every time, but
   `If-None-Match` with the exact ETag and `If-Modified-Since` both returned **200 + full body**
   (Starlette's `FileResponse` sends validators but does not evaluate conditionals; `StaticFiles`
   does). So every re-open of a 7.7 MB grid re-sends 7.7 MB. RFC 9110 §13.1.2:
   https://www.rfc-editor.org/rfc/rfc9110#name-if-none-match ;
   https://www.starlette.io/responses/#fileresponse
2. **No compression.** `T05.dq.json` is 255 KB raw, **20.9 KB gzipped (12×)**. Loopback doesn't
   care; a phone over the LAN/Tailscale does.
3. **No CORS.** The mockups run on `:8710`, the board on `:8700`. `<img>`/`<video>` cross-origin is
   fine; **`fetch()` of a JSON or log from `:8710` is blocked** (no `Access-Control-Allow-Origin`).
   The mockup viewer cannot read live JSON as it stands.
4. **Logs are unreachable.** They live in `logs/<codex>/<stage>/` (sibling of the library, 21 MB)
   and `.log` is not in `library_paths.SUFFIXES`. The viewer's "all unit JSON + logs" needs a route.

Loopback bandwidth is effectively free (7.7 MB in 21 ms). The real costs are **server cold renders**
(100–700 ms of Pillow per thumb) and **browser decode + memory**: decoded bitmaps are w×h×4 —
panel 4 MB, 2×2 grid 16 MB, cast sheet 24 MB — and a full PNG decode is main-thread work unless
`decoding="async"`/`img.decode()` is used.

## 3. Full-view size: a new `/thumb` width 1024, the original only on zoom

Measured Pillow cost of the candidate "view" rendition (same code path as `thumbs.render`, WebP q80 m4):

| Source | 1024 WebP | 1536 WebP | 1024 JPEG q85 | original PNG |
|---|---|---|---|---|
| panel 1024² | **143 KB / 90–117 ms** | (= 1024, no upscale) | 230 KB / 22 ms | 1.61 MB |
| grid 2048² | **150 KB / 196 ms** | 279 KB / 280 ms | 238 KB / 127 ms | 7.76 MB |
| sheet 3072×2048 | **78 KB / 177 ms** (1024×683) | 136 KB / 227 ms | 135 KB / 138 ms | 6.73 MB |

Decision: add **`/thumb/{codex}/1024/{path}`** as the viewer's "fit" image. The viewer stage is at
most ~min(viewport) − chrome: ≈ 900 CSS px on a 1080p desktop, ≈ 400 CSS px on a phone (×2–3 DPR =
800–1200 device px). 1024 covers both. It is **11× smaller than the panel PNG and 50–85× smaller
than grids and sheets**, decodes to 4 MB instead of 16–24 MB, and for panels (1024 native) loses
nothing visible at q80. Do **not** add 1536: the only case that needs more than 1024 is a deliberate
zoom on a grid or sheet, and that should be the **original** `/lib` file (the owner zooms to check a
face or a hand — he wants the real pixels, not a third rendition). Zoom = `Z`/double-click/pinch →
swap to `/lib/…png`, show a spinner on the zoom badge, keep the 1024 underneath until `decode()`
resolves.

Server budget for 1024: cold ≤ 250 ms p95 on grids/sheets, warm ≤ 5 ms, ≤ 200 KB. Keep it in the
same LRU but **raise `CAP_BYTES` 64 → 160 MB** (a whole book's panels at 1024 is ~22×150 KB ≈ 3.3 MB
per unit; 160 MB holds ~1,000 views plus all small thumbs). Two cheap server tweaks:
- **Derive small from big**: when the 1024 bytes are cached, render 320/160 from them instead of
  re-decoding the 7.7 MB PNG (the 677 ms grid / 530 ms sheet cold thumbs become ~20 ms).
- **Bound concurrency**: the route is a sync `def` in Starlette's threadpool (40 threads). A
  preload burst of cold grids could pin 40 cores' worth of Pillow; wrap `render` in a
  `threading.Semaphore(2)` so cold renders queue and the page's own requests stay fast.

## 4. Progressive image: thumb instantly, view swapped in

The tile the owner clicked already shows `/thumb/320/…?v=<mtime>` — warm in the HTTP cache
(immutable) and in the LRU. So:

1. **t=0**: stage `<img>` gets the 320 URL (cache hit, 0 network) scaled up with
   `image-rendering:auto` and a 6 px `filter: blur()` only if the 320 is < ¼ of the stage width
   (on phone 320 is ~enough — no blur). Aspect ratio comes from the 320 itself, so no layout shift.
2. **t=0**: start `const im = new Image(); im.decoding = 'async'; im.src = view1024;` then
   `await im.decode()` (https://developer.mozilla.org/en-US/docs/Web/API/HTMLImageElement/decode)
   and swap `stage.src` only if the **load token** still matches the current item. Cross-fade 120 ms
   (`prefers-reduced-motion`: instant).
3. Zoom only: same pattern with the `/lib` original.

Budget: first paint of the item ≤ 16 ms (cache hit); sharp image ≤ 150 ms warm, ≤ 400 ms cold.

**Fast navigation** (held arrow key, ~30 items/s autorepeat): every keypress swaps the 320 at
once (cheap, cached), but the 1024 request is issued only after the cursor rests **100 ms**.
Stale requests: set the abandoned `Image().src = ''` and drop the reference — Chromium and Firefox
cancel an in-flight image fetch whose element loses its src; the token check guards any late
`decode()`. JSON/log fetches use one `AbortController` per viewer pane, aborted on every move
(https://developer.mozilla.org/en-US/docs/Web/API/AbortController). A server render already started
cannot be cancelled — the semaphore in §3 is what bounds that.

## 5. Neighbour preloading: ±1, images only, after settle

- After the current item's 1024 has decoded, preload **next then previous** 1024 views with
  `fetchPriority = 'low'` (https://developer.mozilla.org/en-US/docs/Web/API/HTMLImageElement/fetchPriority)
  and `decode()` them. Direction-aware: if the owner's last move was →, preload +1 and +2, −1 only.
- **Never preload video bytes.** For a neighbour take or master, preload only its poster (the panel
  thumb) — the moov is fetched by `preload="metadata"` when it becomes current.
- **Never preload originals** (`/lib` PNG) or JSON.
- Hold at most **3 decoded views** in a `Map` keyed by URL (prev/cur/next); evicting drops the
  `Image` reference. Memory ceiling: 3 × 4 MB = 12 MB, plus ≤ 1 original at 24 MB while zoomed.

## 6. Video: one element, metadata only, released on leave

- The unit page already owns `<video id="vid" preload="none">` for the master (`assets/unit.js`).
  The viewer gets **its own single `<video>`**; opening the viewer calls `vid.pause()`, and the
  viewer's element is the only one that may play while the dialog is open. One playing at a time.
- `preload="metadata"`, `poster` = the 1024 view of the take's panel (or 320 if not yet cached),
  `playsinline`. Both takes and masters are faststart (`moov` at byte 32; 14 KB for a take, 112 KB
  for a master), so metadata is one small range request; TTFB 2 ms; a seek to 200 MB costs 4.6 ms.
  (https://developer.mozilla.org/en-US/docs/Web/HTML/Element/video#preload)
- Moving away from a video: `v.pause(); v.removeAttribute('src'); v.load();` — the HTML spec's own
  advice to release the decoder and abort the network fetch
  (https://html.spec.whatwg.org/multipage/media.html#best-practices-for-authors-using-media-elements).
  Reusing one element and re-setting `src` avoids leaking decoders on a 24-take walk.
- Masters are 259 MB at 12.9 Mb/s: fine on loopback, borderline on a phone over the LAN. Not a
  viewer problem and not the web process's job (it never decodes video) — if phone review becomes
  real, the **assemble step** can write a `cut/master_iterN.preview.mp4` (768², ~2 Mb/s, ≈ 40 MB)
  and the viewer prefers it when `matchMedia('(max-width: 600px)')`. Flag only; no work now.
- No blob URLs anywhere: media go by plain URL so the HTTP cache does the work and there is nothing
  to revoke. The one exception — "Download pretty JSON" — creates a blob, clicks, and
  `URL.revokeObjectURL` in the same tick
  (https://developer.mozilla.org/en-US/docs/Web/API/URL/revokeObjectURL_static).

## 7. JSON, JSONL and logs: render budgets

Measured worst cases: 255 KB / 10.6 k pretty lines (`dq.json`), 98 rows with 10.9 KB rows
(`learnings.jsonl`), 782-line logs with a **203 KB single line**.

- **JSON ≤ 64 KB** (most prompt/verdict files): `JSON.parse` + `JSON.stringify(x, null, 2)` into one
  `<pre>` with a hand-rolled ~40-line tokenizer for colour. ~5 ms. No tree needed.
- **JSON > 64 KB** (`dq.json`, `prompts.json`, `shots.json`, `eye_*.json`): a **collapsible tree,
  arrays of > 20 items folded** to `[ 412 numbers ]` and objects beyond depth 2 folded. That alone
  turns the 10.6 k-line `dq.json` into < 100 visible rows — folding beats virtualising here because
  the bulk is numeric arrays nobody reads. Expanding a 400-number array renders it as a wrapped
  inline run, not 400 lines. Highlight only rendered nodes.
- **The item's slice first** (V05 #3): the viewer opens `prompts.json` at the current shot's entry
  (`[index == shot]`), not at byte 0 — 111 KB becomes ~5 KB on screen.
- **JSONL**: one row per line, collapsed to a one-line summary (`ts · kind · first 120 chars`),
  expand on click to the JSON tree. Today's worst is 123 rows → render all. **Virtualise above 500
  rows** (fixed 28 px collapsed rows, a ~60-line vendored windowing loop; expanded rows measured on
  expand). Add `content-visibility:auto; contain-intrinsic-size:auto 28px` per row as the cheap first
  step (https://web.dev/articles/content-visibility).
- **Logs**: tail only (§8), **every line capped at 2,000 chars** with a `… +201,163 chars · show`
  affordance — a 203 KB line in a `<pre>` is a single layout box that stalls the main thread on
  every resize. `white-space: pre-wrap; overflow-wrap:anywhere`.
- Budget: any file pane interactive ≤ 100 ms after the response; main-thread task ≤ 50 ms.

## 8. Recommended server additions (for the real board; the mockups fake them)

| # | Route / change | Behaviour | Budget |
|---|---|---|---|
| S1 | `WIDTHS = {160, 320, 1024}` | the viewer's fit image; WebP q80; small widths derived from cached 1024; `Semaphore(2)`; LRU 160 MB | cold ≤ 250 ms p95, warm ≤ 5 ms, ≤ 200 KB |
| S2 | `/lib` conditional GET | evaluate `If-None-Match`/`If-Modified-Since` → 304 (a 10-line wrapper, or serve through `StaticFiles`' logic). Media URLs with `?v=<mtime>` get `immutable` like `/thumb`; JSON/JSONL/logs stay `no-cache` + 304 | 304 ≤ 3 ms, 0 body |
| S3 | `/json/{codex}/{path}?ptr=/0/shots&rows=a-b` | same guard as `/lib`, `.json`/`.jsonl` only; returns the raw JSON (pretty-printing is the client's job), sliced by JSON Pointer (RFC 6901) or JSONL row range; gzip when `Accept-Encoding` allows; `X-Total-Rows`, `X-Bytes` headers | ≤ 256 KB raw/≤ 32 KB gz, ≤ 30 ms |
| S4 | `/log/{codex}/{stage}/{file}?tail=500&before=<offset>&max_line=2000` | reads from the logs root (`app.state.logs`), filename must match `<codex>__<stage>__\d{14}\.log`; seeks from the end; lines truncated with their full length reported; `before` pages backwards; gzip | ≤ 64 KB, ≤ 20 ms |
| S5 | gzip **only** in S3/S4 | not a global `GZipMiddleware` — it would touch mp4 range responses and the SSE stream (https://www.starlette.io/middleware/#gzipmiddleware) | — |

S3 and S4 also fix the "unit JSON + logs" scope cleanly: `/lib` stays a dumb file server.
For the **mockups** (static, `:8710`): do not add CORS to the board. Copy the handful of files the
viewer demo opens (ep12 `prompts.json`, one `dq.json`, `plan.verdict.json`, `learnings.jsonl`, one
log tail) into `mockups/assets/files/` as read-only snapshots — same pattern as `data_*.js`.
Images and videos keep pointing at `:8700` (cross-origin `<img>`/`<video>` works; 1024 views will
404 until S1 lands, so the mockup falls back to `/lib` originals with `decoding=async`).

## 9. Caching summary

| URL | Cache-Control | Validator |
|---|---|---|
| `/thumb/{w}/…?v=<mtime>` | `public, max-age=31536000, immutable` (today, keep) | — |
| `/lib/…png|mp4?v=<mtime>` | `public, max-age=31536000, immutable` (new) | ETag (+304, S2) |
| `/lib/…json|jsonl`, `/json`, `/log` | `no-cache` | ETag → 304 (S2); a running unit's `learnings.jsonl` grows, so never immutable |

RFC 8246 `immutable`: https://www.rfc-editor.org/rfc/rfc8246 . WebP for the view size:
https://web.dev/articles/serve-images-webp . Faststart reference: https://trac.ffmpeg.org/wiki/Encode/H.264#faststart

## Top 8 recommendations

1. Add **`/thumb/…/1024/`** (WebP q80) as the viewer's fit image: 78–150 KB instead of 1.6–7.8 MB,
   4 MB decoded instead of 16–24 MB; the `/lib` original only on explicit zoom. No 1536.
2. **Progressive swap**: show the already-cached 320 at t=0, swap to the 1024 after `img.decode()`,
   guarded by a load token; on held arrows, request the 1024 only after a 100 ms rest.
3. **Preload ±1 images only** (direction-aware +2), `fetchPriority='low'`, after the current settles;
   never video bytes, never originals, never JSON; keep ≤ 3 decoded views.
4. **One viewer `<video>`**, `preload="metadata"` (faststart: 14–112 KB), panel thumb as poster,
   pause the page's `#vid` on open, `removeAttribute('src')+load()` on leave.
5. **Fix `/lib` revalidation** (304s) and give versioned media URLs `immutable` — today every re-open
   of a grid re-downloads 7.7 MB.
6. **Fold, don't virtualise, JSON**: arrays > 20 folded, depth > 2 folded, open at the item's slice;
   virtualise JSONL only past 500 rows; cap log lines at 2,000 chars (a 203 KB line exists).
7. Add **`/json` (pointer/row slices, gzip — 255 KB → 21 KB)** and **`/log` (tail 500, paged back,
   line-capped)**; gzip only there, never globally. Logs are unreachable through `/lib` today.
8. Bound server cold renders with a **`Semaphore(2)`**, derive 160/320 from the cached 1024, raise
   the LRU to 160 MB; mockups use snapshot JSON copies instead of CORS.

## 2 disagreements I expect

1. **"Just show the original PNG — it's loopback, 7.7 MB in 21 ms."** True for the bytes, false for
   the browser: a 2048² RGBA decode is 16 MB and tens of ms of decode per arrow press, and the
   owner's phone (≥ 400 px is a stated constraint) is not on loopback. The 1024 view is the cheap
   fix; originals remain one keystroke away.
2. **"Virtualise every JSON view, it's the standard answer."** The heavy files are heavy because of
   numeric arrays (`segments`, `energy_q`), not because of many meaningful rows. Folding them makes
   10.6 k lines into < 100 with zero vendored code, and keeps Ctrl-F working; virtualisation breaks
   in-page find. I'd keep virtualisation in reserve for JSONL past 500 rows, which no unit has yet.
