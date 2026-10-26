# Decision Log

Newest first. Every architectural change gets an entry.

---

## 2026-10-19 — The Jekyll Kawajiri ep01 retro: 22 decisions taken on the owner's behalf while he slept (for veto)

Decision id: `2026-10-19-kawajiri-retro`

**Ruling (pending the owner's veto):** five bricks under ep01's 13 failures (a round is a change of
bytes; a gate is as true as its population; one rule per fact; a count cannot see shape; a clock
survives a kill), built as 15 code packages and one docs package. Decision
`architecture/decisions/2026-10-19_kawajiri_retro.md`; tracker
`architecture/plan/2026-10-19_kawajiri_retro.md`; the debate `docs/audit/2026-10-19_kawajiri_retro/`.

- D1 G-WARP FAIL is S > 2.5 only; Se alone is the advisory `eye`; `row()` recomputes the state (41fba62). Evidence: all 8 ep01 fails Se-only, seeds 0 of 4.
- D2 `warp_gate.RETAKES = 1`: one seed, then refine a small face or ship flagged (41fba62).
- D3 A round, climb or redraw is spent only when it changed bytes, or a writer call was made (79b8049, 2f1ef00, cc5a631, eb35ea6).
- D4 A stale flagged plan signature is re-signed over its carried rows with one critic read, no writer round (2f1ef00).
- D5 The plan critic accepts setup-crowd counts extras >= 1 (2f1ef00).
- D6 G-DEAD keeps option A; unknown failing rows on a kept take ship flagged high, never fail closed (f2460f2).
- D7 The face paste stays before the one upscale (owner 2026-10-18); a T18 A/B is owed, never auto-reverted.
- D8 One anatomy ask on panel_content's existing read plus a DWPose orphan-limb measure; advisory until E1 recall >= 0.6 and precision >= 0.8 (5616782, cc5a631).
- D9 The hung-step kill needs 1.5 x the step wall AND flat run-tree CPU AND no output growth for 10 min (222be3b).
- D10 No auto-pause on runtime edits; dirty means runtime code only (9dd9ffb).
- D11 A step's wall stays the sum of its cap rows; shares are report-only; no cap value moves until one run on the new code (6a81488).
- D12 The downstream replay is advisory at plan sign until clean on ep01 and one WotW plan (b2782b4).
- D13 Eval and warp labels made by agents carry `label_source: agent` until the owner labels T07, T10, T16, T20, T21, T24 (5616782, 41fba62).
- D14 The `lead_day` grid lead in look.json is an experiment, never the default (c152d1b).
- D15 The UNLETTERED sentence names only the bait nouns the take holds, never a cheque by default (b83eac4).
- D16 QC is never cut by a timeout; its cap is a CAP line (311bf8e).
- D17 LESSONS.md is an index of 8 KB or less; LESSONS_ARCHIVE.md keeps every heading and every cited anchor.
- D18 Voice keeps 8 tries plus a separate 10 min `lines` wall (37eefbb, 6a81488).
- D19 One model-family-boundary free in step_runner and one in step 03; never a per-read free (dd1e163, 6a81488).
- D20 One package (P16) owns every doc file.
- D21 Tracking's one event stream (C1, C2, C5) and the facenet / EasyOCR torch worker are deferred.
- D22 Docs landed in one P16 commit after the code packages instead of one commit per package, so 15 builders could run in parallel overnight (orchestrator, 2026-10-19, for veto).

---

## 2026-10-10 — Continuity: character looks on a story timeline; a place is its master (owner rulings, retro of WotW)

Decision id: `2026-10-10-continuity-looks-places`

**Ruling:** a character has one picture per story-time LOOK on the book's look table
(`refs/looks.json`), not one picture for the whole book — this reverses the 2026-09-18
"one picture per entity" rule for story-time looks only; places and props keep it. A look,
and a place's state, may be a ONE-step edit of the base sheet / the place master: never an
edit of an edit, never a composite (nothing pasted between pictures). A recurring place's
views are its masters, or one hop from them; a new view is never a fresh room from words.
Budget ≤ 6 h machine time per 2-3 min episode; no shipped episode is re-rendered; an
existing ComfyUI workflow is never edited (a new one is `<base>_<source>.json`). Phase 1
is the skeptic's 9-commit slice; phase 2 arms the judges after the next book's first
episodes. Decision `architecture/decisions/2026-10-10_continuity_looks_places.md`; tracker
`architecture/plan/2026-10-10_continuity_build.md`; the debate
`docs/audit/2026-10-10_continuity_retro/`.

---

## 2026-10-07 — Every LLM tier runs on the Claude Agent SDK under the owner's subscription (owner: "use Claude, like how you used to supervise"; "don't use API for money, I will remove that completely")

**Ruling:** no paid API call anywhere in the studio. Every tier in `models.yaml` (`local`, `canon`,
`workhorse`, `reasoning`, `brain`) names provider `claude-sdk`: `llm.structured` runs one structured
Claude Agent SDK session per call (`studio.brain.ask_structured`, no tools, the schema enforced by the
SDK's `output_format`), under the subscription the owner already pays for. Usage is ledgered as
`<model>@subscription` with a NULL cost so the $3 wall ignores it; `guard_spend` is never called on
that path. The OpenAI / OpenRouter / LM Studio / Ollama providers stay in the yaml only as ledger
history, and the owner removes their keys. This supersedes the luna entry below (2fc2c29; tracker
A38–A39).

---

## 2026-10-07 — The episode writer returns to gpt-5.6-luna (superseded the same day by the entry above)

**Ruling (applied under the owner's 2026-10-06 rule "use whatever models you want but the budget
is $3 for episode"):** since 2026-10-06 17:27Z every provider behind OpenRouter refuses the strict
grammar of the whole Draft for anthropic/claude-sonnet-5.5; split into parts it answers, but the
shots part returned 47k tokens for $0.61 and one draft costs $1.09 — two drafts a wall, where a plan
takes two to four. The loose path cannot answer (reasoning is mandatory for the model and its budget
is advisory). Measured on ep20 and ep21 (eight launches, ~$5 of writer calls, no plan signed). The
`local` tier goes back to gpt-5.6-luna (~$0.03 a call, one strict call, ~2 min). The faults luna
showed on ep19 — the first-dialogue and narration walls, the brief's rate, G-SYNC seating — are cured
in code since (2a50fc4, e64a94b). The parts writer, the loose fallback and the ledgering of failed paid
calls stay, so a future tier change meets a working path. Tracker A17–A19 in
`architecture/plan/2026-10-06_autopilot_build.md`.

---

## 2026-10-06 — The autopilot and the brain on a leash (owner decision: "Approve")

**Ruling:** a Python supervisor (`scripts/episode/autopilot.py`, re-armed by Windows Task
Scheduler) owns the episode lifetime: launches `drive.py` for the next chapter, derives the
state from disk every tick, retries, cures through work orders, parks with a reason and
moves on. Never a silent stop; never a wait on the owner — PARKED is a record. A Claude
Agent SDK brain triages a stop mid-run (read-only, JSON verdict) and fixes with tests only
between episodes, through the saved `/fix-parked` workflow, under a mechanical ratchet
(red-before-green on HEAD~1/HEAD, allow-set diff, no quieter battery on the last three
plans). Gate thresholds, judges, cures' wording and model tiers stay report-only. Brain
spend is ledgered in the `usage` table (`stage='brain'`), $1 triage / $3 fixer caps; the
$3 media wall is unchanged and `OverBudget` becomes a ladder terminal, not a crash. Brain
runs on the owner's subscription login. ep19 parks under the wall; ep20 starts. Decision
`architecture/decisions/2026-10-06_autopilot_and_brain.md`; tracker
`architecture/plan/2026-10-06_autopilot_build.md`.

---

## 2026-10-06 — The episode writer is Claude Sonnet 5.5 (owner decision: "Sonnet 5.5")

**Ruling:** the `local` tier (episode_writer, line_filler) moves from gpt-5.6-luna to
anthropic/claude-sonnet-5.5 via OpenRouter ($2/$10 per M, ~$0.23 a call). Measured cause:
luna failed ep19's plan three rounds running (12 shots for 121 s so takes overflowed; the
first spoken line at 76 % of a chapter that speaks at 9 %). The $3/episode wall
(money.episode_ceiling_usd, studio/llm.guard_spend) is unchanged and gates every call.

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

- **2026-10-11 — the book video.** Each chapter is two videos, its title card and its main video; the Short stays main + title; the book video runs the book's own 7 s main title, then each chapter TITLE FIRST. The main title is unlike the chapter cards and its type is set by code, never drawn by a model; a 16:9 thumbnail is set on the book video. Applies to WotW now and every book after. (Owner: "Build it"; decisions/2026-10-11_book_main_title_and_thumbnail.md)
- **2026-10-11 — retro cycle 1 rulings.** A storyboard panel still seamed or stacked after its one isolate renders its take from the reference sheets only, ships unattended and is flagged in the audit sheet; shipped wotw ep10/T21 and ep26/T25 (a mouth moving in the silent tail) are left as they are and logged as known faults; the Jekyll/Hyde probe is skipped; stubble vs short beard is not ruled. (Owner; architecture/decisions/2026-10-11_cycle1_grid_shape_seam_tail.md)
- **2026-10-11 — retro cycle 3 rulings, made on the owner's behalf.** The owner ordered "don't ask me any more, design it the best way and implement it"; the ruling is `docs/audit/2026-10-10_continuity_retro/C3_verdict.md` §4, D1-D12, each with its reason and open to veto: the clock is the process (D1), a retry never resets it (D2), at the 5 h ceiling missing firsts render, every ladder signs its best flagged and only the closed SAFETY list stops an episode (D3), a resume on moved code is allowed from a boundary (D4), the ceiling stays 5 h (D5), confirm-before-refuse only on the bench's measure (D6), the neutral tile for new refs draws but not the book title plate (D7, D8), G-FRAME advisory floors MCU 0.15 / close 0.25 (D9), plan rungs priced (D10), retirements (D11), content rules unchanged (D12). Built and measured in `CYCLE_3.md`.
- **2026-10-11 — the board implements the 2026-10-01 ruling (no human input at publish).** A published unit (a done `publish` row, or youtube.json plus an upload row with a video id) does not need the owner: the Command Center shows it `done` with its gate chips kept, and its flags leave Needs you, the inbox and the sidebar dots (`views.flags_open`, one rule). A done unit with flags that is not published stays `flagged` until acknowledged. The tick settles an episode published outside the runner from its publish record (`tick.settle_published`); WotW ep01/02/05/18 and Scarlet ep01/02/10-14 settled so. Not a new owner ruling: the 10-01 ruling, now honoured by the board.
- **2026-10-11 — the downstream reserve, decided on the owner's behalf (for veto).** The owner's rule is 6 h for EVERY episode with zero input, so a rescue rung runs only while the spent clock + its price + the shares of the firsts still owed after its step fit under 6 h; a refusal is the ceiling's terminal (flagged, never parked); past the ceiling a verdict on the same bytes stands under moved code. Measure and price: `docs/audit/2026-10-10_continuity_retro/C3_p90_residual.md`; decision: `architecture/decisions/2026-10-11_cycle3_honest_clock.md` (addendum).
- **2026-10-11 — the content gate calibrated on the owner-judged episodes (J5), decided on the owner's behalf (for veto).** "Hills" on a flat place is advisory (mountains still refuse; cliffs refuse unless the place is a pit); the hour is not judged on a daylight/sunset/afterglow setup; an over-the-shoulder shot allows one more figure but never a copy; a pre-`extras` plan declares its crowd in the shot's words. Good ep05 refusals 23/28 → 6/28, ep07 5/27 → 4/27 (all remaining refusals are real faults by eye); bad ep08/09 unchanged. Record: `docs/audit/2026-10-10_continuity_retro/C3_content_gate.md`, commit 78df605.
- **2026-10-12 — Jekyll and Hyde: style A, photoreal gothic (owner).** The book `20260827135504` is drawn on Krea2 turbo t2i with no LoRA, as a Victorian film still with fog, gaslight and deep shadow, led by the book's own refs words (evidence: `docs/audit/2026-10-11_jekyll_look_test/`, `docs/audit/2026-10-12_jekyll_style_samples/`). Declared once in `library/<book>/refs/look.json`; every refs drawer (base sheet, fresh look, place master) and the title plates read it through `studio/book_look.py`, and a book without a declaration keeps the house look. Pre-launch fixes, by the owner's order: Hyde sinister (small, slight, about 25, a sneer, black side-whiskers, a soft low felt wideawake hat), Lanyon's base the ruddy ch2 man with a shock of prematurely white hair (balder only from ch6; a chapter-dated dossier sentence is a state, never the base head), the door's master a layout (a flat blank plaster upper storey, one blistered door). The POC publishes nothing: `publish/standing.json` stays absent, so step 13 parks on G-STANDING.
- **2026-10-13 — a book's narrator is the book's, decided on the owner's behalf ("decide, don't ask"; for veto).** A third-person book gets a dedicated `narrator` voice row -- a calm, low storyteller, never a cast member, never on camera -- set once in `library/<book>/refs/narrator.json` before episode 1; a first-person book declares its "I"; a book that declares nothing keeps the narrator its published episodes share (WotW, Scarlet unchanged). Step 02 stops when a book has none, and no refusal lists the cast as options. Jekyll & Hyde takes the dedicated narrator. With it: the `tale` line kind, G-PACE (2.45 words/s, <= 310 words, >= 15 s of pauses, a line cut never a breath), G-ACTION, G-HOOK / G-SPIKE, dialogue held locked or over the shoulder (G-TALK), five viewer rules in the writer's brief. `architecture/decisions/2026-10-13_the_book_narrator_and_the_viewer.md`, `docs/audit/2026-10-13_jekyll_ep01_review/`.
- **2026-10-12 — the events ledger settles the book-level departments, decided on the owner's behalf (for veto).** A blocked or queued analysis/screenplay/trailer/refs row with terminal step events is what the ledger says: done when the last step completed (flagged when a later re-run failed), failed when nothing delivered and the newest terminal event failed (it lands in Needs you), else its cursor moves. Every stage declares a `deliverable:` in stages.yaml, which settles a row only where the ledger is silent (the pre-runner Jekyll trailer); an upstream row the episode requires is done once a published episode consumed it (Scarlet's legacy refs). `tick.verify` stays out of the tick until the owner rules: it would flip published units stale. `architecture/decisions/2026-10-12_the_ledger_settles_book_stages.md`, `docs/audit/2026-10-12_board_review/`.
- **2026-10-13 — the picture/motion lane, decided on the owner's behalf ("decide, don't ask"; for veto).** No master ships a still held past 2.5 s, a take that failed the take gate, or two such shots in a row (G-DEAD at step 10): the free cure cuts the dead shot and slows its live, non-dialogue neighbours at most 1.5x; what it cannot cure refuses the master for a retake, never a flagged ship. Automatic camera text is linted (`studio/camera_lint`): no garbled aim, no second pace, no distance. The take gate judges a take against its staged panel and a HARD camera-move row (walled on WotW ep01-03). (architecture/decisions/2026-10-13_picture_motion_lane.md)
- **2026-10-13 — Jekyll and Hyde: style 2, Hellsing Ultimate gothic anime (owner).** The owner picked style 2 (HEL) over style A photoreal (2026-10-12, superseded) and ordered ep01 re-made. `library/<jekyll>/refs/look.json` declares `anime_gothic` with its own refs drawer (NoobAI-XL 1.1 on `image_sdxl_t2i_2lora_hires_visurena`, no LoRA, the HEL tag lead, a weighted text/caption negative, per-person tags: the insane grin on Hyde only, Hyde's `mutton chops` tag never "side-whiskers", Jekyll clean-shaven under weighted beard negatives, Utterson about 40, sandy-grey, no glasses, bowler) and its fog outdoors only. All 15 base sheets and ep01's four place masters were redrawn through the refs path (old ones superseded, never deleted); the look table was rebuilt with 0 refusals. Evidence: docs/audit/2026-10-13_jekyll_gothic_anime/, docs/audit/2026-10-13_jekyll_anime_chain/, docs/audit/2026-10-13_jekyll_hellsing_cast/cast_sheet.jpg.
- **2026-10-13 — Jekyll and Hyde: the cast follows the chain test's HEL look (owner).** The owner rejected the first Hellsing cast sheets (flat light-grey studio sheets) as "not the style I asked" and approved the style match (`docs/audit/2026-10-13_jekyll_hellsing_cast/style_match.jpg`): refs/look.json's drawer is the chain test's HEL refs recipe 1:1 (dark grey gradient sheet framing, red and black chiaroscuro, ground shadow; `book_look.drawn_words` keeps the chain's negative order). Decided on his behalf by the main session: Hyde is a slight, human young man with a visible face and the insane grin (no masked shadow-demon), plain wide black wideawake brim, mutton chops; daytime places stay grey overcast daylight in the HEL ink style as the book has them, only night scenes are red-lit; places keep the pipeline's landscape aspect; Utterson's face reads under his bowler. All 15 sheets and ep01's place masters redrawn on it (old superseded), the look table rebuilt. Evidence: `docs/audit/2026-10-13_jekyll_hellsing_cast/cast_sheet_v2.jpg`.
- **2026-10-17 — owner 2026-10-17 approved face refine.** ("I like face improvements a lot in wide shots, go ahead".) Step 09_07: wide/full or small-faced takes that passed their dq get each face re-rendered through H3 at 0.45 with only that person's sheet, gated (identity, seam, flicker, face count), pasted into the master after the 4x upscale; the first thing cut for time. Decision: `architecture/decisions/2026-10-17_face_refine.md`.
- **2026-10-14 — the master is upscaled by NVIDIA RTX Video Super Resolution (owner).** The highest quality under 10 min per episode: 4x standard ULTRA over the joined 768 cut, delivered at 3072, in process (`studio/master_upscale.py`, nvidia-vfx 0.2.0.0); 2x ULTRA → 1536 stays selectable (`VISURENA_MASTER_UPSCALE=rtx2x`); Lanczos 2x is the logged fallback without the GPU. DEBLUR rejected (halos on ink lines). Measured on Jekyll ep01: +3.6 min upscale, +1.6-3.8 min QC; QC passes (`docs/audit/2026-10-14_rtx_vsr_adopt/`).
- **2026-10-14 — Jekyll HEL ep01 v2 rulings (owner side, made by the main session).** (1) **Hyde is clean-shaven:** "a swart growth of hair" is his hand's, never his cheeks; `analysis/heads.json`, the look table (words, then `looks_table.py --remark`: facial_hair `none`), look.json's drawer tags and the bound chapter-1 row now agree with the HEL sheet, which is clean-shaven; Hyde and Enfield share the (dark, none) face family and are kept apart by `apart_from` with its reason (age, stature, cut, hat). (2) **A drawn look is judged by the house stillness rule:** the relaxations 9ea1304 (held run past 2.5 s) and 85ef81c (a speaking dialogue take never HARD-still) are dropped; T01/T02/T19/T20-type holds re-take or are cut. (3) **The take identity row is measured again** with the take's own staged sheets (held back since 4c5f14c, 2026-09-25, and never restored); it is ADVISORY (`take_verdict.TAKE_IDENTITY_HARD = False`) because a replay with sheets refuses 23 of 118 WotW ep19-27 and 37 of 97 Scarlet ep08-14 shipped face takes, and the master eye flags every take with a finding (`master_eye.take_identity`). (4) G-GAIT and the reserve-only check cut are folded into the episode skill. Then ep01 is set aside (`episodes/superseded/ep01_2026-10-14_hel_v1`) and re-made from the plan up. Evidence: `docs/audit/2026-10-14_jekyll_ep01_hel/`, `docs/audit/2026-10-14_jekyll_ep01_hel_v2/`.
- **2026-10-14 — the GPU never waits on a check (owner: "it shouldn't wait, the GPU needs running, and the DQ checks should be done after all videos are done, or in parallel if the GPU is not needed").** Step 09 runs two lanes (`studio/take_overlap.py`, policy `studio/take_schedule.py`): the takes render back to back on the GPU while `take_dq --cpu-only` measures each one as it lands; a cure the dq rows alone order (a move or a seed) is queued as the take ladder's round 1 right behind the first renders (`ladder.json` `early: true`, recorded at launch, ROUNDS_CAP 2 unchanged); the GPU checks (the VL content read, a deferred DINO leak) run once the GPU queue is empty and the CPU lane idle -- never between renders, one VL load. The ladder's own round runs on the same lanes. Every guarantee kept: cap 2, the honest clock (CPU rows `within: takes`), the reserve, checks never cut with room, idempotent resume, renders before checks, G-GAIT/G-DEAD/G-PRESENT unchanged. Replay of the drawn-book ep01 clock (`scripts/episode/take_schedule_replay.py`): 5455 s → 4232 s, 22 %; GPU idle 1464 → 302 s. Decision: `architecture/decisions/2026-10-14-gpu-never-waits-for-checks.md`.
- **2026-10-15 — Jekyll ep01 iter5: the SHEET IS TRUTH (owner) and the decisions taken on his behalf (for veto).** Owner: rows and words are rewritten to the drawn sheets, never the reverse -- Utterson grey hair and a long black double-breasted overcoat with white buttons (no sandy-blond, no dark suit or waistcoat); Enfield a mid-grey coat, cream waistcoat, black gloves and a cane (no dark frock coat); Lanyon's hat and the constable's helmet and eyes fixed now; a plan epithet ("the lawyer", "the little man", "the girl") ALWAYS binds to its staged `<Subject k>`, and a person is described once per prompt. Decided by the main session on evidence, each open to veto: (1) **one door base** -- the door the audits liked (the grey gable block, the blistered red-black door above two steps, the kerb lamp) existed only in the door_day anchor panel, so the house's master `black_mail_house_door/wide_establishing.png` is that panel with its two men taken out (ONE 2511 edit); door_day and pavement_day stand on the base itself (two derived day states drew a lettered lintel and a sunlit new red door), night_door is one edit of it; the second fresh master `court_entry_pavement` (an arched brick court) is retired and the pavement words follow the base. (2) **sunday_street** is re-derived from its grey master under the plan palette (grey sky, oxblood and bone shutters). (3) **Lanyon's row** to his sheet (a black silk top hat with a white band, a navy frock coat). (4) **The constable's sheet redrawn** (try 1 peaked cap and hollow eyes; try 2 a modern short-sleeved hard-hat cartoon, rejected; try 3 kept: Hellsing look, eyes with irises, a rounded helmet) and his row rewritten to it (black hair, thick white moustache, rounded dark-blue helmet with a gold star, long dark-blue greatcoat). (5) **Enfield is "about forty"** (his sheet reads older than the dossier's 35; his drawer tags already said 40) and **Hyde "adult in build but a head shorter than other men", his hands pale, his face a wide cold grin** (the sheet). (6) **plan.py is the source again** (v3): the signed v2 plan.json with every ladder cure is its BASE, rows reach it through `cast_alias.retag`, and the audit's plan-text faults are fixed by name (half-cut aims, over-the-shoulder sides = "behind his RIGHT side puts his shoulder at the LEFT edge", a vertical pan is a tilt, Enfield's gloved hands, Utterson's overcoat buttons, the girl half Hyde's height, the terms named at the corner not the door); `PATCHED_BY_HAND = False`. Evidence: `docs/audit/2026-10-15_jekyll_ep01_ref_audit/` (01-03 and iter5/).
- **2026-10-16 — Jekyll ep01 iter7: the master eye's last flags on master_iter6, decided for veto.** (1) **Shot 2 is a locked medium-close two-shot** (both faces at the thirds before the door), no longer an over-the-shoulder: Qwen 1x1 grids never drew the near shoulder; the size stays medium_close because a driven line needs the speaker's face at close or medium_close. (2) **Shot 15's cell is a flat soot-black brick wall of closed oxblood shutters and the camera pulls back ahead of the lawyer** (was a sideways track past shop fronts): the panel itself had drawn a lettered board. (3) **T06's fourth figure was a duplicate Mr. Enfield**, not a passer-by; cured by aiming his run "toward the fallen girl" (extras already 0); kept the third seed (80 PASS). (4) **Shot 22's crouched figure is the book's tramp**, staged on purpose (`extras: 1`); it stays. (5) **The Sunday anchor was not re-cut and shot 17 not redrawn** (only the named grids redrawn); its room is the iter6 room. (6) **Standing master-eye flags left as they are**: board share 0.526 (ten takes untouched this pass), story (the VLM lists "talking, standing" on the turn though the grip is on screen), content at shots 19/22 (the plan's own push-in and walk-off), identity advisories -- no cheap cut change moves any of them. (7) **The ranker reads the words** (`take_dq.reworded`): an attempt rendered from an older prompt is not current, so a plan cure is never undone by an older higher score. Evidence: `docs/audit/2026-10-15_jekyll_ep01_ref_audit/iter5/VERIFY.md` (iter7 section) and `iter7/`.
- **2026-10-17 — the anime-TV grammar in the planner (owner: "I like the face improvements a lot in wide shots, and reframe. Go ahead with changes").** Every new plan declares `grammar: anime_tv` (set by code from the brief) and is held, until drawn, to: faces at close / medium close on 55 % of the shots; at most 2 wides of 4 s (the opener 5 s); mediums 7 s; inserts as 1-3 s impacts, a long line split across insert and reaction; mostly locked, at most 2 pushes and no amount words; a two-person reaction a locked medium two-shot, the payoff line a locked close, over-the-shoulder medium close; silhouette, Dutch angle and eye close-up refused in words until a panel route exists; a cold open of 10 words or fewer with a sound at 0 s; one act-out at 35-55 % held 1.2 s with the bed turning; narration never captions the frame (CAPTION_WALL now a wall); a silent reaction after each exchange; 3 holds of 1.2 s or more; the dialogue ceiling follows the chapter's speech; a per-book motif; an optional picture-only tease after the button that loops to the hook's place; the `inner` line kind. Decision `architecture/decisions/2026-10-17_anime_tv_grammar.md`.
- **2026-10-17 — the grammar's numbers and walls the owner did not name, decided on his behalf (for veto).** (1) The gates are HARD on a grammar plan before anything is drawn and advice on every legacy plan; the replay of 41 plans found no mechanical misfire on the owner-approved WotW ep01-03 / Scarlet ep05, ep07 after two fixes (CAPTION exempts the narrator acting -- WotW ep03 line 15; 'at a slant' left the unsupported list -- a table surface), and the grammar-definitional fires on legacy plans are the old grammar he replaced. (2) The shot cap is 30 (`studio/episode_capacity`: 7.65 min a shot on the runner's own shares + a retake margin; 23 shots project 5.0 h, Jekyll ep01 measured 4.99 h; 30 -> 5.9 h). (3) A grammar plan renders every shot as its own take. (4) The dialogue ceiling is the chapter's speech + 8 points inside 20-35 % (Jekyll ch1: 35 %). (5) Locked and over-the-shoulder shots leave G-MOVES' share and twice-running rule on a grammar plan; G-VARIETY allows 12 closes a person. (6) A full shot past 5 s is advisory. (7) Free cures: strip amounts, hold a third push locked, widen an OTS close to medium close. (8) The inner voice is the speaker's own engine, hushed, with G1's close-mic chain in assemble, ADVISORY until the owner has heard `docs/audit/2026-10-16_model_tests/voice/G1_inner_voice_AB_sequence.mp3`. Proof: Jekyll ep01 `plan_v3.json` (30 shots) passes the whole battery.
- **2026-10-17 — the title card stays at the END of the Short (owner call, defaulted; for veto).** The G2 bumper (the card at 7.25 s, after the hook) is not adopted: the book video already puts every chapter's card first, and the Short keeps the owner's design.
- **2026-10-17 — the grammar's shot cap is 28, not 30 (decided by the main session, for the owner's veto).** 30 shots project 5.91 h, about 5 min inside the 6 h limit, and the shares that price the downstream reserve still assume ~26 shots; 28 project 5.65 h (`studio/episode_capacity.MAX_SHOTS`, G-SHOTS). Revisit after the first grammar episode's measured clock re-prices the shares. Jekyll ep01 `plan_v3.json` (30 shots) is left as the proof plan it was.
- **2026-10-17 — sound effects land on their measured moment (owner go on the 2026-10-16 test-bench recommendations; built 2026-10-18).** Step 10_04 lays every planned effect where the take shows its event (`studio/sfx_onset.py`): footsteps one Stable Audio 3 slice per measured heel strike, a single event on the take's strongest camera-compensated motion peak within 0.75 s of the planned time, its own onset on the frame; a voice, crowd or weather sound, a slowed or still take, or a missing detector keeps the planned time with its reason in `audio/sfx/onsets.json`; QC hears each cue where it was laid. Decision: `architecture/decisions/2026-10-17_sfx_onset_placer.md`.
- **2026-10-18 — main session, warp gate from measured evidence, for owner veto.** G-WARP (`studio/warp_gate.py`, a hard `warp` row in take_dq, CPU lane): E = face residual - (2.51 x bg + 1.69 x face flow + 1.00), S = p90, Se = p90 over the eyes; FAIL S > 2.5 or Se > 3.0 -> a seed retake (at most 2) then the F2 face refine; WARN 1.5-2.5 and UNMEASURABLE (< 45 % tracked) -> F2. Unlabelled cut (27 clips): it fires now and logs every score to refit on owner-labelled takes. Same day: the face refine filed its INPUT as the refine since daa4aa9 (collect took the first output; v0.41.2 echoes the LoadVideo crop first) -- fixed to the SaveVideo node, a refine identical to its source is refused, and the face count and identity now read drawn faces (architecture/decisions/2026-10-18_warp_gate.md).
- **2026-10-18 — the take model follows the planned shot size (main session, on measured evidence; owner 2026-10-17 picked Wuli V4's faces and approved Spark; for veto).** A take whose every segment is close, medium_close, medium or insert renders on Wuli 8-step HQ int8 + Spark-H3 attention (`takes_r2v.WULI_BASE`); a take with any wide or full segment, or no sizes, renders on the Singularity 8-step + turbo LoRA x2 with Spark attention (`SPARK_BASE`), because Wuli's line work boils on a small face (G-WARP on the Kawajiri W wide S 4.13 / Se 7.22 against Spark 2.65 / 3.12; WARPING.md T22 +2.4/+3.3 against about -0.6) while it is equal or cleaner on close and medium. Each model's takes queue together. Rollback: `ROLLBACK_BASE` (the CK 8-step). Proof: `docs/audit/2026-10-18_wuli_spark/`; decision: `architecture/decisions/2026-10-18_take_model_by_size.md`.
- **2026-10-18 — main session 2026-10-18: final upscale is hqdn3d + realesr-animevideov3 x4, measured, owner asked for no background jitter and sharp faces.** `VISURENA_MASTER_UPSCALE` defaults to `av3` (`studio/master_upscale.py`, frame loop `studio/master_av3.py` under ComfyUI's embedded python; weights in the portable `ComfyUI/models/upscale_models/`): `hqdn3d=0:0:4:4` at 768, run per shot so no frame blends across a cut, then realesr-animevideov3 x4 to 3072 fp16. Bench (docs/audit/2026-10-18_upscale): background jitter -51..-58 % against RTX VSR 4x ULTRA, face crispness +21..+33 %; proof on the Kawajiri C|M|W cut: no ghost at either cut, ~2.5 min per 150 s episode. QC's segment cap is 2.0 for av3 (measured 1.50-1.77). `rtx4x`, `rtx2x`, `lanczos` stay selectable; a missing runtime falls back to Lanczos 2x, said.
- **2026-10-18 — Jekyll's look is Kawajiri Madhouse noir drawn by Krea2 (owner pick); the refs recipe and its fixes decided by the episode agent, for veto.** `refs/look.json` (the Hellsing one is `refs/superseded/look_hellsing_2026-10-18.json`): the refs drawer is Krea2 turbo in prose, the POC recipe 1:1 (card krea2 style + the avoid list said positively + the row's words + one camera/lighting line + the recap; 8 steps, cfg 1, 1 MP, no refiner, no LoRA, a sheet one 2:3 front figure; `book_look.krea2_t2i`, f363e45). Chosen by me: one amber rim for every sheet (the POC gave Utterson teal), a place keeps the pipeline's asked 3:2 shape (the POC drew 1:1), atmosphere `thin fog, haze` (the POC's place words; the Hellsing look said `fog, damp haze`), the grid lead is the card's Qwen line. Every Hellsing sheet, place picture and the ep01 card were moved to `superseded/hellsing_2026-10-18/`, never deleted; the ep02-10 cards (photoreal, 10-12) were left for their own episodes.
- **2026-10-18 — the look-back reads what it asks (episode agent, from the first Kawajiri LOOK; for veto).** `studio/look_back` (17ffa4e, 5006153): a phrase runs to the next trigger; an adjective series asks for the noun it qualifies ('lean, corded, knuckly pale hands' asked for 'lean'); a person's own body (face, jaw, hands ...) is never a must-noun -- the identity and SHEET-ROW rows judge the face; a noun the reader neither lists nor calls ABSENT is not missing (Utterson's drawn band: seen 'hat', absent []). On the five Kawajiri sheets the old rule refused 5/5, every refusal a misread by eye; the new rule passes them and still refuses a reader that names a noun absent. The sheet is truth: Jekyll's look-table body and top were dossier commentary and became what is drawn (a long black frock coat, black waistcoat, white shirt, black tie); Enfield's hat became the dove-grey top hat with a wide brown hatband drawn on every seed. Jekyll and Hyde were re-drawn at their base seeds over the ladder's keep-best (a black-haired brute in a felt hat; Hyde's eyes lost in shadow).
- **2026-10-18 -- voice-measured grammar rows are advice, never a plan refusal (main session, owner: fix the loop; for veto).** studio/grammar_battery: G-WIDE, G-MEDIUM, G-INSERT and G-LOCKED read the recorded voice's seconds, so no writer rewrite moves them; as walls they kept the Jekyll Kawajiri ep01 plan climb refusing for 30+ min (mediums 7.04-7.96 s vs 7.0, a wide 4.58 vs 4.0, locked 0.48 vs 0.5), and a battery that never passes DEFERS and re-authors, a loop with no cap. They now print in advisories(). Tier rule (memory cap-every-loop): only rows a writer can move send it back.
- **2026-10-18 -- the plan climb is capped and its faults tiered (owner order, Jekyll Kawajiri ep01: "add the number of loops we can do and what parts to focus on"; built by the episode agent).** Step 02's climb is three writer rungs (improve x2, model_tier x1) inside a 25-min wall from the climb's start (`plan_ladder.CLIMB_WALL_S`, checkpointed); past the wall a rung writes nothing. Tier 1 -- a line a downstream builder repeats (`plan_tags.builder_lines`: contract, cast bound, take length, plan gates, motion hard, take lint, actor) -- defers and re-authors as before. Tier 2 -- every other battery line (aim, laid, crowd, react ...) -- gets the rungs, then the best draft is signed flagged (keep_best), never a defer-and-re-author. Tier 3 never refuses: the voice-measured grammar rows (0314238) and, on a grammar plan, the G-VARIETY insert count (advice). The ep01 climb had run 13:20-14:05 on tier-3 rows (~45 min lost).
- **2026-10-18 -- owner 2026-10-18 approved the step caps from STEP_CAPS.md** (`docs/audit/2026-10-18_step_caps/STEP_CAPS.md`; `architecture/decisions/2026-10-18_step_caps.md`).
- **2026-10-18 -- the episode page tells the truth, and the run stream and run truth are approved (owner chose batches 1-4 of five experts' list; "write the decision first, build after their commit").** Board half built (`69fcdea`): "episode done ~HH:MM" is the episode's finish from full-run norms only (resumes dropped: 09 shoot 10 vs 80 min), every later step has a projected window or "kept" by the registry's in:/out:; a re-make's old steps and gates read "earlier"; a WHY line names what refused; liveness is the run's clock beat, not moving files; Seattle time everywhere; the live card never freezes. Approved, not yet built: `progress.jsonl` as one typed stream with a Windows-safe writer (open('a') lost 12.7 % of lines across four processes), `studio/run_truth.py` as one stall/lease rule for board, drive and autopilot, the beat renewing the lease, SSE for the live card (`architecture/decisions/2026-10-18_run_stream_and_truth.md`, `docs/audit/2026-10-18_page_experts/`).
- **2026-10-18 -- owner 2026-10-18 approved: a setup's crowd rides only a shot that declares extras, and a locked grammar hold is not frozen (Jekyll Kawajiri ep01).** (1) `episode_ref_official.crowd_of`: a shot's own crowd always; the SETUP's crowd only when the shot's `extras` > 0 -- the night door's "five townsfolk ... pressing in a ring" rode into T00 (Hyde alone at 3 a.m.), T10 and T11 (extras 0) and H3 walked strangers in. 14 takes' prompts changed and re-render (T00, T02, T04, T05, T10, T11, T19-T26). (2) On a grammar plan a LOCKED shot that speaks with a moving mouth (the lip-sync row present and passing) or carries an actor/ambient verb takes `frozen-whole` as a scored advisory (`stillness.grammar_locked`, `take_verdict.grammar_still`); the FROZEN cure never swaps a locked grammar shot to a push (G-PUSH); G-DEAD reads such a take as near_dead, never dead.
- **2026-10-18 -- a run that loops is shown as it is, and three pipeline moves (owner go on D1-D3, P1-P3 after a 10-expert debate, docs/audit/2026-10-18_timeline_debate/PROPOSAL.md).** The runner never steps back inside a run (0 regressions in 3,253 events); loops are a later step re-running an earlier step's work (08 redraws 07's grids, 11 re-runs 09's takes) and relaunches (6.2 per published WotW episode). The live card names them (a loops line, studio/command_center/loops.py), draws a shot x stage work grid (workgrid.py), and its finish carries the measured relaunch rework of the last 9 delivered units (eta.rework_band; each step's longest pair is the pass), firm or rough. No arrows, no Monte Carlo, no runner merge of 07+08. Pipeline: step 06 runs grids.py --prompts (step 07's lint, dry) and says camera_lint faults on the writer's heads as advisories; panel_eye caches a read by its inputs (unreadable reads never kept); a qc refusal names qc.failed_rows (step_11_qc.py is outside QC_MEASURES). The 768 cut gate waits for a replay on refusals that carry rows.
- **2026-10-18 -- owner 2026-10-18 approved (option A): G-DEAD admits a take the take ladder's terminal kept as keep_best at the cap, FLAGGED and logged with its fault; only frozen rows stay dead (Jekyll Kawajiri ep01).** `dead_footage.state_of(..., kept)` -> `flagged` (never in a dead run), `assemble.ladder_kept` reads the newest take-eye verdict's terminal, and assemble prints one `FLAGGED Tnn: kept best at the cap -- <rows>` line per admitted take for the owner's eye. ep01: T01 (gait), T10, T15, T16, T19, T20, T21, T24.
- **2026-10-18 -- owner 2026-10-18: GPU when idle, CPU when rendering.** "If the GPU is rendering, do this on the CPU; if the GPU is empty, do it on the GPU." `studio/compute_device.device_for(job, need_gb)`: cuda only when the ComfyUI queue is empty (twice, 2 s apart), no GPU claim is live and the VRAM is free after a /free sent on an empty queue; any failure is cpu, today's path byte for byte; every decision logged with its reason (`library/.device/decisions.jsonl`); `VISURENA_DEVICE=cpu` forces cpu. Wired: whisper (`studio/routed_whisper` + `studio/whisper_worker` under the embedded python: 22 ep01 lines 498 s CPU -> 9 s GPU, transcripts identical) and the master encode (`studio/video_encoder`: NVENC p7 cq = crf + 5, SSIM-matched to x264 slow crf 14). Next: facenet/EasyOCR through an embedded-python worker; a render claim for the take ladder's between-round gap.
- **2026-10-19 -- owner: the face refine reaches every soft face ("why our fix skipped those shots? fix that, and all fixes that fit without bloating run time").** No plan size and no face-at-end gate the refine; its tracker (face_yolov8m.pt in a worker under the embedded python, GPU when idle, MTCNN behind it) reads every faced take but an insert, and each track whose smallest face is under 120 px (was 60) is refined at a size-scaled denoise (0.45 at 60 px, 0.40-0.55). ComfyUI-H3-FaceRefine's smoothing and cut handling ported, not installed. ep01 replay: 11 takes instead of 2, about 19 min more GPU. The keep/decline walls are unchanged. (studio/face_refine.py, studio/face_detect.py, studio/face_track.py; docs/calibration/face_refine.md)
- **2026-10-19 -- owner ruling (chosen from options): "Own repair clock" -- an owner-ordered repair of a DELIVERED episode runs on its own capped clock, charged and logged separately; the 6 h rule stays intact for normal runs.** Context: Jekyll HEL ep01 had spent 21,673 s, so every launch cut the face refine (REFINE CUT) and the tiny-face rung (TINY FACE CUT) (docs/audit/2026-10-19_face_blur/RERUN.md section 0). Built: an owner redo receipt (K12, an order row `by` owner) naming a step of an episode whose manifest exists opens `repair.json`; the budget is charged from the repair's start under its cap (`studio/repair_clock.cap_for`: the earliest redone step's and every later step's share + the judges' pool, 8,580 s for a redo of 09, never past 6 h; `CAP repair` when spent); its run rows are tagged `repair` and never count in the episode's 6 h; the finish line prints both; the window closes when its drive ends. A normal launch (no owner order, an autopilot cure, an undelivered episode) is unchanged. With it (ship review of the tiny-face rung): a 1024 draw is kept when NO WORSE than the take it replaces (its hard faults a subset of the old take's), and a draw whose canvas scale fails never lands (the old take comes back, a lost take).
- **2026-10-20 -- the owner's veto list V2 and V3 stand as defaulted (none of V1-V11 vetoed; owner: "do the retro one ... made all changes"): the face refine is cut LAST for time and a take it skips parks the publish; 120 px is a refine-eligibility constant, logged, never a wall on the master.** Built by deadline retro package C (architecture/decisions/2026-10-20_face_refine_cut_last.md): step 09 holds N takes x 81 s (ep01's repair refine, 972 s over 12 takes) from its start and cuts a re-measure of unchanged bytes before it; refine_rest cuts the refine only when its own price leaves no reserve; a take still cut ships flagged and a FACE_REFINE terminal in learnings.jsonl holds the publish lock (no judge clears it; a later pass that refines it, or the owner's waiver, releases it). Step 09 ends with the face list in refine.json `face_list` (log only; step 11 QC reads it). An unread outside-the-core measure refuses the paste.
- **2026-10-20 -- the owner's veto list V4 and V7 stand as defaulted (unvetoed): code is held still under a live drive; a pause is a lease {by, why, expires}, a retro pause expires at 2 h and notifies, and the autopilot resumes only pauses it set itself.** Built by deadline retro package E (architecture/decisions/2026-10-20_ops_leases_and_watchdog.md).
- **2026-10-20 -- the owner's veto list V5 and V6 stand as defaulted (unvetoed): an owner-reported defect gets one research fleet, at most 2 build rounds and about 3 h of agent wall, then the repaired master ships or the owner gets a one-line stop; a retro change to prompt words, the ladder or the freeze merges only with an empty (or named) replay diff on delivered ep01.** Built by deadline retro packages A, B2 and G: the launch's dry check, `scripts/episode/regress_delivered.py` in the default test run, and the agent rules in `.claude/skills/episode/OPERATOR.md` "Fixing an owner-reported defect" (round 0 counts the defect and predicts a number; at most 2 fix rounds, capped on rounds, never minutes).
- **2026-10-20 -- the standing publish approval names its episodes (five-iterations build B1.3, enforcing the owner's 2026-10-12 rule "no upload unless asked").** `studio/standing_approval.ok(book, n)` holds only when `publish/standing.json` lists `n` in `episodes`; a file without the list approves nothing. Jekyll's file was signed for ep01 ("Upload it", master_iter3) and as written would have uploaded ep02-ep10 unasked on a resume. Step 13 parks an unlisted episode at G-STANDING, the autopilot holds it at HELD_PUBLISH, and repair_dry_check names the episode. To publish ep02 the owner adds `"episodes": [1, 2]`. Evidence: `docs/audit/2026-10-20_five_iterations/FINAL.md`.
- **2026-10-21 -- the face debate (five rounds, owner order "be 100% convinced through debate and make changes"; `docs/audit/2026-10-21_face_debate/`): what landed and what the owner still rules on.** Landed (A25-A32, no render setting touched): measured clock columns on every refine row and `gpu_busy_s` on the stage row (`episode_clock.cpu_s`); `readable_clause` / `warp_min_px` / `yolo_min_px`; the master eye's cache key without the plan row; the panel eye's books in the signed verdict; panel_dq's `face_px_768` + `tiny_face_advisory` (log only); the GPU whisper worker lazy, respawned once, stderr kept. Rulings recorded as defaults (veto at will): (1) **H3 licence**: the MiniMax-H3 LICENSE names the USA among the Excluded Territories (I.5) and offers a licence on application (II; platform.minimax.io/h3-license); the owner is in Seattle; application status unknown; nothing graded here -- the owner's attorney's item. (2) **Plan-ahead (C11) stays OFF** until ep02's `timing.jsonl` exists (prize <= 28.6 min against a 4.0 h projection). (3) **The A21 bench ran 2026-10-21 in the paused window** under a 45 priced-minute stop (numbers in FINAL.md); no F2 setting changed on its evidence. (4) **Asked**: the anime-eye ONNX download (deepghs/anime_eye_detection, OpenRAIL; `DOWNLOADS_NEEDED.md`) that gates C1, and whether a 2160 square delivery may even be benched (it changes the shipped spec; not benched).
- **2026-10-21 -- the owner's order "build a system or test framework to build that confidence first; I don't need confidence out of thin air; I need proof-backed confidence": confidence is a pass count over distinct points, with its Wilson lower bound, from checks that run the real pipeline code on recorded inputs, never an agent's opinion.** The ep02 proof harness (architecture/decisions/2026-10-21_proof_harness.md; design `docs/audit/2026-10-21_ep02_proof/DESIGN.md`, all 19 skeptic changes taken, five with a change) rehearses on a fenced sandbox library only, never `library/`, with no GPU, TTS, YouTube or paid call; the real autopilot stays paused; `scripts/proof/confidence.py` writes CONFIDENCE_iterN.md (PROVEN / PARTIAL / FAILING / REAL-RUN). The staged real runs SR-0..SR-5 each wait for the owner's explicit go. First result: the time model failed its pre-registered back-test (2 of 4 within 0.15), so Q5 (ep02 under 6 h) is not provable from records.
- **2026-10-21 -- the shot-framework panel's final ruling on the prompt-bench findings (for the owner's veto; `docs/audit/2026-10-21_shot_framework/FRAMEWORK.md`): the anime-TV push rule is UNCHANGED (G-PUSH <= 2, G-LOCKED >= 0.5); R1, a held shot pushed as a freeze cure, is RETIRED (8 of 8 un-froze, 4 of 8 cut a head or hat), so no cure writes a push and a silent locked hold of 5 s or more is cut (G-HOLD, advisory); one rise an episode (G-RISE); tilt_up stays unmeasured on Kawajiri and the +6 px tilt threshold is void.** Landed: d3e6420 (defects D-a, D-b, D-d grammar, D-e lock, D-f); the pre-registered proof then reverted D-b whole and D-a over a shoulder (T13 failed its take gate on 3 of 3 renders) and the framework rows B-1..B-6; HELD for bench R2-3: D-c and the D-d verb count. No stage, step, runner, agent or owner gate moved; the architecture page's grammar gate list names G-RISE and G-HOLD. Research R2-1..R2-8 waits for the owner's go.
- **2026-10-21 ~19:05 PDT -- owner: "do all these".** (1) **FastH3-Omni**: write the split pair (22.1 GB base on C:\models_staging, 126 MB PDD LoRA in ComfyUI loras) if C: has the space (39 GB free), GPU cap raised to 45 min; production stays on Singularity v1.3 until a pre-registered face win. (2) **Lip sync**: a 25-40 min GPU bench (production vs frozen audio latent vs ref-only vs frozen+guide, >= 6 seeds/arm) once a mouth reader passes the exam. (3) **Growth** (`docs/audit/2026-10-21_growth_publishable/VERDICT.md`): add yt-analytics.readonly at the next weekly re-consent; retitle both compilations for search with chapters; one playlist per book with next/previous links; UNLIST (never delete) the ~55 generic 2026-01/02 AI stories; Apache-2.0 LICENSE + root README on the public repo, gitleaks over the full history first, remove btr.pdf and ffmpeg2pass-0.log, then push. (4) **The 9 craft-panel questions** (`docs/audit/2026-10-21_craft_process/RULING.md` section 6) take their stated defaults: dialogue ceiling stays 0.35 (A16 prints both rulers); an `off` line counts in the dial; G-REACT unchanged until T3's count; inner cap 8 words HARD until T16 passes; the button is the book's line when it carries the motif; tease off; one length band; craft card does not exist; the analytics scope is ADDED (item 3 overrides Q8's default). The H3 licence question stays the owner's attorney's item.
- **2026-10-21 -- G-INORDER is advisory after public (main session, recorded for the owner's veto; growth review `docs/audit/2026-10-21_growth_publishable/actions/FOLLOWUPS.md` item 2).** A failed playlist upkeep in step 13 (quota or token, the 5,000-character wall, a deleted predecessor) records a G-INORDER `flag` in `learnings.jsonl` and lets the /shorts/ poll and `done()` proceed, as G-SHORTS does, instead of stopping a step whose video is already public; a later step-13 run retries the upkeep idempotently and a landed retry writes a `pass` row so the publish lock does not hold a recut on it. For the owner's veto.
- **2026-10-21 -- the drive names every park at t=0 (craft ruling A23, wave 3; the owner accepted the craft defaults 2026-10-21).** `scripts/episode/drive.py` runs `preflight` after the dry check: the proof harness's chapter audit (`scripts/proof/preconditions.py`, imported, never moved), `publish/standing.json` listing the episode, and the YouTube token's age plus the 6 h budget against 7 days. Each finding prints "refuse now" (only a chapter with no text) or "will park at step N"; a publish-only gap always parks, never refuses (architecture/decisions/2026-10-21_t0_preflight.md). For the owner's veto.
- **2026-10-26 ~09:20 PDT -- owner: "focus on episode 2 first ... try to finish it in 6 hours"; the research fleet stays stopped ("do not restart any debates").** Rulings (asked, answered): (1) **Upload**: Jekyll ep02 uploads public on its own once the publish lock clears (`publish/standing.json` now lists `episodes: [2]`; the director sign-off still holds every cut). (2) **Fault 5 (TRIAGE_window2)**: option (b) -- when the plan ladder's last climb is still refused, the episode goes downstream FLAGGED, never parks; DESIGN.md's F5 row now expects that, and every such flag is fixed before the cut is signed. (3) **Voice ceiling**: Jekyll's Hyde-Jekyll pair ceiling is filed on the 16 kHz ruler (`below 0.18, ruler ecapa16`, from `docs/audit/2026-10-21_voice_bench/fix/registers_proposed.json`; the untagged 0.55 row it replaces is kept in the row's `replaces`). (4) **Over 6 h**: the run keeps going to a finished, fully checked master and reports where the time went; the 6 h is a target, not a stop.
