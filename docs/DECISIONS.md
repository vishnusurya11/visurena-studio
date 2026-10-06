# Decision Log

Newest first. Every architectural change gets an entry.

---

## 2026-10-05 — The pipeline cures itself (owner decision: "i need python scripts instead to do that using the open api call .. budget is $3 for episode")

**Ruling:** every hand fix Claude made on ep17/ep18 becomes code: gates + cures in the plan
battery (phantom people, clone text, projected silences, take-prompt lint, source spans,
camera moves, machine staging), a local-VLM duplicate judge (G-TWIN, faces N>M hard),
orchestration fixes (clean plans re-sign free, retakes re-judged, dead clock goes to
terminal, comfy transient retry), and publish metadata + sign-off generated from measured
data. Judgement is an API call through studio/llm behind guard_spend; the $3/episode
ceiling stands. Proof of done: ep19 via drive.py alone. Decision:
`architecture/decisions/2026-10-05_self_curing_pipeline.md`; tracker
`architecture/plan/2026-10-05_self_curing_pipeline.md`.

## 2026-10-04 — The board, premium (owner decision)

**Ruling (owner, "looks good go"):** the whole board redesigned as one studio tracking tool —
paper office, dark stage for media, colour means state only; Now landing page with an inbox that
counts flagged-not-acknowledged units (`acknowledge` order kind); screening room for finished units;
run matrix for loops; hand-SVG charts; pulse + morph live updates. Phase 0 fixes nine measured bugs
first (a 36 MB unit page, "Needs you (0)" with five flagged episodes, failing contrast). Decision:
`architecture/decisions/2026-10-04_premium_board.md`; tracker
`architecture/plan/2026-10-04_premium_board_build.md`.

## 2026-10-01 — No human input at publish (owner decision: "Remove that human waiver .. we need automation")

Decision id: `2026-10-01-no-human-input-at-publish`

**Decision.** The publish lock no longer demands an owner-hand `review/waiver.json`
for a terminal that a judge signed. A terminal on a gates.yaml `auto` gate clears the
lock under that gate's decision id, and the upload ledger records the judge's name
beside the clearance (`auto_cleared`). The take roll-up at the upload door carries the
same ruling: judge-signed take terminals ride an automatic override. What still stops
an upload, past every automation: a gate the registry does not call `auto`, a take
nobody judged, a speaker that is not one voice, a missing or unwritten director
sign-off, QC `passed:false` on these bytes, and the Short/square file facts. Context:
`publish_lock.py` (2026-09-26, the ep12 root cause) predated the judges and demanded
the owner's hand; ep13/ep14 masked the gap with per-episode owner orders. Detail:
`architecture/decisions/2026-10-01_no_human_input_at_publish.md`.

---

## 2026-09-30 — The five-hour episode (owner decision: "see how we can get next episode run to 5hrs or less like before")

**Decision.** Five experts read the past ~28 runs (verdict
`docs/audit/2026-09-30_five_hour_plan.md`): the work grew x1.07, the hours x11 — the
loops did it, not the quality layers (~70 min in a single pass). The owner ordered the
P0 fixes built: ONE clock for the whole episode (the 5 h ceiling spans resumes; a spent
ceiling takes terminals, and the driver never auto-resumes it — ep14 got 31 fresh
ceilings); an idempotent picture stage (a reprose re-signs the plan, the climb persists
in storyboard/ladder.json, a redraw re-reads only its panels); QC once per set of
master bytes and the season's title cards pre-baked; ALL renders first then ONE measure
window (the owner's own emphasis); the VL judge resident per pass; TAKE_S re-priced
228 -> 265 and the four unclocked stages stamped; one episode on one commit; and the
105.7 GB working set moved to the C: NVMe (H3 staged ~115 s of weights per take off
the HDD). Tracker: `architecture/plan/2026-09-30_five_hour_build.md`.

**Why.** Every <= 5 h run ever shipped was one pass: one render, at most one batched
retake, one QC, nothing redrawn. Projection with P0: ~4.9 h wall for a 30-shot episode.

**Amended same day (owner): a book's title cards are ALL baked before its first
episode.** The card is the chain's one purely book-deterministic artifact (base art +
chapter title + series aspect), so it is book-level pre-production: drive.py bakes any
missing card book-wide in one i2v session before launching, outside the episode's
clock, and refuses the launch if the episode's own card cannot pass its lettering gate.
Quote glyphs leave the card's asked line (ep17: THE "THUNDER CHILD" failed 6 draws on
its quotes). The just-in-time rule stands for every CREATIVE render; the card is the
exception because nothing an episode produces can change it.

