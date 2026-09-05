# Trailer blind path — retrospect

One entry per unattended run. Each names what the run measured, what broke,
what changed in code (with its test), and what is still open. A retrospect
item is closed only by a test that fails on the old behaviour.

## Run 6 — A Study in Scarlet, 2026-09-04 17:20–22:29 UTC

**Outcome:** no master from the run itself — step 08 crashed. Run 6b
(23:00 UTC, the same 14 takes with B09 re-rendered long enough for the
hold) delivered: 136.33 s, drift +0.003 s, 64 cuts, 45% on beat (onset
grid; baseline 12/35 = 34%), 0% on downbeat, 53% on L0, −14.0 LUFS,
−1.8 dBTP, floor pass, flags `cuts_on_beat, cuts_on_downbeat, cuts_on_L0,
title_on_downbeat`. Sent to Telegram by hand as a 39 MB copy (defect 4).

**What the run did**

| step | rungs | result |
|---|---|---|
| 01 story | 1 (thesis 8 syllables → agent_call) | passed |
| 02 refs | 10 identity rungs; Hope and Holmes UNBOUND | cards were rotation-invented (fixed before this run finished: book-first portraits, `9887c67`) |
| 03 music | 4 → terminal `onset_grid` | fitness 9.2 with 2 slots on seed 1002; the gate `metre AND slots` has never been jointly satisfiable |
| 04 lines | 2 → `music_only` | no hook fits the first slot (fixed before this run finished: `DUCK_OVERRUN`) |
| 06 plan | 2 (19 unbound → 7 unbound → pass) | 22 setups, 58 shots, 0 line windows |
| 07 clips | B12: identity 4.0 → reroll, 3.5 → reroll, bound on take 3; B14–B21 dropped on budget | 14 takes, all bound to the Holmes sheet, similarity ≥ 0.75 |
| 08 assemble | — | **crash**: ffmpeg concat could not open `work/library/.../work/s000.mp4` |

**Defects found, all reproduced by a test**

1. `trailer_assemble.concat` wrote segment paths verbatim into the concat
   list; ffmpeg resolves a relative entry against the LIST FILE's directory,
   so a repo-relative `book_dir` (what the blind path passes) doubled the
   path. Three shipped trailers came from absolute dirs and never hit it.
   Fix: `listing_lines` writes every entry relative to the listing
   (`test_entries_are_relative_to_the_listing_not_the_cwd`).
2. Every take rendered at `CLIP_SECONDS = 7.0` (175 frames, 7.29 s). The
   plan's final hold asked 7.667 s of B09; the hold is exempt from
   `MAX_SHOT` by design. `extract` ran off the end (7.25 s delivered),
   `segment_start` fell back to 0.0 — inside the 2.6 s reference leak — and
   the drift gate refused the picture at 0.423 s. `need_seconds` existed in
   step 07 for exactly this and was never called, and used the 1.0 s
   identity-frame leak instead of the 2.6 s cut trim. Fix:
   `build_clips.take_seconds` = max(`CLIP_SECONDS`, longest shot +
   `HEAD_TRIM`), wired into `take_values` so the recipe changes only for the
   beats that need it (`test_a_take_holds_its_longest_shot_past_the_head_trim`).
   Cost: the hold beat renders 260 frames (~16 min) instead of 175.
3. All 31 learnings carried `seconds: 0.0`. `climb` never timed an attempt,
   so the budget rung's `cost_seconds` (a 660 s guess) had nothing to
   calibrate against. Fix: every rung learning records the attempt's cost
   from the budget clock (`test_every_learning_carries_what_its_attempt_cost`).
