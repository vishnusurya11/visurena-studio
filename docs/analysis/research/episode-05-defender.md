# Episode pipeline — the defender's brief

Date: 2026-09-10. Standard: an artifact, stage, field, validator or file is
KEPT only if it prevents a failure that was MEASURED or records a decision
that was MADE, with the evidence's location. Everything else is conceded.

## 0. The evidence index — what was actually measured, and where it lives

| id | measurement | where the evidence is |
|---|---|---|
| M1 | Qwen-Image-Edit compositor: scene held on two placements, then swapped wardrobe (Watson's bowler + moustache on the man in Holmes's jacket); a pixel copy re-dressed Stamford as a second Watson | prose only: `.claude/skills/episode/SKILL.md` table; `scripts/episode/frames.py:93-98` (kept 0.58 / 0.26); `episodes/ep01/episode.log` "scene kept 0.76 / 0.73 / 0.81 / 0.86 / 0.66 / 0.88 / 0.61". The swapped master images were deleted; nothing on disk shows the swap. |
| M2 | FLF between S00 and S01 morphs: second framing reached by 3.5 s of 5.9 s | `scripts/episode/shots.py:37-43`; `episode.log` "T00 flf_turbo 141f 5.87s in 668s". The take was deleted. |
| M3 | Take-prompt variants on T00, same panel and seed: the official structure with a room paragraph pulled back to a wide of both men; the third still widened to show Stamford | `episode.log` "T00 i2v_turbo 141f 5.87s in 312 / 342 / 327 s"; `episodes/ep01/work/t00_strip.png` (I looked: hand close-up at 0.0 s, both men full-length in a wide by 5.0 s). The FOURTH prompt (framing LOCK + "as drawn") is the one on disk in `shots/T00.prompt.txt` and is UNMEASURED — at the time of writing ComfyUI is running prompt 172 (fl2va), presumably that render. |
| M4 | Honorific WER: "Doctor Watson, Mister Sherlock Holmes" heard as "Dr. Watson, Mr. Sherlock Holmes", WER 0.40, failed twice | `episode.log` lines "BAD l09 wer 0.40" x2, "1 line(s) failed the listen gate twice"; fix `studio/voice_qc.py:87 HONORIFICS`; result `lines/lines.json` l09 `error_rate 0.0, tries 2`. Also l12 haemoglobin/hemoglobin 0.125 passed — the 0.20 band is load-bearing. |
| M5 | Model swap off the D: HDD: reload 250-470 s on top of a 260-300 s take | `docs/analysis/research/episode-02-shot-continuity.md` §1 table (ComfyUI log 2026-09-05); `episode.log` cold T00 668 s vs warm 312-342 s. |
| M6 | gpt-image 3x3 sheet from plate + sheets (+ previous sheet): coherent first try | `frames/board_corridor_0.png`, `board_lab_0.png`, `board_lab_1.png` (2048x3072 on disk). I looked at the corridor sheet: same Watson (tweed, bowler, moustache, silver-headed stick), same Stamford, same corridor across 7 shot panels + 2 reverse-angle alternates. Verdict by eye; no metric anywhere. The SKILL says "sixteen panels"; the plan has 17 shots. |
| M7 | Trailer-domain measurements the episode reuses | `studio/trailer_assemble.py`: mix hang at 25,690,160 bytes (`mix` comment), loudnorm DYNAMIC fallback (+0.53 dBTP), Jekyll title clipped off both edges (`TITLE_SAFE`), -0.03 dBTP over ceiling, `\N` fade never firing without a raw string (`ass_title`). |

Never run, on any episode: the H3 round (0 of 17 takes on disk), `storyboard.py --review` (no `storyboard.html`), `assemble.py` (no `master.mp4`, no `audio/bed.wav`), `qc.py` (no `qc.json`), captions on a real master. Every file under `scripts/episode/`, `studio/episode_*.py`, `tests/test_episode_*.py`, `.claude/skills/episode/`, `.claude/agents/episode-*.md` is untracked (`git status` = `??`). 54 unit tests pass in 1.9 s; none touches a model.

## 1. The table

Verdict key: **KEEP-M** = a measured failure; **KEEP-D** = records a decision the owner or the writer made (nothing measured); **CONCEDE** = neither.

