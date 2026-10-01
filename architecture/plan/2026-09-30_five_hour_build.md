# Build: the five-hour episode (2026-09-30 verdict)

**Status: P0 built** (fixes 1-7, owner-ordered; uncommitted pending the owner's word).
Verdict of record: `docs/audit/2026-09-30_five_hour_plan.md`.

- [x] Fix 1 — one clock for the whole episode: `Budget.charge(spent_before(home))`;
  a spent ceiling takes TERMINALS (judged_gate.affordable, take_ladder.can_afford);
  the driver never auto-resumes a spent episode (`episode_drive.drive(over_budget=)`)
  · tests: test_the_clock_covers_the_whole_episode.py
- [x] Fix 2 — idempotent picture stage: `panel_ladder.write_cured` re-signs a reprose;
  `storyboard/ladder.json` persists the climb (CAP survives resumes); a redraw
  re-reads ONLY its panels (`panel_content_check --only` + `merge_content_rows`)
  · tests: test_the_picture_stage_survives_a_resume.py
- [x] Fix 3 — fixed costs cached: `step_11_qc.qc_report` reuses a matching-sha8 report
  (pass or fail) and verifies the sha after every fresh run; `titles_batch.py`
  pre-bakes the season (no plan needed: `series_title.aspect_of`)
  · tests: test_a_measured_master_is_not_measured_again.py, test_a_title_card_needs_no_plan.py
- [x] Fix 3c — STANDING DESIGN (owner, 2026-09-30: "render all title cards for a given
  book before start of any episode"): `titles_batch.missing/chapters_of`, no-arg form
  bakes whatever is missing; drive.py preflight bakes stragglers book-wide before any
  launch, outside the episode's clock, and REFUSES the launch if the episode's own card
  cannot pass its lettering gate; quote glyphs stripped from the card's asked line
  (ep17 THE "THUNDER CHILD"); baked into episode.md, SKILL.md, GATES.md, the org page
  · tests: test_the_books_cards_exist_before_any_episode.py
- [x] Fix 4a — the working set on the NVMe: 105.7 GB moved to C:\comfy_models,
  `extra_model_paths.yaml` `nvme_fast` stanza (is_default), originals kept as
  .hdd_bak; verified: UNETLoader lists the Singularity int8 and krea2 from C:
- [x] Fix 4b — renders first, then the checks (owner: "run all model executions once
  then do the dq check"): `take_ladder.retake(trims=)` renders every take, then one
  measure window with the trims' re-measures inside it
- [x] Fix 5 — the VL judge resident: `panel_eye.judge` and the master eye in
  `comfy.model_kept`; master eye `run_text` -> `cached_text`; `free_models`
  best-effort and never retried
- [x] Fix 6 — honest prices and clocks: TAKE_S 228 -> 265; `plan`, `panel_eye`,
  `take_eye`, `master_eye` stamp timing.jsonl
- [x] Fix 7 — one episode, one commit: the driver warns when HEAD moved since the
  episode's first run (`episode_drive.first_sha`); rules in GATES.md
  · tests: test_one_episode_runs_on_one_commit.py

## P1 (benched, after ep15 ships)
- [ ] Merged turbo-LoRA UNET + encode-all/sample-all batching (the 115 s/take staging;
  A/B first, ~10 GPU-min)
- [ ] Plan ladder: mechanical-first fixes, monotone acceptance, critic cache by sha,
  plan.ladder.json
- [ ] ep N+1's plan written (API, CPU) while ep N renders; refs.json write made atomic
- [ ] take_dq CPU metrics streamed beside the render (DINO off-queue; bench ep10's
  collision first)

## Log
- 2026-09-30 — five experts debated the past ~28 runs; verdict written; the owner
  ordered fixes 2-7 ("this is really important" on the render-then-check order),
  then fix 1; all built the same day, 105.7 GB moved, ComfyUI restarted and verified.
