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
  On a known face the IDENTITY slots (`facial_hair`, `hair`) are never
  invented, only `neutral` (clean-shaven, the plainest hair nobody has),
  and the card lists them as `neutral`: a third category beside asserted
  and free. A neutral slot is owed as NOTHING ADDED (`distinguish.ADDED`:
  grey, white, bald, long, any facial hair), never as its phrase; no rung
  moves it; what the render drew within that is adopted. Run 8 left them
  movable "if the pixels collide", Lestrade collided with Watson, and the
  rung made him seventy, white-haired and bearded; Watson's reroll drew
  grey on fair, bound BECAUSE it differed from Holmes, and `adopt` wrote
  the grey into every clip prompt. Asserting them instead refused three
  good brown-haired Watsons over the invented "fair" - a neutral phrase
  is a placeholder, not a fact about the man. What is `taken` is what the reader would call the same
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
  Run 9 shipped `music_only` a fourth time on a cue whose troughs held 1.7 s
  against a 2.5 s hook: the trough rule waits for silence the generator does
  not reliably write. A line now lives in a WINDOW, found (a trough) or
  made (a phrase of the grid the mix ducks under it, `made_slots`,
  `windows_of`); roles aim at an even share of the span (`targets`) and
  take the nearest window that holds them (`test_the_run_9_slate_is_not_
  music_only`). A refusal names what a LABEL can change - "no line is
  labelled hook", or "the shortest hook takes 3.3 s, the longest window
  holds 1.7 s; label shorter lines as hook" (`refusal`, `holds`) - because
  the labeller is the one who reads it, and every sheet it applied is kept
  at `work/labels-N.json`. Run 10 placed three lines and SPOKE one: a line
  nobody speaks ships as a text card, and `role_candidates` ranked two
  speakerless source quotes over Watson's spoken line because
  `shares_content_word` related them to the hook on "have" alone. A spoken
  line now outranks a card at every role after the hook (the card is the
  fallback for a role no spoken line fits, never a peer), and
  `FUNCTION_WORDS` (auxiliaries, determiners, prepositions of four letters
  and more) are not content (`test_a_spoken_line_outranks_a_card_at_every_
  role`, `test_an_auxiliary_is_not_a_content_word`). Replayed on run 10's
  own sheet: hook Holmes, answer Watson, both spoken; the threat stays a
  card because the sheet holds no spoken threat - the source pool's
  attribution is conservative by design and leaves many Holmes lines
  speakerless.
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
  And that order shipped run 9 on seed 2003 at 177.8 BPM against the 84
  asked: metric, four slots, fitness 4.4, and heard as "random music, too
  loud, not the tone". Nothing had compared the measured tempo to the asked
  one. The gate is now `grid == metre AND |bpm - asked| / asked <= TEMPO_BAND`
  (0.15, one tempo mark); `best_of` ranks metre, then tempo-error band, then
  fitness; `FITNESS_FLOOR` and the slot criterion are gone (a window is made
  from the grid now, see step 04); `reauthor` holds the register AND the
  tempo ("hold 84 BPM from first bar to last, not double it"); the terminal
  rung is `best_seed` and `ship` warns OFF TONE when it is. On run 9's own 16
  seeds the rule picks 3004 (100.9 BPM, band 1) and, no seed being within
  15% of 84, reauthors (`test_best_of_ranks_on_what_the_gate_grades_before_
  fitness`).
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
  0.3–2.5 — no seed cleared the then `FITNESS_FLOOR = 6.0`; the floor was
  the first number the retrospect moved, and after run 9 it is gone.
- the mix (08) normalised the bed to −14 LUFS and set nothing against it: a
  line rode at whatever level the voice model gave, and a quiet take was no
  key to the sidechain either. `level_lines` now measures the bed under each
  line's window (`bed_level`, silence left out) and the take's integrated
  loudness, and sets the take `LINE_OVER_BED` (8 LU) above the window before
  the duck (`line_gain`, bounded ±20 dB); the levelled takes are the duck's
  keys and are kept beside the master as `line-N.level.wav`
  (`test_a_quiet_take_still_rides_over_the_ducked_bed`, real ffmpeg). The
  mix writes `lines.level.json` (where each levelled line was laid) and QC
  fills `line_over_bed_lu` from it: each line's integrated loudness less
  the ducked bed under its window (`qc.line_over_bed`, target 5 LU; a run
  9 style master with no lines measures nothing rather than passing).
