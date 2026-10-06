# REPO INTEGRATOR — minimal delta for an unattended supervisor + a "brain" session

Repo: `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio` @ 65dc097 (master, clean). Read-only pass, 2026-10-06.
Live state: WotW (`library/20260827135508_the-war-of-the-worlds`) ep01-18 published, ep19 parked on an
uncaught `studio.llm.OverBudget` ($3.10 of $3.00) — `episodes/ep19/drive.jsonl` last row `{"event":"end","code":1}`
at 2026-10-06T14:43, `drive_run01.log` tail = the traceback through `studio/plan_ladder.py:297 → :248 →
agents/episode_writer.py:125 → studio/llm.py:148`.

---

## 1. What exists (the loop, the refusals, the signals)

### drive.py — `scripts/episode/drive.py`
| what | where |
|---|---|
| Refuses a dirty tree (tracked change or untracked file outside `library/`), **exit 2**, Telegram | `drive.py:95-97`, `studio/episode_drive.py:39-41` |
| Bakes missing title cards first (`titles_batch.missing`); card for THIS ep unbakeable → **exit 2** | `drive.py:103-114` |
| Warns (never stops) when HEAD moved since the episode's first SHA | `drive.py:117-121`, `episode_drive.first_sha` 44-57 |
| `drive.jsonl` events: `start{sha}`, `run{n,sha,outcome}`, `end{code,sha}` (UTC ts) | `drive.py:69-71, 122, 127, 133` |
| Runs `uv run --no-sync python episode.py <codex> <n>` → `drive_runNN.log`; polls 30 s; 20-min silence → one Telegram | `drive.py:74-90`, `episode_drive.SILENCE_S` 17 |
| Loop: `completed`→0; `deferred`→resume (≤ MAX_RUNS=6) unless `over_budget()` (timing.jsonl ≥ 18 000 s); `refused`/`failed`→**exit 1 after ONE run** | `episode_drive.drive` 68-88, `drive.py:129-132` |
| `outcome()`: `"EPISODE completed"`→completed; `"DEFERRED: … needs N s"`→deferred (historical only); any other `DEFERRED`→**refused** (a PLAN deferral is never auto-resumed, by design ep14); `REFUSED`→refused; else **failed** | `episode_drive.py:22-36` |
| Telegram = sibling repo `comfy_studio/.../notify_bench.py` (absolute path constant) | `drive.py:50, 59-66` |

**Gap:** `outcome()` has no word for an `OWNER …` escalation line (`studio/escalate.py:20`) nor for `OverBudget`;
both read as **failed**. The ep19 stop is therefore indistinguishable from a crash in `drive.jsonl`.

### episode.py (root) — the runner
- Explicit form `episode.py <codex> <n>`: claims its desk row; **HELD → `SystemExit("REFUSED: … is held")`** (`episode.py:131`); other states WARN and run (134).
- `run_unit` → `step_runner.run_steps` inside `llm.spend_context(conn, codex, "episode", None, unit="epNN")` (`episode.py:94`); outcomes `completed|escalated|deferred`; a raise marks the stage `failed` (96-98).
- `exit_code`: 0 all completed, **2 (PARKED)** for escalated/deferred/skipped (`episode.py:38, 159-161`).

### step_runner — `studio/step_runner.py`
- `Escalation`→`escalated`, `Deferred`→`deferred` (event + log + printed line, unit stops) 66-72; `SystemExit`→`RuntimeError` + event `failed` 73-75; any `Exception`→`failed` 76-78.
- GPU step while `ctx.held()` (RENDER_HOLD file or a hold row) → `SystemExit("HELD: …")` 57-59, 87-88.
- `redo` work orders re-run a done step (41-54); `take_orders` applied once per run (35-38).

### stages.yaml `episode` (525-954): steps 01 bind … 13 publish; `deliverable: episodes/{unit}/manifest.json` (527); `requires: [analysis/06, refs/04]` (528). Step 13 out includes `uploads.jsonl` and in includes `publish/standing.json` (943-947).

