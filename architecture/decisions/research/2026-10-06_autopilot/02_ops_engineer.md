# OPS ENGINEER — the supervisor that triggers, monitors, and never stops silently

Repo: `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio`, Windows 11 Home 26200, uv, local ComfyUI
(`D:\Projects\KingdomOfViSuReNa\alpha\ComfyUI_windows_portable`, pid 16128 up since 10/1), claude CLI 2.1.158
at `C:\Users\vishn\AppData\Local\Microsoft\WinGet\...\claude.exe`. Owner ruling applied: no episode ever rests
on the owner; the one approval is the autopilot's design.

## 1. What drive.py already guarantees, and where it hands back

`scripts/episode/drive.py` (139 lines) + `studio/episode_drive.py` (88 lines):

| guarantee | where |
|---|---|
| refuses a dirty tree (tracked change, or untracked outside `library/`) -> exit **2** | drive.py:95-97, episode_drive.py:39-41 |
| bakes missing title cards book-wide first; refuses (exit 2) if THIS episode's card cannot bake | drive.py:103-114 |
| records the SHA, warns (does not stop) if code moved since the episode's first row | drive.py:115-122 |
| runs `episode.py <book> <n>` with stdout to `drive_runNN.log`, polls size every 30 s, Telegram ONCE after 20 min silence | drive.py:74-90, episode_drive.py:17,60 |
| classifies the run by its LOG TEXT: completed / deferred / refused / failed | episode_drive.py:22-36 |
| resumes only a budget deferral (historical form); a plan deferral or REFUSED or traceback = stop, exit 1; cap 6 runs | episode_drive.py:68-88 |
| refuses to resume once `timing.jsonl` sums >= 18 000 s | drive.py:131-132, run_budget.py:23,113-129 |
| ledger `episodes/epNN/drive.jsonl`: `{"event":"start","sha"}`, `{"event":"run","n","sha","outcome"}`, `{"event":"end","code"}` | drive.py:69-71,122,127,133 |
| Telegram via `comfy_studio/.../notify_bench.py text --message` (never fatal) | drive.py:50,59-66 |

Hand-backs to a human (every one is a process exit, nothing retries):

1. **Dirty tree** -> exit 2 before anything runs (drive.py:97).
2. **Title card unbakeable** -> exit 2 (drive.py:113).
3. **Plan deferral** -> `plan.deferred.json` written (studio/deferral.py, step_runner.py:63-71), `=== EPISODE deferred` printed, episode.py exit 2 (episode.py:38,161), drive outcome "refused" -> exit 1 (episode_drive.py:32-33, 80-82). ep19 did this three times today (drive.jsonl rows 2,5,8).
4. **OverBudget ($3 media wall)** -> `studio.llm.OverBudget` raised inside the writer (llm.py:116,139-149), uncaught -> traceback -> outcome "failed" -> exit 1. ep19 run 4 (drive.jsonl row 11; `drive_run01.log` last line `studio.llm.OverBudget: episode ep19 has spent $3.10 of its $3.00 ceiling`). **No JSON event exists for this**; only the traceback's last line.
5. **Dead clock** -> in-run: `Budget.ceiling_spent()` makes the rung terminal (run_budget.py:65-68, commit 18f147c); between runs drive refuses to resume (drive.py:131). Exit 1 with "ceiling spent" in the notify.
6. **Owner gate (Escalation)** -> only G-STANDING remains (step_13_publish.py:13-16); `publish/standing.json` exists for this book, so it never fires here. Exit 2 "escalated".
7. **Any traceback** (KeyError, ComfyUI EngineLost, etc.) -> outcome "failed", exit 1.
8. **Silence** -> a Telegram line, but the process keeps waiting forever (drive.py:86-89). A hung Qwen3-VL read (memory: run 18 lost 11 h) is NOT killed by drive.py.
9. **Crash of drive.py itself / reboot / the console** -> nothing records an "end" row; drive.jsonl ends on "start" or "run".

Nothing today looks at `uploads.jsonl`, picks the next chapter, or restarts anything.

## 2. Supervisor host: Task Scheduler running a long-lived `autopilot.py run`