### 1a. `plan.json` — the contract (`studio/episode_spec.py`)

| artifact / field | what it prevents or records | evidence | verdict |
|---|---|---|---|
| `Shot.frame` | the only text gpt-image reads per panel; the only text that says "mouth closed" / "strict profile" | `episode_board.prompt` :85; M6 | KEEP-M |
| `Shot.motion` (semicolon beats) | the take's action; `beats()` splits it | `episode_take_prompt.py:35-40`; M3 (the short motion prompt held the close-up) | KEEP-M |
| `Shot.faces` | (a) F1 validator: speaker over own readable mouth; (b) `looks` spelt out only when a face is meant to show — Stamford's face pulled into a hand close-up when described | `episode_spec.py:242`; `episode_take_prompt.py:52` docstring; M3 | KEEP-M |
| `Shot.size`, `Shot.carrier` | F1 needs size; carrier `none` refuses a line | `episode_spec.py:240-244`; research 03 §1.1 (external) | KEEP-D (F1 is the failure the whole VO design exists for, but it was never measured here) |
| `Shot.cast`, `Setup.cast` | which character sheets are attached to a sheet; stranger check | `storyboard.py:86`; `episode_spec.py:226` | KEEP-D |
| `Shot.setup`, `Setup.described` | plate prompt and "every panel is a frame from the same scene" | `frames.py:87`; `episode_board.py:89` | KEEP-D |
| `Shot.t_start/t_end`, `Line.at` | the cut IS the plan; T1 (0.25 s off a cut) | `assemble.picture`; `episode_spec.py:245` | KEEP-D |
| `Shot.section` | one hook / turn / button, turn at 50-70 % | `episode_spec.py:181-194`; research 01 rules 2, 3, 7 (grade B) | KEEP-D |
| `Shot.continues` | FLF chaining — which is OFF | `shots.py:53` only reads it when `CHAIN` is True; M2 says never | CONCEDE (dead with CHAIN False; plan.json sets it on shots 1 and 4 to no effect) |
| `Line.text`, `Line.speaker` | the clone and the caption | `say_lines.render`; `episode_captions.script` | KEEP-M (M4) |
| `Line.tags`, `Line.element` | records the compress step's tagging and provenance | read by nothing (`grep` over scripts/studio: 0 hits) | CONCEDE as fields (zero code cost, zero readers) |
| `Episode.next_hook` | the pair rule: ep N+1 opens on the reaction to N's button; the only place it is written | research 01 rule 6 | KEEP-D |
| `Episode.series_cue`, `button_type`, `chapter`, `Setup.location_id` | rules 21, 5, provenance | read by nothing; the rotation rule 5 and the "cue in first 10 s" rule 21 are NOT validated | CONCEDE |
| `Episode.looks` (added today) | the "as drawn" rule: a look is spelt out only for a face the shot shows | `episode_take_prompt.preserve` :43-55; M3 measured the NEGATIVE (naming shows); the positive value of the paragraph is unmeasured — the fourth prompt is in flight | CONCEDE pending T00 round 4; the measured half of the rule survives without the field ("Everyone stays exactly as drawn in <Picture 1>") |
| `Setup.reaction` (added today) | "environment responds" line in the take prompt | H3 prompt guides (external, research 02); no take measured with vs without | CONCEDE |
| `Setup.sound` | `overall_soundscape:` of the take prompt | `episode_take_prompt.soundscape`; BUT `trailer_assemble.mix` (:271-295) maps `0:v` only and amixes `[1:a]` bed + cues — the take's own audio never reaches the master | CONCEDE (feeds a track that is thrown away; unmeasured whether it steers the picture) |

### 1b. Validators (`episode_spec.py`)

