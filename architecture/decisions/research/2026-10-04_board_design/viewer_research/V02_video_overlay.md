# V02 — Video playback inside the overlay

Researcher V02, 2026-10-04. Playback only: takes, master segments and failed attempts in the in-page viewer, and
how it shares the page with the screening room. Measured read-only on ep12, ep17 and the live board on :8700.

## 1. What the overlay will actually play (measured)

ffprobe is **not on PATH** on this box (`scripts/episode/eye_review.py:83` says so too). I measured with
`D:\Projects\pheonix\dev\ffprobe.exe` (gyan.dev 2025-06-11 build), and parsed MP4 atoms in Python.

| File (under `episodes/ep12/`) | Count | Size | Duration | Picture | Audio | Keyframes |
|---|---|---|---|---|---|---|
| `takes/r2v/T00..T23.mp4` | 24 | 0.55–2.94 MB (38.9 MB total) | 3.75–8.71 s (7.29 s = 175 f is typical) | H.264 High L3.1, 768², 24 fps, yuv420p, ~1.4 Mb/s, B-frames | AAC-LC 32 kHz stereo | **one** I-frame per take (T00: 1 I, 44 P, 130 B) |
| `takes/r2v/attempts/T??_failN.mp4` | 11 (T10 has 3) | ~1.7 MB | ~7.3 s | same as takes | AAC | same |
| `cut/master_iter1..7.mp4`, `master_r2v.mp4` | 8 | 245–249 MB each (**2.08 GB** in all) | 160.256 s, 3846 f | H.264 High **L5.0, 1536²**, 24 fps, 12.7 Mb/s, libx264 | AAC-LC 48 kHz stereo, 255 kb/s | at 0, 7.0, 15.17, 21.96 … = **exactly the planned cuts**; longest GOP 8.46 s |
| `takes/work/seg00..23.mp4`, `picture.mp4`, `mixed.mp4` | scratch | 1.7 MB / 51.6 MB / 56.6 MB | — | 768², pre-upscale | seg/picture have none | — |

- **Every file is already fast-start**: the atom order is `ftyp moov free mdat` for the masters and the takes. The moov is
  112,321 B for the master and 13–14 KB for a take. So `preload="metadata"` costs about 112 KB for the master and
  about 13 KB for a take.
- `master_iter7.mp4` and `master_r2v.mp4` have the same sha256 prefix, **faf11c8f**, which is `qc_r2v.json.sha8`.
  qc names `master_r2v.mp4`. The overlay should play the file whose sha matches qc, and label it "iter7".
- In `qc_r2v.json` → `edit.segments[]` (24 rows), the fields `start` and `n` are **frames at 24 fps** from the start of
  the master. Segment *k* is `#t=start/24,(start+n)/24`. For example T00 is 0–7.000 s (168 of its 175 frames, so the
  take is trimmed) and T01 is 7.000–15.167 s. The segments add up to 3733 frames. The title card is at the **tail**
  (frames 3733–3846, `edit.tail`), so no offset is needed. `offset` is 0 on every row and `held` is empty, but the
  code must still apply `offset`.
- Which takes have sound: only takes with a dialogue line carry a voice (`voice_02/06/07/11/16/20/22.wav` →
  T02 T06 T07 T11 T16 T20 T22). The other 17 takes are narration-lane takes with a **silent** AAC track, because the
  voice lives in the master. The overlay should say so instead of offering a mute button that does nothing.
- ep17 (the running unit) has **no takes and no cut yet** (`takes/r2v/` holds only `prompts.json`), so its overlay
  shows pictures and JSON only. The video state "not rendered yet" is real today.
