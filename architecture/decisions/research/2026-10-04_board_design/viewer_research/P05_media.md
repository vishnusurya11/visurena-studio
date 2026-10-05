# P05 — Media experience (screening room, grids, Viewer, posters, hover-scrub, playback, compare, iterations)

Panelist P05, 2026-10-04. Read-only. Evidence: code on :8700 (`templates/unit.html`, `_unit_live.html`,
`static/progress.js`, `app.py`, `unit_view.py`), the mockups on :8710 (`assets/unit.js`, `viewer.js`), and
live probes with browse. **The real board returned HTTP 500 on every page (`/`, `/d/episode`, ep12, ep17)
during this pass** because the re-skin is mid-way. `/lib` and `/static` still served. So the board findings
below come from reading the code, and the mockup findings were measured live.
Shots: `mockups\shots\panel\P05_mock_finished.png` and `P05_mock_viewer.png`.

## The brick
**Every `<video>` on the board obeys one contract: it is never audible unless it is visible. It plays only
through one owner, never has more than one sibling playing, and has a visible state for every media event
(idle · loading · playing · waiting · error · ended).** The owner's bug (audio with no picture) breaks the first
clause. The bug classes below all come from some element not having a single owner of its lifecycle.

## 1. Playback reliability: what I measured

| Where | Finding | Evidence |
|---|---|---|
| Mockup screening room | **Fixed.** `showPlayer()` is the one show path. A `play` listener re-shows the player. `#bigplay` → `hidden:false, paused:false, videoWidth:1536`, t = 5.6 s a moment later, readyState 4. | browse js probe |
| Mockup Viewer | Opening a take paused the page master (`page.paused:true`, t kept at 29.76). The Viewer owns its own `<video>`. Esc ×2 closed it, removed `src` and cleared the hash. The page did not resume (SPEC v3). | browse probe |
| Mockup, guard gap | The capture-phase guard in `viewer.js:772` pauses a video only when it **starts** under a `[hidden]` ancestor. It misses a video that is **already playing** when its container disappears (dialog closed, `<details>` folded, a tab switched, an htmx swap). It also misses a closed `<dialog>` and `display:none`, because neither is a `[hidden]` attribute. | code |
| **Board lightbox (the same bug class, live in production code)** | `unit.html:20` clones `<video controls autoplay>` (**unmuted**) into `#lightbox`. Closing it (`dlg.close()` or the native Esc) **leaves the clone in `.lb-body`**. No `close` handler empties it or pauses it. So a take opened from the grid keeps playing its **sound with no picture** after Esc. The master in `.mrow` can also play at the same time as it, because nothing on the board enforces "one at a time". | `unit.html:184-196` (could not click it: board 500) |
| Board live master | `_unit_live.html:27` `<video controls muted …>`: the finished master on the live card is **muted by default**. That is the inverse bug (picture with no sound), and the owner will read it as a broken mix. | code |
| Board take tiles | 24 `<video preload=none src=…>` elements with `poster` = **the panel thumb** (`unit_view.py:259`). The tile shows the storyboard panel, and hover swaps to the take. The poster misstates what the tile is. | code |
| Board live sheet hover | `progress.js:156` creates `<video preload=auto>` on mouseover and **removes** it on mouseout. `/lib` sends `no-cache` and ignores `If-None-Match` (V02), so every re-hover re-downloads the take. | code |
| Seek cost | Clicking a fault row seeks the 247 MB master (1536², L5.0, 12.7 Mb/s), which dropped to **readyState 1**. Neither player draws a `waiting` state. The picture freezes with no feedback, and that looks the same as a hang. | browse probe |
| Error state | No player listens for `error`/`stalled`. A 404 or a decode failure leaves the poster up with a play button that does nothing. | grep: no `error`/`waiting` handlers in unit.js, unit.html, progress.js |

## 2. Recommendations

### 2.1 One media contract, enforced in one file (`static/media.js`, ~60 lines)
- **Single owner:** the capture-phase `play` listener moves out of `viewer.js` into a shared `media.js` that
  every page loads (`shell.js` already loads on every page). It handles "one at a time" and "never play unseen".