## 2026-09-30 — The delivered master is a Short (owner decision: "these are hard requirements")

**Decision.** ep14 shipped as a regular video at 182.58 s — YouTube files a square
upload as a Short only up to 3:00, and every runtime wall capped the PICTURE at 180 s
while assemble appends the ~4.7 s card + chip after it. The owner: "it has to be
short .. the format has to be 1*1". Now: `SHORT_WALL_S` (180) and `TAIL_ALLOWANCE_S`
(6) live in the contract and `MAX_SECONDS` (174, the picture budget) is DERIVED —
contract, writer brief, G-RATE and timeline all inherit it; assemble and qc refuse a
delivered master over the wall; and both publish doors judge the FILE itself
(`youtube_publish.file_refusals`: ≤ 180 s and width == height), unwaivable past
`--override`, which had waived qc.passed on the ep14 upload. Proposal:
`architecture/decisions/2026-09-30_the_master_is_a_short.md`.

**Why.** ep01-13 delivered 139.6-175.8 s; ep14 was the first picture cut past 175 s,
so the ungated tail never showed. qc measured 182.58 s and judged it by nothing; no
stage ever opened the final mp4 for length or squareness.

## 2026-09-30 — Every cure rides one batched round (owner decision: "why 32 rounds .. debate and come up with solution")

**Decision.** The owner, on ep14's timing table (takes 18.8 h over 32 rounds), ordered
the five-expert debate (`docs/audit/2026-09-30_rounds_debate.md`, proposal
`architecture/decisions/2026-09-30_batched_ladder.md`) and its solution built. Ruled
with it: the judges' five truth fixes land first (9 of ep14's 11 standing refusals were
false alarms, ~4 GPU-h); the rung-serial ladder is replaced by ONE `batched_cures` rung
(tries 2) — a router assigns every faulted take its measured cure, free cures (head cut,
timeline trim) cost no round, input-borne faults go straight to the terminal, a fault
whose signature does not progress after its own cure is structural and stops;
`ROUNDS_CAP` falls 4 → 2 across resumes; G-CROWD refuses crowd prose under a wide with
`extras=0` at plan time and the battery lists the expects-text set.

**Why.** Measured on ep12-14: seed cured ~0% solo (3.6 GPU-h spent), shorter-on-lag
0/15 (lag is arithmetic — the free trim cures it), replan-content 3/21 (panel redraw
1/1), move_type 89-100% at ~8 min a cure; 86% of ep14's take faults mirrored a panel or
prompt fault. The old process (ep10 synthesis F1) was one person-chosen batched round
per master — automation had lost the batching, not the taste.

## 2026-09-28 — One room per setup (owner decision: "fix all that")