### gates — `gates.yaml:15-21` + `studio/gate_policy.py`
Every episode row is `auto` under `2026-09-24-automate-the-taste-gates`; PLAN `terminal: keep_best, battery_terminal: defer`; EYE_PANELS/EYE_TAKES keep_best (caps 2); MASTER flag; RENDER `ceiling_seconds: 18000`. `gate_policy.check` refuses an auto row without a decision id in `docs/DECISIONS.md` (57-67). `judged_gate.clear` (`studio/judged_gate.py:163-184`): pass → signed + a `pass` learning; fault → priced rungs; out of rungs/time → `ended()` terminal, signed **flagged**, audit row. A no from the budget is **terminal in the same run** (65-87). `INVALID VERDICT` (a judge repeating one fault > 12×) is a `SystemExit` (100-105).

### deferral / escalation
- `studio/deferral.py:10-19` `Deferred(gate, aside, note)` → line `DEFERRED PLAN | <label> | <note> | aside: episodes/epNN/plan.deferred.json`. Raised at **one** site: `scripts/episode/step_02_plan.py:238` (after `plan_repair --from-aside` 231-236 and `cure_aside_first` 191-200 both failed).
- `studio/escalate.py:11-20` `Escalation(gate, verdict, ask)` → `OWNER <gate> | … | sign: <file>`. Live episode sites: **G-STANDING only** (`step_13_publish.py:179-180` via `studio/standing_approval.py:47-52`; signal = `library/<book>/publish/standing.json` absent/malformed). `studio/eye_verdict.require:63` also raises but a test forbids the word in any episode step (`tests/test_no_refs_or_episode_step_raises_an_escalation.py:19-21`).

### money — `studio/llm.py`, `studio/spend.py`
- `OverBudget` (`llm.py:116`) raised by `guard_spend` (139-149) **before** a paid call when `spend.unit_spent(conn, codex, unit) + estimated_cost > models.yaml money.episode_ceiling_usd (3.00)`. Only active inside a `spend_context` with a unit (142).
- `usage` table DDL `spend.py:24-38` (+ `unit` column 63): `recorded_at, codex_id, stage, step_id, tier, model, input_tokens, output_tokens, cost_usd, unit`. `record()` 67-84 prices via `rate_for(model)` (NULL when unpriced). `unit_spent` 103-105 sums **all stages** for `(codex_id, unit)` — a `stage='brain'` row with `unit='ep19'` therefore counts against the same $3 wall with zero new code.
- Today: ep19 `stage=episode step_id=02`: 34 calls, **$3.099**; ep18: 48 calls, $1.054 (db query, this pass).
- `OverBudget` is caught only in `studio/move_llm.py:113` and `studio/plan_llm_cures.py:153`. **Not** in `plan_ladder.Desk.write` (242-268 catches `ValidationError`/`StructuredOutputException` only), not in `judged_gate.climbed`, not in `step_02`, not in `step_runner` → it is a **crash** (`failed`), not a terminal. This is the ep19 stop.

### clock — `studio/run_budget.py`, `studio/episode_clock.py`
`EPISODE_CEILING_SECONDS = 5 h` (23), shares per step (28-33); `spent_before(home)` sums `timing.jsonl` (113-129) and `Budget.charge` makes the ceiling episode-wide across resumes (`studio/episode_run.py:64`). `timing.jsonl` rows `{stage, started, ended, seconds, ok, note}` (`episode_clock.stamp` 53-63). Step 09 refuses a render the ceiling cannot pay **except** round 0 or a zero-cost (judge-only) pass (`step_09_shoot.py:190-203`).

### desk / orders — `studio/tick.py`, `studio/work_orders.py`
- The episode slate is **every `episodes/epNN` folder on disk** (`tick.py:59-71`); blocked→queued when `requires` done and first inputs exist (134-151). No notion of "the next chapter": `drive.py:99` `home.mkdir` is what makes a unit exist.
- `work_orders.KINDS = hold, lift, redo, bump, retry, requeue, acknowledge` (28); `_retry` requeues a `deferred|failed` row (198-202); `redo` forces a done step to run again (212-216, consumed by `step_runner._done`). These are the existing, ledgered "responses" an autopilot can issue without touching a step.