- **Visibility watchdog:** on `timeupdate` (about 4 Hz, so no extra timer) call `if (!v.checkVisibility({opacityProperty:true}))
  v.pause()`. `Element.checkVisibility()` is true only when the element is rendered. It sees `display:none`, a
  closed `<dialog>`, a folded `<details>` and `content-visibility`, in Chrome 105+, Firefox 106+ and Safari 17.4+
  (https://developer.mozilla.org/en-US/docs/Web/API/Element/checkVisibility). This one check covers every way a
  container can disappear, including the board lightbox bug and any future one.
- **Containers clean up:** each `<dialog>` that holds media pauses it and empties it on its `close` event
  (https://developer.mozilla.org/en-US/docs/Web/API/HTMLDialogElement/close_event). On the board: add
  `dlg.addEventListener('close', () => body.replaceChildren())`.
- **Sound policy:** the reviewing owner wants sound. Start unmuted. If the browser blocks it (`NotAllowedError`),
  fall back to muted and show a visible "sound blocked: press M" chip, as `viewer.js:343` already does
  (Chrome autoplay policy: https://developer.chrome.com/blog/autoplay). Remove `muted` from the live master. Hover
  previews alone stay muted.
- **Every state drawn:** `waiting`/`seeking` → a 300 ms-delayed ring on the player, so a fast seek never
  flashes. `error` → the poster plus "can't play `cut/master_iter7.mp4` (HTTP 404 / decode)" with the path and a
  link to open the file. `ended` → a "replay" overlay. Event list:
  https://developer.mozilla.org/en-US/docs/Web/HTML/Element/video#events

**How to know it worked:** add a `media_probe` script in browse that runs on every page. For each player and
each play path (big play, Space, a fault click, a version switch, Viewer open/close, lightbox open/Esc): play,
wait for 3 presented frames via `requestVideoFrameCallback`
(https://developer.mozilla.org/en-US/docs/Web/API/HTMLVideoElement/requestVideoFrameCallback), and assert
`checkVisibility() && videoWidth > 0`. Then close or hide the container and assert that **no** media element in
the document has `paused === false`. It is free (local), and it is the regression test for the owner's bug. Keep
it as `@pytest.mark.local`.

### 2.2 Live refresh must never touch a playing element ("dynamic" without breaking media)
The owner asked for a more live board, and media is where polling breaks things. An htmx `outerHTML`/`innerHTML`
swap that contains a `<video>` destroys its buffer, its position and its play state. A swapped `<img>` with a new
`src` paints blank until it has decoded.
- **Rule:** no player lives inside a polled swap region. Where one must, mark it `hx-preserve` with a stable id
  (https://htmx.org/attributes/hx-preserve/), or morph with idiomorph, which matches nodes by id and keeps
  their state (https://github.com/bigskysoftware/idiomorph). This agrees with 09_liveness_motion (morph, no SSE).
- **A new picture lands (ep17 running):** `progress.js` `patchSheet` already sets `img.src` in place. Change it
  to load into a detached `Image`, `await img.decode()`, then swap and run the single `just` pulse. A panel
  then never flashes empty (https://developer.mozilla.org/en-US/docs/Web/API/HTMLImageElement/decode). For a
  take, put a `▶` corner on the tile only after the MP4's `moov` is readable (the file is fast-start, V02), so
  hover never meets a half-written file.
- **A new master iteration lands while the page is open:** do not reload the player. The version badge gets a
  dot (`v8 •`) and a quiet toast, "iter8 landed · MASTER pending". The owner switches when they choose, and
  the position carries over (the mockup's version switch already does this).
- **Caching, so refresh is cheap:** serve `/lib` media under a versioned URL (`?v=<mtime>` or the sha8 that
  `qc_r2v.json` already holds) with `Cache-Control: immutable`, the way `/thumb` already does. Honour
  `If-None-Match` → 304. Re-hovers and re-opens then cost 0 bytes
  (https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching).

### 2.3 Posters tell the truth
- A **take tile** uses the take's own first content frame (`takes/work/content/TNN_0.png`, already on disk), not the
  storyboard panel. The panel keeps its own `P` frame, as in the mockup pair.
- The **master poster** is the picture the episode publishes with: the YouTube thumbnail if `youtube.json` names
  one, otherwise the frame at the master's first MASTER-flag-free shot. It is never a hard-coded `T19_1.png` (mockup).
- **Missing media** gets a slot that says why ("T14 not rendered · step 09 shoot pending"), never a black box.

### 2.4 Scrub that shows the real frame (trickplay)
The mockup's hover-scrub shows three content PNGs per take, and the timeline tooltip shows the **take's** frame,
not the master's frame at that time. That is what makes it misleading for a review: grading and titles live in
the master. Build one **sprite sheet per master** (1 frame/s, 160 px, about 160 tiles = one WebP of about
300 KB) and a tiny JSON index, generated locally at $0 by the board on first request and cached by sha8. The
timeline hover, the scrubber hover and the iteration stack then show the **actual** master frame. This is how
YouTube/JW/Jellyfin trickplay works (WebVTT thumbnail tracks:
https://docs.jwplayer.com/platform/docs/add-preview-thumbnails). It also feeds the poster wall and Home's poster.

### 2.5 Review proxy: instant seek on a 247 MB master
Keyframes sit only on the cuts (longest GOP 8.46 s, V02), so a mid-shot seek decodes up to 200 frames at 1536²,
which is the readyState-1 stall measured above. NLEs and Frame.io review on proxies. The board makes a
**768², about 2.5 Mb/s, keyframe-every-12-frames proxy** once per sha8 (ffmpeg, local, $0, about 20 s on this
box) and plays that by default. `F` swaps to full resolution with the position kept. A fault click, J/L and frame
step then always land within one GOP of 0.5 s (https://web.dev/articles/fast-playback-with-preload). It goes
under the episode's `cut/.proxy/` with a relative path only.

### 2.6 Compare that actually compares
The mockup compare uses stills. Build it as two `<video>`s on one clock: A drives, and B corrects through rVFC
whenever the drift is over 1/48 s. Modes: side by side · wipe · flip (Tab). Because the master cuts are fixed
by plan, an iteration pair lines up frame for frame. Default B = the previous **distinct** hash (the mockup's md5
de-duplication is right). Mark changed shots by comparing per-segment sprite tiles (dHash on the 2.4 sprites), so
there is no need to wait for `master_iterN.cut.json` from the pipeline. Pattern: Frame.io's Comparison Viewer
(https://frame.io/features).

### 2.7 Iteration stacks everywhere, not only the master
A take with `attempts/T10_fail1..3.mp4` gets a `+3` badge (Viewer filmstrip, SPEC v3). On the **grid tile**
itself, ↑/↓ in the Viewer walks the attempts. A tile shows a tiny "try 3" plus the newest first, and the retired
attempt's reason (when the pipeline keeps it) appears beside it, never a guessed pairing (V06).

## Proposals
| id | page | change | effort | files |
|---|---|---|---|---|
| **P05.1** | all (board) | `media.js`: a single play owner, a `checkVisibility` watchdog, `close`-clears-media on every dialog, and drawn waiting/error/ended states. **Fix the board lightbox Esc-keeps-playing bug and the muted live master today.** | S | `static/media.js` (new), `templates/unit.html`, `_unit_live.html`, `base.html`, mockup `viewer.js`/`unit.js` |
| **P05.2** | all | A `media_probe` browse script: every play path → 3 rVFC frames visible; every close → zero media playing. Marked local, $0. | S | `tests/ui/media_probe.js` (new), `tests/test_media_probe.py` |
| **P05.3** | unit (running) | Live landing without flicker: `decode()`-then-swap tiles, one `just` pulse, `hx-preserve` on every player, no player inside a polled region. | S | `static/progress.js`, `_live_sheet.html`, `unit.html`, `_unit_head.html` |
| **P05.4** | board server | Versioned `/lib` URLs + `immutable`, `If-None-Match` → 304 (re-hover and re-open cost 0 B). | S | `app.py`, `library_paths.py`, `unit_view.py` |
| **P05.5** | unit | Truthful posters: take tile = the take's frame, master = the publish thumbnail, missing = "why" slot. | S | `unit_view.py`, `thumbs.py`, `unit.html` |
| **P05.6** | unit (finished) | New-iteration badge and toast; never reload a playing master. | S | `progress.js`, `unit.html`/the screening-room partial |
| **P05.7** | unit, book, Home | A master trickplay sprite (1 fps, 160 px, cached by sha8) for timeline hover, scrubber and posters. | M | `thumbs.py` → `trickplay.py` (new), `app.py` route `/trick/…`, `unit.js` |
| **P05.8** | unit (finished) | A review proxy (768², GOP 12) by default, `F` = full resolution. | M | `proxies.py` (new), `app.py`, the screening-room JS |
| **P05.9** | unit (finished) | Real video compare (two players, one clock, side/wipe/flip, changed-shot marks from sprites). | M | the screening-room JS, `viewer.css` |
| **P05.10** | Viewer | The attempt stack on grid tiles plus ↑/↓ attempts with kept reasons. | M | `unit_view.py`, `viewer.js` |

Publishable: P05.1 + P05.2 as **"media-contract"**, a ~100-line MIT drop-in plus a Playwright probe that catches
"audio with no picture" and "two players at once" on any site. Small, general, and there is no prior package that
does exactly this. P05.7 + P05.8 as a "local trickplay + proxy for review boards" FastAPI helper.

## I will argue against
1. **An autoplaying, looping muted master or take "hero" on Home or the department page to feel premium and
   alive.** One GPU box, a 1536² L5.0 decode, and a page left open all day. It burns decode and attention, and
   it breaks 09's "one animation per viewport" rule. A poster plus a trickplay hover is the living version that
   costs nothing until it is asked for.
2. **SSE/WebSocket push, or a faster full-region htmx poll, as "more dynamic".** It is not needed at 2–10 s
   cadence for one viewer (09 already ruled no SSE). A region swap that wraps a player is exactly what kills
   playback state. Make the polled patch smaller and morph it, rather than pushing more often.
3. **Skeleton shimmer on every tile/grid, or virtualised/infinite grids.** Thumbs are about 14 KB from
   localhost and a grid holds at most about 24–36 tiles. A shimmer flashes for 20 ms and adds motion
   everywhere. Use a fixed-size slot that says why it is empty, plus `decode()`-then-swap.
