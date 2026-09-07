---
name: trailer-voice
description: Speak the chosen lines with local Qwen3-TTS — design one reference voice per character from the cast card, clone every line from it, gate on speaker similarity, measure the seconds, and hand the editor files and verdicts, not predictions.
---

# Voice

`studio/voice.py` + `scripts/trailer/step_05_voice.py`, outputs under
`library/<book>/trailer/<run>/voice/`. **Qwen3-TTS 1.7B** as
`qwen3-tts-comfyui`: local, free, 24 kHz mono.

## The brick — Brick 1 again: a voice is BOUND by a reference clip, never described per line

`generate_voice_clone()` takes **no `instruct`** (signature read from the
installed pack); `generate_custom_voice` drops it on 0.6B — a line's emotion
has nowhere to live but the reference clip.

## The recipe, per character with a bound line

1. **Instruct** from the cast card, English, 15–40 words: age band, gender,
   register from `profile.mental` ("precise, quick, dry"), class/role,
   texture, pace. **Never** an accent (drifts to US), a real actor (blocked),
   or a duration ("finish in 5 seconds" does nothing) — era is *diction*.
2. **Reference**: `audio_qwen3tts_design`, one clip per character on a
   sentence of the character's own — what lies BETWEEN the quote marks, not
   what a strip left at the ends — NOT a trailer line, cached at
   `voice/refs/<id>.wav` with `.txt` (ref_text) and `.instruct.txt` beside
   it. **One** reference per character — there is no calm/peak pair; emotion
   one designed voice cannot carry is a line `04-lines` should have scored
   down (`synthesis_risk`).
   `reference_text` (`voice.py:88-95`) takes the FIRST card quote landing in
   the 6–25-word band and `.strip()`s only its ENDS, so a scraped quote
   carrying an internal `”` keeps its attribution clause. Measured 2026-09-07:
   Holmes's quote #0 is 20 words, 14 of them the narrator's — `he shouted to
   my companion, running towards us with a test-tube in his hand` — so
   `refs/sherlock_holmes.wav`, 6.777 s — the clip every Holmes line is cloned
   from, whose `.txt` is every Holmes clone's `ref_text` (`voice.py:182`), and
   what every Holmes similarity is scored against — is mostly narration read
   in Holmes's voice. Watson's and Hope's refs carry no internal mark: 1 of 3.
   Quote #1, "You have been in Afghanistan, I perceive.", 7 clean words, sits
   in the same band and is lost to first-fit ORDER alone. Rule: **speech is
   what lies between the marks; a strip removes only the marks that happen to
   sit at the ends.** The extractor exists one module over
   (`trailer_story.py:672` `QUOTED`) and no pool line carries an attribution
   clause (`tests/test_line_pools.py:83`); `reference_text`'s only test is the
   no-quote fallback (`tests/test_voice.py:155-157`). Refuse a candidate still
   holding a `"` or `”` after stripping — but do not just take the next quote:
   #1 is in run 19's own pool as a `sherlock_holmes`/`hook` candidate, so that
   repair can make `ref_text == target_text`. The cache below freezes this for
   the life of the book, and run 19's one Holmes line still scored 0.7813 — "a
   consistency check, never a quality one" is consistency with THIS.
3. **Lines**: `audio_qwen3tts_clone`, `ref_audio` staged under a
   content-hashed name (two books' `narrator.wav` collide in ComfyUI's one
   input dir), `ref_text` supplied — without it you are in x-vector mode.
   One seed per **character**; `max_new_tokens` ≤ 512 (`MAX_LINE_TOKENS`),
   past which a ≤ 12-word line is hallucinating, not speaking.
4. **Gate**: resemblyzer GE2E cosine, line against its reference, ≥
   `voice.SIMILARITY_FLOOR = 0.65`. Measured 2026-09-04 on the live render by
   `test_threshold_separates_two_designed_voices` (Holmes + Lucy, five lines
   each): same-voice 0.696–0.884, cross-voice 0.393–0.521. 0.75 was the guess
   and fails a 0.63 s two-word line on an under-supported embedding. That floor
   belongs to a CHAIN, not to a voice: `design_reference` writes the reference
   through a bare `_render` (`voice.py:161`), `clone_line` writes the line
   through `post_process` (`:187`), and `attempt_line` scores the PROCESSED
   line against the RAW reference (`step_05_voice.py:88`) — the 2026-09-04
   measurement included, which designs with the one and clones with the other
   (`tests/test_voice.py:210-224`). Rule: **a threshold measured through a
   processing chain belongs to that chain.** `POST_CHAIN` and
   `SIMILARITY_FLOOR` are one fact in two places: raise the HPF to clear the
   bed and a low voice loses the fundamental the embedding leans on, and lines
   start failing a gate nobody touched. Change either and re-run the local test
   before the next book.
