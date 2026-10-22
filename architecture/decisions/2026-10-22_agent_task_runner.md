# 2026-10-22 -- agent triggering, the shut usage window, and the agent task runner

Status: **PART BUILT 2026-10-22** (group R wave 0: A1, A2, A5); the task runner is **PROPOSED**
(design adopted by the group R gavel, build gated). Owner questions open: (1) does "openapi agents"
mean the OpenAI Agents SDK; (2) yes or no on the design below. Evidence (git-ignored, on disk):
`docs/audit/2026-10-22_fleet/R_Agent_triggering_and_durable_task_running/` (RULING.md, PREREG.md,
bench/BENCH.md, SKEPTIC.md).

## What was true before

Every pipeline LLM call was already a headless job: each claude-sdk tier in models.yaml goes
through `studio/llm.py::_SdkStructuredCaller` to `studio/brain.py::ask_structured`, which spawns the
same `claude.exe` that `claude -p` runs. No run waited on an interactive session. The gap was a
defect: `brain.RateLimited` was raised and caught nowhere by type, so `llm.structured` slept 3 s and
10 s inside a window shut for hours, asked twice more, and the autopilot sent the stop to a brain
whose own session hit the same window three times, then parked the episode `brain_exhausted`
(bench R-B1 arm A: 3 calls and 13 s of sleep on every limit input, 60/60).

## Built (each test-first)

| # | Change | Where | Test |
|---|---|---|---|
| A1 | `RateLimited` is an `llm.LimitWait(resets_at, window)`; `structured` re-raises it after one call, no sleep. Limit words on a failed result with no rejected event are the same wait (unknown reset, or the legacy `limit reached|<epoch>` epoch). The drive's `usage window <w> shut until <epoch>` line is the hand-back kind `quota` and the autopilot state **WAIT_QUOTA**: not a stop on the relaunch cap, no brain call while it lasts, ONE global `library/.autopilot/quota.json` for every book, one Telegram with the wake time in Seattle time, a relaunch on the first tick past `resets_at + 90 s`; an unsaid reset re-checks in 30 min; a wait past 8 days parks `quota_wait_too_long`. A brain session that meets a shut window burns no attempt. | `studio/llm.py`, `studio/brain.py`, `studio/episode_drive.py`, `studio/autopilot.py`, `scripts/episode/autopilot.py` | `tests/test_llm_a_shut_usage_window_is_a_typed_wait_never_a_sleep.py`, `tests/test_autopilot_a_shut_window_waits_and_never_asks_the_brain.py` |
| A2 | `.env` never loads an `ANTHROPIC_*` name into `os.environ`; `brain.turn` and `brain.ask_structured` refuse to spawn while `ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN` is visible (`ApiKeyVisible`, never retried). R-B3: a visible key wins over the login in both `claude -p` and the SDK, and `ClaudeAgentOptions.env` merges onto `os.environ`, so an options allowlist cannot remove it. | `studio/llm.py::_load_dotenv`, `studio/brain.py::refuse_api_key` | `tests/test_brain_refuses_a_visible_api_key_and_dotenv_never_loads_one.py` |
| A5 | The PreToolUse write fence matches PowerShell and reads its command text for Set-Content/sc, Add-Content/ac, Out-File, New-Item/ni, Copy-Item/cpi, Move-Item/mi, Remove-Item/ri and `[IO.File]::Write*` into library/. A defect fix, not a fence (dontAsk already denies an unlisted tool). | `studio/brain.py` | `tests/test_brain_the_write_fence_reads_powershell_too.py` |
| A10(b) | Claude is never wrapped as a Strands Model: a regression test pins `_caller_for` on a claude-sdk tier to the SDK caller. | `tests/test_llm_a_claude_tier_is_never_a_strands_agent.py` | itself |

The 8-day wait cap replaces the gavel's 26 h (skeptic m4): the weekly window's `resetsAt` is known
and can be up to 7 days out, so 26 h would park every weekly wait.

## Records (no code)

- (a) The **OpenAI Agents SDK is not adopted**: it bills an API key per token (against the owner's
  2026-10-07 "don't use API for money"), studio/ has no handoffs or tool graphs to attach to, a
  schema miss has no re-ask, it is not durable without a Temporal server, and it is not installed.