| validator | rule | evidence | verdict |
|---|---|---|---|
| `_runs_the_length_of_an_episode` 80-120 s | research 01 rule 1 (Deloitte A, Opus Clip C) | external | KEEP-D (the owner's scoping answer: 90 s default, 120 ceiling — `memory/project_episode_pipeline.md`) |
| `_shots_tile_the_runtime` | assemble concatenates by shot seconds; a gap is a hole | `assemble.picture` | KEEP-D |
| `_the_shape_is_present` (one hook/turn/button, hook by 0:05, setup by 0:15, turn 50-70 %) | rules 2, 3, 7 (B) | external | KEEP-D |
| `_the_button_is_the_worlds_answer` (not the protagonist; on the button shot; 2 s silence) | rules 5, 14 (B) | external | KEEP-D |
| `_the_voice_leaves_room` VO <= 60 %, <= 3 speakers, <= 3 setups, cast-in-setup, no 30 s gap | rules 10, 12, 14 (B) | external | KEEP-D; MAX_LINE_GAP and MAX_SETUPS are the weakest (rule 10's "20-30 s" is a corpus claim, rule 12 says 2 places and the code allows 3) |
| `_no_line_on_a_readable_mouth` F1 + T1 + carrier none | research 03 F1 ("the one failure every source names"), T1 | external | KEEP-D — the closest thing to a brick the design has |
| `Line._short_enough_to_land` 18 words | rule 13 (B) | external | KEEP-D |

None of these has ever refused a real plan on record (no validator failure appears in any log). They are the spec; each is 4-8 lines; deleting any saves nothing measurable and loses the only written form of the rule.

### 1c. Stages and scripts

| stage / file | what it prevents or records | evidence | verdict |
|---|---|---|---|
| `say_lines.py` clone + listen gate, renders-then-listens | a line that says the wrong words (Brigham Young hallucination, trailer); honorific false failure; two model swaps not twenty-six | M4; M5; docstring :10 | KEEP-M |
| `lines/lines.json` measured `seconds`, `heard`, `error_rate`, `tries` | captions and QC windows are timed off the FILE, not the word count; the l09 story is only readable here | `lines.json` l09, l12 | KEEP-M |
| `frames.py` `plates` (Krea plate per setup, `conform` centre-crop) | Image 1 of every sheet; 768x1344 is the one canvas H3 does not stretch (`nodes_minimax_h3.py:145`, research 02 §1) | `storyboard.py:85-86`; M6 by construction | KEEP-D (the recipe measured as a whole in M6; the plate's individual contribution unmeasured) |
| `frames.py` `sheet_for` / `STAMFORD` | a body for a character the trailer never drew | `refs/characters/char-stamford.png` exists; M6 shows him consistent | KEEP-D — but it REWRITES the book-level `refs/refs.json` (585-line diff in `git status`); an episode step mutating a shared file is a defect |
| `frames.py` compositor lane: `SCENE_KEPT`, `scene_kept`, `WARDROBE`, `place_prompt`, `place`, `BLOCKING`, `group_prompt`, `place_group`, `GROUP_WHERE`, `master`, `start_frame`, `masters`, `main` (lines 93-315) + `tests/test_episode_frames.py:28-71` | the lane M1 measured as failing | SKILL 03-frames: "OFF the blind path" | CONCEDE — 220 lines of code and 5 tests defending a path the measurement rejected; the measurement is already recorded in prose |
| `storyboard.py` `draw` (gpt-image `images.edit`, cached on disk) | the paid step spends nothing twice | `draw` :61; the log shows six reruns with no redraw | KEEP-D (owner's spend rule, `memory/feedback_spend_approval.md`) |
| `episode_board.chunks` (even spread, fewest sheets) | ten shots are two fives, not nine and one | log: earlier run 3/3/1 + 3/3/3/1 sheets = 7 sheets; now 7/5/5 = 3 sheets — 4 fewer paid calls | KEEP-M (cost measured in the log) |
| `episode_board.CANVAS` 2048x3072, `panel_box` | a cell face survives 1.33x upscale; on 1024x1536 it does not; the model accepts the size | SKILL 04 "probed 2026-09-10"; sheets on disk are 2048x3072 | KEEP-M |
| `episode_board.ALTERNATES` prompt text | the owner sent back a sheet with black cells | `episode_board.py:51-55` docstring; SKILL 04 | KEEP-D (owner decision) |
| `S*_altK.png` crops + `storyboard.json.alternates` | "what an editor asks for first when a take fails" | read by nothing (`shots.py`, `assemble.py` do not know them); 10 files, ~11 MB | CONCEDE the crops and the record; keep the prompt text |
| `frames/board_<setup>_<k>.prompt.txt` | what was sent to the paid model | written at `storyboard.py:59` BEFORE the cache check at :61, so on every rerun it is rewritten with the CURRENT prompt: the files on disk (02:13) are not the prompts that drew the sheets (01:45-01:47) | KEEP-D in intent; as built it records the wrong thing — fix the order or delete |
| `frames/storyboard.json` panels map | `shots.panels()` reads it | `shots.py:90-93` | CONCEDE-able: fully derivable from `frames/S??.png` filenames; one glob replaces it |
| `shots.py` i2v round, `CHAIN=False`, `HEAD=0.0`, `STEPS=8`, `HANDLE=0.25`, `legal_frames` | M2 (no FLF); HEAD 0 measured on T00 ("opens on its panel"); frames%17==5 is H3's grid | `shots.py:37-43`; SKILL 04b; research 02 §1 | KEEP-M |
| `studio/episode_take_prompt.py` official structure + `LOCK` + "as drawn" | M3: the room paragraph widened the shot; "no zoom past the described framing" was not enough (`LOCK` docstring :106) | `work/t00_strip.png`; log | KEEP-M for `LOCK`, `preserve`'s faces rule, `composition` (no eye-line sentence on a hand insert); CONCEDE `reaction()`, `ending()`, `position()` prose scale, `soundscape()` — reasoning from guides, unmeasured, and the fourth prompt is the first that carries them all |
| `shots.py --prompts` -> `shots/prompts.json` | run cards so the owner can validate or run on another host | SKILL 04b "EVERY PROMPT IS SAVED before anything renders" (owner ask today) | KEEP-D one copy |
| `shots/TNN.prompt.txt` x17, and `prompt` inside `shots.json` | the same prompt a second and third time | `shots.py:77` rewrites `TNN.prompt.txt` at submission; `render()` :85 stores it again | CONCEDE two of the three copies |
| `storyboard.py --review` -> `storyboard.html` + `storyboard/S??.png` stills | the ONLY panel-vs-take identity gate today | SKILL "Known open items": "the review page is the gate today"; never run | KEEP-D (a stand-in for the missing ArcFace gate; 45 lines; delete it and there is no gate at all) |
| `assemble.py` (cut, ACE-Step bed, `mix_with_lines`, captions, end chip) | the trailer's mixer under an episode plan; all the mix measurements are the trailer's (M7) | never run on an episode | KEEP-M for the reuse (mix hang, loudnorm, TP ceiling are measured); CONCEDE `bed()` ACE-Step generation as untested here and `with_end_chip` as reasoning (rule 20, grade C) |
| `studio/episode_captions.py` | phrase captions, name chip off-screen, safe box | research 01 rules 17-18 (external A/C); raw-string note is M7's `\N` bug; never rendered on a real master; `ink_bounds` check (research 03 §4.7) unbuilt | CONCEDE as unproven: the module has never produced a frame anyone looked at; keep only after one burned master is measured for ink inside y 130..1436 |
| `qc.py` (seconds, LUFS band, TP, planned-vs-seen cuts, WER on the master's windows) | "a line lost in the sum" (trailer 08); TP -0.03 over ceiling (M7) | trailer-domain; never run here | KEEP-M for LUFS/TP/lines-on-master (trailer-measured); CONCEDE `seen_cuts` threshold 0.1 as unmeasured (a hard cut between two panels of the same corridor may score under 0.1 and fail every plan) |
| `episode.py` runner (each step skips what exists) | resume without re-spending; one stage's model resident | log: `say_lines` skipped 13/13 on nine reruns; M5 | KEEP-M |
| `studio/episode_home.py` (`book_dir`, `home`, `plan_path`, `load_plan`, `*_dir`, `master_path`, `relative`, `read_json`, `write_json`) | one place that resolves the absolute root (CLAUDE.md: never store an absolute path); `load_plan` is the gate | used by every script; `test_episode_home.py` | KEEP-D for `load_plan`, `relative`, `book_dir`; CONCEDE the five one-line path helpers and `read_json`/`write_json` (they save a `/` each) |
| `HEAD` in 3 files, `W, H` in 4 files, `conform` in 2 files, a test guarding `assemble.HEAD == shots.HEAD` | — | `assemble.py:111`, `shots.py:34`, `storyboard.py:32`; `frames.py:44`, `storyboard.py:36` | CONCEDE the copies: one constant in `episode_spec` or `h3`, and one `conform` |
| `episodes/ep01/episode.log` | the only surviving record of M2, M3, M4, M5 timings | this brief was written from it | KEEP-M |
| `frames.log`, `say_lines.log` (0 bytes) | — | empty | CONCEDE |
| `work/` (t00 frames, strip) | M3's picture | `t00_strip.png` | KEEP as scratch until T00 round 4 is read; then delete |

### 1d. Docs and agents

| file(s) | what they record | verdict |
|---|---|---|
| `SKILL.md` "Why the storyboard is the input" table + "Constants that are decisions" + "Known open items" | M1-M6 and the owner's choices (gpt-image, 3x3, no compositor) | KEEP-M |
| `subskills/04-shots` | the M2/M3/M6 measurements in detail | KEEP-M (fold into SKILL.md; it says "leave spare panels black", which `episode_board.py` no longer does — drift) |
| `subskills/01-compress`, `02-carriers` | research 01 §2 procedure and research 03 §1 tables restated | KEEP-D as the writer's procedure; the validator is the enforcement, the doc is the method |
| `subskills/03-frames` | mostly describes the OFF lane | CONCEDE (two sentences survive: plate per setup, sheet per speaker, 768x1344) |
| `subskills/05-voice`, `06-assemble`, `07-qc` | 19 + 25 + 18 lines restating the scripts' docstrings | CONCEDE as separate files; fold into SKILL.md |
| `.claude/agents/episode-{writer,art,cinematographer,editor,showrunner}.md` (127 lines) | three practices with measurement behind them: LOOK at every sheet (M6 is by eye), render T00 and READ it before the round (M2/M3), queue empty so nothing swaps H3 (M5); the rest restates the skill | CONCEDE the five files; keep those three sentences in SKILL.md |
| `docs/analysis/research/episode-0{1,2,3}` | the graded external evidence every KEEP-D row cites | KEEP-D |

## 2. Exists from reasoning only — cheapest to delete first

1. `frames.log`, `say_lines.log` — 0 bytes. Delete.
2. `Shot.continues` — dead while `CHAIN=False`. One line in the spec, two values in plan.json.
3. `Line.tags`, `Line.element`, `Episode.series_cue`, `button_type`, `chapter`, `Setup.location_id` — six fields nobody reads; no validator enforces the rules they name (5 rotation, 21 cue-in-10 s).
4. `shots/TNN.prompt.txt` x17 and the `prompt` key inside `shots.json` — duplicates of `prompts.json`.
5. `S*_altK.png` x10 + `storyboard.json.alternates` — no consumer. (The ALTERNATES prompt text stays: owner decision.)
6. `frames/storyboard.json` — a glob of `S??.png` is the same map.
7. `HEAD` x3, `W,H` x4, `conform` x2 and the test that checks two copies agree — one definition each.
8. `Setup.reaction`, `take_prompt.reaction()`, `ending()`, `position()` prose scale — H3-guide reasoning, unmeasured (T00 round 4 pending).
9. `Setup.sound` + `take_prompt.soundscape()` — feeds a track `mix()` discards.
10. `Episode.looks` + `preserve()`'s named paragraph — the measured half is the NEGATIVE (naming a look shows it); the positive half is unmeasured.
11. `subskills/03-frames`, `05-voice`, `06-assemble`, `07-qc`; the five agent files — 215 lines of restatement; three sentences worth keeping.
12. `frames.py` lines 93-315 (compositor lane) + `test_episode_frames.py:28-71` — 220 lines and 5 tests for a lane M1 rejected.
13. `episode_captions.py` — 102 lines never rendered on a real master; research grade A for the rule, zero measurement of this code's output.
14. `assemble.bed()` ACE-Step generation — untested here; `with_end_chip` — rule 20 grade C.
15. `qc.seen_cuts` at threshold 0.1 — unmeasured on any H3 cut; the WER-on-master, LUFS and TP gates are trailer-measured and stay.
16. `storyboard.py --review` — reasoning, but it is the only gate; last to go, and only when an ArcFace gate replaces it.

## 3. The per-episode tree

Root: `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\library\20260822113400_a-study-in-scarlet\episodes\ep01\`

KEEP (28 files + takes):

```
plan.json                         the contract
episode.log                       the measurements
lines/l00..l12.wav (13)           the lines
lines/lines.json                  measured seconds, heard text, WER, tries
frames/plate_corridor.png         Image 1 of every corridor sheet
frames/plate_lab.png
frames/board_corridor_0.png       the paid artifact, cached
frames/board_lab_0.png
frames/board_lab_1.png
frames/board_*.prompt.txt (3)     ONLY once written before the cache check is fixed
frames/S00..S16.png (17)          the panels = H3 start frames
shots/prompts.json                one copy of every run card
shots/T00..T16.mp4 (17, pending)  the takes
shots/shots.json                  measured seconds and render_s (drop the prompt key)
storyboard.html + storyboard/     the only identity gate until ArcFace
audio/bed.wav, master.mp4, qc.json (pending)
```

DELETE (36 files today):

```
frames.log, say_lines.log                       empty
frames/S00_alt7.png ... S15_alt8.png (10)       no consumer
shots/T00.prompt.txt ... T16.prompt.txt (17)    duplicates of prompts.json
frames/storyboard.json                          derivable from S??.png
work/t00_*.png, work/t00_strip.png (5)          after T00 round 4 is read
work/ (seg*, picture, mixed, captioned, final.txt, end_chip, level sheet, bed-ducked) after qc passes
```

Code to delete with them: `frames.py:93-315`, `tests/test_episode_frames.py:28-71`, `subskills/03-frames`, `05-voice`, `06-assemble`, `07-qc`, the five agent files, the duplicated `HEAD`/`W,H`/`conform`, the seven unread plan fields.

## 4. The three biggest risks to an unattended run the current design does not cover

1. **No automatic panel-vs-take identity gate.** M6 was verified by eye on a sheet; M3 shows the take can leave its panel entirely (hand close-up -> wide of both men) and nothing in `shots.py` or `qc.py` would notice — `qc.seen_cuts` would even PASS such a take, because the pull-back is inside one shot. Research 02 §5 names the tools (ArcFace `buffalo_l` cosine on the take's 25/50/75 % frames vs the sheet's face; DINO subject consistency; LPIPS across the cut) and says insightface is not installed. Until one of these runs after every take, an unattended round of 17 takes at ~5 min each (M5) can finish with a morph or a wrong-room take and report success. The `storyboard.html` page mitigates only if someone opens it.

2. **The model-swap tax off the D: HDD is one interleave away.** M5: 250-470 s per reload, disk-bound. The design keeps each stage's model resident (`episode.py` STEPS order, `say_lines` renders-then-listens), but a single Whisper listen, Krea plate or ACE-Step bed slipped between two H3 takes — a resume after a partial round does exactly this, because `episode.py` re-enters `say_lines` and `frames:plates` before `shots` — pays the swap again. The fix is user-side (weights to C: NVMe, unmeasured) and the runner does not detect an occupied queue (the `episode-cinematographer` says "the queue is empty" as a human rule; nothing checks `/queue` before submitting). At the time of writing the queue IS running an fl2va job.

3. **The storyboard is the one paid step and needs an eye before it is committed to 17 takes — and the prompt beside a cached sheet is not the prompt that drew it.** `storyboard.py:59` rewrites `board_*.prompt.txt` before the cache check at :61, so after any prompt change the record on disk claims a prompt the sheet never saw; a redraw decision made from that file is made on false evidence. Combined with M6 being a by-eye verdict (no metric, "sixteen panels" for a 17-shot plan), an unattended run that changes `Shot.frame` or `looks` either spends again on every sheet (if someone deletes them) or animates a stale sheet under a new prompt (if nobody does). A content hash of (prompt, reference paths) written INTO the sheet's record, checked before `shots.py` starts, closes this; it does not exist.

Two further defects found while reading, not risks to the run but wrong today: `frames.sheet_for` rewrites the book-level `refs/refs.json` (585-line diff) from an episode step; `trailer_assemble.mix` drops the picture's audio, so every H3 soundscape the take prompt asks for is generated and discarded.