5. **Below the floor**: three seeds, then the pool's next unused line of the
   same `function` **spoken by a voice already designed**, then the terminal
   rung. That second rung is live (`LADDER` `step_05_voice.py:28-30`,
   `climb_line` `:104-109`, `test_the_next_line_with_the_same_function_can_win`)
   and has never fired: 344 learnings, four step-05 rows, all `speaker_card`,
   **zero** `gate: "similarity"`. The qualifier is its real reach —
   `climb_line` passes `set(refs)` (`:105`) into `next_candidate`, which
   demands `line.speaker in speakers` (`:74`,
   `test_a_candidate_needs_a_designed_speaker`), while `design_refs` iterates
   `slate.spoken()` only (`:55`). Run 19 was lucky — 23 of 25 pool lines
   belong to speakers the slate had already voiced; when `refs == {}` the
   rung returns `None` for EVERY line by this filter alone, so bypassing the
   `:120` card would not revive it. Rule: **a fallback that filters on a set
   the failing phase produced cannot escape that phase's failure** — design
   from `slate.spoken() ∪ pool`, which on run 19 adds zero references.
   A failed alternate is never spent, either: `used.add` sits AFTER the
   terminal return (`:127`, `:125-126`), so the alternate that just failed
   stays first in pool order and `next_candidate` hands it back to the next
   same-function line, which `attempt_line` renders at `seed_for(alt.speaker,
   0)` — rung 2's try index is 0 (`ladder._tries`) — the identical
   (reference, text, seed) triple, scoring identically. Rule: **a fallback
   whose candidate set is not narrowed by its own failures is a repeat, not a
   rung.** Derived only — no test drives two climbing lines — and bounded at
   one wasted render per later same-function line, 7.8 s each on run 19,
   ≤ 12 under `MAX_LINES` ≈ 94 s of the 900 s share. `used.add` belongs on
   every rendered attempt, not only on the winner.
   **And a similarity death cannot be NAMED.** `climb_line` calls `climb`
   with no `substep` (`:111-112`) — step 02 passes `substep=char_id`
   (`step_02_refs.py:150`), step 07 `substep=beat_id` (`:282`), step 05 alone
   passes none — and `Climb.ask`'s terminal row carries neither `measured`
   nor `threshold` (`ladder.py:78-79`), so the row reads `{step:"05",
   substep:"", gate:"similarity", action:"card", attempt:4, terminal:true}`
   and nothing more (pinned: `tests/test_step_05_voice.py:136-139` asserts
   `threshold` only over `learned[:-1]`). The four `speaker_card` rows name
   their speaker only because `measured` was handed a string (`:121`), and
   `Climb.settle` logs nothing when an attempt PASSES (`ladder.py:92-99`), so
   a rung-2 win leaves three anonymous failure rows and no record of what was
   spoken instead. Two lines dying at the gate write two byte-identical rows,
   and the retrospect cannot separate one bad reference from two bad
   speakers: opposite repairs off identical evidence. Rule: **a learning is a
   message to the next run, and a row that cannot name its subject turns a
   per-line failure into a per-step count** — pass `substep=f"{index:02d}"`
   on the climb and on the `speaker_card` Learning before the next book.
   Nothing reads them this run either: step 06 loads learnings only for
   `frame_budget.Cycle.from_rows` (`step_06_plan.py:405`) and step 10 dumps
   them into the manifest (`:96-103`). The editor learns nothing from this
   step's ladder; `voice.json` is the whole channel.
