# Trailer skill — blueprint status: built vs proposed

The skill describes the trailer the evidence says to cut. This file says how
much of it exists in code. Every rule tagged PROPOSED in a subskill is bound
to one item below and one named test; an item is done when its test passes
on `uv run pytest -q` without a paid call.

Evidence: `docs/analysis/research/trailer-music-structure.md`,
`trailer-iconic-lines-and-moments.md`, `trailer-critic-audit.md` (118 claims:
43 MEASURED, 11 DERIVED, 64 ASSERTED), `trailer-debate-verdicts.md`.

## What exists (3 trailers shipped, all Scarlet)

- the blind path: `trailer.py` runs the ten registry steps of `stages.yaml`
  (`scripts/trailer/step_01_story.py` … `step_10_deliver.py`) under one 6 h
  wall-clock ceiling; every gate has an adapt ladder and a terminal rung,
  every rung writes `learnings.jsonl`, step 10 writes `manifest.json`.
- items 1–12 below are built and green (`uv run pytest -q`: 1439 passed,
  4 local deselected, 2026-09-04). Item 13 (vocal path) is not.
- the identity gate is a TRAIT CARD, not a face recogniser: `studio/describe.py`
  asks the local Qwen3-VL (comfy_studio's `image_qwen3vl_caption` /
  `video_qwen3vl_caption`) to describe a face in a closed vocabulary of seven
  at-a-distance traits, and two faces are two people when ≥ `DISTINCT_AT`
  (3) seen traits differ - `cast_card.refuse_collision` applied to pixels.
  Steps 02 and 07 gate on it; `studio/distinguish.py` is step 02's second
  rung, rewriting exactly the matched card slots. The SFace cosine gate
  (`identity.py`, 0.363) it replaced said only THAT two sheets read alike,
  so its one rung was another seed: Lestrade collided five times in a row
  (run 3, 2026-09-04). Under the trait card Lestrade bound on the second
  sheet (run 4). A take's three frames go to the model as ONE contact sheet:
  comfy_studio's `video_qwen3vl_caption` batches them, and `Qwen3_VQA`
  reads `image[0]` only, so it described a take whose first frame was hands
  holding a note as "face not visible" (run 4, B02).
- measured but not yet re-cut through the new chain: the delivered Scarlet
  master under the new `qc.py` reads 30/45 cuts on beat (onset grid, the
  audio measured rubato), 0/45 on downbeat, 5 target flags, floor pass.
  Metre report over the 9 real seeds: 5 of 9 on a metric grid, fitness
  0.3–2.5 — no seed cleared `FITNESS_FLOOR = 6.0`, which is therefore the
  first number the retrospect will move.

Baseline before this build: 12/35 cuts on beat, 4/35 on downbeat (chance
12% / 4%); 0 spoken lines; 1 slot in the chosen cue.

## Build order

Each item is one PR-sized change, test first. Order is by what unblocks what.

