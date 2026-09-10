# Episode 03 — Dialogue as voice-over over cutaways (no lip-sync)

Researched 2026-09-09/10. Scope: 90–120 s, 9:16, ~10–15 shots, designed Qwen3-TTS
voices (`studio/voice.py`, `studio/voice_qc.py`), lines laid by
`studio/trailer_assemble.py:mix_with_lines` under the rules in
`.claude/skills/trailer/subskills/08-assemble/SKILL.md`. Nothing here replaces
that stage; it adds the PICTURE rules a line needs and the checks the episode
adds on top of the trailer's.

Legend: **MEASURED** = run on this machine. **SOURCED** = a cited page says it.
**REASONED** = follows from sourced facts + arithmetic; a default to beat.

## 0. The brick

A spoken line with no lip-sync is believable exactly when **the frame gives
the eye nothing to check the voice against.** Every rule below is that
sentence applied to one shot type. The classical evidence is that film has
always hidden imperfect sync this way (ADR over the listener; "Filming for Easy
Dub" — behind, silhouette, mouth obscured; anime cuts off-mouth to skip
re-timing flaps), and the AI-creator evidence is that the failures are the
same failures: a frontal still face while a voice talks.

Sources: TV Tropes *Filming for Easy Dub*
(https://tvtropes.org/pmwiki/pmwiki.php/Main/FilmingForEasyDub);
ScreenWeaver, *AI Voices Are Still the Tell*
(https://www.screenweaver.ai/blog/ai-voices-lip-sync-film) — "Put it over the
listener's reaction. Films have hidden imperfect sync this way forever, and it
also buys you freedom to use a better vocal take"; OutlierKit micro-drama
teardown (https://outlierkit.com/resources/ai-tools-vertical-micro-drama-2026/)
— "render with the mouth closed or unclear. Then add voice later";
Bonthous, *The Two-Character Problem* (Medium, May 2026,
https://medium.com/@info_13818/the-two-character-problem-why-dialogue-driven-ai-shorts-almost-always-fail-265acda5a1cd)
— "Build dialogue scenes reaction-first … Shoot partial frames over full
faces. A profile. A shoulder and ear. A hand in motion. The less full-face you
show, the less surface area the viewer has to detect drift" (read via search
excerpt only — see §5).

## 1. RULES a skill can enforce

Vocabulary is the repo's: sizes from `studio/shot_grammar.py:LADDER`
(`insert, extreme_close, close, medium_close, medium, full, wide, extreme_wide`),
angles from `ANGLE` (`eye, low, high, profile, overhead`), speaker modes from
`speaker_mode_for` (`listening, ots, two_shot, look_up`), line windows from
`lines.level.json` (`at`, `seconds`). "Under a line" = any frame inside
`[at − 0.15, at + seconds + 0.5]` (the duck predelay and the reaction hold).

### 1.1 What may carry a line (per spoken line, the CARRIER shot)

| # | carrier | allowed when | evidence |
|---|---|---|---|
| A1 | **Listener's face**, `medium_close`/`close`, mouth closed, `speaker_mode=listening` | default carrier; listener is NOT the speaker | Murch: "while that person is still talking, you turn to look at the listener" (https://www.premiumbeat.com/blog/when-and-where-to-make-the-cut-inspired-by-walter-murchs-in-the-blink-of-an-eye/); Bonthous "reaction shots require less lip-sync precision and carry as much emotional information"; Kuleshov effect (https://en.wikipedia.org/wiki/Kuleshov_effect) |
| A2 | **Over-the-shoulder / back of the speaker** (`ots`), listener's face or the room beyond | speaker's mouth out of frame | TV Tropes *Filming for Easy Dub* ("seen from behind") |
| A3 | **Speaker in strict `profile`** at `medium` or wider | nose breaks vertical centre (`ANGLE["profile"]`), no frontal mouth | Bonthous: "a three-quarter profile with the eyes visible … forgives inconsistency"; *Easy Dub* |
| A4 | **Speaker in silhouette / backlit / face in shadow** any size | mouth region < ~8% luma, i.e. unreadable | *Easy Dub* ("in silhouette") |
| A5 | **`full`, `wide`, `extreme_wide`** including `two_shot` | every head ≤ 1/5 of frame height (`FRAMING["medium"]` boundary) | REASONED from A3/A4: a mouth under ~15 px tall at 1080 wide cannot be read for sync |
| A6 | **`insert` / hands / object** (`kind=accent`) | static object or slow motivated move; hands NOT gesturing to the speech rhythm | OutlierKit ("framing shots above the hands or cutting away at the moment hands enter"); Bonthous ("A hand in motion") |
| A7 | **Slow push-in on the listener or on an object** | push, not drift (`motivated_move`) | REASONED: a move gives the eye a task other than the mouth |
| A8 | **Black / card** (`line.card`) | only the line the plan marks as a card | repo 08: cards are never laid — a card line has no file |

### 1.2 What is FORBIDDEN under a line

| # | forbidden | why | evidence |
|---|---|---|---|
| F1 | **Speaker's frontal face at `medium_close` or tighter, mouth still** — the ventriloquist frame | the one failure every source names | ScreenWeaver: "when a character opens their mouth and the voice is off by even a little, the film dies in about four seconds"; *Easy Dub* |
| F2 | **Speaker's face with any generated mouth motion** at ≤ `medium` | unsynced motion reads worse than a still mouth | ScreenWeaver ("late synchronization reads dubbed immediately") |
| F3 | **`speaker_mode=look_up` or `two_shot` at `medium` or tighter** | `look_up` puts the speaker's face to lens on their own line (`shot_grammar.py:264` `LOOK_UP`, `:381`); a two-shot at MCU shows two mouths | derived from F1 — **this is the repo's CURRENT default when the speaker is in cast** (`speaker_mode_for`, `shot_grammar.py:370-382`); the episode must remap it to A2/A3/A5 |
| F4 | **Listener's face with mouth motion** | reads as the wrong speaker | OutlierKit "mouth closed or unclear" |
| F5 | **Gesturing hands in rhythm with the line** | AI hands fail and gesture-sync is checkable | OutlierKit |
| F6 | **A line straddling 3+ cuts** | that is montage, not dialogue; the J/L grammar needs one carrier + one overlap | REASONED from §1.3 |
| F7 | **A `medium_close` frontal face of ANYONE at the cut that lands on the line's first word** | the eye checks the mouth hardest on onset | REASONED from F1 + Murch |

### 1.3 Cut timing (every number in seconds; 24 fps → 1 frame = 0.0417)

| # | rule | value | evidence |
|---|---|---|---|
| T1 | **Every line is a J-cut or an L-cut, never a hard cut on onset** | line onset ≠ any cut ± 0.25 s (6 frames) | SpotlightFX/FilmDaft: dialogue "can feel robotic and unnatural if dialogue starts and stops precisely with each cut" (https://spotlightfx.com/blog/what-are-j-cuts-and-l-cuts-professional-dialogue-editing-explained, https://filmdaft.com/the-l-cut-and-j-cut-how-film-editors-use-audio-to-control-time/) |
| T2 | **J-cut lead**: line starts before the cut to its carrier | 0.3–1.0 s | FilmDaft: dialogue overlap "usually between half a second and two seconds"; lower bound tightened because our shots are 1.5–4 s |
| T3 | **L-cut tail**: line runs past the cut to the next shot | 0.5–2.0 s | FilmDaft (same); WeVideo (https://www.wevideo.com/blog/j-cuts-l-cuts) |
| T4 | **Alternate J and L** across consecutive lines; no more than two of the same kind in a row | — | SpotlightFX: alternating "never settles into a predictable pattern" |
| T5 | **Cut to the listener before the line ends** (the reaction beat) | cut 0.3–0.8 s before last word end | Murch: "cutting to a reaction shot before a dialogue is complete causes a viewer to consider the worth of what is being said"; cut "just slightly before" the blink |
| T6 | **Hold after the last word** before any cut, unless the next line interrupts | ≥ 0.5 s (12 frames) | Murch (the idea completes, then the blink); REASONED value |
| T7 | **Duck opens before the line** | 0.15 s predelay, already `DUCK_PREDELAY` | `trailer_assemble.py:341` |
| T8 | **Line length** | ≤ 12 words (`voice.MAX_LINE_TOKENS` note), ≤ 5 s spoken; one intention per line | ScreenWeaver "under fifteen words"; Bonthous "3–5 seconds per line" |
| T9 | **Gap between two lines of different speakers** | 0.2–0.6 s (a breath), never < 0.1 s unless scripted as interruption | ScreenWeaver ("breaths before scene-opening lines"); REASONED value |
| T10 | **Off-screen speaker side** | listener's eyeline points to the speaker's `axis_side` (`screenplay_spec.Shot.axis_side`) | standard 180° practice (StudioBinder J-cut page https://www.studiobinder.com/blog/what-is-a-j-cut-in-film/); REASONED application |
| T11 | **A hit or designed cue never lands inside a line window** | already `bed_under_line_lu` > 18 dB = placement fault | repo 08 (`DUCK_DEPTH_MAX`) |

### 1.4 The skill's per-line checklist (what to assert in `plan.json`)

For each `lines[i]`: carrier shot resolved by `at`; `carrier.size`,
`carrier.angle`, `carrier.speaker_mode`, `carrier.binds_face`, `carrier.cast`;
assert (A1–A8) ∧ ¬(F1–F7) ∧ (T1–T6). If the speaker is in `carrier.cast`
then `angle == profile` or `size ∈ {full, wide, extreme_wide}` or `ots`.
Prompt text for a listener carrier must contain "mouth closed" / "lips
pressed" (F4); for a speaker profile carrier, "seen in strict profile"
(`ANGLE["profile"]`).

## 2. AUDIO SPEC (9:16 social delivery)

### 2.1 Levels

| item | value | status | source |
|---|---|---|---|
| Master integrated | **−14.0 LUFS** (floor −15.5..−12.5 stays) | SOURCED | YouTube normalises to −14 and only turns loud content DOWN ("Stats for nerds" → Volume/Normalized) https://www.criticallisteninglab.com/en/learn/loudness/youtube ; TikTok/Reels: community-measured −14, hot masters turned down more than the gap https://trackgleam.com/learn/master-for-tiktok-reels-shorts , https://mrvocal.com/posts/loudness-for-shorts . No TikTok/Meta official doc found (§5) |
| Master true peak | **≤ −1.0 dBTP measured on the delivered AAC**; keep `TARGET_TP` −2.0 pre-encode | SOURCED −1.0 (all guides above); −2.0 pre-encode is the repo's AAC headroom (`trailer_assemble.py:38`) |
| Master loudness range | **LRA ≤ 8 LU** | REASONED: phone speaker + platform gain makes a quiet line vanish; the trailer's cue LRA is wider than loudnorm's 7 by design, an episode is not a trailer |
| Each line, levelled file | **−16 LUFS integrated** (`LINE_TARGET_LUFS`), re-MEASURED after the limiter (08: limiter revises it by up to 1.8 dB) | repo 08 §"The limiter revises the target" |
| Line on the MASTER | short-term ≥ **−20 LUFS** inside every window; line over ducked bed **≥ 8 LU** (`LINE_OVER_BED`) | repo; the spread 7.3–16.1 LU on run 18 is the number to flatten |
| Bed under a line | momentary peak **≤ −24 LUFS** (`BED_UNDER_LINE`); depth 10–18 dB full-band; attack 20 ms, predelay 150 ms, release 800 ms | repo. Practitioner range is shallower — 6–10 dB, 30–60 ms attack, 300–700 ms release (iZotope https://www.izotope.com/en/learn/mixing-audio-for-video-part-4-mixing-techniques.html , OpenClip https://openclip.app/learn/audio-ducking) — the deeper duck is justified by a TTS voice with no human dynamics and by phone playback |
| Bed between lines | short-term **−18..−20 LUFS** | REASONED so that speech occupancy 0.30–0.50 sums to −14 without the master limiter working |
| Ambience/room tone | **continuous, −40..−35 LUFS momentary, never digital silence**; under every trough | ScreenWeaver ("continuous ambient tone under entire scenes, including gaps"); repo 08 measured −89 LUFS holes. Reconcile `ROOM_TONE_LUFS` −45 with `AUDIBLE_M` −40 (`qc.py:149`) — today the floor sits under the gate's own audibility line |
| Designed hits vs cut | if wrong, wrong LATE: ≤ 1 frame early / ≤ 3 late | ITU-R BT.1359 via repo 08 |

### 2.2 Phone-speaker intelligibility

- Phone speakers roll off below ~200–500 Hz (12 dB/oct under resonance) and
  boost 2–4 kHz (https://blog.audiokinetic.com/loudness-and-frequency-response-on-popular-smart-phones/ ,
  https://auxfeed.com/learn/why-mix-sounds-bad-on-phone-speakers/). Consequence: nothing
  below ~150 Hz in the VOICE matters (`POST_CHAIN` HPF 90 is fine); everything
  that makes a line intelligible is 1.5–4 kHz.
- **Subtractive EQ on the bed, not more duck**: −2..−3 dB, 1.5–4 kHz, only
  inside line windows (iZotope: "subtractive EQ on the score around 1.5–4 kHz
  will often buy you more clarity than 3 dB on the dialogue stem"). Implement
  as `equalizer=f=2500:width_type=o:width=1.4:g=-3` gated by the same
  `bed_expr` envelope, never a crossover (08: band-split ducks failed).
- **Mono check**: fold the master to mono (`pan=mono|c0=0.5*c0+0.5*c1`) and
  re-run the loudness + WER gates in §4; a phone is one driver. Keep the bed's
  <200 Hz mono.
- **Phone emulation for QC** (REASONED): `highpass=f=300,lowpass=f=6000` on the
  mono fold, then WER on each line window must still pass 0.20.

### 2.3 Burned-in captions (9:16, 1080×1920)

Safe box = the union of platform UI margins:

| platform | top | bottom | left | right | source |
|---|---|---|---|---|---|
| TikTok (April-2025 template, called official by three third parties) | 130 | 484 | 44 | 140 | https://www.recharm.com/blog/tiktok-video-ad-specs , https://creamate.ai/en/blog/tiktok-safe-zone-guide |
| Instagram Reels | ~108 | ~320 | ~60 | ~60 | Kreatli safe-zone hub, Jan 2026 https://kreatli.com/guides/safe-zone-guide ; ignitesocialmedia |
| YouTube Shorts | keep in central 4:5 (1080×1440); bottom 10–15% clear; right ~15–20% | | | | Kreatli; Blitzcut https://blitzcutai.com/blog/safe-zones-youtube-shorts-reels-tiktok |
| **Union → caption box** | **y 130..1436, x 60..940** | | | | arithmetic |

Style, sourced from the caption-tool guides (OpusClip
https://www.opus.pro/blog/tiktok-caption-subtitle-best-practices , Subclip
https://www.subclip.app/blogs/animated-captions-2026-best-practices-reels-shorts-x-exporting-srt ,
Blitzcut https://blitzcutai.com/blog/best-caption-style-tiktok):

- **1–3 words on screen at a time, ≤ 2 lines, ≤ 24 characters/line**; the
  current word highlighted (karaoke `\k` in ASS, which `stable_whisper`
  already emits and `ass=` already burns — `trailer_assemble.py:807`).
- **Position**: horizontally centred; vertically in the lower-middle third,
  i.e. baseline at **y ≈ 1250–1400** (never below 1436, never in the top
  130). "Lower-center … 20% offset to avoid the UI overlay" (Subclip).
- **Face**: bold sans, white fill, black outline 3–4 px or a box, NEVER pure
  white on a bright frame without the outline. Cap height ≥ 3% of frame
  height (≥ 58 px) — REASONED minimum, not measured.
- **Timing**: word onset from forced alignment (§4.2); show a phrase from
  first-word onset −80 ms to last-word end +150 ms; minimum on-screen 300 ms;
  never carry a caption across a cut by more than 2 frames (REASONED).
- **Speaker identity**: an off-screen speaker's line gets the character's
  name once, small, in the caption's first phrase (`— HOLMES`), since the
  face is not on screen. REASONED; no source measures it.
- Reuse `card_fits`/`ink_bounds` (`trailer_assemble.py:832-859`) to assert
  every rendered caption frame's ink lies inside the union box.

## 3. LIP-SYNC FUTURE LANE (local, 24 GB 4090, ComfyUI, as of 2026-09)

Installed here now (MEASURED): `ComfyUI-WanVideoWrapper`, `ComfyUI-LTXVideo`,
`ComfyUI-GGUF-FantasyTalking.disabled`; no LatentSync/MuseTalk/Sonic node.
`python_embeded` has `whisper`, `stable_whisper`, `mediapipe`, `torchaudio`.

| model | kind | VRAM | time per 5 s (4090) | quality verdict | ComfyUI |
|---|---|---|---|---|---|
| **LatentSync 1.6** (Jun 2025) | v2v mouth-region inpaint, 512² | **18 GB** (README); wrapper "optimized for 20 GB" | not verified; 20–50 steps, 1.5 reports were ~realtime-ish on 24 GB (UNVERIFIED) | best local drop-in for an EXISTING clip; needs a frontal, unoccluded mouth — i.e. exactly the F1 frame this doc forbids, so it is the lane that would UNLOCK F1 | `ShmuelRonen/ComfyUI-LatentSyncWrapper` (1.5+1.6) https://github.com/ShmuelRonen/ComfyUI-LatentSyncWrapper ; https://github.com/bytedance/LatentSync |
| **MuseTalk 1.5** (Mar 2025) | v2v, 256² face | works on 4 GB (8 s in ~5 min on a 3050 Ti); 30 fps+ on V100 | ~seconds on a 4090 (REASONED from V100 realtime claim) | jitter, loses moustache/lip colour (README's own list); below 1.6 | third-party `chaojie/ComfyUI-MuseTalk`, authors do not maintain https://github.com/TMElyralab/MuseTalk |
| **Wan2.2-S2V 14B** (Aug 2025) | image+audio → whole shot | fp8_scaled fits 24 GB | not verified; 77 frames/chunk at 16 fps (~4.8 s), 20 steps or 4 with Lightning LoRA; Wan2.2 14B i2v 720p 5 s ≈ 4 m 20 s on a 4090 https://www.thundercompute.com/blog/wan-2-2-comfyui-ai-video-model so expect 1–5 min | generates the shot, so identity is the reference image only — bypasses our H3 reference-bound clips; FID 15.66 / CSIM 0.677 (vendor) | native nodes https://comfyui-wiki.com/en/tutorial/advanced/video/wan2.2/wan2-2-s2v |
| **InfiniteTalk** (Aug 2025, Wan2.1) | v2v sparse-frame: re-drives an EXISTING clip, keeps framing | fp8 + `num_persistent_param_in_dit 0`; 28 GB used for 40 s 480×832 on an L40 (kijai issue #1229) | "around 70 seconds on an RTX 4090" per NextDiffusion (clip length unstated; page 403'd — UNVERIFIED) | strongest v2v candidate: our clip, our voice, mouth + head re-driven; long-context stable | `kijai/ComfyUI-WanVideoWrapper` (installed) https://github.com/MeiGen-AI/InfiniteTalk |
| **LongCat-Video-Avatar 1.5** (May 2026, InfiniteTalk's successor) | image/video + audio | fp8 12 GB; full 24 GB+ | 8 steps (down from 20); no 4090 s/5 s found | Whisper-large audio encoder, "strict identity consistency" (vendor); the one to test first | WanVideoWrapper + GGUF (`vantagewithai/LongCat-Video-Avatar-1.5-GGUF-ComfyUI`) https://huggingface.co/meituan-longcat/LongCat-Video-Avatar-1.5 |
| **OmniAvatar** (Wan 1.3B / 14B) | image+audio → shot | 8 GB min; 21 GB with 7B persistent | 1.3B: 5 s 480p ≈ **4 min** (README) | body+lip; slower than the above for less | WanVideoWrapper request #836 — not confirmed shipped https://github.com/Omni-Avatar/OmniAvatar |
| **Sonic** (SVD-based) | portrait talking-head | ≤ 8 GB | ~10 s ≈ 8 min on a 4090 (InstaSD) | SVD look, portrait only — no | `ComfyUI_Sonic` https://app.instasd.com/workflows/comfyui-sonic-lip-sync |
| **LTX-2.3 / 2.5** (2026) | joint audio+video, image+audio→video | runs on 4090 (NVIDIA guide) | "~90 s a clip" on a 4090 (LTX blog, length/res unstated) | native lip-sync from OUR audio requires the frozen-audio-latent workaround (HF discussion #44); Lightricks: dubbing pipeline for 2.5 "very soon" | `ComfyUI-LTXVideo` (installed) https://huggingface.co/Lightricks/LTX-2.5/discussions/44 , https://comfy.org/workflows/video_ltx2_3_ia2v-adca306765ce/ |
| FantasyTalking | image+audio | — | — | node present but disabled here; not evaluated | `ComfyUI-GGUF-FantasyTalking.disabled` |

**What adding the lane costs**: one more render pass per speaking shot
(1–5 min GPU per 5 s on today's reports), a face-identity gate (CSIM or the
existing `image_qwen3vl_caption` identity check on the re-driven clip), and
the sync gate (§4.5). It buys: F1 becomes legal for the shots the lane
touches. Order of trial: LongCat-Video-Avatar 1.5 v2v (node pack already
installed) → InfiniteTalk → LatentSync 1.6 for mouth-only. Nothing in this
table was run here.

## 4. QC CHECKS and the local tools

Every check reads the **delivered master** unless it says "levelled file",
because 08's own audit shows the sidecar grading itself.

### 4.1 Said the line (exists; extend)

`studio/voice_qc.py:check` — WER ≤ 0.20 on the levelled line. **Add** the same
check on the master's window: extract `[at−0.2, at+seconds+0.3]` from the
master (`ffmpeg -ss -t -ac 1 -ar 24000`) and transcribe; a line "lost in the
sum" (08 names it) then fails here. Tool: `openai-whisper large-v3-turbo`,
already at `ComfyUI/models/whisper` (MEASURED present).

### 4.2 Word timestamps (captions + timing)

We KNOW the text, so use **forced alignment**, not ASR-derived timing:

| tool | status here | verdict |
|---|---|---|
| `torchaudio.functional.forced_align` + `torchaudio.pipelines.MMS_FA` | **MEASURED present in the pinned torchaudio 2.11.0 (+cpu)** — deprecation was reversed (pytorch/audio#3902) | first choice: zero new deps, CTC alignment of known text; CPU is fine for ≤ 5 s lines |
| whisperX (faster-whisper + wav2vec2 alignment) | not installed; needs CUDA 12.8 | second choice; "<100 ms" word timing claims; cannot time non-dictionary tokens ("2014.", "£13.60") — spell numerals out in lines https://github.com/m-bain/whisperX |
| stable-ts (`stable_whisper`) | installed in ComfyUI python | **archived 2026-05-30, read-only** — usable for ASS karaoke output today, do not build on it https://github.com/jianfch/stable-ts |
| CrisperWhisper | not installed | best verbatim/pause timing in its paper: F1 84.7 vs WhisperX 76.7 (clean synthetic, 200 ms collar); 79.5 vs 59.0 noisy https://arxiv.org/abs/2408.16589 — only if 4.2's first choice fails on our voices |
| faster-whisper `word_timestamps=True` | not installed | DTW on cross-attention; ±200 ms class (stable-ts README) — captions only |

Gate: every word aligned; word start/end monotone; alignment score per word
above the aligner's own floor; total aligned span within ±0.1 s of
`clip_seconds`.

### 4.3 Placement on the master (new)

Cross-correlate `line-N.level.wav` against the master's mono audio in a ±1 s
search around sheet `at`; the peak lag must be within **±1 frame (41.7 ms)** of
`at`, else FAIL. numpy/scipy only. This closes the "sheet is an intention, not
a measurement" gap in 08 without un-mixing anything.

### 4.4 Picture rules on the carrier (new; §1)

- From `plan.json`: assert A/F/T rules per line (§1.4). Pure metadata, no ffmpeg.
- **Frontal-face-under-line detector**: sample the carrier's mid-window frame;
  `mediapipe` FaceMesh (installed) → face box height / frame height > 0.33 and
  yaw < 30° while the line plays → FAIL (F1). If the speaker's own face is in
  the carrier, also compute lip-aperture variance over the window; > baseline
  → FAIL (F2). REASONED thresholds; unbuilt.
- **J/L check**: first-word onset (4.2) vs `qc.scene_cuts()` at 0.1: no cut
  within ±0.25 s of onset (T1); a cut exists 0.3–1.0 s after onset (J) or
  0.5–2.0 s before last-word end (L) (T2/T3); at least one cut before
  last-word end −0.3 s… −0.8 s (T5) on lines ≥ 2 s.

### 4.5 Speech is actually there (new)

Silero VAD (pip `silero-vad`, torch-only; not installed) or whisper's
`no_speech_prob` over the master: VAD speech must cover ≥ 90% of every sheet
window and ≤ 5% of the runtime outside windows. Compute `speech_occupancy`
from THIS, not from the sheet (08: the sheet restates the mix's intention).

### 4.6 Loudness (exists; two additions)

Existing gates stay. Add: (a) re-measure the delivered .mp4's true peak
≤ −1.0 dBTP and integrated −14 ± 1; (b) mono-fold + phone-emulation WER (§2.2)
on every window.

### 4.7 Captions (new)

Render the caption ASS to frames at each phrase's mid-time; `ink_bounds` must
lie inside x 60..940, y 130..1436; ≤ 2 lines; ≤ 24 chars/line; every word's
highlight interval equals its 4.2 alignment ± 50 ms.

## 5. What could NOT be verified

- **Reddit r/aivideo**: fetch blocked (`old.reddit.com` refused; search index
  returned no threads). No creator thread was read directly; the AI-creator
  rules rest on ScreenWeaver, OutlierKit and Bonthous (Medium, read only via
  search excerpt — the page 403'd).
- **TikTok / Instagram normalisation**: no first-party document; −14 LUFS is
  the consensus of measurement-based guides. YouTube's is observable in Stats
  for nerds. Reels/Shorts safe-zone pixels are third-party; TikTok's
  130/484/44/140 is described as official by third parties only.
- **Lip-sync timings**: LatentSync 1.6 s/5 s on a 4090, Wan-S2V s/5 s,
  LongCat 1.5 s/5 s — none found; InfiniteTalk "70 s" is a snippet of a page
  that 403'd. OmniAvatar's ComfyUI availability unconfirmed.
- **Caption font size and phrase timing constants** are convention, not
  measurement; retention claims in the caption guides are unsupported.
- **Radio-drama-to-film** conventions: no source read; omitted rather than
  invented. Anime off-mouth practice rests on TV Tropes only.
- **CrisperWhisper** numbers are on synthetic speech; no result on TTS voices.
- **torchaudio here is the +cpu build** — alignment will run on CPU; fine for
  5 s lines, not measured.
- `stable_whisper` presence in ComfyUI python was import-probed, not run.

## Repo paths touched by this doc

- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\studio\trailer_assemble.py` (mix, duck, ASS title, `ink_bounds`)
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\studio\shot_grammar.py` (`LADDER`, `ANGLE`, `speaker_mode_for`, `LOOK_UP` — F3)
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\studio\voice.py`, `studio\voice_qc.py`
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\.claude\skills\trailer\subskills\08-assemble\SKILL.md`
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\.claude\skills\trailer\subskills\09-voice\SKILL.md`
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\.claude\skills\cast-voices\SKILL.md`
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\scripts\trailer\qc.py` (`scene_cuts`, `music_only_runs`)
- ComfyUI: `D:\Projects\KingdomOfViSuReNa\alpha\ComfyUI_windows_portable\ComfyUI\custom_nodes\ComfyUI-WanVideoWrapper`, `ComfyUI-LTXVideo`, `models\whisper\large-v3-turbo.pt`