- **Live board `/lib/`**: `Range` → `206` with `accept-ranges: bytes`, a strong `etag` and `content-range`, and
  `416` past EOF. **`HEAD` → 405** (GET only; the media stacks don't need HEAD). `cache-control: no-cache`, and
  **`If-None-Match` is ignored (200 + full body)**, so every reopen of a take re-downloads it. That costs about 7 ms
  for 2.9 MB on localhost; on a phone over the LAN it is a few hundred ms. A 4 MB range from the middle of the master
  takes 13 ms. `/thumb/` only exists at 160 and 320 (a request for 1024 returns 404). A 320 WebP is about 14 KB.

## 2. Controls: custom, thin, keyboard-first (no native `controls`)

Why not native controls inside the overlay:
- They differ by browser, and they draw light chrome on Studio black. Chrome adds download/PiP/cast menus
  (`controlsList="nodownload"` and `disablePictureInPicture` only trim some of that).
- When the native control bar has focus it **takes the arrow keys and Space for itself** (seek/volume), and this
  overlay already uses ←/→ for "previous/next item", as the current shot view (`#sv`) does.
- There is no frame step, no frame-accurate timecode, and no segment marker. Frame.io, the YouTube player and every
  NLE draw their own controls.

So: `<video playsinline preload="metadata" disablepictureinpicture tabindex="-1">` with no `controls`, plus one bar
underneath. If the script fails, `controls` is added in a `<noscript>`-safe way, so the video still plays.

**Bar (left → right, 36 px high, Studio-black tokens):** play/pause · timecode `0:03.12 · f75 / 175` · scrubber
`<input type=range step=any>` with `aria-valuetext="3.1 seconds, frame 75 of 175"` · speed button `1×` (cycles 1 → 0.5 → 0.25 → 2) ·
loop toggle · sound toggle (disabled with the text "silent take, voice is in the master" on narration takes) ·
**source switch `Take | In master`**. When the master is selected, the scrubber covers only the segment, and a thin
second track underneath shows where the segment sits in the full 2:40.

**Keys (live only while the overlay is open; never when focus is in input/textarea; Esc is handled by `<dialog>`):**

| Key | Action | Source / note |
|---|---|---|
| Space or K | play / pause | YouTube K; the shot view already uses Space |
| L | play forward; pressed again → 2× (NLE habit); K resets to 1× | Avid/Premiere/Resolve JKL |
| J | jump back 1 s (to the segment start at most) | browsers cannot play backwards: Chrome throws on a negative `playbackRate` |
| `,` / `.` | pause, then step one frame back / forward | YouTube convention, and the overlay is already paused for it |
| Shift+`,` / Shift+`.` | speed down / up (0.25 · 0.5 · 1 · 2) | YouTube `<` `>` |
| Home / 0 | go to the start of the take or segment | |
| O | loop on/off | L is taken by play forward |
| M | sound on/off (remembered) | YouTube M |
| T | toggle Take ↔ In master for this shot | new |
| ← / → | previous / next item (picture or video) | consistent with `#sv` |
| ↑ / ↓ | panel → take → master stage | consistent with `#sv` |

**Frame step done right.** At 24 fps, set `currentTime = (f + 0.5) / 24`. Seeking to the middle of the frame avoids
landing on the frame before it through float rounding. Read the frame that is actually shown from
`requestVideoFrameCallback`'s `metadata.mediaTime`, not from `currentTime`. rVFC is available in Chrome, Edge,
Safari 15.4+ and Firefox 132+. Fall back to `timeupdate` where it is missing. Going backward costs a decode from the
last I-frame: on a take that is from frame 0 (one GOP, at most 209 frames at 768², which is instant), and on the master
it is from the segment start, because the keyframes sit on the cuts. Use `fastSeek()` only while dragging the
scrubber, and only where it exists (Firefox/Safari; Chrome has none), then make a precise seek on release.

**Speed:** `playbackRate` keeps pitch by default (`preservesPitch`), so 0.5× still works for checking lip-sync on
dialogue takes. The speed is remembered per viewer (`localStorage`, wrapped in try/catch).

## 3. Autoplay and sound

The rules, from the browser policies:
- Muted autoplay is always allowed.
- Sound is allowed when `play()` runs with a **user activation**. In the HTML spec, an activation comes from
  keydown (except Esc), mousedown, pointerdown/up and touchend.
- Chrome also lets a site play with sound once the site has sticky activation or a high Media Engagement score.
- iOS Safari needs `playsinline`, and `play()` must be called **synchronously inside the gesture handler**, not after
  an `await fetch()`.

What the overlay does:
1. **Open by click, Enter, or ←/→ to the next item.** These are all activations. The overlay calls `video.play()`
   inside the same handler, with sound on (unless the viewer muted it before, which is remembered). It sets `src`
   first, synchronously, and never waits for JSON before calling play.
2. If `play()` rejects (`NotAllowedError`), the overlay mutes and retries, then shows a one-line chip
   "sound off, press M" instead of failing silently. `AbortError` from a quick src change is ignored.
3. The hover-dwell play on the take grid (`unit.js:692`) stays **muted**, because pointerover is not an activation.
4. `prefers-reduced-motion`: the overlay still opens on a video, but **does not autoplay**. It shows the poster and a
   play button.
5. **Loop defaults:** a take loops (3.75–8.7 s; a reviewer watches it 2–3 times). A master segment does not loop and
   pauses at its end. O toggles looping for both.

## 4. Switching between a picture and a video without the layout jumping

- **One stage box at a fixed size**, decided before any media loads:
  `width: min(100vw - 32px, 100dvh - <chrome h>); aspect-ratio: var(--ar, 1)`. Every ep12 video and panel is square
  (768², 1024², 1536²). The non-square items come from the item's own data before load: `storyboard/contact.png`
  is 1536×1024 and a grid such as `ep12_grid_bank_2x2.png` is 2048². The page sets `--ar` from those numbers.
  Media inside the box uses `object-fit: contain`, so the box never resizes.
- `<img>` and `<video>` are **siblings in the box**, and switching one is a `hidden` toggle. The `<video>` element is
  not destroyed and recreated. Give both `width`/`height` attributes (768/768 for takes), so the intrinsic size is known
  before metadata arrives.
- The controls bar **always takes its 36 px**. For a picture, it holds the picture's own row (size · zoom 1:1 ·
  open original), so the item caption under the box does not move up or down.