| # | item | module | test that proves it | status |
|---|---|---|---|---|
| 1 | `line_value`: drop `<5 words → −3.0` and `? → −4.0`; add length band (+1.0 for 3–12 words) | `studio/trailer_dialogue.py` | `test_sparta_outscores_ferrier_errand`, `test_no_data_yet_does_not_top_the_book` | [x] |
| 2 | held-out corpus: `tests/fixtures/trailer_lines.json` (38 lines) + Cornell pairs fixture | `tests/fixtures/` | `test_line_value_beats_chance_on_cornell_pairs` (≥ 0.55, iconicity off) | [x] |
| 3 | `fetch_wikiquote(title, author)` → `analysis/iconicity.json`, revid-keyed cache, resolver order book → author § → character | `studio/iconicity.py`, `scripts/analysis/iconicity_coverage.py` | `test_iconicity_cache_invalidates_on_new_revid`, `test_resolver_refuses_film_page` (recorded fixtures) | [x] |
| 4 | `line_pools(book)`: screenplay + character quotes + source quoted speech (tag + sibling attribution) + narration; dedupe; sentence split | `studio/trailer_story.py` | `test_scarlet_thread_line_is_in_pool`, `test_split_attribution_is_refused` | [x] |
| 5 | dependency group `music`; `beatmap.metre()` from Beat This!; tempo from span not median IBI; `phrases()` | `pyproject.toml`, `studio/beatmap.py` | `test_click_track_recovers_beats_and_downbeats` (synthetic click 60–180 BPM), `test_tempo_has_no_octave_double` | [x] |
| 6 | `metre_report.py` → `trailer/music/metre.json` per seed; hand-tapped 16-bar fixture for the drumless seed | `scripts/trailer/metre_report.py`, `tests/fixtures/` | `test_tracker_agrees_with_hand_taps_within_60ms` (`@pytest.mark.local`) | [x] |
| 7 | `trailer_fitness`: metric, tempo, title (pre-title trough holds threat + 2 beats), lift, slot terms; `slots()` | `studio/music_tone.py` | `test_fitness_ranks_metric_seed_above_rubato_seed`, `test_fitness_prefers_cue_with_two_slots` | [x] |
| 8 | `plan_cuts(metre, events, duration, stretch)`: the beat walk, constants filter before the arc, one hold, `MAX_SHOT = max(4.0, 1.25·bar)` | `studio/trailer_edit.py` | `test_walk_never_emits_under_min_shot_at_any_tempo`, `test_walk_cuts_on_every_L0_event`, `test_exactly_one_hold` | [x] |
| 9 | `qc.py` on the delivered master: extract, track, scene-detect verified against manifest, report on-beat / on-downbeat / L0 / cap / title | `scripts/trailer/qc.py` | `test_qc_reports_manifest_cuts_missing_from_picture` (recorded fixture) | [x] |
| 10 | `design_reference()`, `clone_line()`, similarity gate, measured seconds; two comfy workflows | `studio/voice.py`, `workflows/audio_qwen3tts_*.json` | `test_clone_line_writes_measured_seconds` (FakeComfy), `test_threshold_separates_two_designed_voices` (local) | [x] |
| 11 | line layer in `assemble.py`: crossover + mid-band sidechain, one window per line, cards without duck | `scripts/trailer/assemble.py` | `test_line_sits_six_lu_over_bed_in_its_window` (synthetic bed + tone, `ebur128`) | [x] |
| 12 | `order_lines(top, slots, figure)` hook → answer → threat → title → button; `lines = min(slate, slots)` cap 4; whole-beat placement; never `atempo` | `studio/trailer_dialogue.py` | `test_order_refuses_slate_without_hook`, `test_line_chosen_for_slot_from_measured_seconds`, `test_line_naming_the_figure_is_refused` | [x] |
| 13 | vocal path: eligibility (thesis + register + ≥ 2 stem gaps), Vocal Details sheet, demucs stem, refrain-on-downbeat | `scripts/trailer/build_music.py` | `test_vocal_path_refused_without_thesis`, `test_refrain_first_syllable_on_downbeat` (local) | [ ] |

Prerequisite for 12 and 13: `01-story` emits `narrator`, `register`, `thesis`
(`test_story_emits_register_from_enum`, `test_thesis_has_no_proper_noun`).

## Rules of the build

- Nothing in this chain spends a credit. MiniMax Music 3 and MiniMax-H3
  run on the local ComfyUI (`studio/comfy.py`); Beat This!, demucs, Qwen3-TTS
  and Wikiquote are free. The only cost is GPU wall-clock, so the budget of
  an unattended run is TIME, not money.
- Every threshold in the skill is a number to beat, not a number to pass:
  a gate is only trusted after it has failed once on a real file.
- Items 1–4 change which lines are chosen; 5–9 change where cuts land;
  10–12 make a line exist; 13 is last because it needs 5, 7 and 10.
- After item 9, re-cut Scarlet from the existing clips and publish the QC
  numbers next to the 12/35 baseline before rendering anything new.