- (c) No Temporal, Celery, RQ or Huey: a server or Redis, Unix fork or SIGALRM, or no pause on a
  login-bound `resetsAt`. One Windows box, one login.
- (d) No `--bare`: it accepts only an API key (`claude --help`, 2.1.286).
- (e) Single-shot structured tasks re-run from scratch; only tool-using multi-turn tasks may use
  `--resume` (a first-turn kill leaves "No conversation found").
- (f) `CLAUDE_CODE_RETRY_WATCHDOG` stays unset: unbounded 429/529 retries on CLI 2.1.286.
- **Engines:** `claude -p` and the Agent SDK are one binary on one subscription pool; switching
  between them moves neither the 5-hour nor the weekly window. The only levers are parking well and
  fewer tokens per call.

### One retry owner per fault (A6, documentation; unmeasured)

| Fault | Owner | Cap |
|---|---|---|
| HTTP 429/529 inside a call | the CLI's own retries | its default |
| schema refusal | `llm.structured` re-ask | 3 |
| transient (connection) | `llm.structured` backoff 3 s, 10 s | 2 |
| shut usage window | the autopilot (WAIT_QUOTA) | 8 days, then park |
| visible API key | nobody: refused at once | 0 |
| crash of the drive | the autopilot relaunch | CRASHES_BEFORE_BRAIN |
| a Strands ModelRouter (none today: every tier is claude-sdk) | `ModelRetryStrategy(max_attempts=1)` | 1 |

## Proposed: the agent task runner (not built)

One SQLite lease queue, stdlib only: `studio/agent_jobs.py`, `jobs.db` in `%LOCALAPPDATA%\visurena`
(C:, WAL). Tables `job` (relative paths only, `lease_epoch`), append-only `attempt` (raw stream,
stderr, rc), `quota` (the row WAIT_QUOTA's file would become). Key = sha256(kind | full model id |
effort | profile | schema sha | prompt sha). Claim under `BEGIN IMMEDIATE` with the lease set IN the
claim; settle by temp file + `os.replace`, then `UPDATE ... WHERE lease_epoch = ?` (fencing). Ten
outcome classes from the stream, never the exit code; limit text parks, never `unknown`. Transports
`sdk` (default) and `cli` (`claude -p`, scratch cwd outside the repo, `--strict-mcp-config
--disable-slash-commands`). Global width 3. `scripts/ops/tasks.py` submit / work / status / why /
retry / pause / resume for jobs outside the episode clock.

Gates: the build gate is open (R-B1 arm C 200/200, R-B2 arm B 30/30), but four prototype faults are
fixed first: the claim race (lease set after the claim, skeptic M6), the lease renewed to
timeout + pad (a crash seen only after 720 s, M3), limit text dead-lettering the queue (M2), a dead
worker's attempt keeping no stream or tokens (m3). The default-transport gate is NOT open: R-B4
fails its registered lifecycle-wall rule (p95 157.5 s and 301.6 s against 111.7 s). Publishable once
built and benched: the queue as a standalone package (lease queue, limit-aware park, stream
classifier, fake CLI) -- the owner's call.

## Not wired, and why

- A3 classifier, A7 utilization rows, A8 version fields, A9 watchdog reason: they belong to the
  runner or are instrumentation, not defect fixes; A1's single notice covers the wait today.
- A4 alias refusal and token pricing: every tier already names a full id (no alias to refuse);
  pricing wants models.yaml rate rows, and models.yaml is not edited by a builder. The hidden
  Haiku 4.5 helper call the SDK makes per session (~11k tokens) stays summed into the tier's row.
- A11 scratch cwd and lean MCP flags: the token win was measured on the `claude -p` transport
  (R-B5 arms C/D, a 0.01 margin under one reading, skeptic M4); the production SDK path was not
  measured with them, so it is not changed.
- The SDK path has no wall-clock timeout (BENCH finding); not in the adopted list.
- A step that catches every `Exception` around its LLM call (studio/canon.py) still swallows the
  wait into its fallback.
