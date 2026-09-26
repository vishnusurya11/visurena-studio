# Command Center build — the department tables and the board

**Status: IN PROGRESS — owner ruled "looks good" 2026-09-25; build started the same day.**
Decision: `architecture/decisions/2026-09-25_command_center.md`. Built in waves so no two
agents edit the same file: W1 = C1 · W2 = C2 + C4 + C6 · W3 = C3 + C5 + C7 · W4 = C8 + C9 ·
W5 = C10 · W6 = C11. Each commit is green on the full suite before it lands.

## Progress

- [x] C1 the tables, the migration, a view per department — 19 tests; the migration only CREATEs and ADDs (a live runner was writing; the plan's "rebuild" wording is superseded)
- [x] C2 rows written from `add_event` — 31 tests; attempts = passes over the unit (a `started` under a new run_id)
- [ ] C3 verdicts and flags on the row
- [x] C4 `in:`/`out:` in the registry, the manifest, the drift guard — all 16 episode+refs steps covered; `deliverable_of('episode')` is the manifest (it names the master)
- [ ] C5 cost per unit
- [ ] C6 holds, orders, `studio_cli`
- [ ] C7 the tick, `v_queue`, `v_attention`; Current tab + README — must also settle a unit whose every step was `skipped` (outputs on disk): it stays `blocked` under C2's map until the tick/verify marks it done
- [ ] C8 backfill (dry-run listed to the owner before `--write`)
- [ ] C9 runners take the queue
- [ ] C10 the board, read-only (FastAPI pinned when no GPU run is live)
- [ ] C11 actions; README, DECISIONS, republish

## Rules for every commit

- Test first; a function does one thing in 10–20 lines; no test touches the GPU, a model or a
  paid API; nothing book-specific in the code tree; every path book-relative.
- The row is a projection: disk stays the truth of a step, events the journal. A commit that
  makes a runner read the table to decide whether a step is done is wrong.
- The web process never runs a step, never writes anything but `orders`, opens SQLite
  read-only, serves `library/` only through the guarded route.
- `architecture/index.html` Current tab and `architecture/README.md` move with C7, C9, C11.

## Commits

| # | commit | tests (before the code) | size |
|---|---|---|---|
| C1 | `work_orders`, `work_steps`, `holds`, `orders` DDL; `db._migrate_work_orders` (idempotent, rebuilds a table missing a word like `_migrate_events`); one VIEW per `registry.stage_names()`; `events.order_id`, `usage.unit`, `usage.order_id` | `test_every_department_has_its_own_view_generated_from_the_registry.py`, `test_the_migration_adds_the_department_tables_to_an_old_db.py`, `test_a_second_gpu_claim_is_refused_by_the_index.py` | ~160 lines |
| C2 | `db.upsert_work_order` called inside `add_event`: state map (`started → running (+attempts)`, final step `completed → done`, `failed/escalated/deferred → the word`), `step_id`, `run_id`, timestamps; `work_steps` row per event | `test_a_finished_unit_is_one_row_in_its_departments_table.py`, `test_a_deferred_unit_is_a_deferred_row.py`, `test_a_started_step_makes_the_unit_running_and_counts_an_attempt.py`, `test_no_runner_changed_to_write_a_row.py` (grep) | ~120 |
| C3 | Verdicts on the row: `work_steps.verdict_*` from the judge files at `completed` (`plan.verdict.json`, `eye_<sha8>.json`, `refs/verdict.json`), `flags` from audit rows; `deliverable` from the stage's last `out:` | `test_a_signed_verdict_reaches_the_steps_row.py`, `test_a_stale_verdict_sha_is_marked_stale.py`, `test_flags_count_the_audit_rows.py` | ~100 |
| C4 | Standard I/O in the registry: `in:`/`out:` per step for episode and refs (`{unit}` templating, `book:` prefix); `registry.inputs_of/outputs_of`; `input_sha8` at claim; `UnitManifest` (pydantic) written by `step_12_deliver` and `refs/step_04`; the drift guard | `test_every_declared_output_is_a_path_its_step_reads_as_done.py`, `test_a_manifest_names_every_verdict_and_the_deliverable.py`, `test_a_changed_input_sha_makes_a_done_row_stale.py` | ~180 |
| C5 | Cost: `spend_context(unit=)` from every runner; `gpu_seconds` from `timing.jsonl` at unit end (stage-name → step-id map); `cost_usd` NULL while an unpriced call exists | `test_a_units_paid_cost_is_answerable.py`, `test_gpu_seconds_sum_every_pass.py` | ~70 |
| C6 | `holds` and `orders`: `StageContext.held()` reads the file OR a hold row; `studio/work_orders.py` (`queue, hold, lift, bump, retry, redo`); runners take orders at the top of `run_steps`; `studio_cli.py queue|hold|lift|bump|retry|redo` | `test_a_book_hold_stops_its_units_before_the_first_gpu_step.py`, `test_a_retry_order_requeues_a_deferred_unit_once.py`, `test_a_redo_reruns_a_done_step_and_notes_the_casebook.py` | ~150 |
| C7 | The tick: `studio.py tick` materializes rows from the registry × the slate, promotes on `requires` + `in:`, mirrors `RENDER_HOLD`, sweeps leases; `v_queue`, `v_attention`. **Architecture page Current tab: the desk between the org chart and the runners; README tables** | `test_a_tick_materializes_a_row_per_unit_the_slate_names.py`, `test_a_row_is_queued_only_when_its_requires_are_done_and_its_inputs_exist.py`, `test_an_expired_lease_is_stale_not_requeued.py` | ~140 |
| C8 | Backfill: `scripts/audit/backfill_work_orders.py` (dry-run, `--write`, `source='backfill'`, never a live `run_id`); run on WotW + Scarlet; the derivation printed to `docs/audit/2026-09-2x_backfill.md` | `test_backfill_derives_a_published_unit_from_its_files.py`, `test_backfill_never_overwrites_a_row_with_a_live_run.py`, `test_an_ambiguous_folder_is_listed_not_guessed.py` | ~130 |
| C9 | Runners take the queue: `episode.py <book>` (no unit) claims queued rows in `priority, sequence`; `refs.py`/`trailer.py` `ready()` read the table; explicit invocation unchanged | `test_the_no_unit_form_takes_the_queue_in_order.py`, `test_the_explicit_form_claims_its_own_row.py` | ~80 |
| C10 | The board, read-only: `uv add fastapi==… uvicorn==… jinja2==… python-multipart==…`, `httpx` to dev, `uv sync --all-groups`; `studio/command_center/{app,views,templates}`; `command_center.py` (port 8700); pages `/`, `/floor`, `/d/{stage}`, `/d/{stage}/{codex}/{unit}`, `/b/{codex}`, `/org`; htmx partials + `/api/*.json` twins; the guarded `/lib/{codex}/{path}` | `test_the_home_page_shows_the_floor_and_the_attention_strip.py`, `test_a_departments_page_is_its_table.py`, `test_a_unit_page_lists_its_steps_verdicts_and_deliverable.py`, `test_the_artefact_route_refuses_a_path_outside_the_book.py`, `test_the_board_copies_the_org_charts_tokens.py`, `test_the_web_process_imports_nothing_from_scripts.py` | ~600 |
| C11 | Actions: POST `hold/lift/redo/bump/retry` → one `orders` row; the buttons on the floor, department and unit pages; README, `docs/DECISIONS.md` line, republish the claude.ai copy | `test_an_action_is_one_orders_row_and_never_a_subprocess.py` | ~120 |

## Sizes

~1,850 lines, ~30 tests, 11 commits. C1–C3 are the table (a day); C4–C6 the contract and the
hand (a day); C7–C9 the drive (a day); C10–C11 the board (a day).

## Order of work

C1 → C2 → C3 → C4 → C5 → C6 → C7 → C8 → C9 → C10 → C11. C8 runs `--write` only after the
owner has read the dry-run listing. C9 lands with the queue as a *request*; the worker loop
that would make it an instruction is a separate decision.

## Log

- 2026-09-25 — five reports (A–E) under `architecture/decisions/research/2026-09-25_command_center/`;
  the chair's ruling in the decision file; this tracker; the *Command Center* tab on the page.
  Owner review pending.
- 2026-09-25 — owner: "looks good .. use sub agents and also a way to track progress and build it". Status → IN PROGRESS; this list is the tracker.
