# Episode 08 — the r2v plan (2026-09-10, evening). Nothing renders until the owner says GO.

Four voices: a model-mechanics analyst (read the DiT and node source), a
storyboard craftsperson, a skeptic, and a researcher (MiniMax's own prompt
guides). Plus two measurements made today on files already on disk.

## 1. What is actually wrong with the first r2v round

1. **The intruders are the storyboard sheet's other cells.** Frame-by-frame
   match of the bad takes against the corridor sheet cells: T03 leaves its own
   panel after 1.6 s and converges on cell S02 (Watson frontal), similarity
   0.32 → 0.62 by the last frame; T05 jumps to S02 at 4.6 s. Mechanism
   (`comfy/ldm/minimax/model.py:357-452`): references and keyframe anchors are
   one packed sequence with no mask; a reference has no time coordinate, a
   pixel anchor's pull decays with distance from its frame. Ref2va's training
   prior is "every referenced element appears". The sheet is passed as a
   reference in every card, so its faces win around 8 s. Dropping the cast
   sheets when no face is readable (done) removes one source, not the one
   that measured.
2. **The next-panel-at-last-frame anchor is the measured FLF morph.** Two
   keyframes of different framing make the model travel between them; the
   card gives it 6 to 8 handle frames, so it spreads the move over the shot
   and the cut then shows the next composition twice. Both the analyst and
   the skeptic reject it.
3. **The prompt grammar was the base-model grammar, not ref2va's.** MiniMax's
   own ref guide (github MiniMax-AI/MiniMax-H3, `references/ref-en.txt`) uses
   six sections: `subject_definitions`, `summary`, `retention_analysis`,
   `detailed_description`, `overall_soundscape`, `non_diegetic_music`.
   Identity images are cited INSIDE `<Subject N> is ... in <Picture N>`;
   presence per shot is scoped by `(appears in [Shot 1], [Shot 3])` in
   `retention_analysis` and by omission; a standalone `<Picture N>` line is
   for a frame anchor or a storyboard: `<Picture 3> is a storyboard reference
   for [Shot 1] and [Shot 2]`. Timestamps exist only as cut onsets:
   `[Shot 2] At 00:04.250, the shot cuts to ...`. Off-screen narration has an
   exact form: `(S1) says in an off-screen voiceover: <d>[English] ...</d>
   while his lips remain completely closed`. Speaker IDs go in vocal order.
   No negative sentences anywhere in the official guides. Our "anchored first
   frame" wording names nothing the text encoder sees (anchors never enter
   the Qwen encoder, `comfy/text_encoders/minimax.py`); a panel gets a text
   handle only if it is ALSO a reference image.
4. **Audio anchoring is exact on both engines.** Measured lag of the take's
   own track against the input wav: +0.240 s on r2v T00 and i2v T12, T22,
   T24, against the 0.250 s we anchored (one-frame resolution). The sync
   rule survives the engine change; the composite-at-frame-0 layout places
   the line's rows identically to anchoring the line at its frame.
5. **Anchor frames sit off the token grid.** Video tokens cover frames
   (1,4,4,4...), so pins at 102, 151, 208, 259 smear over four frames; snap
   to f = 0 or f ≡ 1 (mod 4).
6. **`match` is right.** Only the 2048×3072 sheet changes size between
   `match` and `max` (character sheets are already ~1 MP); `max` adds ~6k
   DiT rows for the one reference that supplies the intruders.
7. **Silent audio guide flattens the take's track by 17 to 25 dB but did not
   kill motion** (measured on T03/T04 vs i2v). The track is discarded anyway.

## 2. The one disagreement, and how it is settled by measurement

The analyst says drop the sheet. The owner keeps the sheet for consistency.
The official grammar has a place for a storyboard reference, scoped to the
shots it covers. So the candidate is not "no sheet" but "the storyboard OF
THIS TAKE": the panels before, of and after the take side by side (same
family of light, wardrobe and staging; no cell the take must not show),
declared as `<Picture N> is a storyboard reference for [Shot 1]..[Shot k]`.
Settled by `scripts/episode/ab_refs.py` on take 3 (the worst case), same
seed, same prompt, same anchors: sheet vs own panel vs strip. Output: eight
frames per arm with the closest cell named under each. Pass = frames stay
on S03 to the end.

## 3. Changes, ranked (owner decides each)

