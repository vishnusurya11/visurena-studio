# Episode 10 — ten-analyst DQ synthesis and the change list (2026-09-16)

Ten read-only analysts each took one dimension of the published episode 10
(https://youtu.be/nftf6bbjQMs, master_iter4, sha8 514491f8) and the four
episodes before it. Their full reports, with the per-take tables and the
scripts that measured them, are in the session scratchpad `dq10/A.md … J.md`.
This page is the deduplicated change list, grouped by the file that owns the
fix, each item with its evidence and its test. Items marked **[ep11]** change
how the next plan is written; the rest are gates, tools or the clock.

## What held (do not touch)
- Identity: the same three faces in all 30 takes; frame 0 of every take IS its
  cell (similarity 0.997–1.000).
- The floor: take-median p5 1.5 / near-black 0.53 / one-hue share 0.41 — ep05's
  numbers, against ep09's 17.8 / 0.09 / 0.67. Light direction obeyed 24/30.
- The edit: 29/33 cuts frame-exact; no jump cuts, flash frames or duplicated
  frames; narration and dialogue level-matched (0.08 LU); tone changes on cuts;
  the title card identical to ep05/ep07. `assemble.py` handles/trim and
  `episode_takes.BUDGET` stay.
- The button: Lucy's line, the world's answer, on her lips, last.

## The faults that reached the viewer, ranked
1. **The push has no brake and the size word is not the size.** 31/34
   motions were pushes; "a hand's/finger's breadth" governed 0 of 16 head
   amounts; every ratio ≥ 1.9 has a subject-at-lens clause. Six shot-ends
   leave the crown out of frame. Face-in-frame separates what scale cannot:
   MTCNN face-height/frame at the last frame — nostrils 2.13–2.20 vs KEEPs
   0.54–0.98 — and `face_end ≈ face_start × ratio` on 7/8 takes.
2. **Sunlit faces go flat.** 0/6 "LEFT half in sun, RIGHT half in shadow"
   splits were drawn or rendered; 14/16 practical-light directions were. The
   plate of the path is the flattest object in its chain. Shot 20 is the one
   frame with no floor in the cut; T16/T28 warm to one orange over their length.
3. **The lead's words went to the narrator.** Six narration lines report a
   present character's speech (0 in ep07/ep09); the lead's decision is narrated
   over a window insert; the protagonist is not in his own turn shot.
4. **The tail.** 11.25 s without a line after the button (ep05 4.4, ep07 4.5);
   the bed dies at 166 s and the `np.tile` loop seam restarts it at 167.8 s in
   the only voiceless stretch. `light` came back 38 % music and was tiled ×3.
5. **John Ferrier's voice.** Design clip self-similarity 0.498 (cast 0.56–0.77);
   Ferrier–Young designs 0.847, the closest pair; 3/5 of his lines score higher
   against Young; l27 cloned from ep08 is a different man from his other two
   lines in the same room.
6. **Time.** 5.0 h; 30.8 min of renders never in the picture across four
   retake waves, five ~300 s cold loads, qc 32 min in a FIFO behind retakes,
   53 min of no-stage gaps.
7. **The storyboard ladder collapsed between MCU and close** (head fraction
   phrase in 0/34 at_rest vs ep07 20/26); three "instant before" panels were
   drawn finished; the four panel redraws ran under the ep08 style line
   (`redraw_panel.py` never adopts house style) and two lost their size class.

## Change list by owner file

### A. Take gate — scale, face, look, tails (`studio/take_zoom.py`, new `studio/take_look.py`, new `studio/take_edit.py`, `studio/take_coherence.py`, `studio/take_verdict.py`)
- A1 face-in-frame in the zoom row: `face_start` from the cell (measured at board time, stored beside the anchors) and `face_end` from the last frame (MTCNN via facenet-pytorch, CPU); `FACE_HARD = 1.5`, `FACE_ADVISORY = 1.0`; when the face model is absent, `face_pred = face_start × ratio`. The reach-word wall stays advisory. Tests: judge({1.93, face 0.69}) hard; judge({2.16, face 0.21}) ok.
- A2 `NO_MOVE = 0.05` advisory (T05 0.99×); judge `camera` when `camera − ratio ≥ 0.3` (a following camera, T06); the wrong-way sentence reports travel in the planned direction.
- A3 read zoom and last-vs-cell per anchor segment, not the head only (T29's second shot turned away unjudged); an exit clause ("drops out of the frame") silences last-vs-cell and caps the zoom read at the last on-board sample (T17 lost 25 points for obeying).
- A4 `take_look` row: HARD when the take-median has no floor (p5 > 15 and near-black < 0.10: T20 43/.01 fails, T31 1.0/.68 clean); scored advisory when black is lost over the length (near-black drop ≥ 0.20 or Δshare ≥ 0.25: T16, T28). Level advisory: median mean > 100 with p5 > 15.
- A5 `take_edit` advisories from the frames the edit trims: `post_cut` (rest mean > 2× placed last-10 mean and max > 8: T28, T29; 0 in ep05/07) and `pulse` (autocorrelation of per-frame diff at lags 12–36 f, r > 0.5 over ≥ 3 cycles: T05's 22-frame pulse).
- A6 `look_gate.one_hue` per picture: lifted floor required on BOTH branches (Q28_0A: share 0.85 over p5≈0 is a lamp, not a print).
- A7 lip-sync: `take_lag` correlates the mux with the wav that made it (r 0.86–0.95 at HANDLE on all seven) — rename the field `mux_lag_s`; a mouth-vs-envelope measure is the open item.

### B. Plan gates — story (`studio/plan_gates.py`, `studio/story_layer.py`, `studio/episode_spec.py`) **[ep11]**
- B1 G-STORY hard: a narration line reporting speech (`… , he said`, `he would …, he said`, `<name> said`) on a shot whose `faces` holds that speaker → "make it dialogue"; advisory when the speaker is off the shot.
- B2 G-STORY hard: the turn shot's `faces` must contain `protagonist`, and `turn` must be the lead's act.
- B3 `Episode.answer` (shot or line index) and `story_layer.report` prints where the question is answered; the chapter's own answering sentence is a line.
- B4 G-NAMES advisory: a proper name's first hearing in the series (against earlier episodes' lines.json) carries a role noun.
- B5 caption-line advisory: content-word overlap of a narration line with its shot's frame+motion; top three printed; wall from ep07.
- B6 wordless tail: `wordless_tail_s ≤ 6.0` after the last line (hard; ep05 4.4, ep07 4.5 pass, ep10 11.25 fails); the button shot carries `beat_s + coda_s ≥ 0.6`. `qc.longest_gap_s ≤ 6.0` as the delivered-file check.

### C. Plan gates — picture (`studio/plan_gates.py`, `studio/house_style.py`, `studio/episode_take_prompt.py`) **[ep11]**
- C1 G-SIZE: a close/medium_close `at_rest` names the head fraction (`HEAD_FRACTION`: close "half the frame height", medium_close "a third", medium "a quarter"); an MCU whose at_rest spans the head "from the TOP edge to the BOTTOM third" is a close and is refused.
- C2 G-SUNSPLIT advisory: under a sun (no practical in the setup's light) an at_rest that splits a face into lit/shadow halves is advised to name the shadow-caster at a frame edge instead ("the hat brim's black across his eyes").
- C3 G-LIGHT: each camera light clause names a FRAME side, and the side flips when the shot faces away from the landmark (ep10 shots 16/17/18 named the wrong side); the light sentence is core and must reach every block (T16's was the one of 34 dropped).
- C4 `house_style.light_for(setup)` with the episode `light` as fallback: the evening/bedroom blocks of ep10 carried "low side sun" from the episode line.
- C5 travel cap by cell face height: `plan_gates` refuses a push whose allowed ratio `1 / face_h(cell)` is under the planned reach (T05 cell 0.69 → 1.45× max).
- C6 lints: `keeps the frame edge` alongside any travel is refused (a push removes the edge, a pull-back moves it inward); `toward the (door|window)` inside a head clause is a reposition word; amount words are dropped from ACTION clauses (0/16 governed).

### D. Storyboard (`studio/sheet_gate.py`, `studio/episode_seq_board.py`, `scripts/episode/redraw_panel.py`, `scripts/episode/seq_boards.py`)
- D1 `redraw_panel.py` calls `house_style.adopt(episode.where, episode.light)` before `sq.single`; `single_picture` opens with the size word.
- D2 `instant_before`/`end_state` match the motion verb's participle or out/up state on its own object in at_rest (Q10 "raised hand" for "lifts", Q12 "hand out" for "throws out", Q27).
- D3 ladder clause only when the landmark noun is in `frame`; the ladder size may not contradict the at_rest size for the same noun; `_thing()` rejects a phrase ending in an adjective ("the black", "the lamp warm").
- D4 no strict retry without a named offender (`strict_prefix()` empty → refuse the $0.13 re-roll).
- D5 panel vs sheet redraw rule in the skill: panel ≤ 2 cells per sheet, sheet redraw ≥ 3.

### E. Audio (`scripts/cast/cast_voices.py`, `scripts/episode/say_lines.py`, `studio/voice_qc.py`, `studio/episode_bed.py`, `scripts/episode/assemble.py`)
- E1 cast-time gates: design clip half-vs-half self-similarity ≥ 0.65; nearest cast design ≤ 0.80. Recast John Ferrier (up in register; Young is the low one).
- E2 `line_reference` attempt ≥ 2: the alternate-reference render is accepted only if its line-vs-line similarity against the speaker's other PASSED lines in the episode is ≥ 0.75; else keep the design-clip render.
- E3 `episode_bed.compose`: overlap-add with the equal-power crossfade at every tile boundary; `assemble.one_tone` treats live music < 0.75 × want as dead and rerolls.
- E4 `similar_floor(seconds)`: 0.70 at ≥ 4 s, 0.65 at 2–4 s, 0.60 under 2 s (a true voice truncated to 1.5 s reads 0.64–0.69); `voice_qc.check` adds `ends_abruptly` (last 50 ms within 30 dB of peak and trail < 0.05 s) and `WPS_MAX = 3.8`; `voice_say` pads 120 ms of room.

### F. Time (`scripts/episode/run.py`, `studio/comfy.py`, `studio/episode_clock.py`, `scripts/episode/takes_r2v.py`, `studio/voice_qc.py`, `scripts/episode/qc.py`)
- F1 retake policy: one batched round per master; `--retake` requires `--why=` written into the clock note; a single-take round is refused unless declared the last.
- F2 `comfy.busy()` (queue running+pending) and `run.py` refuses GPU-touching stages while busy (`ok=False, note="refused: queue busy"`), `--after` waits.
- F3 Whisper in-process on CPU (`uv add openai-whisper==<pin>`; `voice_qc.transcriber(device="cpu")` default) so take_dq/qc never enter the ComfyUI queue and can overlap renders.
- F4 parallel plan: frames before lines; sheets alongside lines; title still during takes; `submit_all` appends the title animation then the bed tones last.
- F5 `episode_clock.NORMS` per condition: takes = 300 + Σ(60 + 1.2·frames); take_dq = 30 + 8·n; qc = 60 + 5·lines; lines = 20·lines; title = 40 + 100; `slow()` flags ok=False rows.
- F6 `qc.py` internal cuts checked against `episode_takes.grid_frame(planned)` and reported `late_frames`, not "missing" (a 3-frame snap is 0.125 s > 0.12).

### A′. Identity and wardrobe (`studio/identity_gate.py`, `studio/describe.py`, `studio/cast_agree.py`, `studio/cast_refs.py`)
- A′1 Implement `identity_gate.observe` (facenet-pytorch MTCNN + VGGFace2 on CPU: 69 s for an episode) and recalibrate before it goes hard: `FRONTAL 0.50 → 0.35`, `READABLE 0.12 → 0.15`, drift = min cosine of each readable frame against the segment's median embedding when n ≥ 3 (first-vs-last only when n = 2). As calibrated today it would have refused four good takes (T06/T21/T29/T33 same-person pairs 0.60–0.69 on small, pitched or turned faces) and caught nothing — no stranger appeared. Advisory for one episode.
- A′2 The wardrobe row is where ep10 actually drifts (T31 short black beard, T33 trimmed grey beard, T21 sandy hair, T06 check coat → plain fawn) and it has no measurer: `wardrobe_dq` reads the largest face at first/middle/last sample of each segment through `describe` and diffs against `identity.traits + wardrobe[state]`; `facial_hair` needs LENGTH, `hair_colour` read from the take. A trait changing ≥ 1 notch within one segment is a fault.
- A′3 Wardrobe state follows the SCENE: a setup may declare `cast_state: {"john_ferrier": "indoor"}` overriding `outdoors`; a plan gate refuses a state flip for one character across consecutive setups of one section-run (ep10: hat+coat → bare-headed → hat+coat inside one conversation).
- A′4 `cast_agree` R1 extended to `wardrobe[state]` vs the card read back through `describe` (Ferrier's sentence says fawn homespun, the card shows brown check tweed; T06 starts as the picture and ends as the sentence).
- A′5 `identify()` margin: best − second-best ≥ 0.15 else "ambiguous" (Ferrier × Stangerson sheets 0.62–0.66; chapters XI–XII put them in one room); a readable face in a segment whose cell declares `faces: []` is a hard row once `observe` exists (T29's window insert gained Lucy's head).

### J′. Prompt text (`studio/episode_ref_official.py`, `studio/house_style.py`) — measured on ep05/07/08/09/10
- H3 obeys what is IN the pinned cell and the DIRECTION of the camera verb; it ignores amounts, angles, absences and anything asking for a thing the cell does not show. "hand's breadth" occurred 61 times in ep10's prompts and the pushes ran 1.11–2.16×; direction obeyed 34/34.
- Length separates nothing (GOOD 178/210, WORSE 198/196, ep10 223); the overruns were duplicates — the arrival repeats the camera head (11.6 words/block, "across the whole shot" twice in 34/34), the light sentence grew 5.5 → 14.0 words. Keep L14 at 150–240; shorten the arrival (≤ 16 words, no word of the head repeated) and cap the light sentence at 10.
- A kept-clause holds only a sharp static edge object under a small move (1 of 4 standalone, and that one trivial); it cannot brake a scale, hold a blur or exclude a thing. Pull-back direction 3/3, amount 0/3; an insert pulled back 0.54× off its panel.
- Inserts 1/7 bad, wides 2/3 bad; faces on a dialogue lane push hardest (median 1.50 vs 1.34).
- The style line "low side sun" stood over moon/lamp/candle setups in 16/34 blocks — harmless only because every `described` names its own source; the ep08 configuration. `light_for(setup)`.

### G. The skill (`.claude/skills/episode/SKILL.md`)
Each owner above writes its paragraph. The plan-writing rules for ep11 in one place: a close takes a pull-back or a pan; an insert a pan or a tilt; head fraction is the size; no sun split on a face — name the shadow-caster; the lead speaks his own decision on his own face; the turn shot holds the protagonist; the last line lands within 6 s of the end; a name's first hearing carries its role; one batched retake round with a written reason.

## Cost of the day, for the record
$1.45 of images (8 sheets, 4 panels, 1 title still, 2 cast cards); 5.0 h of stages of which ~1.5 h was retakes and their re-cuts and ~0.9 h authoring gaps between stages.