4. Run 6b's master (14 takes, 52,473,989 bytes) was 45 KB over the Telegram
   Bot API's 50 MiB cap; three sends died with `EOF occurred in violation
   of protocol` and step 10 went `undelivered`. A CRF-20 copy (39 MB) went
   through first time. Fix: `deliverable` sends the master when it fits and
   a shrunk copy otherwise; the manifest names the file sent
   (`test_a_master_over_the_bot_limit_sends_a_shrunk_copy`).
5. Learnings written by step 07 in this run have an empty `substep`: the
   process loaded the code before `fe87828` landed. Not a new defect;
   noted so the run-6 rows are not read as a regression.

**Measured, still open**

- Identity reroll is the wrong rung for a small distance. B12 read 4.0
  then 3.5 against `DISTINCT_AT` 3 on two seeds: the seed moved it half a
  trait. Two rerolls cost 33 min — three beats' worth — before the third
  seed bound. CLOSED 2026-09-04: the ladder now climbs to `alternate_setup`
  (a framing the reader can see the face in) after ONE reroll
  (`test_a_face_that_never_binds_ships_its_best_take_short`). Admitting a
  take within one notch when the beat has no line stays open until run 7
  measures how often the close-up binds.
- Step 03's gate has never passed. Measured over the 16 Scarlet seeds:
  every metre-grid seed scores `title_term` 0.3 and `slot_term` 0.4 (the
  struck-pulse captions produce no pre-title trough and no slot); the one
  seed with both (1002, fitness 9.2) reads `bars_in_mode` 0.43. The fix is
  upstream — a caption/section sheet the generator obeys, or a tracker that
  reports beat regularity beside downbeat regularity — not a lower floor.
  MEASURED 2026-09-05, all 16 seeds re-tracked on CPU: (1) the troughs are
  not what breaks the metre — bars-in-mode outside the stopdowns/slots is
  within 0.02 of the whole-cue figure on every seed; (2) four seeds held a
  steady BEAT for 40–58 s (beats-in-mode 0.89–0.96) and were graded rubato
  because the downbeat tracker alternated two- and four-beat bars
  ({2: 29, 4: 31}) — `Grid.of` now re-votes the downbeats every modal bar
  along the beat when the beat is steady (`beatmap.rebar`, `TestRebar`):
  metre seeds 6 → 9 of 16, the shipped seed unchanged; (3) the generator
  DOES obey the Outro — seven seeds put a stop before a late hit — but the
  caption asked for "one beat of silence" and `title_term` grades a bar
  (2001: 1.5 s against 3.0 s), and one seed landed the hit at 99%, past the
  95% the title moment accepts; the sheet and caption now ask for two full
  bars of silence, the impact, and an eight-second decay
  (`test_the_closing_section_asks_for_what_the_gate_grades`); (4) three of
  the five metric seeds read 175–201 BPM against 84 asked because the
  caption said "the pulse doubles" — it now holds the tempo and doubles the
  subdivision. (5) FIXED 2026-09-05: the fitness floor of 6 is carried by
  dynamic range, so the rubato seed with a title moment (1002, 9.2) outranked
  every metric seed (best 2.4) and `best_of` SHIPPED it -- the delivered
  run-7 trailer cut on the onset grid with 0% of cuts on a downbeat.
  `best_of` now ranks on what the gate grades before fitness: a metric grid,
  then a slot, then fitness (`test_best_of_ranks_on_what_the_gate_grades_
  before_fitness`). Still open: whether the floor itself should weigh the
  metric term more -- measure on run 7c's seeds under the new caption.
- The identity gate among men has five live traits (figure, complexion,
  build are shared on every "shares" list). Run 7 measures the unbound
  count under book-first cards before any threshold moves.
- Budget: step 06 caps setups at what 07's share affords with ONE take in
  reserve (262 min → 22 setups). B12's two rerolls spent three takes, so
  the reserve covered one and eight beats went unrendered — not because
  of the reroll alone: step 07's share was measured from the run's start
  and steps 02–06 had already used 48 min of it. Fixed the same night:
  `ladder_for` prices every retry rung at `660 × (beats_left + 1)`, so a
  retry that would cost a later beat's first render goes terminal instead
  (best take, capped) and the beat is kept
  (`test_a_retry_never_spends_a_later_beats_first_render`).
- `describe.TIMEOUT` includes ComfyUI queue wait, so a VLM read behind a
  render times out for the render's reason. CLOSED 2026-09-05:
  `comfy.wait_record` polls `/queue` and starts the clock when the job
  leaves `queue_pending` (`QUEUE_SECONDS` caps the wait in line).
- Holmes's hair and facial hair are still invented when the book is
  silent; the card should say "unspecified" and let the render decide, so
  the fidelity gate does not enforce an invention. CLOSED 2026-09-04, the
  hard way: run 7's first launch spent 20 min refusing four Holmes sheets
  for `hair_colour` (dark hair under a bowler; the card said "receding
  sandy hair") and unbound the lead. The invention stays on the card (the
  cast must still be told apart in the prompt) but only `asserted` slots
  are owed, and the bound card's text follows the render
  (`test_an_invented_slot_the_render_reinterprets_binds_and_the_card_follows`).
  Measured on the way: a sheet render + read costs 286 s, not the 90 s the
  rung was priced at (step 02's `RENDER_SECONDS`/`DESCRIBE_SECONDS`; now
  180 + 110, `TestRungPrice`; the old run's budget went to -300 s three
  times while it believed 90). And
  rebuilding the five Scarlet cards offline found the generator of the
  over-assertion: `book_match` matched adjectives ("brown as a nut" -> a
  brown bowler hat; "long rifle" -> long black hair; "tall" -> a tall beaver
  hat on two men; "felt long-forgotten" -> a felt hat), each then owed by
  the render. It now needs the object named plus one attribute
  (`TestBookNamesTheObject`); stated values are reserved cast-wide before
  invention; a woman's age reads "in her"; women get bonnets, not top hats.
  After the fix the five cards share nothing in Tier One and only
  clean-shaven between Hope and Lucy.
- One sheet per beat. `build_plan.beat_of` casts ONE principal, `h3_prompt`
  declares <Subject 1> = that person and <Subject 2> = the place, and step 07
  measures one face. The delivered run-6b trailer shows the cost: all 14
  takes referenced the Holmes sheet, and the Watson who appears in B05/B09/
  B11/B13 is prompt-only -- a different clean-shaven man each time. H3's
  workflow takes two reference slots, so a two-person beat could bind
  Holmes + Watson and carry the place by prompt (locations were measured
  as `attribute_transfer` anyway). Needs the GPU: render B05 with
  (a) Holmes + place and (b) Holmes + Watson over three seeds and read BOTH
  faces -- `describe_frames` returns one card, so the read must name which
  person it describes ("the man in the bowler" / "the man with the
  moustache"). Do not build the two-subject path before that A/B says H3
  keeps two faces apart rather than blending them.
  BUILT 2026-09-05 (unmeasured): `scripts/trailer/two_subject_ab.py` renders
  a beat both ways over the same seeds and reads each expected face by its
  own sheet's cue (`describe.prompt_for(whom=...)`).  `take_values` now turns
  two bound cast members into <Subject 1> and <Subject 2> (`h3_prompt.build
  (second=...)`); the blind path is unchanged because `beat_of` still casts
  one principal.  Run after run 7: `uv run python -m scripts.trailer.
  two_subject_ab 20260822113400 --beat B05 --second john_watson --seeds 3`.
- CLOSED 2026-09-05: `identity.py` and `identity_gate.py` retired with their
  tests and the `qc` group's OpenCV/onnxruntime pins; only `frame_times` /
  `frame_at` were still used (step 07) and now live in `studio/frames.py`.
  FP8 Qwen3-VL and moving it to NVMe are user-side.