6. **Measure, because `seconds` is an existence flag.** `clone_line` writes
   `seconds` from the file (`ffmpeg`), never from the text — and only for
   lines that RENDERED. Every other line is sized by
   `trailer_dialogue.speech_seconds` (`0.22 × vowel groups + 0.45`), which
   run 19 applied to the line it could not speak **and got right**: over the
   four lines it DID speak, 11.26 s estimated against 11.39 s measured — 1.1 %
   low, worst −24 % on a 1.75 s line. `voice.py:8`'s "40 % wrong" is not what
   this run measured, so sizing accuracy is not why we measure. The reason is
   `measured.get(text) or speech_seconds(text)`
   (`trailer_dialogue.py:393-395`), which makes absence indistinguishable
   from presence. Rule: **an existence fact must never ride on a value that
   has a plausible default**; a fallback accurate enough to be invisible is
   worse than a wrong one, because only a wrong number raises an alarm. So
   the one check that caught run 19's hole is a presence check —
   `qc.py:115-128` counts the rows the mix laid, four not five.
7. **Post**: `POST_CHAIN` = HPF 90 Hz + 2 dB at 3 kHz, then one gain pass to
   `LINE_LUFS = −20`, measured after the filter because the HPF took energy
   out. Per line, not per character: `08-assemble` levels the master to
   `LINE_TARGET_LUFS = −16` and sizes each duck against the bed under THAT
   window, so a per-character offset lands there as an unexplained depth.

**What rung 7 hands over is a loudness, not a peak.** Measured 2026-09-07 with
`astats`: the wavs THIS step wrote are flat factor **0.000** at peaks −1.39
(`00-0.wav`) and −3.93 dB (`01-0.wav`); the mix's copies of both peak at exactly
**−3.500248** (`level_line`, `volume=…,alimiter` at `LINE_TP − LIMITER_MARGIN`,
`trailer_assemble.py:616-629`, `:88-90`) and `line-1.level.wav` alone comes
back flat **0.869314**. `lines_are_clean` is
`flat == 0.0` (`trailer_stage_spec.py:328`) over `lines.level.json`'s
`rel_path` (`qc.py:429`) — an equality on a continuous statistic, taken on the
mix's copy, never on `voice/lines/` — so step 09 printed `CLIPPED lines` three
times (learnings 341-343) about files this step wrote clean. Rule: **normalise to
a loudness and you have handed the next step an unspecified peak; the verdict
that comes back names your file and measures theirs.** `LINE_LUFS = −20` says
nothing about crest, so the gain up to −16 meets the limiter differently on
every line. State a true peak beside `LINE_LUFS` and the mix's gain is the
only variable left.

## What the editor is handed

`voice.json` is a list of `VoiceLine` and the only authority on which lines
became files. Step 06 does not read it that way: `step_06_plan.py:262` is
`measured = {v.text: v.seconds for v in voiced if v.seconds}`, the **only**
use of `voiced` there. Speaker, order and card come from `lines.json`:

- A carded line is merely ABSENT from `measured`. `windows()`
  (`step_06_plan.py:247`) filters on `SlateLine.card`, the property
  `speaker is None` (`trailer_stage_spec.py:147`), never `VoiceLine.card`, so
  the line keeps its slot and is sized by `speech_seconds`. Run 19 carded
  line 3 at 01:58:42.282Z and step 06 windowed it 5.5 s later (learnings row
  317, 01:58:47.756Z) — `lines_refused: [{"index": 3, "at": 64.908, "why":
  "no shot of Police Inspector in M3"}]` — and it went only because that same
  broken speaker string ALSO matched no face. **Bound** (derived from
  `step_06_plan.py:134`, `:247` and `trailer_assemble.py:522`; not yet
  observed): a carded line whose speaker DOES hold a card and a face passes
  `speak_on_face`, keeps its window, and is skipped in silence by
  `line_windows`' `if line.card or not line.rel_path` — a face held for an
  ESTIMATED 2–6 s with nothing on it, "no dialogues" produced on purpose.