- On a phone (≥ 400 px), the stage is 368 px square and the bar wraps the speed and loop buttons into a `⋯` menu.

## 5. Posters while loading (the board never decodes video)

- `poster` = **the thumbnail the user just clicked**. It is already in the HTTP cache, so it costs nothing and gives
  the feel of the same element growing. A take gets `/thumb/…/320/takes/work/content/T{i}_1.png` and a master segment
  gets `T{i}_2.png`. These PNGs are written by the take content check, so no frame is ever extracted from an mp4 in
  the web process.
- Note: the `content/T{i}_k.png` frames are sampled **after the one-second H3 head leak**
  (`take_content_check.py:42`). So the poster is not frame 0, and on a slow link the first decoded frame "jumps" away
  from the poster. That is acceptable, because locally the first frame arrives in under 50 ms. Do not show a spinner
  before 300 ms.
- The 320 px poster is soft when stretched to about 800 px. Fade it out on the video's `loadeddata` (120 ms, and none
  under reduced-motion).
- **Failed attempts** have no content frames. Their poster is the kept take's `_1` with an "attempt 2 of 4 · failed"
  badge.

## 6. Range requests from `/lib/`, and preloading the neighbour

- The current item gets `preload="auto"`, because it is about to play. That is safe: a take is ≤ 3 MB, and Chrome
  fetches the master in ranges (the moov first, then the bytes around the seek).
- **Neighbours (←/→):** prefetch their **poster only** (`new Image().src = thumb320`, 14 KB each). Do **not** create a
  second `<video preload=metadata>` for them. It would be a second media player, and Chrome counts it toward its
  per-tab player limit (WebMediaPlayer). It would also only save the 13 KB moov, which takes 2 ms on localhost. If you
  want to warm the neighbour anyway, `fetch(url, {headers:{Range:'bytes=0-16383'}})` is the most to do, but because
  of `no-cache` + ignored ETag (§1) the media stack will fetch again regardless. So don't.
- Fix for the later board (FastAPI side, not the mockup): answer `If-None-Match`/`If-Range` with 304, and send
  `cache-control: private, max-age=300` on `/lib/**/*.mp4`. Do not mark them `immutable`, because
  `master_r2v.mp4` is overwritten each run, while `master_iterN.mp4` never is.
