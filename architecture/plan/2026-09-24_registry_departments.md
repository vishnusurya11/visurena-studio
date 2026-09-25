# Registry departments — the proposal into stages

**Status:** NOT STARTED — awaiting the owner's ruling on
[../decisions/2026-09-24_future_departments.md](../decisions/2026-09-24_future_departments.md).

**Decision:** the big-studio shape: five divisions by function, one registry stage per
format line inside Production, `unit`/`requires` keys in the registry, seven owner
gates with a retirement rule. Draft registry:
[../decisions/2026-09-24_stages_future.yaml](../decisions/2026-09-24_stages_future.yaml).

**Done means:** `stages.yaml` carries `refs`, `episode`, `shorts` (empty), `publish`,
`analytics`, `promo`; each has a root runner; every step writes a ledger event with
its `unit`; the episode and shorts skills are desks whose command tables are generated
from the registry; every owner gate is a file the next step refuses without; the
scheduler launches a unit when its `requires` are complete. No new capability — the
scripts that exist today, organised.

## Steps

Sizes from the codebase memo (§5 of the decision). Tests first, every step.

- [ ] **1. Registry keys and the unit column** — ~150 lines, 5 tests.
  Tests: a stage's `unit` parses; `requires` parses; `mark_stage` accepts a registered
  stage and refuses an unregistered one; two units of one stage do not collide in
  `events`; `codex_ready_for_stage(stage, unit)` takes a unit.
  Code: `studio/registry.py` reads `unit`/`requires`; `events.unit` column with an
  idempotent migration; `db.STAGES` derived from `stages.yaml`.
- [ ] **2. `refs` stage** — ~300 lines, 8 tests.
  Tests: registry ids match module `STEP_ID`s; the runner brackets each step in events;
  `refs.json` is written only by this stage (a test greps the writers); the verdict
  file binds to the pack sha and a stale pack is refused.
  Code: `refs.py` from the `trailer.py` template; wrappers over `cast_rows`,
  `build_pack`/`prop_refs`, `cast_voices`; `refs/verdict.json` writer; the
  `cast-voices` skill becomes the desk.
- [ ] **3. `episode` stage, wrappers only** — ~1,400 lines, ~30 tests.
  Tests: ids match; every eye step parks the unit and writes no verdict; a take step
  refuses without all three panel verdicts; the skill's command table equals the
  registry; `RENDER_HOLD` stops the runner before the first GPU step.
  Code: `episode.py` + `studio/episode_run.py` (the GPU lease moves out of
  `scripts/episode/run.py`); `step_NN` wrappers for 01, 03–12 with every eye =
  ESCALATE; `plan` wraps `plan_check` and reads the existing `plan.json`.
- [ ] **4. Distribution contracts** — ~200 lines, 6 tests. `FinishedFile`,
  `PublishManifest`, `CatalogEntry` in `studio/`; a `local` tier in `models.yaml`.
- [ ] **5. `publish` stage** — ~700 lines, 15 tests. `publish.py` +
  `studio/publish_run.py`; wrappers for upload/review/release; intake, catalog,
  `studio/notify.py` (pinned client, replaces the trailer's subprocess); `episode/12 deliver`.
- [ ] **6. The new agents** — ~600 lines, 12 tests. `episode_writer` + `plan_brief` +
  improve loop; `cast_lister`; `metadata_writer`; `look_back`; each behind its
  deterministic gate with FakeModel tests; the plan scripts move under the library.
- [ ] **7. `studio.py` scheduler** — ~250 lines, 6 tests. The loop over `requires`;
  batched call sheet; `series.json` slate.
- [ ] **8. `analytics`, `promo`** — ~600 lines, 12 tests. Contracts, runners, the two
  agents each.
- [ ] **9. Higgsfield client + credit ledger → `shorts` stage** — ~1,700 lines, 31 tests.
- [ ] **10. Gate retirements** — one `(format, gate)` at a time, cheapest first, each a
  `docs/DECISIONS.md` line with its count.

## Log

- 2026-09-24 — proposal written from five reports and a chair's ruling; plan filed;
  nothing applied.