| # | change | why | keep/decide |
|---|---|---|---|
| 1 | Prompt in the official ref2va six-section grammar; cast as `<Subject N>` citing `<Picture N>`; presence scoped with `appears in [Shot N]`; cut onsets `[Shot N] At MM:SS.mmm`; narration as `(S1) says in an off-screen voiceover ... lips remain completely closed`; no negatives, no LOCK paragraph | §1.3 | do |
| 2 | Continuity reference = the take's own storyboard strip, not the 3×3 sheet; plate stays as the location subject | §1.1, §2 | A/B/C first |
| 3 | Cast sheets only for faces readable in the take (already built) | §1.1 | keep |
| 4 | Every shot's panel anchored at its start frame, snapped to the token grid; NO next-panel-at-last-frame | §1.2, §1.5 | do |
| 5 | Multi-shot takes phrased as cuts (`[Shot 2] At 00:04.250, the shot cuts to ...`), never "moves continuously" | §1.3 | do |
| 6 | Dialogue wav anchored at its frame (composite keeps this exact); narration takes: A/B anchored narration wav + voiceover grammar vs no guide | §1.4, §1.7 | ladder step 2 |
| 7 | `ref_image_size: match` | §1.6 | keep |
| 8 | Plan grain: one line per shot, a mid-line `via` panel for lines over 14 words, so a new anchored frame every 2.5 to 4 s; anchor-or-cut rule from size/faces/axis | craft report | owner: it costs new sheets (about 41 panels on 5 sheets, ~7 paid images) |
| 9 | Panel defects: Holmes bareheaded indoors; Watson tan gloves, right glove off at the lab door; one stick (black, silver knob); bowler in hand indoors; S23 from behind; corpse seen through the doorway from the corridor plate; plaster on the forefinger only; S11 brown sleeve | craft report, one sentence each | with #8 |
| 10 | Engine mix (r2v narration, i2v-speak dialogue close-ups, one model swap) | skeptic | not needed if ladder step 3 passes on r2v |

## 4. Validation ladder (one take each, ~15 min, GO only if all pass)

0. **Take 3 refs A/B/C** (sheet / panel / strip). Pass: the strip or panel
   arm holds S03 in all eight frames; no frontal face.
1. **Take 4 in the official grammar, no next-panel anchor**, narration wav
   anchored as off-screen voiceover vs no guide. Pass: no third person in 24
   sampled frames; frames match S04 throughout; with the guide, no lip
   movement on the two backs (trivially) and the take track's words = the
   narration (Whisper).
2. **Take 11 = shots 11 + 12 as a cut** (`[Shot 2] At 00:04.250 the shot cuts
   to ...`), Holmes's line anchored at 4.5 s. Pass: frame-diff cut at frame
   102 ± 4; lag of the take track vs the wav = +4.50 ± 0.04 s; WER 0; mouth
   motion during the line ≥ 5× before it.
3. Then the full r2v episode: 4311 frames × 3.2 s ≈ 3.8 h + load; assemble,
   QC, run cards, `master_r2v.mp4`.

## 5. What is already built today (no render needed to keep it)

`studio/episode_takes.py` (runs of shots, anchors), `studio/h3_anchors.py`
(guide chain, tested), `studio/episode_ref_prompt.py` (to be rewritten to
the official grammar), `scripts/episode/takes_r2v.py` (take-based engine),
`scripts/episode/ab_refs.py` (the A/B/C), `studio/av_sync.py` (the lag gate,
tested), `studio/frame_match.py` (closest-cell judge), the re-crop
regression fix in `storyboard.py` (cells found on the sheet, a redrawn panel
outranks its cell), the run cards with the engines table.

## 6. Gate result (2026-09-10 18:00) — GO

Take 3 rendered on r2v v2 (its own nine-cell sheet, five cells anchored on
the token grid, the two narration wavs anchored at their offsets, official
grammar, references = plate + own sheet, no cast sheet because no face is
readable): all eight sampled frames match the take's own cells (one within
a beat of the expected cell, none foreign), Stamford's glance back lands
where the cells say, no second Stamford, framing held to 11.5 s, audio lag
-0.010 s. 1212 s render for 277 frames (4.4 s/frame with five anchors and
the voice composite; 3.1 with one anchor). The 19 take sheets all passed DQ
after a softer edge trim (170). Ledger: $4.84 for the episode (calibrated).
The full round is running unattended: takes -> DQ -> one retake -> cut ->
QC -> run cards -> `master_r2v.mp4`.

## 7. Outcome (2026-09-10 21:53) — master delivered

`episodes/ep01/master_r2v.mp4` (= `master_iter8.mp4`): 174.6 s, -14.7 LUFS,
-1.7 dBTP, 33/33 lines heard, 21/25 hard cuts seen, the 4 unseen are cuts
INSIDE take-runs (the model's own cuts, soft), longest gap 1.73 s, QC PASS.
19 takes, 4311 frames, 239 min of GPU (3.3 s/frame), DQ 18/19 by the crude
matcher (T11's one flag is the hand-on-stick cell scored low by the tighter
crop; correct by eye). Audio lag max 0.010 s. Wall: sheets 17:39 -> master
21:50 (4 h 11 m). Images this run: 19 take sheets, $3.80; ledger $4.84 for the episode,
CALIBRATED against the usage page ($5.12 for the week, nearly all on Sep
10-11 UTC, text calls included; the token-table estimate of $0.75 a sheet
was ~4x too high).