- Master over a phone/LAN: 12.7 Mb/s at 1536² with H.264 L5.0 decodes fine on current phones, but it is the heaviest
  thing the board serves. **Never** fall back to `takes/work/picture.mp4`/`segNN.mp4` as a "light" master. They are
  pre-upscale, silent, scratch files that can be stale, and they are not what shipped.

## 7. Showing a take's panel and its master segment

The overlay item for shot *i* is a small set of related files, and ↑/↓ moves across them (the same model as `#sv`):

| Stage | File | Notes |
|---|---|---|
| Panel | `storyboard/shot_{i:02}.png` (1024²) | image |
| Staged ref | `storyboard/h3/shot_{i:02}.png` (768²) | image; `prompts.json[i].refs[0]`, the picture H3 was actually given |
| Take | `takes/r2v/T{i:02}.mp4` | the kept take, looped; JSON tabs: `T{i}.dq.json`, `T{i}.content.json`, `shots.json[i]` |
| Attempts | `takes/r2v/attempts/T{i:02}_failN.mp4` | a dot strip "1 2 3 ✓" (T10 has 3 fails); only when they exist |
| In master | `cut/master_r2v.mp4#t={start/24},{(start+n)/24}` | the segment row from `edit.segments` where `take == i` |

**Media-fragment `#t=` caveats** (W3C Media Fragments):
- Browsers apply the end time **only on the first playthrough**. After a seek, or a second play, the end is ignored.
- `timeupdate` only fires every 15–250 ms, so a JS stop placed in `timeupdate` overruns into the **next shot**,
  showing up to about 6 frames of the wrong picture.

So: set `#t=` for the initial position, **and also** enforce the end with rVFC. Pause when
`mediaTime >= end - 1/48`, and loop by seeking to `start + 1/48`. The seek to the start is cheap because every
segment start is a keyframe (§1).

**Changing src costs a reload.** Moving between "Take" and "In master" changes `src`, which means a new moov fetch
(13 KB or 112 KB, 2–3 ms locally). That is acceptable, so don't keep two decoders alive to avoid it.

## 8. One video playing at a time, with the screening room

Today `unit.js` keeps **exactly one `<video>`** and moves it between the player, the hover tiles and `#sv`
(`parkVideo`, `dataset.src` checks). Rule for the overlay:

- **On open:** save `{src, currentTime, wasPlaying}` from the screening player, call `pause()`, and leave its `src`
  in place, so the master's buffer and position stay warm.
- **Enforce one playing across the whole page, not per widget:**
  `document.addEventListener('play', e => { for (const v of document.querySelectorAll('video')) if (v !== e.target) v.pause(); }, true)`.
  The listener must be on the capture phase, because media events do not bubble. This makes "one plays at a time"
  structural, so it does not depend on every caller remembering to park.
- **On close:** **do not auto-resume.** Restore the screening player to the saved position and show its play button
  with "paused at 1:23 · Space resumes". Sound starting by itself after Esc surprises the user, and the reviewer has
  usually moved on. The one exception: if the overlay was opened *from* the screening room's fault list while it was
  playing, and nothing was played in the overlay, then resume.
- **Lifecycle:** `visibilitychange → hidden` pauses. Closing the overlay calls `pause()`, then
  `removeAttribute('src')` + `load()` on the overlay's video, to release the decoder and the connection.
  `pagehide` does the same.

## 9. States the overlay must draw

`loading` (poster, no spinner < 300 ms) · `playing` · `paused` · `ended-segment` (frame held, "▶ again · ↓ next stage")
· `not rendered yet` (ep17: "take 09 is not rendered · panel ✓", video tab disabled) · `error` (`video.error.code`,
4 = decode/format → "can't play here · open original"; 2 = network → retry) · `stale` (a take's mtime is newer
than the master, from `edit.stale_takes`/`provenance`: "the master predates this take").

## Sources