### publish — `studio/publish_lock.py:98-104`
Stops = open terminals on gates NOT `auto` (none today) ∪ owner `review/waiver.json` ∪ `speaker_check.json ok:false` ∪ sign-off missing/stale. Sign-off is **generated from measures** (`scripts/publish/signoff.py`, step 13 line 182). Judge terminals auto-clear under `2026-10-01-no-human-input-at-publish` (`publish_lock.judge_waivers` 44-61; ledger `auto_cleared`, seen on ep16-18 upload rows).

---

## 2. The episode skill's hand instructions, classified

Source: `.claude/skills/episode/SKILL.md` (THE RUN 33-79, Rule One 83-128, chain 132-204, pictures 268-333, takes 337-376, before-leaving 380-393, resuming 408-417, send-back table 419-429), `GATES.md`, `LESSONS.md`, `.claude/agents/episode.md`.
(a) already code · (b) codeable deterministically · (c) genuinely needs judgment

| # | hand instruction (SKILL.md line) | class | where it is / would be |
|---|---|---|---|
| 1 | Clean tree, on master, code committed (41) | (a) refuse / **(c) the commit itself** | `drive.py:95`; a code change is a human/brain act outside the run |
| 2 | `nvidia-smi` + ComfyUI `/queue` idle before a run (42, 412) | (a)+(b) | `stage_run.wait_free` 95-102 waits 2 h; autopilot pre-check `comfy.busy()` (`studio/comfy.py:316`) |
| 3 | Bind the cast `--cast=a,b` (43, 89) | (a) | `step_01_bind.chapter_cast` 57-73 reads `analysis/scenes.json`; refuses only when the analysis names nobody (79) |
| 4 | Launch `drive.py` detached AND put a waiter on `drive.jsonl`; never end a turn with an unwatched run (45-52) | (b) | the supervisor loop |
| 5 | 02 plan: "nothing" (56); 05: "-" (57); 11: "-" (60) | (a) | `step_02` ladder + `plan_repair`; `step_05.autotrim` 112-121; `step_11` |
| 6 | 07-08: read the contact sheet while 09 renders (58, 330) | (a) | `judge:panel_eye` signs (stages 08_05); `storyboard/contact.png` is still written for a human |
| 7 | 09: read the take strips (59, 351) | (a) | `take_strip.py` + `judge:take_eye` (09_04) |
| 8 | 12: watch + listen full size; write the sign-off (61, 389-391) | (a) | retired by decision 2026-10-01; `signoff.py` from measures |
| 9 | Never hand-edit plan.json / heads / stills; never touch a timestamp (66-67) | (a) rule | nothing to build; the brain must be **denied** these (see §6) |
| 10 | One launcher, no guard-stops, no bare step scripts mid-run (69) | (b) | autopilot calls `drive.py` only |
| 11 | No code changes on a live episode; fix, test, commit, then resume once (71) | **(c)** | the F-findings (§3) — a bug found in a run is a commit, not a runtime action |
| 12 | A terminal is not a pass; only the owner waives (72) | (a) | `publish_lock.judge_waivers` under the 2026-10-01 ruling |
| 13 | When the owner says upload it goes public (79) | (a) | step 13 + `publish/standing.json` (written for WotW) |
| 14 | Rule One sequence: cast_rows → step_02 → plan_check → `--prompts` before any grid (89-94) | (a) | steps 01, 02, 06 in registry order |
| 15 | Look at every picture you draw; defining state first (274-281) | (a)/(c) | refs `judge:look` (gates.yaml:14); residual taste only |
| 16 | Match the cure to the cause table (356-366) | (a) | `take_ladder` rungs (stages 09_05), `studio/take_ladder.py:420-445` terminal |
| 17 | Retakes in one batched round with `--why` (368-374) | (a) | batched ladder (decision 2026-09-30) |
| 18 | Before publish: read `learnings.jsonl`, open terminals, fix or ask the owner (387-388) | (a) | `publish_lock.open_terminals` 36-41 + auto-clear |
| 19 | A test run stays private until he says public (393) | (a) | `approval.require("publish")` + standing.json |
| 20 | Resuming: read `drive.jsonl` + last log, say where the episode is, resume with drive.py once (410-411) | (b) read/resume · (c) "say where" | autopilot `last_outcome()`; a one-paragraph status is the only brain-shaped part |
| 21 | If a job ignores `/interrupt`, restart ComfyUI (413; memory `project_comfy_restart`) | (b) | `comfy.down()` already waits 600 s for a restart (`comfy.py:106-115`); the restart itself is a kill-by-PID + relaunch script, not yet code |
| 22 | Kill a run by its process tree, never `uv.exe` alone (416) | (b) | memory `project_kill_run_tree`; codeable (`CommandLine` match) |
| 23 | Send-back table (421-429): plan refusal → plan.py; wrong clothes → cast_rows; missing subject → G-SCALE cells; panel fault → redraw grid; count wrong → extras; QC gap → the silent shot | (a) ×5 · **(c)** wrong-person/wardrobe | ladders, `G-CROWD` cure, `step_05.autotrim`, panel ladder; a wrong row in `refs.json` is a refs-department correction |
| 24 | Agent def: "Decide, go, correct after feedback; never hand him a form" (`.claude/agents/episode.md`) | (a) policy | autopilot's default is run, not ask |