**Choice: Windows Task Scheduler, task `visurena-autopilot`, action = the long-lived loop, re-armed every 5 min with
MultipleInstances=IgnoreNew.** The scheduler is the supervisor's supervisor; the loop is the drive's supervisor.

Why not the alternatives, on THIS box:
- **NSSM/WinSW service**: runs in session 0 under LocalSystem or a service account. `claude` auth lives in the user's
  `%USERPROFILE%\.claude\`, the YouTube token and `thikkana/.env` Telegram creds are user files, `uv` is user-installed,
  ComfyUI is launched in the interactive session. A service means a second identity to provision for every one of
  those; nothing is gained because the GPU server is reachable at 127.0.0.1:8188 from any session anyway.
- **Bare long-lived loop started from a terminal**: dies with the terminal and with the Claude session that started
  it — the exact failure this design exists to remove.
- **Precedent on the box**: `studio-foreman` (thikkana) is already a Task Scheduler task, PT5M repetition,
  IgnoreNew, user `vishn`, LogonType S4U, LastTaskResult 0 today at 09:02 — it works under this account's
  policy. Reuse the shape; do not reuse its 72 h ExecutionTimeLimit or DisallowStartIfOnBatteries.

Task definition (written by `autopilot.py install`, via `Register-ScheduledTask`):
- Action: `uv run --no-sync python scripts/episode/autopilot.py run`, WorkingDirectory = repo.
- Triggers: AtStartup; AtLogOn(vishn); Daily 00:00 with Repetition PT5M, no duration end.
- Settings: ExecutionTimeLimit PT0S (unlimited), MultipleInstances IgnoreNew, StartWhenAvailable true,
  RestartCount 3 / RestartInterval PT1M, DisallowStartIfOnBatteries false, WakeToRun true, RunOnlyIfIdle false.
- Principal: vishn, S4U, RunLevel Limited (same as foreman). If the brain's `claude` login fails under S4U
  (DPAPI), the install prints the one fallback: re-register with `-LogonType Password`.
- Sleep: `powercfg` today says AC standby 0, AC hibernate 0 (never) — verified. `install` asserts this and runs
  `powercfg /change standby-timeout-ac 0` if not.

Survival matrix:
| event | what happens |
|---|---|
| supervisor loop crashes | 5-min trigger finds no instance (IgnoreNew) and starts a new one; it reads the lock + heartbeat and adopts |
| reboot | AtStartup/AtLogOn start it; ComfyUI absent -> engine_ops.start() first (memory: `python_embeded\python.exe -s ComfyUI/main.py --windows-standalone-build --reserve-vram 2`, wait for `GET /system_stats`, ~2 min); then the derive step sees a lock whose pid is dead -> stale -> RELAUNCH, and episode.py skips every step whose output exists (step_runner.py:91) |
| drive.py python child dies | lock pid dead, drive.jsonl has no "end" after its last "start" -> crash counter +1 -> RELAUNCH; 3 crashes -> NEEDS_BRAIN(crash_loop) |
| hung ComfyUI | drive RUNNING, `drive_runNN.log` not grown for > 2 x `vitals.step_budget(step)` (studio/command_center/vitals.py:28) AND `GET /queue` shows the same `queue_running` prompt_id across the window (comfy.py:286-293) -> kill the run tree by CommandLine match (`episode.py`, `drive.py`, step scripts; memory kill-run-tree), kill `ComfyUI/main.py` pid, relaunch engine, wait /system_stats, RELAUNCH. Cap 2 engine restarts per episode -> PARK(engine) |
| engine unreachable > 600 s with no drive | restart it (same path); 3 failures/hour -> PARK(engine) and notify once |

Files (all under `library/`, gitignored, never an absolute path inside):
- `library/.autopilot/gpu.lock` — created with `os.open(O_CREAT|O_EXCL)`; body `{"drive_pid","started","book","episode"}`.
  One GPU, one episode: no launch while a live lock exists. **Stale** = pid absent from the table or its command
  line is not `drive.py <book> <n>` (reuse `studio/command_center/procs.py:find_drive`, `vitals.pid_alive`) -> remove, log `stale_lock`.
- `library/.autopilot/supervisor.lock` — own pid; same liveness test; the second instance exits 0 silently.
- `library/.autopilot/heartbeat.json` — `{"ts","tick","state","episode"}` every 30 s loop. A new instance that finds
  a heartbeat older than 10 min writes `supervisor_died_at` to the event log once.
- `library/<book>/autopilot/series.json` — the goal: `{"book","first":1,"last":<book.json episodes>,"paused":false}`.
- `library/<book>/autopilot/parked.jsonl` — one row per parked episode (see §3).
- `library/<book>/autopilot/status.json`, `events.jsonl` — §5.

## 3. State machine per episode — every transition reads a file or an exit code

States: `IDLE -> RUNNING -> {PUBLISHED | NEEDS_BRAIN(reason) | WAIT_TREE} ; NEEDS_BRAIN -> BRAIN_RUNNING -> {RELAUNCH -> RUNNING | PARKED(reason)}`.
`PARKED` replaces BLOCKED(owner): it is a RECORD, not a wait — the loop moves to N+1 in the same tick.

Derivation is pure over `(drive.jsonl rows, lock, process table, uploads.jsonl rows, home files, log tail)` — `studio/autopilot.py:derive()`.

| from | signal (exact) | to |
|---|---|---|
| IDLE | `uploads.jsonl` has a row `episode==N and privacy=="public"` (youtube_publish.py:67-96; row keys `episode,video_id,privacy,sha8,at,title`) | PUBLISHED (skip) |
| IDLE | `parked.jsonl` has `episode==N` | PARKED (skip) |
| IDLE | `git status --porcelain` dirty by episode_drive.dirty() | WAIT_TREE (poll 5 min; Telegram once after 6 h: "tree dirty, autopilot waiting"). The one deliberate wait: the dirt is the owner's own in-progress edit, and a brain that commits his WIP is worse than a pause |
| IDLE | clean tree, no live gpu.lock, engine answers /system_stats | RUNNING: `Popen(uv run --no-sync python scripts/episode/drive.py <book> <N>, env DRIVE_QUIET=1, stdout -> episodes/epNN/drive_launchNN.log)`; write gpu.lock |
| RUNNING | lock pid alive (procs table) | RUNNING; silence rule from §2 |
| RUNNING | pid dead, last drive.jsonl row `event=="end"`, `code==0`, uploads row public | PUBLISHED |
| RUNNING | pid dead, `end code==0` but no public uploads row | NEEDS_BRAIN(no_upload_row) |
| RUNNING | pid dead, `end code==2`, log tail has `REFUSED to start: the working tree is dirty` (drive.py:96) | WAIT_TREE |
| RUNNING | pid dead, `end code==2`, log tail has `title card could not be baked` (drive.py:111) | NEEDS_BRAIN(title_card) |
| RUNNING | pid dead, `end code==1`, last `run` row `outcome=="refused"` and `episodes/epNN/plan.deferred.json` exists | NEEDS_BRAIN(plan_deferred) with the packet: `plan.deferred.json.faults[]`, last `learnings.jsonl` row with `gate=="PLAN" and terminal==true` |
| RUNNING | `end code==1`, `outcome=="failed"`, run log's last line matches `^studio\.llm\.OverBudget:` | **MEDIA WALL policy, no brain, no owner**: if `plan.json` exists and `plan.deferred.json` does NOT (the plan battery signed; the rest of the chain is $0 local) -> RELAUNCH once with `episode.py` resuming past step 02; else PARK(over_budget: no signed plan under $3). (Required 1-line code change: `guard_spend` keeps a `publish_reserve_usd: 0.10` so step 13's single metadata call — step_13_publish.py:17-20 — never hits the wall after the writer spent it.) |
| RUNNING | `end code==1`, `run_budget.spent_before(home) >= 18000` | PARK(clock_spent) — a brain cannot buy GPU hours; a parked episode is retried only by `autopilot.py retry N`, which clears the row and resets timing (owner's explicit act, not a wait) |
| RUNNING | `end code==1`, `outcome=="failed"`, any other traceback | NEEDS_BRAIN(failed: `<last traceback line>`) |
| RUNNING | `end code==1`, `outcome=="refused"`, no deferred file (e.g. `REFUSED: qc FAIL`, G-SHORTS) | NEEDS_BRAIN(refused: `<REFUSED line>`) |
| RUNNING | pid dead, NO `end` row after last `start` | crash_count+1; <3 -> RELAUNCH; else NEEDS_BRAIN(crash_loop) |
| NEEDS_BRAIN | no live gpu.lock, clean tree, `brain_attempts(N) < 3` | BRAIN_RUNNING: `studio/autopilot_brain.run(packet)` |
| NEEDS_BRAIN | `brain_attempts(N) >= 3` | PARK(brain_exhausted) |
| BRAIN_RUNNING | verdict file `episodes/epNN/brain/attempt_NN.json` says `{"verdict":"relaunch","commit":"<sha>"}` AND tree clean AND `git rev-parse HEAD == commit` | RELAUNCH -> IDLE (next tick launches) |
| BRAIN_RUNNING | verdict `park`, or no verdict file, or `ResultMessage.is_error`, or session > 45 min, or tree dirty after it | brain_attempts+1 -> NEEDS_BRAIN (loop) |
| any | `series.json.paused == true` or file `library/<book>/autopilot/STOP` | PAUSED (a global brake like RENDER_HOLD; not per-episode, never required for progress) |

PARK writes `parked.jsonl`: `{"ts","episode","reason","evidence":{"drive_row":..., "last_line":..., "brain_attempts":n}}`,
Telegram once, and the tick proceeds to `next_episode()`.

The brain (`studio/autopilot_brain.py`): `claude-agent-sdk` (pin `==` in pyproject; it drives the installed CLI).
`query(prompt, ClaudeAgentOptions(cwd=ROOT, permission_mode="bypassPermissions", setting_sources=["project"]
so CLAUDE.md + the episode skill load, max_turns=80, env without CLAUDECODE — the skill-creator scripts already
strip it at `.claude/skills/skill-creator/scripts/run_eval.py:80`))`, wrapped in `asyncio.wait_for(45 min)`.
Prompt = the packet (drive row, last 40 log lines, deferred faults, learnings terminal row, `git log -3`) + the contract:
"fix the cause, run the free tests, commit on master, then write `episodes/epNN/brain/attempt_NN.json`
with verdict relaunch|park, commit sha, why". The supervisor trusts the FILE and `git`, never the prose.
Transcript saved to `episodes/epNN/brain/attempt_NN.jsonl`; `ResultMessage.total_cost_usd` logged; brain wall
$5/episode separate from the $3 media wall -> PARK(brain_budget).

## 4. Series progression

The repo knows the unit list from `library/<book>/source/book.json`: `episodes: 27`, `chapters[n=0..27]` with
`ch_00` front matter, so **ep N == chapter n=N** (ep18 "The Fifth Cylinder" = n 18 "I. UNDER FOOT."; ep19 plan
`number: 19` = n 19). `titles_batch.missing(book)` already enumerates the book's cards (drive.py:105). The desk
(`studio/tick.py:59 episode_units`) only slates folders that exist; `drive.py:99 home.mkdir` creates the folder and
`episode.py:124-134 take_explicit` runs with no row ("none"), so **no registry edit is needed**: launching
`drive.py <book> N+1` is the whole handoff.

`next_episode(book_json, uploads_rows, parked_rows, series)` = min n in `[first..last]` with no public uploads row
and no parked row; `None` -> SERIES_COMPLETE: Telegram once ("27/27 public; parked: [...]"), status
`state: complete`, the loop idles at 5-min ticks. Stop conditions: complete, PAUSED, or WAIT_TREE.
`autopilot.py retry N` deletes the parked row -> the next tick picks N up again (its home is intact; resume is idempotent).

## 5. Observability

`library/<book>/autopilot/status.json`, rewritten atomically every tick:
```json
{"ts":"...","supervisor_pid":1234,"heartbeat_age_s":12,"engine":{"up":true,"queue_running":1,"restarts_today":0},
 "series":{"book":"20260827135508","first":1,"last":27,"published":[...18],"parked":[{"episode":19,"reason":"over_budget","ts":"..."}],"next":20,"state":"running"},
 "episode":{"n":20,"state":"RUNNING","drive_pid":5678,"sha":"2a50fc4f","run":1,"step":"09","log_quiet_s":40,"clock_spent_s":3120,"media_spent_usd":1.42,"brain_attempts":0},
 "last_events":[...5]}