**Decision.** The owner, on ep14's grids ("the background keeps on changing for the
character"), after the five-agent debate (`docs/audit/2026-09-28_grid_place_constancy_plan.md`,
proposal `architecture/decisions/2026-09-28_one_room_per_setup.md`): "fix all that". Ruled
with it: D4 (a cross-panel place gate) is BUILT as `panel_place`, advisory until calibrated;
a recurring place is PINNED — the 2026-09-24 decision text "never pinned to one picture"
is superseded by the owner's 2026-09-17 ruling (one picture per place, staged everywhere;
per-episode views are drawn from it); D3 (the 2x2 minimum) is closed as moot under the
four-cell cap; the panel ladder's `copy`/`repeat` cures no longer push a panel off the
place picture. The rule: a place is held by pixels — every panel of a setup is conditioned
on the same picture of that place (one render, or later renders staged on the first
render's own cut panel), and words pin only what the picture leaves free.

**Why.** The grid code did not change between ep11 (held) and ep12 (broke); a setup had
become 2-12 independently seeded renders, redrawn one at a time, from cells written before
any picture existed. Measured: panels from one render agree 0.56, from different renders
0.31; ep14 drew two biology classrooms, a mirrored Waterloo and an attic that became a street.

## 2026-09-26 — A terminal is not a pass; the episode has sound and a voice (owner decision)

**Decision.** The owner, after episode 12 was judged bad: "finish all 1-d" of the root
cause (`docs/audit/2026-09-26_ep12_root_cause.md`). A gate that cannot afford a rung
DEFERS the run instead of signing its terminal; a judge repeating one fault is an
invalid verdict; "cannot tell" is an n; every pass is learned. Both publish doors
(`youtube_upload`, `youtube_privacy public`) refuse on `studio/publish_lock.py`: an
open terminal without the owner's waiver, a speaker that is not one voice, or no
`review/director_signoff.md` for the cut. The plan must cover its chapter (G-COVER:
90 % of paragraphs and the title event) and file shouts as dialogue (G-SHOUT). Lines
carry a delivery and are said with a per-register emotion clip, lifted and levelled
by it. The episode has a sound layer (Shot.sounds, Setup.ambience, Stable Audio 3,
G-SOUND, a QC row). The take gate reads whole-frame stillness (`frozen-whole`).

**Why.** Episode 12 went public with every taste gate ended in a terminal, a plan that
stopped at paragraph 57 of 69, no sound effects (an empty cue list since 2026-09-13),
shouts read flat (the reading clip was the emotion reference), and five frozen shots
the block-max meter could not see. The owner: "this is fucked up and not acceptable".

## 2026-09-25 — The Command Center: departments driven by their tables (owner decision)

**Ruling (owner, "looks good"):** one work-order row per (book, department, unit) in a
`work_orders` table with a generated view per department; standard inputs and outputs
declared once per step in `stages.yaml` (`in:`/`out:`) and carried across a department
boundary by the unit's `manifest.json`; rows materialized on a tick from the registry's
`requires`, pulled by the runner (`episode.py <book> <n>` unchanged; the no-unit form drains
the queue); nine stored states; a deferred unit waits for an order; the owner's hand is one
`orders` table; a local read-only board (FastAPI + Jinja2 + htmx, port 8700) over the ledger.
Not built on purpose: a worker loop that starts a GPU job unattended — a queued row is a
request until the owner rules it an instruction. Full ruling and the five reports:
`architecture/decisions/2026-09-25_command_center.md`; tracker
`architecture/plan/2026-09-25_command_center_build.md`.
**Built 2026-09-26:** all eleven commits; open it with `uv run python command_center.py` →
http://127.0.0.1:8700 (loopback only; `--read-only` refuses every order) — pages read the
ledger read-only, and the hold / lift / bump / retry / requeue / redo buttons each write one
`orders` row through `studio/work_orders`; the home page's Orders strip shows which run took it.

## 2026-09-24 — Automate the taste gates (owner decision)

Decision id: `2026-09-24-automate-the-taste-gates`

**Decision.** No step of the refs or episode line parks on a person. LOOK, PLAN, the
EYE on the storyboard panels, the EYE on the takes and the MASTER rubric are signed by
judges (`signed_by: judge:<name>@<version>`): detectors for counts and geometry,
embeddings for identity, a local VLM that only names, code that judges. Every judge
climbs a priced adapt ladder under the episode's time ceiling and ends in `pass` or
`flagged` — never a park, never a silent pass, never a waiver. Every terminal rung
writes a flagged verdict, a learning and an audit-sheet row. The owner's eye moves
off the critical path: `library/<book>/audit/<unit>.html` shows every flag and a
seeded sample; his findings append to the casebook and re-calibrate the judges through
a bench with a ratchet test. Who signs each gate is `gates.yaml`, every refs/episode
row `auto` with this decision id. PUBLISH, MONEY (paid credits), OVERRIDE, the synthetic
declaration and `RENDER_HOLD` stand. Design and debate:
`architecture/decisions/2026-09-24_judges_replace_the_eye.md`; build:
`architecture/plan/2026-09-24_judges_replace_the_eye_build.md`.

**Why.** The owner, 2026-09-24: "It says there are human eye checks, DQ checks, gates —
remove them. We should automate them all, using agents or existing ComfyUI models. Fix
all of them." Five research reports found no owner-signed verdict file on disk and
~8 owner catches with an artefact id: the human gate was already retired in practice
without evidence. The judges make the casebook executable and measurable; the audit
sheet makes the owner's taste a recorded input instead of a gate.

## 2026-09-24 — The episode line is a registry department led by a runner (owner-delegated)

Decision id: `2026-09-24-episode-department`

**Decision.** `refs` and `episode` are stages in `stages.yaml`, led by root runners
(`refs.py`, `episode.py`) like analysis, screenplay and trailer. A stage declares its
`unit` (the grain of its production id: `[book, chapter]` for episodes, unit string
`epNN`) and its `requires`; events carry the unit. Every step is a module that runs
alone from the command line and from the runner; a step whose output exists is
skipped; an owner gate (LOOK, PLAN, EYE ×2, MASTER) is a **file** the next step
refuses without, and a run that reaches one parks with an `escalated` event and a
printed call-sheet line — a sentence in chat signs nothing. A plan is data under the
library (`episodes/epNN/plan.json`), written by the `episode_writer` agent through
`plan_check` and an improve loop of two rounds, or regenerated by a hand-authored
`plan.py` beside it; the 18 plan scripts moved out of the code tree. The episode
skill is the desk: its command table is generated from the registry and a test keeps
them equal. Build plan and the decisions made inside it:
`architecture/plan/2026-09-24_episode_department_build.md`.

**Why.** The episode chain was ~30 tested scripts run by hand from a Claude skill that
wrote no ledger events; the skill was both manager and worker (audit
`architecture/decisions/2026-09-24_future_departments.md` §1.10). The owner asked for
the episode department to be built to the same shape as analysis and screenplay and
delegated the build's decisions (2026-09-24, "make decisions on your own").

## 2026-09-24 — One folder; the code tree is book-neutral (owner decision)

**Decision.** The studio is one checkout, `visurena_studio` on `master`. No git
worktrees, no per-book branches, no symlinked or copied libraries. The code tree
(`studio/`, `scripts/`, `tests/`, `.claude/`, `docs/`) names no book, character,
place, episode or take; everything book-specific lives under `library/<book>/`.
See [ARCHITECTURE.md](ARCHITECTURE.md), "One folder".

**Why.** A worktree made on 2026-09-18 for the War of the Worlds refs-only POC
(`visurena_studio_wotw`, branch `wotw-refs-poc`) ran 115 commits ahead of `master`
while the skill was mirrored into `master` by hand, uncommitted. Sessions opened in
either folder read a different skill. In the same period the skills and agents filled
with one book's episode and take IDs, character names and owner quotes, and an agent on
another book read them as canon (audit `docs/audit/2026-09-24_skills_book_neutral_plan.md`).

**Done the same day.** `master` fast-forwarded to `f6ea1e0` (the POC branch; `master`
had no commits of its own); the worktree and branch removed; the episode skill's
"where to run" rewritten. The scrub of the skills and the move of book content out of
the code tree follow the audit's plan.

## 2026-08-22 — Library structure: flat, book-id-anchored (owner decision)

**Every book has a unique id (the codex id) and everything starts from there.** Folder
structure is flat and id-keyed: `library/<codex_id>_<slug>/` per book — hierarchy
(universe/world/series) lives in the DB only, never in paths (the taxonomy is a DAG:
crossovers/Hoid break any real tree). Codex grain stays BOOK-level, always. Series/universe
level artifacts and the `atlas`/`entity`/`appearance` tables come later, trigger-based —
see [db/LIBRARY_STRUCTURE.md](db/LIBRARY_STRUCTURE.md). Existing folders are disposable;
the id is the anchor. `library/`, `views/`, `logs/` gitignored.

---

## 2026-08-22 — Storage model: codex + events + file logs (owner decision)

Owner simplified the proposed 6-table stepwise schema to three pieces: the `codex` master
table; **one append-only `events` table** (event_ts, codex_id, stage, hierarchical `step_id`
in **fixed-width 2-digit segments** like `01_01_02` so plain text sort = pipeline order —
growth rule: a level nearing 99 gets restructured into a sub-level; insertions get a sub-level,
never renumbering — event, small detail; current status derived from latest event per key); and
**file-based logs** (Python-logging / Glue-style JSONL, one file per run, joined to events via
`run_id`) — errors and detail live in logs, never in the events table. Pipeline shape lives in
a **step-registry folder** (`stages/<stage>.yaml`, file order = execution order) so future
steps/substeps are added by editing a file, never by migration. Details + the step_id text-sort
pitfall and its fix: [db/EVENT_MODEL.md](db/EVENT_MODEL.md). The stepwise 6-table design stays
as reference for gates/ledger/staleness ideas.

---

## 2026-08-22 — Main table is `codex`

Considered: `books`, `works`, `titles`, `tomes`, `volumes`, `slate`, `texts`,
`properties`, `chronicles`, `sources`, `corpus`.

**Chosen: `codex`** — singular, not `codices` (misspelling magnet; reads as a collective
the way `corpus` does). Gives `codex.name`, `codex_id`, `codex_stages`, `Codex`.
No Python collisions.

Rejected `properties` because `property` is a Python builtin. Rejected `titles` because
`titles.title` is awkward — though the column is `name`, so it was survivable.

Note: `/codex` is also the OpenAI Codex CLI skill in the gstack setup. Ambiguous in
conversation only, not in code. Say "the codex table" when referring to the data.

---

## 2026-08-22 — Row id reduced to second precision (owner decision)

**Supersedes the microsecond entry below.** The id is `TEXT`, fixed **14 chars**,
`YYYYMMDDHHMMSS`, UTC. It is **THE id across the entire system** — stages, production
folders, artifacts all reference it; it is never reformatted downstream.

Collision handling at second precision: entry is manual for now; any bulk insert must
wait ≥1 second between rows or retry with +1 second on `PRIMARY KEY` conflict. The PK
makes a collision a loud failure, not a silent overwrite.

`source_type` + `source_ref` approved the same day (no longer PROPOSED).

---

## 2026-08-22 — [superseded] Row id is microsecond UTC text

**Chosen: `TEXT`, fixed 20 chars, `YYYYMMDDHHMMSSffffff`, generated from UTC.**

- Microseconds as INTEGER is **impossible**: `20260822143015123456` is 20 digits
  (~2.0e19) and SQLite's 64-bit signed INTEGER maxes at ~9.22e18. Milliseconds
  (17 digits) would fit; microseconds do not. So the real choice was
  *ms-as-INTEGER* vs *us-as-TEXT*.
- Fixed-width zero-padded text sorts identically to numeric. `ORDER BY id` just works.
- Range filters use the index:
  `WHERE id >= '20260801000000000000' AND id < '20260901000000000000'`.
  **Do not use `LIKE '202608%'`** — SQLite's LIKE optimization depends on collation
  settings and will silently fall back to a full table scan.
- Drops straight into a path: `20260822143015123456_the_way_of_kings/`, matching the
  existing shorts production folder convention.

**Must be UTC.** With local time, the DST fall-back repeats an hour once a year and ids
go *backwards* — sort order breaks silently and the cause is near-impossible to find.

**Uniqueness:** `PRIMARY KEY` + retry with +1us on conflict. A timestamp is
collision-*unlikely*, not collision-*proof*; a batch import can land two rows in the same
microsecond. Retry costs nothing in the normal case. A sleep-based delay layer is a poor
substitute — Windows `time.sleep()` granularity is roughly 1–15 ms, thousands of times
larger than the window being guarded, and it would slow bulk imports for no benefit.

---

## 2026-08-22 — Database lives in-repo at `db/visurena_studio.db`

Covered by the existing `*.db` gitignore, so `db/` needs a `.gitkeep`.

**Open:** `studio_parser` currently writes `parsed_stories` to
`D:\Projects\GlobalDatabases\visurena_studio.db`. That split must be resolved before P0
lands — two databases with the same name in different places is a guaranteed confusion.

---

## 2026-08-22 — Four-level hierarchy

`universe > world > series > book`. The Cosmere is the *universe*, Roshar is a *world*,
Stormlight Archive is a *series*, The Way of Kings is the book. `world` is included now
rather than deferred, since Cosmere-shaped material is a stated target.

---

## 2026-08-21 — Strands Agents SDK over Pydantic AI, LangChain, LangGraph

**Chosen: Strands**, scoped to `visurena_studio` only. pheonix and visurena_novel keep
LangChain.

An initial Pydantic AI recommendation was **withdrawn** — it rested on two claims that
proved false on checking the docs:

1. *"Wider provider coverage"* — false. Strands' list is longer, OpenRouter is
   first-class, and LM Studio is reached the same way on both (OpenAI-compatible
   `base_url`; neither ships a dedicated LM Studio provider).
2. *"Better local structured output"* — false. Strands' llama.cpp provider constrains at
   decode time via native `json_schema` **and** exposes raw GBNF grammars, which Pydantic
   AI does not. LM Studio is llama.cpp underneath, and `gpt-oss:20b` is the default local
   model, so this favours Strands for exactly this setup.

Remaining reasons to prefer Strands: OpenTelemetry built in; better tool loops for the two
genuinely agent-shaped jobs (story scout, QC/retry ladder); no fresh major version
(Pydantic AI V2 shipped 2026-06-23).

Known gap: Strands raises `StructuredOutputException` on schema violation and does **not**
auto-retry. The `extract()` wrapper in `studio/llm/` owns retry — about six lines.

**LangChain / LangGraph rejected** because v1 is `create_agent` over LangGraph, and
LangGraph checkpoints graph state rather than artifacts-and-credits. See the load-bearing
rule in [ARCHITECTURE.md](ARCHITECTURE.md).

**Strands' own Graph / Swarm / workflow primitives are deliberately unused** for the
production DAG, for the same reason. They persist agent/session state, not artifacts and
spend.

---

## Deferred

| Item | Status |
|---|---|
| Stage tracking: columns on `codex` vs a `codex_stages` table | Owner will decide at build time |
| Resolving the two database locations | Before P0 lands |