- A SUBSTITUTED line is invisible the same way: `windows()` keys on slate
  text, so the alternate's text is in no window, and `speakers` is `{i:
  l.speaker for i, l in enumerate(slate.lines)}`, so `speak_on_face` judges
  that window against the ORIGINAL speaker. Best case the render is never
  laid; worst case `by_index` lays one character's voice at a window sized
  for another's line, over that other's face.

Rule: **a consumer filters on the LAST verdict written about a line, never on
an earlier step's field of the same name.** Order of repair: step 06 reads
`voice.json`'s speaker and card, or `Rung("next_line_same_function", …)`
comes OUT of `LADDER` — one of the two before the next run.

The bound is not one line. `design_refs` skips every speaker with no cast
card (`step_05_voice.py:59-60`) and `voice_line` cards every line whose
speaker is not in `refs` (`:120-123`) — per line, no whole-slate check —
while the step's one whole-run fallback, `slate.music_only or not
slate.spoken() -> "[]"` (`:135-138`), never sees "spoken, but nobody
designed". A screenplay whose `speaking` carries display names throughout
designs **zero** references, writes N of N cards, and by the two bullets
above gets N estimated silent windows over N held faces: run 19's failure at
100 %, with no gate failing (derived; scene 11 is already half that
screenplay). The card at `:120` also fires BEFORE the ladder, so the rung
built for exactly this is never asked. Rule: **the condition that empties a
step's output must reach that step's
whole-run fallback, not its per-item terminal N times** — `refs == {}` is the
music-only case wearing cards, and the count of `speaker_card` rows in a run
IS the dialogue lost.

## The bound: the fifth line is 4.2 s of an 18.4 s hole

Step 05 spoke 4 of 5 at similarity 0.781 / 0.833 / 0.884 / 0.776 — no gate
fired, no ladder climbed, and the four renders took 31.2 s of a 900 s share
(`run_budget.py:16-20`; wav mtimes 01:58:16.242 → 01:58:47.422), 3.5 % spent.
The picture is 99.2 s (`lines.level.json` `hard_out`) and the laid lines are
1.59 + 2.31 + 5.74 + 1.75 = **11.39 s**, so `qc.json` reads
`speech_occupancy 0.115` against `speech_target 0.30`. Give the fifth line
back at its own estimate (4.19 s) and the run reads **0.157, 52 % of
target**: repairing `Police Inspector`, or any rung in this file, cannot
clear that flag.

The rest is arithmetic settled before this step runs. Run 19's measured mean
is **2.85 s a line** (11.39 / 4) — the count-to-occupancy constant only THIS
step can produce. 0.30 of 99.2 s therefore needs **10.4 lines**, while
`speech_refusal` passes a slate at `wanted_speech` = `ceil(5 × 99.2 / 100)` =
**5** (`trailer_dialogue.py:522-532`, `:306`), `MAX_LINES` = 13 capping it.
Run 19's slate is 5: it cleared step 04 at exactly its floor, and a slate at
that floor can only ever reach 0.14. Nothing stops it either —
`speech_occupancy` is in `flags` (`trailer_stage_spec.py:359-360`) and not in
`floor_pass` (`:331-335`). Rule: **a step whose gate never fired and whose
budget is 96 % unspent is not the cause of the deficit measured downstream —
the ceiling on its output is the count handed to it.** All this step owes
that argument is the number nothing consumes: seconds per line. One repair is
outside this file and real — `04-lines` sizing the slate from `speech_target ×
runtime ÷ measured seconds-per-line` instead of `SPOKEN_PER_100S`. The other,
promoting `speech_occupancy` into `floor_pass`, is already disproven: run 19's
`floor_pass` IS `False` and the master was `delivered` on the first send
(`manifest.json`), because step 09's ladder terminates in `ship_flagged`
(`step_09_qc.py:22-23`, `:58-66`; learnings 341-344) and step 10 carries
`floor_pass` as a manifest FIELD, never a condition
(`step_10_deliver.py:95-104`) — its only gate is the notifier's exit code
(`:81-93`). It even prints the flag list into the caption (`:65-72`), so the
owner's "no dialogues" arrived under a caption that already read
`speech_occupancy`. Rule: **a measurement changes a run only where a rung can
act on it** — and no rung after this step renders a voice, so a promoted
metric buys two picture recuts and ships the same file.

## The terminal rung is a file, or it is a deletion

`card` here is a synonym for *dropped*. `ShotSpec.line` exists
(`trailer_spec.py:120`) and no step assigns it — run 19's `plan.json` carries
a `line` on 0 of 22 shots — and the only `drawtext`/`ass` in
`trailer_assemble.py` (218, 817) is the title card. Step 04's speakerless
cards vanish identically: a refrain reaches the screen only when it is
spoken. A terminal rung may be named for an artifact only when a consumer is
proven by test to render it; until
`test_a_carded_line_is_burned_over_its_window` passes, call it `dropped` — and
the COUNT must be caught upstream of the mix, not in `09-qc`, whose every
failure ends in `ship_flagged`.

## Who speaks what

- `SlateLine.speaker` is a **cast-card id** — `analysis/characters/<id>.json`
  must exist — or `None`. Never a display name, and nothing normalises it:
  `trailer_story.py:418` copies `element["character"]` verbatim,
  `step_04_lines.py:296` hands it to `SlateLine`, whose contract declares no
  domain. Run 19 lost "Do you consider, Doctor, that there is immediate
  danger?" to `speaker: "Police Inspector"` in four runs — rows 205, 260, 289
  and 316 of `learnings.jsonl`, byte-identical but for `ts` — while 23
  snake_case cast cards sat on disk.
- `cast: people_in(scene)` is **not** the fix: `people_in` is `cast |
  speaking` and the screenplay puts the display name in `speaking` too
  (scene 11: `["Police Inspector", "jefferson_hope", "john_watson"]`). No
  card resolves it by name or alias, so the honest resolution is `None` —
  which by the section above is a deletion. **The repair belongs to
  `04-lines`**: a line whose speaker resolves to no cast card must not win a
  voiced slot; it goes to a pool line that can be spoken (run 19 held four
  unused `jefferson_hope`/`stakes` candidates); `group_*` and `unnamed_*`
  cards are reachable by id only, so "TWO DETECTIVES" dies this way too.
- A first-person narrator (Watson, Utterson) is a character with a card;
  design them. `01-story` must emit `narrator` per book.
- The ban is on the FAMILY, not the name. Measured 2026-09-07 across the pack
  `comfy.WORKFLOWS` globs (`comfy.py:18,25`): the `_tts_single_speaker`
  workflows for `audio_qwen3tts_`, `audio_fish_s2_` and `audio_indextts2_`
  each hard-code `voice_narrator_attenborough.wav`, `audio_chatterbox_`
  hard-codes `voice_narrator.wav`. Four real-narrator defaults, one named in
  a ban, all four local and free — so the banned voice comes back without the
  banned line being touched. Rule: **ban the default, not the filename.**
  This step calls only `DESIGN_WORKFLOW` and `CLONE_WORKFLOW`
  (`voice.py:37-38`); a TTS workflow is admissible only when its `ref_audio`
  is a path THIS run wrote under `voice/refs/`.

## Layout, the mix, the tests

```
voice/refs/<id>.wav .txt .instruct.txt   reference, ref_text, instruct
voice/lines/<index:02d>-<try>.wav        24 kHz mono, post-processed
voice.json                               a bare list of VoiceLine
```
Line files are SLOTS, not recipes: `{index:02d}-{try}.wav`
(`step_05_voice.py:83`), `try` per RUNG (`ladder.py:41-45`), in the one
`trailer/main` every run reuses (`trailer_run.py:19-33`). So run 19's
five-line slate sits in a directory of SEVEN wavs — `03-0.wav` is an older
run's audio at the index run 19 carded `rel_path: null` — and rung 2's try is
0 too, so a substitution overwrites the take that failed. `rel_path` in
`voice.json` is the only authority: never glob this directory, never read a
take number as history. The one cache is `design_reference`'s
`if out.exists(): return out` (`voice.py:150-155`), keyed on the bare speaker
id and returning before instruct and ref_text are computed, so a reference
outlives every edit to its card — run 19 cloned one designed 37 h earlier
(recomputed 2026-09-07: all three match, no drift). The gate cannot see that
either: a line is scored against that same reference, so similarity is a
consistency check, never a quality one.

`08-assemble` owns the mix — `trailer_assemble.py:324-380`; the band-split
duck this file used to specify was run 10's, measured failing at 6.2 LU.

Contract tests fake `studio.voice` at design, clone and similarity: what is
tested is which lines the step tries and how it climbs. Nothing renders;
anything that renders is `@pytest.mark.local`.