```
Telegram: PUBLISHED (`https://youtu.be/<video_id>`, 1 line), PARKED (reason + episode), SERIES_COMPLETE, and the
6-h WAIT_TREE line. Nothing else: `DRIVE_QUIET=1` makes drive.py's `notify()` print only (3-line change at drive.py:59).
Logs: `events.jsonl` (one JSON row per transition, the audit trail), `autopilot.log` via
`RotatingFileHandler(5 MB x 5)`; `drive_runNN.log` / `drive_launchNN.log` stay per episode (bounded by MAX_RUNS);
brain transcripts kept (evidence for the audit folder).

## 6. Build: files, CLI, tests

| file | lines | does |
|---|---|---|
| `studio/autopilot.py` | ~150 | pure: `derive(signals) -> State`, `decide(state) -> Action`, `next_episode`, `status(...) -> dict`, `classify_exit(code, outcome, tail, home)` |
| `studio/autopilot_brain.py` | ~60 | packet builder, SDK session with timeout, verdict-file reader |
| `studio/engine_ops.py` | ~50 | `alive()` (/system_stats), `queue()`, `kill_run_tree(book, n)`, `restart()` — the memory's PowerShell, in Python via `procs` |
| `scripts/episode/autopilot.py` | ~120 | CLI: `run [--book]`, `tick` (one pass, for tests/cron), `status`, `install [--every 5]`, `uninstall`, `pause`, `resume`, `retry N`, `park N --why` |
| `scripts/episode/drive.py` | +3 | `DRIVE_QUIET` env |
| `studio/episode_drive.py` | +4 | `run` ledger row gains `"error": "<exception class>"` so OverBudget stops being a log-prose read |
| `pyproject.toml` | +1 | `claude-agent-sdk==<pinned>` |

