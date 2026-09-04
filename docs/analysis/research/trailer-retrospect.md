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
  seed bound. The ladder should climb to `alternate_setup` (a framing the
  reader can see the face in) after ONE reroll, or the gate should admit a
  take within one notch of the threshold when the beat has no line.
- Step 03's gate has never passed. Measured over the 16 Scarlet seeds:
  every metre-grid seed scores `title_term` 0.3 and `slot_term` 0.4 (the
  struck-pulse captions produce no pre-title trough and no slot); the one
  seed with both (1002, fitness 9.2) reads `bars_in_mode` 0.43. The fix is
  upstream — a caption/section sheet the generator obeys, or a tracker that
  reports beat regularity beside downbeat regularity — not a lower floor.
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
  render times out for the render's reason.
- Holmes's hair and facial hair are still invented when the book is
  silent; the card should say "unspecified" and let the render decide, so
  the fidelity gate does not enforce an invention.
- Retire the OpenCV identity parts (`identity.py`) now that the trait card
  gates steps 02 and 07; FP8 Qwen3-VL and moving it to NVMe are user-side.
