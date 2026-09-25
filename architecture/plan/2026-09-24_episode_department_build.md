# Episode department — build

**Status:** IN PROGRESS (started 2026-09-24; the owner delegated the decisions for this
build: "make decisions on your own").

**Decision:** [../decisions/2026-09-24_future_departments.md](../decisions/2026-09-24_future_departments.md)
§2.3 (refs), §2.4 (episode), §3 (owner gates), §5 (registry). Owner's scope answers,
2026-09-24: the full department (stages, runners, wrappers, the new agents); the
agents' `local` tier points at the paid workhorse for now; the 18 plan scripts move
under `library/` now.

**Done means:** `stages.yaml` carries `refs` and `episode` with `unit`/`requires`; each
has a root runner (`refs.py`, `episode.py`) beside `analysis.py`; every step is a module
`scripts/<stage>/step_NN_<name>.py` that runs on its own from the command line and from
the runner; every step writes `started/completed/failed/skipped/escalated` events with
the unit; a step whose output exists is skipped (resume = output on disk); every owner
gate (LOOK, PLAN, EYE ×2, MASTER) parks the unit with an `escalated` event and a
printed call-sheet line, never a silent pass; the plan of a new unit is written by a
registered agent through `plan_check` and an improve loop; the episode skill's command
table is generated from the registry and a test says so; the 11 + 7 existing episodes
still regenerate their `plan.json` byte for byte from plans that now live under the
library; the suite is green; nothing here touches a GPU or a paid model in a test.

## Decisions made in this build (owner delegated)