Honest total ~380 lines + tests; the 200 target holds only for the pure core (`studio/autopilot.py`) which is the
part that must be right.

Tests (all free; fake drive = a 10-line script that appends the given drive.jsonl rows and exits with the given
code; fake brain = a callable that writes the verdict file; fake procs table = list of `ProcInfo`; fake engine = dict):
1. `test_autopilot_derives_state_from_disk` — every row of the §3 table as a parametrised case.
2. `test_no_silent_stop` — the invariant: after any `tick()` on any fixture, exactly one of {live drive pid, brain running, PARKED row, PUBLISHED row, PAUSED, WAIT_TREE} holds, and `status.json` names it. Run over a product of (exit code x outcome x files present).
3. `test_a_stale_lock_is_recovered_and_the_episode_relaunched` (dead pid; pid of a different command line).
4. `test_a_crash_without_an_end_row_relaunches_then_asks_the_brain_after_three`.
5. `test_over_budget_ships_a_signed_plan_once_and_parks_an_unsigned_one`.
6. `test_a_dead_clock_parks_without_a_brain`.
7. `test_the_brain_is_trusted_by_its_file_and_git_not_its_prose` (verdict relaunch + dirty tree -> not relaunched; attempts capped at 3 -> PARKED).
8. `test_a_hung_engine_is_killed_restarted_and_the_run_relaunched_at_most_twice`.
9. `test_next_episode_skips_published_and_parked_and_completes_at_the_book_end` (book.json fixture, 27).
10. `test_telegram_only_on_published_parked_complete`.
11. `test_tick_is_idempotent_and_the_second_instance_exits`.
12. `test_status_json_has_the_contract_keys`.

Open ops facts to carry: the VIRTUAL_ENV warning in every launch log (drive.py:63 runs `uv run` in comfy_studio with the
studio venv exported) is noise, not a fault; `episode.py` exit 2 is BOTH "escalated" and "deferred" (episode.py:161) —
the deferred file is what tells them apart, which is why the table reads it.
