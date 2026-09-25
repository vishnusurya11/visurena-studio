# Judges replace the eye — build

**Status:** DONE 2026-09-24 ( the owner delegated: "remove them. We should
automate them all, using agents or existing ComfyUI models. Fix all of them.")

**Decision:** [../decisions/2026-09-24_judges_replace_the_eye.md](../decisions/2026-09-24_judges_replace_the_eye.md)
(`2026-09-24-automate-the-taste-gates`; `docs/DECISIONS.md` entry of the same date). Implements §3 of
`architecture/decisions/2026-09-24_future_departments.md` as amended: no refs or
episode step parks on a human; the owner audits after the fact.

**Done means:** `gates.yaml` at the repo root names a judge for every refs and
episode gate with `state: auto` and a decision id, and a test says so; no
`Escalation` is raised anywhere under `scripts/refs/` or `scripts/episode/` (a test
greps); every gate's substep runs a judge, climbs a priced ladder under the episode
ceiling, and ends in `pass` or `flagged` — never a park, never a silent pass; every
terminal rung writes a flagged verdict, a learning and an audit-sheet row;
`library/<book>/casebook/` holds the harvested labels and the owner overlay;
`studio/judge_bench.py` reports recall on owner catches, false refusals and flag
rate per judge into `docs/calibration/<judge>.md` with a committed baseline; the
ratchet test refuses a commit that loses a catch; `scripts/audit/sheet.py` builds
the audit page and no step reads it; the Future tab draws judges in the line and the
bench in Platform; the suite is green at every commit; no test touches ComfyUI, a
model, or a paid API (recorded fixtures and synthetic pictures only).

## Rules for every commit

- Tests first, named below; functions 10-20 lines, one thing each.
- No GPU, no model, no credit in a test: `tests/conftest.py` monkeypatches
  `studio.comfy.run_text` and `studio.comfy.run` to raise `RuntimeError("a test
  reached ComfyUI")`; judges take `reader=` / `run=` / `model=` callables.
- Fixtures are recorded outputs (DWPose JSON, GroundingDINO boxes, EasyOCR results,
  embedding vectors, `panel_content.json` rows, `T??.dq.json` rows) with book ids
  scrubbed, or synthetic pictures drawn in the test with PIL / numpy.
- Every dependency pinned `==`; every `uv add` followed by `uv sync --all-groups`.
- Book-neutral code tree: no book, character, episode or take name outside
  `library/` and `docs/calibration/`.

## Commits

### Group 1 — calibration ledger, harvest, bench, ratchet

- [x] **C0 plan + decision** — this file under `architecture/plan/`; the decision
  file; the `docs/DECISIONS.md` entry; `architecture/README.md` index line. Docs only.

- [x] **C1 the casebook** — ~180 lines, 6 tests.
  Tests first: `tests/test_a_casebook_row_names_a_class_from_the_closed_list.py`,
  `test_an_unverified_row_is_not_counted.py`, `test_an_owner_row_outweighs_a_default_row.py`,
  `test_a_harvested_line_becomes_a_candidate_row.py`,
  `test_a_timestamp_resolves_to_its_take_through_placed.py`,
  `test_the_owner_overlay_is_append_only.py`.
  Files: `studio/casebook.py` (`Row` pydantic model: codex, unit, kind, path, sha8,
  verdict, fault_class, verdict_by, verdict_at, after_publish, source, region,
  machine, machine_version; `CLASSES` closed list from D §2; `load`, `append_owner`,
  `weight`); `scripts/calibration/harvest_labels.py` (regex over prose sources +
  the machine json beside each artefact -> `library/<book>/casebook/labels.jsonl`;
  timestamps resolved through `placed.json`; attempts re-judged with
  `take_dq.main(attempts=True)` behind an injectable runner).
  Fixtures: `tests/fixtures/casebook/{story_snippet.md, placed.json, dq_rows.json}`.

- [x] **C2 bench, synthetic negatives, ratchet** — ~280 lines, 9 tests.
  Tests first: `test_a_judge_that_refuses_nothing_has_zero_recall.py`,
  `test_a_judge_that_refuses_everything_has_full_false_refusals.py`,
  `test_recall_carries_a_wilson_interval.py`, `test_misses_name_paths_not_content.py`,
  `test_a_synthetic_row_counts_in_its_own_column.py`,
  `test_the_report_lands_beside_the_judges_calibration_doc.py`,
  `test_a_pasted_word_is_a_lettering_fault.py` (synthetic generator only),
  `test_two_panels_tiled_are_a_stacked_fault.py`,
  `test_a_judge_may_not_lose_a_catch.py` (the ratchet: globs `library/*/casebook/`,
  skips when absent, compares to `docs/calibration/bench/<judge>.json`).
  Files: `studio/judge_bench.py` (`load_rows`, `run`, `confusion`, `recall`,
  `false_refusals`, `flag_rate`, `misses`, `report`, `main`); `studio/judges/__init__.py`
  + `studio/judges/registry.py` (names -> wrappers over `take_zoom.judge`,
  `face_end.verdict`, `take_look.verdict`, `panel_dq.verdict`,
  `panel_content_check.judge`, `take_verdict.gates`, reading stored json, never
  decoding video); `studio/synth_faults.py` (paste text, duplicate a crop, tile two
  panels, draw a gutter, re-save a reference); `scripts/calibration/bench.py`;
  `docs/calibration/bench/` (baselines written by the bench, committed).
  Fixtures: `tests/fixtures/judge_bench/{labels.jsonl, owner.jsonl, baseline.json}`.

### Group 2 — the judge contract, the policy file, signed_by

- [x] **C3 `Verdict` and the three signatures** — ~150 lines, 7 tests.
  Tests first: `test_a_judge_signs_a_pass_or_a_flag_never_a_fault.py`,
  `test_a_flagged_verdict_lets_the_next_step_run.py`,
  `test_a_fault_file_is_still_refused_by_require.py`,
  `test_the_owner_path_is_unchanged_by_the_signer.py`,
  `test_a_judge_never_waives_it_flags.py` (eye_review: an `n` with `flagged_by`
  clears; an `n` with neither does not), `test_confidence_is_a_count_of_reads.py`,
  `test_a_summary_is_never_empty.py`.
  Files: `studio/judges/verdict.py` (`Fault`, `Verdict`, `signer`, `summary`);
  `studio/eye_verdict.py` (`VERDICTS` gains `flagged`; `passed`; `sign(signed_by=,
  faults=, terminal=)`; `sign_verdict`); `studio/plan_verdict.py` (`sign(signed_by=,
  faults=, flagged=)`); `studio/refs_verdict.py` (same); `scripts/episode/eye_review.py`
  (`refusals` accepts `flagged_by`; `flags()`); `studio/youtube_publish.py` (flags
  recorded beside waivers in `uploads.jsonl`); `tests/conftest.py` (the ComfyUI trap).

- [x] **C4 `gates.yaml`, policy, `judged_gate.clear`, audit rows, the ceiling** — ~240 lines, 10 tests.
  Tests first: `test_every_refs_and_episode_gate_is_auto_with_a_decision.py`
  (and the decision slug is a heading in `docs/DECISIONS.md`),
  `test_an_auto_row_without_a_decision_id_is_refused.py`,
  `test_a_shadow_judge_writes_a_sidecar_and_signs_nothing.py`,
  `test_clear_on_a_pass_signs_with_the_judge_name.py`,
  `test_clear_on_a_fault_returns_to_the_ladder_and_writes_no_file.py`,
  `test_a_terminal_rung_writes_a_flag_a_learning_and_an_audit_row.py`,
  `test_no_step_reads_the_audit_rows.py` (greps `scripts/refs`, `scripts/episode`),
  `test_a_ladder_that_cannot_afford_takes_the_terminal_rung.py`,
  `test_the_episode_ceiling_is_five_hours_in_shares.py`,
  `test_render_is_registered_auto_with_the_build_decision.py`.
  Files: `gates.yaml`; `studio/gate_policy.py` (`Policy`, `load`, `of`, `STATES`);
  `studio/judged_gate.py` (`clear(ctx, gate, judge, sign, ladder, terminal)`);
  `studio/audit_rows.py` (`append(book_dir, row)`); `studio/episode_run.py` (ctx gains
  `learn`, `learnings_path`, `budget`, the port of `trailer_run.py:36-41`);
  `studio/run_budget.py` (`EPISODE_CEILING_SECONDS = 18000`, `EPISODE_SHARES` incl.
  `judges`, `ladders`); `scripts/episode/step_09_shoot.py` (the flag replaced by the
  policy row + `can_afford`).

### Group 3 — picture judges

- [x] **C5 measures: keypoints, boxes, copy, OCR, faces, gutter thirds** — ~420 lines, 12 tests.
  Tests first: `test_a_hat_on_a_head_is_worn_and_at_a_wrist_is_held.py`,
  `test_a_handed_back_reference_is_a_copy.py` (pHash <= 10; SSIM corroborates a crop),
  `test_a_gutter_that_stops_at_a_figure_is_still_a_gutter.py` (thirds),
  `test_a_torso_past_sixty_degrees_is_lying.py`,
  `test_ankles_in_frame_is_not_a_medium_close.py`,
  `test_a_third_wrist_is_an_extra_limb.py`,
  `test_two_faces_that_read_as_one_man_are_a_clone_pair.py` (cosine >= DRIFT),
  `test_a_small_face_uses_the_structural_prefilter.py`,
  `test_a_cast_id_in_the_lettering_is_a_leak.py`,
  `test_a_box_without_a_recognised_string_is_not_lettering.py`,
  `test_a_landmark_the_setup_lacks_is_invented.py`,
  `test_a_take_uses_the_style_it_was_bound_to.py` (the identity observe: MATCH /
  STRANGER / DRIFT from injected vectors; `identity_gate.ARMED = True`).
  Files: `studio/measure/keypoints.py` (DWPose JSON -> posture family, shot size,
  limb counts, wrists), `studio/measure/boxes.py` (GroundingDINO -> worn/held hats,
  landmark words vs `place_text`), `studio/measure/copy.py` (pHash, SSIM in numpy,
  reuse of `edit_gate.py:145`), `studio/measure/ocr.py` (EasyOCR wrapper + the
  string judge: cast id, plan word, gibberish), `studio/measure/faces.py` (facenet
  embed, pairwise clones, `identity_gate.observe`), `studio/panel_dq.py`
  (`stacked` by thirds; the measured number recorded in `content_gate.md`);
  workflow files `image_dwpose_keypoints.json`, `image_groundingdino_boxes.json`,
  `image_embed.json` + manifests in the sibling `comfy_studio` workflows folder
  (`studio/comfy.py:19`), called through `comfy.run_text`.
  Deps: `torchvision==0.29.0`, `facenet-pytorch==2.6.0` (no-deps), `easyocr==1.7.2`;
  then `uv sync --all-groups`; a test asserts the lock still carries `music` and `voice`.
  Fixtures: `tests/fixtures/measures/{dwpose_*.json, gdino_*.json, ocr_*.json,
  faces_*.npy}`; synthetic panels drawn in-test.

- [x] **C6 `panel_eye`, the panel ladder, the layout rule; step 07 and 08 rewired** — ~320 lines, 10 tests.
  Tests first: `test_a_setup_lays_out_into_grids_of_at_most_nine.py`
  (5 -> 3 + 2; 7 -> 4 + 3; `cols x rows == shots`), `test_a_board_never_parks_for_a_layout.py`,
  `test_rows_become_faults_with_a_where.py`, `test_an_unread_close_is_a_fault_an_unread_wide_is_not.py`,
  `test_a_panel_fault_climbs_seed_then_reprose_then_flags.py`,
  `test_a_reprose_never_touches_a_timing_input.py` (`placed.json` stays current),
  `test_a_third_climbing_grid_is_kept_best_and_flagged.py`,
  `test_the_panel_eye_signs_flagged_with_its_faults_listed.py`,
  `test_the_size_read_is_a_second_vote_never_the_wall.py`,
  `test_step_08_raises_no_escalation.py`.
  Files: `studio/grid_layout.py`; `scripts/episode/step_07_board.py` (writes
  `layout.json` by rule; the raise removed); `studio/judges/panel_eye.py`;
  `studio/panel_ladder.py` (`redraw_grid_seed`, `reprose` from a cure table,
  `superseded/`, cap 2); `scripts/episode/step_08_panels.py` (`judged_gate.clear`
  between `panel_contact.write` and the old `require`).
  Fixtures: `tests/fixtures/vlm/{panel_content_rows.json, size_reads.json}` (one
  malformed answer must raise `Unreadable`).

- [x] **C7 `look`, the sheet ladder; refs/04 rewired** — ~220 lines, 7 tests.
  Tests first: `test_a_sheet_missing_a_must_noun_is_redrawn_state_first.py`,
  `test_two_sheets_that_read_as_one_face_are_bound_flagged_lookalikes.py`,
  `test_a_lettered_sheet_is_refused.py`, `test_a_style_outlier_is_flagged_never_refused.py`,
  `test_a_pack_signs_itself_when_every_row_passes.py`,
  `test_a_stale_pack_judges_only_its_new_rows.py`, `test_step_04_raises_no_escalation.py`.
  Files: `studio/judges/look.py` (trait card + facenet + `look_back` MUST nouns +
  OCR + limbs + DINOv3 outlier vs the pack's place pictures); `studio/sheet_ladder.py`;
  `scripts/refs/step_04_verdict.py` (both raises replaced).
  Fixtures: `tests/fixtures/vlm/trait_cards.json` (distances 0, 2, 3, 4; one
  unverifiable), `tests/fixtures/measures/style_vectors.npy`.

### Group 4 — take judges

- [x] **C8 measures: flow, rotation, leak, refs-only board, cut vote, mouth** — ~340 lines, 9 tests.
  Tests first: `test_scenery_that_slides_through_a_held_man_is_a_pass_through.py`
  (synthetic: a translating background with a fixed patch),
  `test_a_world_that_turns_round_a_fixed_face_is_a_rotation.py` (synthetic rotation),
  `test_a_walker_the_camera_tracks_is_not_a_pass_through.py` (eligibility kept),
  `test_a_leak_is_measured_from_the_pictures_that_were_staged.py`,
  `test_heads_json_is_written_from_the_measured_leak.py`,
  `test_a_refs_only_take_is_still_judged_against_its_panel.py`,
  `test_a_second_vote_on_a_cut_needs_two_of_three.py`,
  `test_an_unreadable_mouth_cannot_tell.py`, `test_a_lag_row_reports_frames_not_a_feeling.py`.
  Files: `studio/measure/flow.py` (DIS, 4-parameter RANSAC fit with theta, warp
  residual), `studio/take_lock.py` (DIS + face band; `fitted_on`), `studio/take_zoom.py`
  (`cum_theta`), `studio/take_leak.py` (first 12 frames vs every staged picture ->
  `heads.json`), `studio/take_coherence.py` (`last_vs_cell` from `storyboard/shot_NN.png`),
  `studio/measure/cuts.py` (scenedetect vote), `studio/measure/mouth.py` (FaceMesh
  aperture -> `av_sync.lag_seconds`).
  Deps: `scenedetect==<resolved, pinned>`, `mediapipe==<resolved, pinned>`; `uv sync --all-groups`.
  Fixtures: numpy-generated frame sequences; `tests/fixtures/flow/{take_dq_rows.json,
  lag_arrays.json}`.

- [x] **C9 `take_eye`, the take ladder, the still; step 09 rewired** — ~380 lines, 11 tests.
  Tests first: `test_a_stochastic_row_gets_one_seed_then_the_cause_rung.py`,
  `test_a_row_that_repeated_on_a_fresh_seed_skips_the_seed.py`,
  `test_a_lag_row_never_takes_a_seed.py`, `test_a_length_just_changed_is_restored_before_shortened.py`,
  `test_a_replan_edits_the_cell_never_the_timing.py`,
  `test_a_narration_shot_with_a_hard_content_fault_becomes_a_still.py`,
  `test_a_still_keeps_its_placed_seconds.py`, `test_two_stills_are_never_adjacent.py`,
  `test_a_dialogue_shot_is_kept_best_and_flagged_high_never_a_still.py`,
  `test_a_round_of_one_is_refused_unless_last.py`, `test_step_09_raises_no_escalation.py`.
  Files: `studio/judges/take_eye.py` (dq + content + identity + clones + pass-through
  + rotation + leak + board + cut vote + mouth; FRAMING and ACTION names added to
  `take_content.ASK`); `studio/take_ladder.py` (rungs from F §2; the cause ->
  substitute-move map read from `docs/calibration/camera_catalog.md` phrasings);
  `scripts/episode/assemble.py` (the still substitute: panel held for its seconds
  with a slow push, ffmpeg injectable); `scripts/episode/step_09_shoot.py`.
  Fixtures: `tests/fixtures/flow/take_dq_rows.json`, `tests/fixtures/vlm/take_content_rows.json`,
  `tests/fixtures/clock/timing_ep.jsonl`.

### Group 5 — plan critic

- [x] **C10 G-MOVES and G-SOURCE** — ~160 lines, 6 tests.
  Tests first: `test_fewer_than_eight_moves_is_a_refusal.py`,
  `test_one_move_on_a_quarter_of_the_shots_is_a_refusal.py`,
  `test_the_same_move_twice_running_is_a_refusal.py`,
  `test_the_orbiting_plan_fails_and_the_varied_plan_passes.py` (fixture lock on two
  scrubbed move lists), `test_a_count_without_a_chapter_span_is_invented.py`,
  `test_a_span_must_be_found_in_the_chapter.py`.
  Files: `studio/plan_gates.py` (`G-MOVES` classifier over the camera head via
  `episode_ref_official.camera_clause`; `G-SOURCE` fuzzy match), `studio/episode_spec.py`
  (`Shot.source: list[str] = []`, required with `extras > 0`, a posture word or a
  prop id), `scripts/episode/plan_check.py`.
  Fixtures: `tests/fixtures/episodes/moves_{orbit,varied}.json`, a chapter snippet.

- [x] **C11 `plan_reader` critic; step 02 rewired** — ~300 lines, 9 tests.
  Tests first (FakeModel returns a canned `PlanReading`):
  `test_the_critic_lists_and_the_code_judges.py`,
  `test_a_turn_with_no_two_people_is_a_story_fault.py`,
  `test_a_silent_drop_of_a_timeline_row_is_refused.py`,
  `test_a_claim_without_a_span_is_invented.py`,
  `test_the_critic_fails_the_known_bad_and_passes_the_known_good.py` (the known-bad
  and known-good scrubbed plan fixtures, with canned readings; else advisory),
  `test_a_battery_refusal_is_never_signed_the_unit_is_deferred.py`,
  `test_critic_faults_end_in_the_best_draft_flagged.py`,
  `test_a_structured_output_exception_retries_once.py`, `test_step_02_raises_no_escalation.py`.
  Files: `agents/plan_reader.py` + `agents/skills/plan_reader.md` (Strands,
  `structured_output_model=PlanReading`, a family other than the writer's, plain-text
  plan with `why`/`turn`/`section` stripped, k=3 on turn and claims); `studio/judges/plan.py`;
  `studio/plan_ladder.py` (`improve` x2, `fresh_brief` x1, `model_tier` x1, `defer`);
  `scripts/episode/step_02_plan.py` (both raises replaced; `plan.deferred.json`).
  Fixtures: `tests/fixtures/llm/plan_reading_{good,no_turn,no_answer,dropped}.json`.

### Group 6 — master ensemble and the audit sheet

- [x] **C12 `master_eye`, recut/retake ladder, audit sheet; step 11 rewired** — ~340 lines, 10 tests.
  Tests first: `test_each_rubric_field_is_answered_from_its_measure.py`,
  `test_a_judge_flags_an_n_and_never_waives.py`, `test_a_flagged_rubric_clears_the_master_step.py`,
  `test_the_story_field_is_a_listed_action_against_the_plans_verb.py`,
  `test_a_repeat_is_a_pair_not_explained_by_a_shared_setup.py`,
  `test_a_cross_take_identity_collapse_is_a_fault.py`,
  `test_a_recut_is_tried_twice_before_a_retake.py`,
  `test_an_audit_sheet_shows_every_flag_and_a_seeded_sample.py`,
  `test_an_owner_note_becomes_a_casebook_row.py`, `test_step_11_raises_no_escalation.py`.
  Files: `studio/judges/master_eye.py`; `studio/master_ladder.py`;
  `scripts/episode/step_11_qc.py`; `scripts/audit/sheet.py`; `scripts/audit/note.py`.
  Fixtures: `tests/fixtures/flow/{take_look_medians.json, frame_match.json}`,
  `tests/fixtures/vlm/master_reads.json`, `tests/fixtures/audit/rows.jsonl`.

### Group 7 — wiring checks, docs, the org chart

- [x] **C13 no park anywhere; docs; the Future tab** — ~120 lines of code, 4 tests, docs.
  Tests first: `test_no_refs_or_episode_step_raises_an_escalation.py` (grep + import),
  `test_every_auto_gate_names_its_judge_in_the_registry_desc.py`,
  `test_the_skill_command_table_is_the_registry.py` (existing, regenerated),
  `test_the_lock_carries_every_dependency_group.py`.
  Files: `stages.yaml` (`desc` lines for refs/04, episode 02_05, 07_01, 08_05, 08_06,
  09_04, 09_05, 11_03, new 11_05 audit row); `docs/ARCHITECTURE.md` ("automation is
  gates you retire one at a time" gains: the taste gates are judged from day one;
  the owner's eye is an audit, never a gate); `docs/DECISIONS.md`; `.claude/skills/episode/GATES.md`
  (the judge rows, `fitted_on`); `docs/calibration/<judge>.md` seeded by the bench;
  `architecture/index.html` (`TEAMS` and `FUTURE` rows per `H_architecture_delta.md`;
  the "seven signatures" box becomes five plus the audit sheet); `architecture/README.md`.

## Sizes

~3,450 lines, ~110 tests, 14 commits (C0-C13). Wiring commits (C6, C7, C9, C11, C12)
each remove exactly the raises they name; until each lands, its step still parks, and
the suite stays green because the policy row is read only by `judged_gate.clear`.

## Order of work

C0 -> C1 -> C2 (the bench exists before any judge, so every judge is benched on its
first commit) -> C3 -> C4 -> C5 -> C6 -> C7 -> C8 -> C9 -> C10 -> C11 -> C12 -> C13.
C5 and C8 (measures) may be built in parallel by two workers; C6/C7 wait on C5, C9 on
C8; everything else is serial.

## Log

- 2026-09-24 — plan written from the chair's ruling over reports A-E; owner away,
  decisions delegated.
- 2026-09-24 — built: C1/C2 `c4d2b6a`, C3/C4 `d737534`, C8 `27f01e2`, C10 `d573d8f`, C5 `cdeff9a`, C11 `6e28d0a`, C9 `59fc491`, C6 `9e65517`, C7 `081c370`, C12 `d181fd6`, C13 (this commit). Eight builders in three waves; two cross-builder conflicts (a raw timeline path; the face model loading on blank test cards) fixed at integration. Known gaps carried: no DINOv3 embedding node exists in the installed ComfyUI packs (the `image_embed` workflow is a marked placeholder; the leak and style measures read "not measured" until one does); the critic runs on the same model family as the writer until a second provider is configured; the DWPose pack's checkpoint path needs a one-time copy on first run.