- QC graded every cut against the BEATS and read run 10 at 75% on beat: the
  walk cuts on every L0 event (`test_walk_cuts_on_every_L0_event`), the
  tracker places hits and stopdowns between beats, and 8 of the 13 "off"
  cuts sat on one; the intro shot before the first beat and the card over
  the tail had no pulse to be on. `qc.on_music` is the beats and the L0
  events together, `qc.graded` keeps only the cuts inside the span the grid
  covers, and `report` grades on those (`test_the_report_grades_on_the_
  music_over_the_pulse_it_has`). Run 10 re-measured: 0.90 on the music,
  0.43 on a downbeat or L0, two flags left - `cuts_on_L0` 0.53 (stutter
  stopdowns 0.5 s apart cannot each take a cut under `MIN_SHOT`) and the
  title at the cue's end where no downbeat falls.
- step 06 bound a beat on the SCENE's cast: any face in the scene's ninety
  seconds without a sheet refused the setup. Every Utah scene holds a Mormon
  or a hunter nobody sheets, so run 9 plated all six Utah beats and shipped
  nineteen Holmes-in-Baker-Street beats out of nineteen bound. A setup now
  carries `subjects` - who its own prose names, from the scene cast
  (`subjects_of`: whole names first, a shared surname credited to the sharer
  the prose does not name by their own token, all sharers when it names
  neither) - and `unbound`, `alternates` and `beat_of` bind on those. On
  the same 18 setups the old rule refused 15, the new one 6, all six
  substitutable; Utah binds on Hope and Ferrier (`test_a_shot_binds_on_who_
  it_names_not_on_who_is_in_the_scene`).

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
| 14 | windows: `made_slots`, `windows_of`, `targets`; actionable `refusal`; label sheets kept | `studio/trailer_dialogue.py`, `scripts/trailer/step_04_lines.py` | `test_the_run_9_slate_is_not_music_only`, `test_a_hook_that_fits_no_window_names_the_room` | [x] |
| 15 | tempo gate: `tempo_error`, `on_tone`, `best_of` on the gate's order, tempo-holding `reauthor`, terminal `best_seed` | `scripts/trailer/step_03_music.py` | `test_verdict_needs_a_metric_grid_on_the_asked_tempo`, `test_best_of_ranks_on_what_the_gate_grades_before_fitness` | [x] |
| 16 | line levelling before the duck: `integrated`, `bed_level`, `line_gain`, `level_lines`; `lines.level.json`; QC `line_over_bed` | `studio/trailer_assemble.py`, `scripts/trailer/qc.py` | `test_a_quiet_take_still_rides_over_the_ducked_bed` (real ffmpeg), `TestLineOverBed` | [x] |
| 17 | subject binding: `subjects_of`, `TrailerBeat.subjects`, `unbound`/`alternates` on the frame not the scene | `studio/trailer_story.py`, `scripts/trailer/step_06_plan.py` | `test_a_shot_binds_on_who_it_names_not_on_who_is_in_the_scene`, `TestSubjectsOf` | [x] |
| 18 | a spoken line outranks a card at every role; `FUNCTION_WORDS` are not content | `studio/trailer_dialogue.py` | `test_a_spoken_line_outranks_a_card_at_every_role`, `test_a_card_is_placed_when_no_spoken_line_fits` | [x] |
| 19 | QC grades on the music: `on_music` (beats + L0), `graded` (inside the pulse only) | `scripts/trailer/qc.py` | `test_a_cut_on_a_stopdown_or_hit_is_on_the_music`, `test_cuts_where_the_grid_has_no_pulse_are_not_graded` | [x] |
| 20 | the step banner is printed AFTER the step opens (run 10: `−199 min left` at 08 was 07's clock) | `trailer.py` | `test_the_banner_reads_the_budget_of_the_step_it_opens` | [x] |
| 21 | one take, one shot: `one_each` replaces `best_scatter` in `shots_for`; `TrailerPlan._one_take_per_shot` | `studio/trailer_order.py`, `studio/trailer_spec.py`, `scripts/trailer/build_plan.py` | `test_every_beat_plays_once_in_story_order`, `test_a_beat_used_twice_is_refused`, `test_every_shot_has_its_own_setup` | [x] |
| 22 | the render sizes the plan: `RENDER_SECONDS = 16 min` (run 10, measured), `affordable_takes`, `fit_points`, `agree` | `scripts/trailer/step_07_clips.py`, `scripts/trailer/step_06_plan.py` | `test_the_takes_are_what_step_07_can_afford`, `test_the_walk_is_shortened_until_its_cuts_fit_the_takes`, `test_agree_trims_the_beats_to_the_cuts_it_fitted` | [x] |
| 23 | the title lands only where the picture reaches: `music_of(metre, ends)`; line windows filtered by `inside` | `scripts/trailer/step_06_plan.py` | `test_a_picture_that_stops_short_has_no_title_moment`, `test_lines_are_windowed_into_the_slots` | [x] |
| 24 | a promoted clip is identifiable: `fresh`, `stored_fingerprint`, `promote` copies the sidecar, `clip_record` carries the fingerprint | `studio/clip_cache.py`, `scripts/trailer/step_07_clips.py` | `test_a_clip_left_over_from_an_earlier_plan_is_not_fresh`, `test_the_recipe_travels_with_the_take` | [x] |
| 25 | the cut reads only fresh clips of THIS plan: `takes_for`, `clips_doc`; no resolver, no glob | `scripts/trailer/assemble.py` | `test_a_clip_left_over_from_an_earlier_plan_refuses_the_cut`, `test_a_beat_with_no_clip_refuses_the_cut` | [x] |
| 26 | a missing, capped or stale take shortens the trailer: `usable` + `step_06_plan.refit` | `scripts/trailer/step_08_assemble.py`, `scripts/trailer/step_06_plan.py` | `test_a_missing_take_shortens_the_cut_instead_of_borrowing_one`, `test_refit_keeps_only_the_takes_that_exist_in_plan_order` | [x] |
| 27 | QC proves the rule on the delivered master: `reused_shots` and `stale_shots` in the floor | `studio/trailer_stage_spec.py`, `scripts/trailer/qc.py` | `test_a_repeated_take_fails_the_floor`, `test_a_shot_cut_from_a_stale_clip_fails_the_floor` | [x] |
| 28 | `PLATE` says what IS in frame; no negation reaches an image model | `scripts/trailer/step_06_plan.py` | `test_rung_beats_substitutes_then_plates` | [x] |
| 29 | story spine: `Movement` M1/M2/M3 on every beat, `movement_quota` 25/45/30 %, `identity_scenes` after `late_floor`, `select_by_movement`, `arc_of(movement, last)` | `studio/trailer_story.py`, `studio/trailer_plan.py`, `studio/trailer_spec.py` | `test_the_movements_play_in_order`, `test_the_answer_never_plays_before_three_quarters`, `test_three_movements_always_reach_a_climax` | [x] |
| 30 | every line on its speaker's face: `face_in_movement`, `speak_on_face`, `lay`; the picture swaps, never the line; `lines_refused` recorded | `scripts/trailer/step_06_plan.py` | `test_the_step_lays_every_line_on_its_speaker`, `test_the_line_is_never_moved_only_the_picture`, `test_the_swap_stays_inside_the_movement` | [x] |
| 31 | ranker by function: `KEPT_BONUS`/`BOLD_BONUS` 2.0/1.0, `WHERE_WEIGHT` book > author > character, `quota_fill`, `thesis_card`; `drop_story_rules` before `music_only` | `scripts/trailer/step_04_lines.py`, `studio/trailer_dialogue.py` | `test_the_aphorisms_no_longer_own_the_window`, `test_the_books_own_threat_reaches_the_labeller`, `test_every_role_has_something_to_label` | [x] |
| 32 | thesis never null: `clauses`, `thesis_from` takes the shortest accepted clause on the retry | `scripts/trailer/step_01_story.py` | `test_eight_syllables_then_six_is_taken_on_the_retry`, `test_three_over_long_answers_still_ship_a_refrain` | [x] |
| 33 | `MAX_LINES` derived (12 per 100 s over the pinned cue = 13, not 4); `roles_for(budget)` alternates answer/threat in the middle; budget bounded by the lines offered | `studio/trailer_stage_spec.py`, `studio/trailer_dialogue.py` | `test_the_ceiling_is_a_dialogue_led_cue_at_the_pinned_length`, `test_a_longer_cut_alternates_answer_and_threat_in_the_middle`, `test_the_lines_offered_bound_the_budget` | [x] |
| 34 | sound chain: `LIMITING_DB` 2.0, `BED_TP`/`LINE_TP` at the source, `level_line` through alimiter, precomputed full-band duck (20 ms attack, 150 ms lookahead, 800 ms release, `BED_UNDER_LINE` -24) | `studio/trailer_assemble.py`, `scripts/trailer/assemble.py` | `test_the_limiter_only_catches_what_the_headroom_missed`, `test_it_is_already_at_full_depth_when_the_line_starts`, `test_the_pulse_and_the_air_duck_too` | [x] |
| 35 | the title is a made shape: `PRE_TITLE_SILENCE` 2.2, hard out on a downbeat, `sfx.room_tone` under the silence, `riser`, `FINAL_HOLD` 4.5; QC `hard_out`, `pre_title_silence_s`, `title_hit_lu` | `studio/trailer_cut.py`, `studio/sfx.py`, `scripts/trailer/qc.py` | `test_the_hit_lands_after_a_held_silence`, `test_a_fade_is_not_a_hard_out`, `test_the_card_never_shrinks_below_the_final_hold` | [x] |
| 36 | QC measures SHAPE: `music_only_fraction`, `speech_occupancy` vs `speech_target`, `peak_position`, `act3_over_act2_lu`, line TP/flat/crest, `on_beat_by_act`; `cuts_on_beat_act1` <= 0.5, `_act3` >= 0.8; `act_caps_of` | `studio/trailer_stage_spec.py`, `scripts/trailer/qc.py` | `test_the_report_carries_a_measured_shape_and_flags_what_it_missed`, `test_an_act_one_shot_is_measured_against_its_own_act_s_cap`, `test_the_peak_position_is_a_fraction_of_the_picture` | [x] |
| 37 | cut rhythm by act: `ACT_BANDS`, `ACT_BARS` 1.40/0.80/0.44, nine-shot `FIGURE`, `BEAT_LOCK` 0.66 with `off_grid` in acts 1-2, `ACT_CAPS`, `HOLD_MIN` 3.0 | `studio/trailer_edit.py` | `test_the_acts_shorten_the_shots`, `test_acts_one_and_two_do_not_ride_the_beat`, `test_the_climax_rides_the_beat`, `test_no_four_shots_in_a_row_are_the_same_length` | [x] |
| 38 | render in rounds: `bind_for` -> `render_round` -> `read_round` -> `settle_round`; H3 resident through a round, one reader session per round; `learn_cycle` writes gate=`cycle`; `render_seconds(rows)` is the measured median, the constant only until measured; step 06 sizes the plan from it | `scripts/trailer/step_07_clips.py`, `scripts/trailer/step_06_plan.py`, `studio/ladder.py` | `test_the_takes_of_a_round_are_rendered_before_any_of_them_is_read`, `test_every_round_learns_what_a_take_cost_it`, `test_with_nothing_measured_the_cycle_is_the_constant`, `test_a_measured_cycle_resizes_the_plan` | [x] |
| 39 | frames per shot: `take_seconds = shot + HEAD_TRIM + HANDLE`, `frames_of` samples past the head leak, `FAST_INSERTS` off until one 4-step take is measured | `scripts/trailer/build_clips.py`, `scripts/trailer/step_07_clips.py` | `test_frames_of_samples_three_stills_outside_the_head_leak` | [x] |
| 40 | step 08 settles: `settle(ctx)` re-fits until `usable == plan shots` in `SETTLE_PASSES`, else refuses | `scripts/trailer/step_08_assemble.py` | `test_a_refit_that_lengthens_a_capped_shot_is_fitted_again`, `test_a_walk_that_never_settles_is_refused` | [x] |
| 41 | the title look-back is the grid's own: `look_back_of(metre)` = two bars and a beat | `studio/beatmap.py` | `test_the_look_back_is_two_bars_and_a_beat`, `test_metre_of_looks_back_by_its_own_grid` | [x] |
| 42 | no negation reaches any model: `studio/affirm.py` lint over `studio scripts`; all six trailer workflows use `ConditioningZeroOut` | `studio/affirm.py` | `uv run python -m studio.affirm --scan studio scripts` exits 0 | [x] |
| 43 | the cue's measured spans ARE the shot list: `CueSpan`/`CueSection`/`CuePlan` contract (contiguous, section starts are cuts, sustain >= `SUSTAIN_BARS`, accent <= a beat, movements ordered, `hard_out` opens the tail, no two sustains adjacent); `CueAsk.for_bars` derived from bars by the story quota | `studio/cue_plan.py` | `test_spans_cover_the_cue_without_gaps`, `test_a_section_start_that_is_not_a_cut_is_refused`, `test_movements_never_run_backwards`, `test_an_ask_is_bars_split_by_the_story_quota` | [x] |
| 44 | cut-opportunity map: Foote novelty sections (kernel clip(s/6, 12, 24)), 8 s phrases, 2 s level steps >= 6 dB, dropout spans, swells, top-10 % accents, `snap` +-0.6 s to the grid, `merge` 0.3 s, hold spans, hard outs; `CutMap` JSON with rank 3/2/1 | `studio/music_events.py` | synthetic-signal suite: tone join -> one boundary, +8 dB -> one lift, click train -> accents 85 % on-beat, silence -> dropout | [x] |
| 45 | `spans_of(cut_map, metre)`: cut on every rank >= 2 event, hold otherwise; `plan_of`; `plan_fit` drops accents latest first, merges phrases inside a section, never touches a sustain or trough, else `ShorterCue(bars)` | `studio/cue_spans.py` | `test_every_rank_two_event_is_a_cut`, `test_fit_never_touches_a_sustain`, `test_fit_refuses_with_the_bars_it_needed` | [x] |
| 46 | frames first: `take_frames = legal_frames(24 * (shot + 2.85))`, `Cycle(a, b)` fitted from gate=`cycle` rows carrying `frames`, typed `b` 2.49 s/frame until measured; `affordable_frames` keeps `RETRY_RESERVE`; `cue_seconds_for` -> `bars_for` sizes the ask | `studio/frame_budget.py` | `test_longer_shots_are_cheaper_per_picture_second`, `test_two_frame_counts_fit_a_line`, `test_a_sixty_second_trailer_fits_the_share` | [x] |
| 47 | the ask in the model's grammar: register table (nine rows), `ask_for(tone, bars)`, `caption_from(ask, tone)` affirmative only and inside `CAPTION_WORDS`, `verify` fills `measured` within `SECTION_TOL`, `plan_score` weights stop and title 2x, `synth_from_ask` fixture | `studio/cue_ask.py` | `test_the_caption_is_affirmative_only`, `test_verify_fills_measured_from_the_synth`, `test_an_event_a_bar_late_still_matches_and_two_bars_late_does_not` | [x] |
| 48 | the cue is edited, never stretched: `slice_bars`, `splice` (equal-power, beat/2 or 10 ms on a hit), `splice_out`, `repeat_bars`, `hole`, `stop_at`, `section_gains`, `compatible`, `conform`; `conform` rung in step 03 before reauthor; the grid layer (`Recut`, `bars_covering`, `remove_bars`, `conform_bars`, `hole_bars`) edits by bar index for step 08; the derived `Recut.metre` is a grid, not a re-measurement | `studio/cue_edit.py` | `test_splicing_out_a_bar_shortens_the_cue_by_a_bar_and_keeps_the_downbeats_on_the_grid`, `test_a_join_on_a_hit_is_ten_milliseconds` | [x] |
| 49 | step 03 asks for what the frames afford: `bars_for(affordable)` -> `CueAsk` -> caption; `best_of` ranks by `plan_score`; `ship` writes `music/plan.json` (a `CuePlan`, fitted to the frames); `ShorterCue` shrinks the next ask, a shorter ask retires the longer cues; a hold longer than a take is cut on the grid | `scripts/trailer/step_03_music.py` | `test_the_ask_is_sized_from_the_budget`, `test_the_best_cue_is_the_one_whose_events_landed`, `test_a_cue_that_offers_too_many_spans_is_asked_for_shorter` | [x] |
| 50 | step 04 windows are the plan's troughs and sustains (`windows_of(plan)`), each line ends >= 1 beat before its span ends; `studio/line_windows.py` (`load_plan`, `windows_for`, `beat_for`); metre windows are the fallback when no plan shipped | `scripts/trailer/step_04_lines.py` | `test_a_line_window_is_a_trough_or_a_sustain`, `test_a_line_ends_a_beat_before_the_span` | [x] |
| 51 | step 06 fills spans, invents no cut: `shots_from_spans`, grammar per kind (section = widest frame + reveal on the downbeat; sustain 5-10 s = one move + three timed actions + `speaker_mode`; phrase = one fact; accent = insert, no bound face; trough = static answer), `counts_by_movement`, `fit_to_frames` via `plan_fit`; `ShotSpec` gains `span_kind`, `movement`, `move`, `actions[TimedAction]`, `speaker_mode`, `reveal_at`, `binds_face`; `plan.json` carries `path` (spans|walk) and `spans`; the walk is the fallback when no plan shipped; `refit_spans` re-zips beats to folded spans until row 53 settles properly | `scripts/trailer/step_06_plan.py`, `studio/shot_grammar.py` | `test_every_shot_is_a_span_and_every_span_is_a_shot`, `test_a_sustain_carries_one_move_and_three_actions`, `test_an_accent_never_carries_a_bound_face`, `test_the_reveal_arrives_on_the_downbeat` | [x] |
| 52 | step 07 renders frames, learns frames: `learn_cycle` rows carry `frames`; round 1 includes one 243-frame take so `b` is measured; `Cycle.from_rows` replaces `render_seconds`; `LONG_TAKE` 243, `take_cost`/`retry_cost`/`ladder_for` priced per frame off the fitted `Cycle`, one `cycle` row per fresh take; `render_seconds_for` kept as a legacy hook for step 06's walk path | `scripts/trailer/step_07_clips.py` | `test_every_cycle_row_carries_its_frames`, `test_round_one_measures_a_long_take` | [x] |
| 53 | step 08 settles like an editor: a lost accent is absorbed by its predecessor, a lost phrase or sustain is `splice_out` of the cue and the plan re-derived, a lost button moves `hard_out`; each pass removes >= 1 span | `scripts/trailer/step_08_assemble.py` | `test_a_lost_accent_is_absorbed_by_the_shot_before_it`, `test_a_lost_sustain_is_cut_out_of_the_music`, `test_every_settle_pass_removes_a_span` | [ ] |
| 54 | QC grades the cut against the cue: `cuts_on_events` >= 0.90, floors `section_changes_cut` 1.0, `cuts_inside_sustain` 0, `long_shots_on_sustains` 1.0, `lines_in_troughs` 1.0; `accents_cut`, `movement_medians_s`, `frames_rendered`/`frames_played`; `cuts_on_beat_act1` and `on_cap_fraction` retired; `cue_qc.py` is pure, `qc.measure_cue` reads `music/plan.json` + the chosen seed's `music/cutmap-{seed}.json`; unmeasured when no plan | `studio/trailer_stage_spec.py`, `scripts/trailer/qc.py` | `test_a_section_change_the_picture_missed_fails_the_floor`, `test_a_cut_inside_a_sustain_fails_the_floor`, `test_the_report_counts_frames_rendered_against_frames_played` | [x] |
| 55 | the walk is gone: `ACT_BARS`, `FIGURE`, `BEAT_LOCK`, `ACT_CAPS`, `walk` removed from `trailer_edit`; `MusicBed.sections` are the measured `CueSection`s, `cuts` are span starts | `studio/trailer_edit.py`, `studio/trailer_spec.py` | `test_the_bed_carries_measured_sections`, no test imports the walk | [ ] |
| 56 | the short is bar blocks of the verified long cue: `conform(keep_bars)` from `CuePlan.sections`, one render, two lengths | `scripts/trailer/step_03_music.py`, `studio/cue_edit.py` | `test_the_short_is_whole_bars_of_the_long_cue` | [ ] |

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