- Chrome autoplay policy (MEI, user activation): https://developer.chrome.com/blog/autoplay
- MDN autoplay guide: https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Autoplay
- HTML user-activation (activation-triggering events): https://html.spec.whatwg.org/multipage/interaction.html#user-activation-processing-model
- WebKit video policies for iOS (`playsinline`, muted autoplay): https://webkit.org/blog/6784/new-video-policies-for-ios/
- W3C Media Fragments URI 1.0, temporal `#t=`: https://www.w3.org/TR/media-frags/
- `requestVideoFrameCallback`: https://developer.mozilla.org/en-US/docs/Web/API/HTMLVideoElement/requestVideoFrameCallback and https://web.dev/articles/requestvideoframecallback-rvfc
- `fastSeek()`: https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/fastSeek
- `timeupdate` firing rate (15–250 ms): https://html.spec.whatwg.org/multipage/media.html#event-media-timeupdate
- YouTube keyboard shortcuts (K J L, `,` `.`, `<` `>`, M): https://support.google.com/youtube/answer/7631406
- `<dialog>` / `showModal()` (focus trap, Esc, inert): https://developer.mozilla.org/en-US/docs/Web/HTML/Element/dialog

## Top 8 recommendations

1. **Use custom controls and no native `controls`.** The bar is play · frame timecode · scrubber · speed · loop ·
   sound · **Take | In master**. The keys are Space/K, L (2× on repeat), J (−1 s), `,` `.` frame step, `<` `>` speed,
   O loop, M sound, T source, with ←→ for items and ↑↓ for stages.
2. **Make frame step frame-true:** seek to `(f+0.5)/24` and read the frame shown from rVFC `mediaTime`. Takes are a
   single GOP and the master's keyframes sit on the cuts, so stepping is cheap everywhere.
3. **Call `play()` synchronously in the opening click/keydown, with sound on.** On `NotAllowedError`, mute and show
   "press M". Hover previews stay muted. Under reduced motion there is no autoplay. Narration takes show
   "silent take, voice is in the master" instead of a dead mute button.
4. **Play the master segment as `master_r2v.mp4#t=start/24,(start+n)/24`** from `qc_r2v.json edit.segments`,
   **and enforce the end with rVFC** (`end - 1/48`), because `#t` end does not survive a seek and `timeupdate` overruns
   into the next shot. Label the file "iter7 · faf11c8f".
5. **Use one fixed square stage** (`aspect-ratio` from the item's known size). `<img>` and `<video>` are siblings that
   toggle `hidden`, both carry `width`/`height` attributes, and the controls bar always takes 36 px, so nothing jumps.
6. **The poster is the clicked thumbnail** (the 320 WebP of `content/T{i}_1/_2.png`, already cached), and it fades out on
   `loadeddata`. No frame is ever extracted from an mp4 in the web process.
7. **Prefetch the neighbour's poster only.** The current item gets `preload=auto`. Do not create a second
   `<video preload=metadata>`. Board fix later: honour `If-None-Match`/`If-Range`, and use `max-age=300` on mp4,
   with `master_r2v.mp4` never marked immutable.
8. **Pause the screening player on open, and do not resume on close.** Restore its position and show "paused at
   m:ss · Space resumes". Enforce "one plays" with a capture-phase `play` listener over all `<video>`, and release the
   overlay's decoder on close (`removeAttribute('src'); load()`).

## 2 disagreements I expect

1. **"Exactly one `<video>` on the page" (unit.js invariant) vs. an overlay-owned second element.** I recommend
   *two* elements: the screening player's and the overlay's, with "one *playing*" enforced by the capture-phase
   listener. Moving the one element into the dialog throws away the 247 MB master's buffer, position and `src` on
   every open, and it keeps the fragile `parkVideo`/`dataset.src` bookkeeping. Whoever wrote the invariant will say
   two elements risk two decoders. The answer is that a paused element holds no playing decoder, and the brief's rule
   is "one playing", not "one element".
2. **Resume on close.** Others will want the screening room to pick up where it left off when Esc closes the overlay,
   the way YouTube's miniplayer does. I say restore the position but stay paused, because sound returning by itself
   after a review detour is the larger surprise. The only exception is a fault-list jump where nothing was played in
   the overlay.