| # | decision | why |
|---|---|---|
| D1 | Stage names `refs`, `episode`; runners `refs.py`, `episode.py` at the repo root; steps in `scripts/refs/`, `scripts/episode/` beside the scripts they wrap | the registry convention (`scripts/<stage>/step_NN`), and "episode" not "production" (decision §1.7) |
| D2 | Unit string for the episode stage today is `epNN` (the folder name); `unit` is an opaque text column on `events`; the stage declares its grammar in the registry | one chapter = one episode in every existing book; renaming folders would break 11 + 7 episodes for no gain; a range is a new folder name later |
| D3 | Step wrappers launch the existing script as a subprocess with the same argv `scripts/episode/run.py` uses, under the same clock and GPU queue guard | behaviour identical to today; a GPU script stays isolated; every step is runnable alone by `uv run python scripts/episode/step_NN_x.py <codex> <n>` |
| D4 | Resume: each step defines `done(ctx)` from its output on disk; the runner skips a done step with a `skipped` event | EVENT_MODEL "a step's resume key is its OUTPUT's existence" |
| D5 | Owner gates: a step raises `Escalation`; the runner writes `escalated` with the call-sheet line and stops the unit cleanly (no `failed`); the next run resumes past the gate once the verdict file exists | decision §3; ESCALATE parks, never blocks |
| D6 | `cast_lister` is code, not an agent: the chapter's cast is already in analysis (casting_director rows) and `cast_rows.py` binds it | no judgement left to make; an agent would be theatre |
| D7 | `listener` is not a new agent: Whisper already reads every line back inside `say_lines` (`studio/voice_qc`) | exists |
| D8 | New agents: `episode_writer` (reasoning → `Episode`, through `plan_check` + improve ≤2 → ESCALATE PLAN) and `look_back` (VLM reads a drawn picture against its prompt's nouns; advisory this pass, logged, no refusal) | the two judgements only prose held; look-back has no calibration yet, so it cannot refuse |
| D9 | `local` tier in `models.yaml` = openai `gpt-5.6-luna` for now, with the comment that it is a yaml edit to make it $0 | owner's choice 2026-09-24 |
| D10 | Plan scripts move to `library/<book>/episodes/epNN/plan.py` (untracked; `library/` is gitignored); a hand-patched plan declares `PATCHED_BY_HAND = True` in its own file; the regenerate test globs the library | owner: "anything book related goes in library"; the marker keeps the test book-neutral |
| D11 | `scripts/episode/episode.py` (stale blind path) is deleted; `grids_ep11.sh` moves under its book | the runner replaces one; the other is book-named code |
| D12 | The episode skill keeps its rules; its "how to run" section becomes a table generated from the registry (`scripts/episode/commands.py`), asserted equal by a test; `.claude/agents/episode.md` points at `episode.py` | decision §1.10: a skill is the desk, the runner is the leader |

## Commits

- [x] **C0 plan** — this file.
- [x] **C1 registry keys and the unit column** — tests first: `tests/test_registry_units.py`
  (a stage's `unit` and `requires` parse; a stage without them parses as before;
  `stage_names()` equals the yaml), `tests/test_events_carry_a_unit.py` (two units of one
  stage do not collide; `unit` NULL for book-level stages; `mark_stage` refuses an
  unregistered stage; `init_db` adds the column to an old db). Code: `studio/registry.py`
  (`load`, `stage`, `stage_names`, `unit_of`, `requires_of`); `studio/db.py` `STAGES`
  from the registry, `events.unit` column with an idempotent migration,
  `add_event(unit=)`, `unit_status`; `studio/tracking.Tracker(unit=)`; `models.yaml`
  `local` tier. Registry: the `refs` and `episode` blocks land here too (ids fixed).
- [x] **C2 the runner shape** — `studio/escalate.py` (`Escalation`), `studio/stage_run.py`
  (`StageContext`: conn, codex, book_dir, unit, tracker, `hold()`), `studio/step_runner.py`
  (`run_steps(ctx, steps)`: skip when `done`, bracket events, catch `Escalation` →
  `escalated` + stop, `SystemExit` → `failed`), `studio/subprocess_step.py` (launch a
  script under the clock and the GPU guard, injectable). Tests: `tests/test_step_runner.py`
  (done → skipped; escalation parks and stops; failure → failed; RENDER_HOLD refuses
  before the first GPU step; ids match the registry).
- [x] **C3 `refs` stage** — `refs.py`; `scripts/refs/step_01_canon.py` (wraps cast_rows),
  `step_02_sheets.py` (wraps build_pack + prop_refs; look_back advisory), `step_03_voices.py`
  (wraps cast_voices), `step_04_verdict.py` (ESCALATE LOOK → `refs/verdict.json` bound to
  `pack.jsonl` sha); `agents/look_back.py` + `agents/skills/look_back.md` +
  `studio/look_back.py`. Tests: ids match; runner brackets; verdict binds to the pack
  sha and a stale pack is refused; look_back diff with a fake reader.
- [x] **C4 `episode` stage, wrappers** — `episode.py`, `studio/episode_run.py`;
  `scripts/episode/step_01_bind.py` … `step_12_deliver.py` (deliver = manifest + the
  path printed first; notify stays out of scope). Every eye = `Escalation`. Tests:
  ids match; every step is importable and runnable alone (`--help`); eye steps park
  without a verdict and pass with one; the take step refuses without the three panel
  verdicts; the runner on a finished episode skips every step.
- [x] **C5 `episode_writer`** — `agents/episode_writer.py` + `agents/skills/episode_writer.md`
  (book-neutral, distilled from the skill's plan rules) + `studio/plan_brief.py`; step 02:
  brief → write → `plan_check` → improve ≤2 → lock (`write_plan`) → ESCALATE PLAN. Tests
  with a FakeModel: schema validates; a refusal is quoted back; the loop stops at 2; an
  existing `plan.json` is never rewritten.
- [x] **C6 plans under the library** — move the 18 scripts; `PATCHED_BY_HAND` markers;
  `test_a_plan_script_regenerates_its_plan.py` globs the library; delete
  `scripts/episode/episode.py`; move `grids_ep11.sh`.
- [x] **C7 the desk** — `scripts/episode/commands.py` generates the command table;
  `.claude/skills/episode/SKILL.md` carries it between markers; `.claude/agents/episode.md`
  names the runner; test asserts equality. `docs/DECISIONS.md` line; the architecture
  README/index states flip to "runner built; gates escalate".
- [ ] **C8 full suite green, push.**

## Log

- 2026-09-24 — plan written; owner away, decisions delegated.
- 2026-09-24 — C1 `0a5153f`, C2 `6bcf854`, C6 `3cdf25a`, C3 `820d64a`, C5 `004d219`, C4 `d0ea098`, C7 `ea0a7df` on master. Three subagents built C3/C4/C5 in parallel; one conflict (a raw `placed.json` path in step 02) fixed through `episode_home.has_timeline`.
- 2026-09-24 — D13 (added during the build): a plan whose timeline already exists is grandfathered past the PLAN signature; a plan is never rewritten once it ran. D14: `cast_lister` dropped (D6) and `listener` dropped (D7) as agents; `look_back` and `episode_writer` are the two new registered agents.