Count: 24 instructions → **(a) 18, (b) 6, (c) 3** (the commit after a found bug; a wrong cast row/wardrobe seen in a picture; the one-paragraph "where are we" narrative). Tracker F5 (`architecture/plan/2026-10-05_self_curing_pipeline.md:33`) already says THE RUN table is stale and the agent's job is "WATCH + report, not fix".

---

## 3. F1-F20 — code or brain?

`architecture/plan/2026-10-05_self_curing_pipeline.md:29-48`.

| class | findings | n |
|---|---|---|
| Fix landed as **code** (a bug or a missing cure) | F6, F7, F8, F9, F11, F14, F15, F17, F18, F19, F20 | 11 |
| Fix is **code/config proposed**, not landed | F1 (xdist/timeout), F4 (migrate in refs 04), F10 (pre-launch dry check), F12 (deliverable key, in progress) | 4 |
| **Doc / process** (skill, test hygiene, watcher) | F2, F5, F13, F16 | 4 |
| **Owner's one-time hand** (not brain, not code) | F3 (`standing.json`) | 1 |
| Needed a brain **at runtime** to resolve | — | **0** |

But: F7, F8, F9, F11, F14, F17, F18, F19, F20 (9 of 20) were **diagnosed** by a Claude session reading a parked run's log/plan — the fix was a commit, which non-negotiable #4 forbids on a live episode. So the honest brain job for an F-class stop is: triage the stop into {retry, cure-order, block} and write the finding row (`Seen | Cost | Change`) for a human commit — **never** patch, never waive. A brain could not have shortened ep19 by more than the retry/triage it would have decided in seconds instead of hours of waiting.

---

## 4. Every hand-back point today → signal on disk → correct automated response

