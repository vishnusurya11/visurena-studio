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
- items 1–12 below are built and green (`uv run pytest -q`: 1484 passed,
  4 local deselected, 2026-09-04). Item 13 (vocal path) is not.
- the identity gate is a TRAIT CARD, not a face recogniser: `studio/describe.py`
  asks the local Qwen3-VL (comfy_studio's `image_qwen3vl_caption` /
  `video_qwen3vl_caption`) to describe a face in a closed vocabulary of seven
  at-a-distance traits, and two faces are two people when ≥ `DISTINCT_AT`
  (3) seen traits differ - `cast_card.refuse_collision` applied to pixels.
  Every beat binds ONE face by design (`build_plan.beat_of` casts one
  principal; `h3_prompt` puts the place in the second slot), so a two-shot's
  second person is prompt-only and drifts. `take_values` can now bind two
  cast members as <Subject 1>/<Subject 2> and `describe.prompt_for(whom=)`
  can read one face out of a two-shot; whether H3 keeps two faces apart is
  measured by `scripts/trailer/two_subject_ab.py`, not assumed - the plan
  keeps casting one principal until that A/B says otherwise.
  Steps 02 and 07 gate on it; `studio/distinguish.py` is step 02's second
  rung, rewriting exactly the matched card slots - and its FIDELITY gate:
  `expected(card)` is what a faithful render reads back as, `disobeyed`
  names the `RELIABLE` traits (hair colour/length, facial hair, headgear)
  the render ignored. Run 6 (2026-09-04): Lestrade's card said walrus
  moustache, the render read clean-shaven/grey, and the ladder rewrote the
  card as if Hope had been matched; complexion and build were on every
  "shares" list and no rung could move them (dead traits: 7/7 sheets read
  fair/average in run 4), and the hair phrase carried a length no slot
  owned. A disobedient render now goes again as written; a moved slot the
  book itself asserted drops the book sentence from the prompt, which had
  been contradicting the card ("a full beard ... with a heavy walrus
  moustache"). Run 7 (2026-09-04): the book is silent on Holmes's hair, the
  rotation said "receding sandy hair", the render put dark hair under his
  bowler four times, and the LEAD went unbound over an invention. A render
  owes the BOOK: `cast_card` records the slots the book (or the person's
  sex) filled as `asserted`, `disobeyed` counts only those, and a bound
  sheet's text follows the render on the rest (`distinguish.adopt`), so
  the take prompts agree with the sheet they condition on. Rebuilding the
  cards offline showed WHY so much was asserted: `book_match` scored
  adjectives, so Watson "as brown as a nut" owned a brown bowler hat, Hope's
  "long rifle" long black hair and a long untrimmed beard, Lucy "felt
  long-forgotten thoughts" a felt hat, and "tall" put two men in a tall
  beaver hat. The book asserts an object when it NAMES it (`OBJECT`) with an
  attribute (`BARE`): "a hat" asserts no kind of hat. Stated values are
  reserved before the rotation invents (Gregson's stated sandy hair had
  already gone to Holmes), a woman's age is hers, and women get bonnets.
  `cast_card.infer_gender` also tokenised on spaces after
  dropping only full stops, so "a thin man," was nobody. The SFace cosine gate
  (`identity.py`, 0.363; retired 2026-09-05 with its OpenCV/onnxruntime pins,
  the frame sampler alone survives as `studio/frames.py`) it replaced said only THAT two sheets read alike,
  so its one rung was another seed: Lestrade collided five times in a row
  (run 3, 2026-09-04). Under the trait card Lestrade bound on the second
  sheet (run 4). A take's three frames go to the model as ONE contact sheet:
  comfy_studio's `video_qwen3vl_caption` batches them, and `Qwen3_VQA`
  reads `image[0]` only, so it described a take whose first frame was hands
  holding a note as "face not visible" (run 4, B02).
- the cast card is BOOK-FIRST: `studio/portrait.py` quotes the book's own
  portrait sentences (`refs/portraits.json`) and `portrait.stated` fills the
  slots the book fills, outranking the pool. Run 6 drew a white-haired,
  bearded Holmes at forty because `profile.physical` said "limited physical
  description" and the rotation invented the rest; the middle band's hair
  pool held white and bald. Found on the way: `describe.nearest` matched
  substrings ("flaxen-hai-RED"; "unshaven" read clean-shaven), and an alias
  by relation ("my companion") gave Watson Holmes's portrait. Costs one
  reasoning call per character with candidates (≈ $0.002).
- the card's authority order is BOOK > KNOWN LOOK > ROLE > INVENTION.
  Run 7 (2026-09-05) drew Holmes at forty with a walrus moustache under a
  bowler, and the identity gate passed it: it compared the render to its
  own card, and the card was the invention. Silence in the text is not
  licence when the audience knows the face. `studio/canon.py` asks the
  `canon` tier (luna at `reasoning_effort: high` - at `none` three asks
  AGREED on a bearded, sandy, forty-five-year-old Watson) three times in
  the card's closed vocabulary, keeps each slot by majority reading, caches
  `refs/canon.json`, and `stated` fills the slots so the render OWES them.
  On a known face the IDENTITY slots (`facial_hair`, `hair`, `age`) are
  never invented, only `neutral` (clean-shaven, the plainest hair nobody
  has), and they are ASSERTED: the render owes them, no rung moves them,
  `adopt` does not rewrite them. Run 8 left them movable "if the pixels
  collide", Lestrade collided with Watson, and the rung made him seventy,
  white-haired and bearded; Watson's reroll drew grey on fair, bound
  BECAUSE it differed from Holmes, and `adopt` wrote the grey into every
  clip prompt. What is `taken` is what the reader would call the same
  (`cast_card.alike`: two moustaches are one reading); a rung moves only
  what the sheet can express (`RELIABLE`: hair colour and length, facial
  hair, headgear - never age, complexion or build); and a collision on
  anything else binds `accepted_as_written`. ≈ $0.02 a character, once
  per book.
- step 04 shipped `music_only` on runs 4, 5 and 6 ("no hook fits the first
  slot"): the delivered cue's troughs were 2.6 and 2.0 s and the best hook
  3.3 s. `rank` admits a line at twice the longest slot, `fits` refused it at
  the trough's edge, and `duck_bed` (08) keys a duck on every line for as
  long as it runs. `order_lines` now grants an overrun of one ducker release
  (`DUCK_OVERRUN`) to at most `MAX_DUCKS` lines (`test_run_6_troughs_hold_a_
  hook_that_ducks_and_a_short_threat`). Run 7 is the first with a voice line.
- step 03 has ended on the terminal `onset_grid` rung every run. Measured
  over the 16 Scarlet seeds (2026-09-04): every metre-grid seed scores
  `title_term` 0.3 and `slot_term` 0.4 - the struck-pulse captions produce
  no pre-title trough and no slot - while the one seed with both (1002,
  fitness 9.2) reads `bars_in_mode` 0.43. Its beats are 14% in mode and its
  bars come out 3 or 6 beats (a cue in 3, jittered pulse): folding half-bars
  lifts it to 0.77, but a jittered beat grid is not a grid to cut on. So the
  gate `fitness >= 6 AND grid == metre AND slots` has never been jointly
  satisfiable by this generator; the pick (1002) is the right trade and the
  fix is upstream: a caption/section sheet the generator obeys, or a tracker
  that reports beat regularity beside downbeat regularity. Both, measured
  2026-09-05 on the same 16 seeds: `Grid.of` re-votes downbeats along a
  steady beat (`beatmap.rebar`; four seeds the tracker had graded rubato by
  alternating 2- and 4-beat bars are metric, 6 -> 9 of 16), and the caption
  asks for the shape `title_term` grades - two full bars of silence, the
  impact by 95%, an eight-second decay - and holds the tempo instead of
  "the pulse doubles" (three metric seeds had read 175-201 BPM against 84).
  The seven seeds that obeyed the old Outro gave 1.5 s of silence against a
  3 s bar, which is what "one beat" asks for. Run 7 measures the new sheet.
  And "the pick (1002) is the right trade" was wrong once nine seeds were
  metric: `best_of` ranked on fitness alone, run 7 shipped 1002 on the onset
  grid and the QC read 0% of cuts on a downbeat. `best_of` now ranks a
  metric grid first, a slot second, fitness last - the order the gate
  grades - so an onset grid ships only when no seed counts.
- run 6 (2026-09-04) reached step 08 and died there, twice: the concat list
  held repo-relative paths that ffmpeg resolves against the list file's
  directory (`listing_lines`), and every take was `CLIP_SECONDS` while the
  plan's final hold outran it, so the cut started inside the reference leak
  and the picture came up 0.42 s short (`take_seconds`). Every learning also
  said `seconds: 0.0` -- `climb` now times each attempt. Run 6b's master
  then sat 45 KB over the Telegram Bot API's 50 MiB cap and step 10 sent it
  three times into a bare TLS EOF: `deliverable` now sends a CRF-20 copy
  when the master does not fit. Full account:
  `docs/analysis/research/trailer-retrospect.md`.
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