Classes: **retry** (relaunch drive.py), **cure** (a `work_orders` order, then relaunch), **wait** (owner's brake), **brain** (SDK triage), **block** (stop + report; a human act follows).

| # | hand-back (file:line) | how it surfaces | signal on disk | response |
|---|---|---|---|---|
| H1 | dirty tree `drive.py:95-97` | exit 2, Telegram | `git status --porcelain` non-empty outside `library/`; no new `start` row | **block** (a commit is human; never auto-commit) |
| H2 | title card unbakeable `drive.py:109-113` | exit 2 | `title/epNN.mp4` missing after `titles_batch` | retry ×1 → **block** |
| H3 | PLAN deferred `step_02_plan.py:238` | `DEFERRED PLAN \| … \| aside:` → `outcome()=refused` → exit 1 after one run | `episodes/epNN/plan.deferred.json` (`passes`, `faults[].note`), `learnings.jsonl` last PLAN row `terminal:true action:keep_best … -> defer` | **retry ×2** (each relaunch runs `cure_aside_first` for $0, `step_02:191-200`, and `resume()` from the aside on the reasoner `plan_ladder.py:230-240`); still deferred → **brain** reads `faults[].note` → `block` with a finding (a battery rule the writer cannot satisfy = F18/F19 class) |
| H4 | `OverBudget` `llm.py:148` uncaught (`plan_ladder.py:248`, `judged_gate.climbed`) | traceback → `failed` → exit 1 | `drive_runNN.log` tail `studio.llm.OverBudget: episode epNN has spent $X of $3.00`; `usage` `unit_spent ≥ 3.00` | **block (money)** — a retry costs $0 but cannot progress. Code fix (not brain): catch `OverBudget` in `Desk.write` → `self.pending = ["MONEY: …"]` so the ladder ends at its terminal (`keep_best`/`defer`) instead of crashing (~6 lines) |
| H5 | refs row/sheet missing → battery `CAST BOUND` → PLAN defer; `step_01:79` nobody in the analysis | as H3 / `REFUSED` | `refs/refs.json` lacks the row; `plan.deferred.json` note `CAST BOUND` | **cure**: run the refs runner `refs.py <book>` (SKILL.md:149) then retry; still missing → **block** (refs department) |
| H6 | speech gap after trim `step_05:112-121` (`REFUSED` / `SystemExit(why)`) | `failed` | log `speech gap … over 6.0 s`; `placed.json` fresh | rendered → **block**; not rendered → **cure** `redo 02` then retry (the writer gets the measured hole as a refusal line) — today a hand |
| H7 | `step_07:116` no shots; `step_08:105` no panels; `step_09:210` no takes | `failed` | log line; `storyboard/`, `takes/r2v/` empty | 07 → **block** (plan broken); 08/09 → **retry ×1** (ComfyUI), then **block** |
| H8 | `step_09:187` takes wait on panels | `failed` | `eye_*.json` older than a panel, or a panel verdict missing | **cure** `redo 08` → retry |
| H9 | `step_09:201` ceiling refuses the render | `failed` | `timing.jsonl` sum vs 18 000; log `the takes want N s and the episode ceiling leaves M s` | **retry ×1** (a resume with takes on disk is a judge-only pass, `step_09:195-200`), then **block** (the owner's GPU hours) |
| H10 | `step_09:114` RENDER not auto | `failed` | `gates.yaml` row | **block** (config) |
| H11 | `step_11:148/158` qc FAIL for these bytes | `failed` | `episodes/epNN/qc_r2v.json` `passed:false`, rows naming the fault | **brain → cure**: a silence/sound row → `redo 10` (recut) then retry; a take row → `redo 09`; else **block**. Deterministic mapping is possible from `qc.json` row names (b), the brain is only the fallback |
| H12 | `step_11:152/155` qc.py did not finish | `failed` | `qc_r2v.json` missing / stale sha8 | **retry ×1** |
| H13 | `judged_gate.py:103` INVALID VERDICT | `failed` | log `INVALID VERDICT: <gate>` | **block** (judge bug → commit) |
| H14 | `stage_run.py:110` queue busy 2 h | `failed` | log `ComfyUI's queue stayed busy`; `/queue` | **cure (infra)**: comfy restart (kill `main.py` PID + relaunch; memory `project_comfy_restart`) → retry; a second time → **block** |
| H15 | `stage_run.py:119` script exit rc; any `Traceback` | `failed` | log | `comfy.transient()`/`down()` text → **retry ×1**; else **brain** triage → `retry` or `block` + finding row |
| H16 | `stage_run.py:38` unregistered book | `failed` | `codex` table | **block** |
| H17 | HELD `step_runner.py:59`, `episode.py:131`; RENDER_HOLD `approval.py:19` | `SystemExit`/`failed` | `RENDER_HOLD` file at repo root; `holds` table rows (`work_orders.active_holds`) | **wait** (poll until lifted; never lift) |
| H18 | G-STANDING `step_13:179-180` | `OWNER G-STANDING \| …`, PARKED 2 → drive `failed` | `library/<book>/publish/standing.json` absent | **block** (owner's one-time hand per book; written at book setup per F3) |
| H19 | `step_13:189` not public; `:107` no ledger row | `failed` | `uploads.jsonl` lacks `privacy:"public"` row for the sha8 | **retry ×1** (YouTube API), then **block** |
| H20 | `publish_lock.speaker_stops` 71-76 | upload refused | `review/speaker_check.json` `ok:false` | **block** (voice recast is the refs/cast department) |
| H21 | G-SHORTS advisory `step_13:150-155` | learning `flag`, no stop | `learnings.jsonl` G-SHORTS | none |
| H22 | clock spent after a deferral `episode_drive.py:83-86` | exit 1 | `timing.jsonl` ≥ 18 000 | as H9 |
| H23 | silent 20 min `drive.py:86-89` | Telegram, run continues | `drive_runNN.log` mtime | none until 2 h: then H14 path |
| H24 | still deferred after 6 runs `episode_drive.py:87-88` | exit 1 | `drive.jsonl` six `run` rows | **brain** triage → block |
| H25 | series: which chapter next | nothing exists | `uploads.jsonl` public rows vs `source/chapters/ch_NN.json` | **code** (§5) |

Classes: retry 8 · cure 5 · wait 1 · brain 4 (H3-fallback, H11-fallback, H15, H24) · block 11 (most are human-only: commit, money, owner's hand). Nothing here asks the brain to write a plan, a verdict, a waiver, or a patch.

---

## 5. The series driver

- Unit grammar: one chapter = one episode, `ep{n:02d}` (`studio/episode_run.py:4-6, 24-25`).
- Chapter list: `scripts/episode/titles_batch.chapters_of(book)` 27-33 reads `source/chapters/ch_NN.json` (ch_00 excluded) — WotW has 27; `source/book.json["episodes"] = 27` (WotW only; the "Ep 16/27" title uses it, `uploads.jsonl`).
- Published = `uploads.jsonl` row `privacy:"public"` for the episode (`step_13.public_row` 76-78, `yp.ledger_path`).
- **No code picks the next chapter.** The desk's slate is folders on disk (`tick.py:59-71`); `drive.py:99` creates the folder. `episode.py <codex>` (queue form) runs what is queued and exits (150-156).
- `SERIES_GOAL.md` (`docs/SERIES_GOAL.md`, `library/20260822113400_a-study-in-scarlet/SERIES_GOAL.md`) is a **prose watchdog for a Claude session** on A Study in Scarlet, chapters 4-14, discharged 2026-09-18 (docs copy line 65). Its ledger `SERIES_PROGRESS.json` exists only for Scarlet. WotW has neither. It is not code and nothing reads it.
- Pre-requisites per chapter the pipeline already handles: cast from the analysis (`step_01.chapter_cast`), title cards (`drive.py:103-114`), places/sheets just-in-time (steps 03, 07 stage sheets). What it does NOT handle: a new character's **sheet** (refs stage 04) — `CAST BOUND` refuses (GATES.md:29) → H5.

`next_unit(book)` = `min(n for n in chapters_of(book) if not public(n))`, capped at `book.json["episodes"]` when present. For WotW today → 19 (in flight, resumes).

---

## 6. Output: hand-back → signal → response → exists? / to build

| hand-back | signal | response | exists (file) | to build (file, ~lines) |
|---|---|---|---|---|
| H1 dirty tree | porcelain | block | `drive.py:95`, `episode_drive.dirty` | `autopilot.preflight` (6) |
| H2 title card | `title/epNN.mp4` | retry→block | `drive.py:103-114` | counts in `autopilot.loop` |
| H3 PLAN deferred | `plan.deferred.json` | retry×2 → brain → block | cure: `step_02:191-200`, `plan_ladder.resume` | `autopilot.classify` row (regex `^DEFERRED PLAN`), `brain.ask` |
| H4 OverBudget | log `OverBudget`, usage ≥ 3 | block | wall: `llm.py:139-149` | **fix** `plan_ladder.Desk.write` catch (6) + `episode_drive.outcome` word `overbudget` (2) |
| H5 refs missing | `refs.json`, aside note `CAST BOUND` | cure: refs runner → retry | `refs.py` (root) | `autopilot.cure("refs")` (8) |
| H6 speech gap | log, `placed.json` | redo 02 / block | `work_orders.order(kind="redo", step_id="02")` | classify row (2) |
| H7-H9, H12, H19 | log line | retry×1 | `drive.py` | classify rows (1 each) |
| H8 takes wait on panels | log | redo 08 | `work_orders.redo` | classify row |
| H11 qc FAIL | `qc_r2v.json` rows | redo 10 / redo 09 / brain | `work_orders.redo`; stages 11_02 | `autopilot.qc_cure(report)` (12) |
| H13, H10, H16, H18, H20 | log / config / file | block | — | classify rows |
| H14 queue busy | `/queue`, log | comfy restart → retry | `comfy.down/busy` | `autopilot.restart_comfy()` (12) — kill `main.py` PID + relaunch portable python (memory) |
| H15 crash | traceback | transient → retry; else brain | `comfy.transient` 102-103 | classify fallback → `brain.ask` |
| H17 HELD | `RENDER_HOLD`, `holds` | wait | `approval.HOLD`, `work_orders.active_holds` | `autopilot.wait_brake()` (8) |
| H24 6 deferrals | `drive.jsonl` | brain → block | `episode_drive.MAX_RUNS` | — |
| H25 next chapter | `uploads.jsonl` + `ch_NN.json` | code | `titles_batch.chapters_of`, `step_13.public_row` | `autopilot.next_unit(book)` (10) |
| brain spend | `usage` stage=`brain` | ledgered + walled | `spend.record` 67-84, `llm.guard_spend` | `brain.ledger` (8) + models.yaml rate key (2) |

### The shortest build

**A. `scripts/episode/autopilot.py` — the supervisor (~110 lines, 9 functions, each 10-20 lines, each with a test)**
1. `next_unit(book) -> int | None` — chapters_of minus public rows; cap by `book.json["episodes"]`.
2. `preflight(porcelain, busy) -> str | None` — H1/H2 reasons, no spawn.
3. `last_outcome(home) -> dict` — last `run` row + `end` code from `drive.jsonl`, tail of the last `drive_runNN.log` (`episode_drive.tail`).
4. `classify(tail, home) -> Verdict` — an ordered regex table over the H-list → `kind ∈ {completed, retry, cure, wait, brain, block}`, `order: (kind, step_id) | None`, `why`. Pure.
5. `cure(conn, codex, unit, order)` — `work_orders.order(...)` only (`redo`/`retry`/`requeue`); never a file edit.
6. `wait_brake(held, sleep, cap)` — poll `approval.HOLD.exists() or work_orders.active_holds(...)`.
7. `launch(codex, n) -> int` — `subprocess.run([uv, run, --no-sync, python, scripts/episode/drive.py, codex, n])`; the ONE spawn.
8. `loop(book, launch, classify, brain, notify, caps) -> int` — pure driver like `episode_drive.drive`: per unit, `launch → classify → {retry|cure→launch | wait | brain→verdict | block}`, retry/cure caps (2/2), then `next_unit`. Writes `episodes/epNN/autopilot.jsonl` rows `{ts, unit, launch, kind, why, order}` (relative paths only).
9. `main(argv)` — `<codex> [--until=N] [--once]`; exit 0 when `next_unit` is None.
Supervisor-level stop (not per unit): a `block` → Telegram via `drive.notify` + exit 1 with the finding row text.

**B. `studio/brain.py` — the SDK wrapper (~70 lines, 5 functions)**
1. `brief(home, tail, learnings, spent_usd) -> str` — book-relative paths, last 40 log lines, last learning per gate, `plan.deferred.json` fault notes, the allowed answers. No absolute path (`tests/test_no_artefact_stores_a_drive_letter.py` pattern).
2. `ask(brief, *, unit_ctx, _client=None) -> BrainVerdict` — pydantic `{response: Literal["retry","cure","block"], order: {kind, step_id} | None, note: str}`; one `claude_agent_sdk.query(prompt, ClaudeAgentOptions(allowed_tools=[], max_turns=1, model=<models.yaml brain tier>))` (read-only, no tools: the brain never touches disk); `_client` is the test seam (the `FakeCaller` shape, `tests/publish_fixtures.py:39-49`). Verify the SDK call signature against the pinned version before writing it.
3. `walled(conn, codex, unit, model, prompt)` — `with llm.spend_context(conn, codex, "brain", step_id, unit=unit): llm.guard_spend(model, prompt)` → `OverBudget` → `block("money")`. Reuses the $3 wall; a separate `money.brain_ceiling_usd` would need `spend.stage_spent` (4 lines) — recommend the shared wall first.
4. `ledger(conn, codex, unit, step_id, model, usage)` — `spend.record(conn, codex, "brain", step_id, "brain", model, in, out, unit=unit)`; add the SDK model id to `models.yaml rates:` so `cost_usd` is not NULL (`spend.py:11-12` rule).
5. `allowed(verdict) -> BrainVerdict` — clamps `order.kind` to `{"redo","retry","requeue"}` and `step_id` to the registry (`registry.steps("episode")`); anything else → `block`. This is the CLAUDE.md line: Strands owns department calls, `stepwise`/`step_runner` owns the DAG, the brain only places orders the desk already accepts.

**C. Two small fixes in existing code (no new module)**
- `studio/plan_ladder.py:242-268` `Desk.write`: `except llm.OverBudget as over: self.pending = [f"MONEY: {over}"]; return` — the ladder ends at `terminal()` 305-313 (keep_best or defer) instead of a crash. Test: `tests/test_a_spent_wall_is_a_terminal_not_a_crash.py`.
- `studio/episode_drive.py:22-36` `outcome()`: `"OWNER "` → `"escalated"`, `"OverBudget"` → `"overbudget"` before the `failed` default; `drive()` treats both as stop-and-tell (same as refused). Test extends `tests/test_the_driver_resumes_and_reports.py`.

**D. Config**
- `models.yaml`: `tiers.brain` (provider/model used only for the ledger's `model_for`), `rates.<sdk model id>`; `money` unchanged.
- `pyproject.toml`: `claude-agent-sdk==<exact>` (uv add; then `uv sync --all-groups`, memory `project_uv_groups_sync`).

**E. Tests (no spend; fake drive, fake SDK)**
- `tests/test_autopilot_picks_the_next_chapter.py` — tmp book with `ch_01..03.json`, an `uploads.jsonl` public row for 1 → 2; cap by `book.json episodes`.
- `tests/test_autopilot_classifies_every_handback.py` — parametrized over the H-table log tails (the ep19 `OverBudget` tail, `DEFERRED PLAN |`, `OWNER G-STANDING |`, `REFUSED: qc FAIL`, `HELD:`, `queue stayed busy`, `EPISODE completed`) → expected kind/order.
- `tests/test_autopilot_loop_spawns_only_drive.py` — `launch` is a recording lambda; asserts the argv is `drive.py`, retry/cure caps hold, `block` stops, `wait` polls `held()` until False, `brain` is called once per block-candidate.
- `tests/test_autopilot_cures_through_work_orders.py` — a `redo 08` lands in `orders`/`work_orders` (`db.get_connection(tmp)` like `tests/test_step_runner.py:21-25`) and `step_runner._wants_redo` sees it.
- `tests/test_brain_is_ledgered_and_walled.py` — `FakeClient` returns a canned verdict + usage; asserts one `usage` row `stage='brain' unit='epNN'` with non-NULL `cost_usd`; `unit_spent` at 2.95 + estimate → `OverBudget` → `block("money")`; `allowed()` clamps `{"kind":"waiver"}` to `block`.
- `tests/test_brain_brief_stores_no_drive_letter.py` — brief text has no `D:\` / `C:\`.

**Not to build:** a second runner, a step caller, a plan/verdict/waiver writer, a Telegram path (reuse `drive.notify`), a `SERIES_PROGRESS.json` for WotW (the `uploads.jsonl` ledger + chapters on disk already answer it), a brain tool loop (allowed_tools=[]).

**Architecture page:** this is a new runner over the episode department → `architecture/index.html` Future tab + `architecture/decisions/2026-10-06_autopilot_and_brain.md` + `architecture/plan/` tracker + a `docs/DECISIONS.md` line, in the same commit (project CLAUDE.md).
