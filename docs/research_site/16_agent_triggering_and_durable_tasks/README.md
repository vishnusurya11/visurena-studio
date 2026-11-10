# Agent triggering and durable tasks

**Date:** 2026-10-22 (Seattle time)

**Abstract:** Can the studio's AI agent calls run as durable jobs that survive a crash and wait out a usage limit? We found that a usage-limit defect, not a missing framework, caused the autopilot to park episodes. We fixed that defect and benched a job runner before building it.

## The question

The studio makes short video episodes from public-domain books. Each episode needs many calls to Claude. Those calls run on one subscription login with a shared usage limit. Two questions followed:

1. Should agent tasks run as standalone jobs that survive a crash, and resume later?
2. Why did the autopilot park whole episodes when the usage window shut?

## What existed before

- **Calls were already headless.** Every pipeline call to Claude ran as a background process. No step waited on an open chat session.
- **The limit defect.** When the usage window closed, the code raised a typed "rate limited" error. Nothing caught that error by type. A generic retry wrapper treated it as a fault. It slept 3 seconds and then 10 seconds, and then gave up. Inside a window that stays shut for hours, that is useless. The autopilot then parked the episode after three tries.
- **Three prototype runners.** Earlier work had built three small job runners. Each one had gaps. One could overwrite a result after a late worker finished. Another left child processes running after a crash.
- **A key leak risk.** A stray API key in the environment file would load into the process environment. Claude would then bill that API key instead of using the subscription login.

## Method

- **Expert panel.** Ten expert agents (nine lenses and one skeptic) argued over two rounds. Each round built on the last.
- **Gavel.** An Opus agent read both rounds and wrote the ruling. It adopted the fixes that were measured or clearly defective. It held the rest behind benches.
- **Pre-registered benches.** Pass rules were written before any bench ran. The rules were not changed after a run. Nine benches (R-B1 to R-B9) were set up, plus a real-process sub-arm inside R-B2.
- **Budget.** $0 spend. No GPU minutes. At most 250 real model calls, with an abort if the weekly usage gauge reached 0.90. The benches used about 125 real calls.
- **Skeptic.** An Opus skeptic attacked the ruling and recomputed the numbers from the raw files. Its findings are listed under limits below.
- **Builder.** An Opus builder landed the defect fixes test first. Each change had a failing test before its code.

Versions used: Claude command-line tool 2.1.286, Claude Agent SDK 0.2.159, model `claude-sonnet-5` for the metadata and critic tasks.

## Results

Every number below comes from the bench record (BENCH.md) unless marked "skeptic", which means the skeptic recomputed it from the raw files.

### R-B1: limit classes (fake streams, fake clock)

Ten failure inputs, 20 runs each. Inputs included a five-hour limit, a seven-day limit, a model-family limit, a bad login, an outage, a timeout, a killed process, a schema failure, a success, and limit text with no event.

| Arm | What it tests | Result | Calls | Sleep | Calls in shut window |
|---|---|---|---|---|---|
| A (today's code) | Real wrapper and brain code, fake transport | Limit inputs: 60 of 60 runs reproduce the defect | 3 per failing input | 13 s | 2 (20 of 20 runs each) |
| B (one-clause prototype) | Limit inputs only | 60 of 60 runs | 1 | 0 s | 0; 1 call after the reset |
| C (shared classifier and park path) | All 10 inputs | 200 of 200 (10 inputs x 20 runs) | 1 after reset | 0 s | 0 |

Notes:
- B makes exactly one notice per wait.
- C waited 3 days on a seven-day reset with no probe. It probes only when the reset time is unknown.
- The timeout input could not be tested. The brain call has no timeout at all. That is a finding.
- The skeptic notes that the 200 of 200 result is 10 cases repeated 20 times on fakes written by the same author as the classifier. It is close to 10 unit tests. Only the authentication text and the warning events came from real streams.

### R-B2: crash, fencing and orphans

Time was scaled for the test: task timeout 4 s, lease pad 1 s, heartbeat 1 s. Production uses 600, 120 and 30 s.

| Measure | A (first prototype) | A2 (second prototype) | B (reconciled runner) |
|---|---|---|---|
| Kills | 20 hard kills | 20 hard kills | 20 (5 each at four points) |
| Tasks done | 30 of 30 | 30 of 30 | 30 of 30 |
| Done exactly once | 30 of 30 (by event count) | 0 (no ledger, no result file) | 30 of 30 |
| Late settle: stale overwrite | Yes | Yes | No (late settle refused) |
| Late settle: ledger rows | 2 | None | 1 |
| Late settle: result files | 1 | None | 1 |
| Hung child alive 60 s after kill | 1 | 1 | 0 |
| Watchdog notice in 20 fake minutes | Not applicable | Not applicable | 10 of 10, exactly one notice each |
| Real sub-arm (3 real metadata tasks, worker killed at 5 s) | Not run | Not run | 3 of 3 valid, one row and one file each |

A and A2 failed the late-settle test, as predicted. The reaper matches a child by process ID plus its start time. A plain process-ID check reported false orphans.

### R-B3: API key precedence (dummy key, cannot bill)

Three runs per arm.

| Arm | Result | Auth source reported |
|---|---|---|
| A: command-line tool, dummy key in child environment | 3 of 3 fail, "Invalid API key" | The key |
| B: allowlist environment, no key | 3 of 3 succeed | Subscription |
| C: SDK in-process, dummy key in process environment | 3 of 3 fail, same error | The key |
| D: C after the fix (guard, plus key removed from the process environment) | 3 of 3 succeed | Subscription |
| Spawn guard when a key is visible | Refused 3 of 3 | Not applicable |

The leak is proven. A key in the parent environment makes both transports ignore the subscription login. The SDK merges its options onto the environment, so an allowlist alone cannot remove a key. The key must be removed from the process environment as well, and a guard must refuse to start.

### R-B4: one real task, with kills (the proof bench)

Task: draft publish metadata for a Jekyll and Hyde episode. Output must match a fixed schema. Model: `claude-sonnet-5`, medium effort.

| Measure | A: production SDK (n=10) | B: runner, run 1 (n=10) | B: runner, run 2 (n=10) |
|---|---|---|---|
| Final valid | 10 of 10 | 10 of 10 | 10 of 10 |
| First attempt valid | 9 of 10 (one retry at 101.7 s) | 10 of 10 | 10 of 10 |
| Wall median / p95 / max | 12.1 / 101.7 / 101.7 s | 11.5 / 20.9 s (attempt wall) | 12.0 / 20.6 s (attempt wall) |
| Total input tokens, median | 19,214 | 12,217 | 12,225 |
| Output tokens, median | 862 | 683 | 658 |
| Notional cost, median | $0.0470 | $0.0307 | $0.0310 |
| Workers killed | Not applicable | 5 kills, 3 distinct tasks | 5 distinct tasks |
| Killed tasks done exactly once | Not applicable | 3 of 3 | 5 of 5 |
| One ledger row and one result file per task | Not applicable | 10 of 10 | 10 of 10 |
| Orphan process at end | Not applicable | 0 | 0 |
| Auth variables in child environment | Not applicable | 0 | 0 |
| Weekly usage gauge before / after | 0.83 / 0.83 | 0.83 | 0.84 |

Pass rule, line by line (as the bench record reports it):

| Rule | Result |
|---|---|
| Final valid 10 of 10 | Pass |
| First attempt 9 of 10 or better | Pass (10 of 10) |
| p95 wall no more than A's p95 plus 10 s | Pass on attempt wall (20.9 s against 111.7 s) |
| Median input tokens no more than 1.2 times A | Pass (0.64 times) |
| Each killed task done exactly once | Pass (5 of 5 in run 2) |
| No auth variables in child environment | Pass |

**The skeptic's correction.** The rule defines wall time as enqueue to settled, not attempt wall. Measured that way, the runner's p95 was 157.5 s in run 2 and 301.6 s in run 1. The limit was 111.7 s. The cause is design: a crash is noticed only when the full lease runs out. Under the registered rule, the wall test fails. The bench record reports the attempt-wall pass. Both readings are shown here.

### R-B5: transport and flags (plan critic, 39,827-character brief)

Ten calls per arm, run in turn so cache warmth was shared. Baseline is the production SDK path.

| Arm | Valid | Median total input | Mean | Max | Median wall | p95 wall | Turns |
|---|---|---|---|---|---|---|---|
| A: SDK in-process (production) | 10 of 10 | 82,809 | 90,388 | 168,089 | 26.7 s | 145.5 s | 2 to 4 |
| B: command-line, parity flags, repo folder | 10 of 10 | 152,511 | 135,303 | 307,405 | 24.95 s | 35.6 s | 2 to 3 |
| C: B in a scratch folder | 10 of 10 | 26,692 | 115,406 | 336,094 | 26.55 s | 42.6 s | 2 to 4 |
| D: C plus no slash commands, strict empty MCP config | 9 of 10 (one max-turns error) | 48,958 | 51,407 | 75,189 | 23.55 s | 39.6 s | 2 to 4 |

Pass rule: median input at most 0.6 times A, valid at least A minus 1, median wall at most 1.1 times A.

| Arm | Input vs A | Valid | Wall vs A | Verdict |
|---|---|---|---|---|
| B | 1.84 | 10 | 0.93 | Fail (repo folder costs tokens) |
| C | 0.32 | 10 | 0.99 | Pass |
| D | 0.59 | 9 | 0.88 | Pass, narrowly |

Other counts:
- Calls above 130k input tokens: A 1 of 10, B 6 of 10, C 4 of 10, D 0 of 10.
- Initialization timeouts: none raised as errors, but the SDK path needed a second session on 2 of 10 calls (145.5 s and 69.0 s). One more slow retry came in the metadata run (101.7 s).
- The large outlier (138k to 183k input tokens) traced to connector tool schemas. Two claude.ai connectors connected before the first request and their tool definitions went into the prompt. When the connection finished late, the call was small. That makes the cost a race.
- The SDK path also made a hidden call to a smaller Haiku model on every session, about 11k uncached tokens each. That is 120,615 helper tokens across 11 sessions. The studio's spend ledger priced those tokens at the Sonnet rate.

### R-B6: parallel, three at a time

Five frozen plans, three readings each.

| Plan | Serial batch wall (A) | Concurrent batch wall (B) | Agree A | Agree B |
|---|---|---|---|---|
| Episode 5 fixture | 90.3 s | 23.3 s | Yes | Yes |
| Jekyll episode 1 | 59.8 s | 30.0 s | Yes | Yes |
| Scarlet episode 1 | 72.2 s | 37.3 s | Yes | Yes |
| Scarlet episode 5 | 105.0 s | 47.5 s | Yes | Yes |
| War of the Worlds episode 1 | 71.7 s | 34.3 s | Yes | Yes |
| **Median / count** | **72.2 s / 5 of 5** | **34.3 s / 5 of 5** | | |

- Concurrent median wall is 0.475 times serial, against a 0.5 rule. Pass, with little margin.
- Agreement 5 of 5 for both. Pass.
- 0 rejected events across 30 sessions at three at a time. Pass.

The skeptic notes an ordering problem. B always ran right after A on the same prompt, so B started warm. On one plan, A named shot 8 twice and B named shot 18 three times. The critic's verdict depended on which batch ran.

### R-B7: usage-window gauge and real-limit capture

- Weekly gauge: 0.83 at the first read, 0.84, 0.85, and 0.86 at the end. Five-hour gauge: 0.40 to 0.54.
- About 125 calls moved the weekly gauge by about 0.03. The gauge resolves only 0.01. Other sessions shared the window.
- **No admission threshold is wired.** The per-call share cannot be shown to be stable.
- **No real rejected event was captured.** The limit path stays unverified. The 14-day capture window had just started.

### R-B8: write fence, on a copy of a fake library

Twelve write attempts were run in a sandbox. Hashes of the fake library were compared before and after.

| Attempt | Today's hook | Hook plus PowerShell | Scratch copy |
|---|---|---|---|
| Python open for write | Leak | Leak | Unchanged |
| cp | Leak | Leak | Unchanged |
| mv | Leak | Leak | Unchanged |
| rm | Leak | Leak | Unchanged |
| PowerShell Set-Content | Leak (hook never fired) | Blocked | Blocked |
| PowerShell Out-File | Leak (hook never fired) | Blocked | Blocked |
| Shell redirect | Blocked | Blocked | Blocked |
| tee | Blocked | Blocked | Blocked |
| sed -i | Blocked | Blocked | Blocked |
| git checkout | Leak | Leak | Unchanged |
| Write tool through a directory junction | Blocked | Blocked | Unchanged (wrote into scratch tree) |
| pytest that writes to library | Leak | Leak | Unchanged |
| **Blocked / leaked / unchanged** | **4 / 8 / 0** | **6 / 6 / 0** | **5 / 0 / 7** |

The hook is a pattern fence. The scratch copy is the real wall. The skeptic adds that the scratch test used relative paths only, and that the PowerShell pattern misses several aliases. The pattern fence is a defect fix, not a full fence.

### R-B9: cheaper model for mechanical tasks

**Not run.** The precondition was that the weekly gauge stay below 0.85. It read 0.85 or higher from R-B5 onward. No decision follows.

## Verdict

1. **The defect is real and measured.** Today's wrapper made 3 calls and slept 13 s inside a shut window. That is what parked the episodes.
2. **The fix is small and landed.** A shut window now becomes a typed wait. It makes no model call, burns no attempt, and sends one notice with the wake time. The autopilot has a new waiting state.
3. **There is no engine switch.** The command-line tool and the SDK draw on one login and one usage pool. Moving between them does not free any limit.
4. **The job runner is designed, not built.** The reconciled prototype passed the crash test (30 of 30 done exactly once) and the classifier test (200 of 200). Its build gate is open. Making it the default for episode steps is not yet supported, because the registered wall rule fails (see R-B4).
5. **The OpenAI Agents SDK is not adopted.** It bills per token, and the studio's single-call tasks have nothing to attach to. It was not benched.
6. **Claude is not wrapped as a Strands model.** That would duplicate retries and hide usage data.

## What was wired

Commit subjects, in plain words (all on the same day):

| Commit | Plain-words change |
|---|---|
| 408ab77 | The write fence now blocks PowerShell commands that write into the library folder. |
| 219b0da | The environment file never loads an API key for Claude. Claude sessions refuse to start while one is visible. |
| a33e4f5 | A shut usage window is a typed wait signal. It raises after one call, with no sleep. |
| 1f2484e | The autopilot gets a waiting-for-quota state. One wait file, one notice, and a resume after the reset plus 90 seconds. |

Test result: 15,334 passed, 1 failed, in 30 minutes 42 seconds. The one failure is in two git-ignored documents written by other authors, not in these changes.

**Not wired:** the job runner itself, and several smaller fixes from the ruling. A wait cap of 8 days is in the code. The ruling had said 26 hours. The owner has to approve the 8-day cap.

## Limits and open questions

- **No real limit event has ever been seen.** Every limit path rests on fakes and the SDK's documented event shape. Until a real rejected event is captured, the limit path is marked unverified.
- **Skeptic findings still open.**
  - Limit text with no event is treated as a retryable fault. In a probe, that dead-lettered every queued job after about 33 minutes. It should park instead.
  - The prototype's claim step sets the lease to "now", so a second worker can grab a live task. A probe reproduced it. The design says the lease must be set inside the claim.
  - The wall test fails as registered (see R-B4).
  - The token ratios rest on one brief, repeated, with no raw streams kept for the token arms. Before quoting a ratio, re-measure on different briefs.
  - R-B6 has an ordering problem and a turn that flipped between batches.
  - The SDK's extra helper call is priced at the wrong rate in the spend ledger.
  - The wait-cap text differs between two files.
- **Scale numbers are guesses.** The estimate of about 1,000 calls a week, or about 25 episodes a week, has no support. The gauge is too coarse for it.
- **Test conditions.** The benches ran on one machine, on one login, during a shared weekly window. The runner's timeouts were scaled down for the crash test. Most limit tests used fake streams.
- **Not run:** the Codex CLI second lane, an overflow lane on monthly API credit, the OpenAI Agents SDK arm, and Strands with a local model (no local model was installed).

**Decisions pending with the owner:** confirm that "openapi agents" meant the OpenAI Agents SDK; approve the runner design; approve the 8-day wait cap; decide on a second vendor lane; decide on an overflow lane; decide whether to release the runner as a standalone open-source package once it is built.

## Images

Eight strip images from the bench record, in `images/`:

| File | What it shows |
|---|---|
| `images/00_SUMMARY.png` | Summary table of all benches and the pick |
| `images/R1_limit_classes.png` | Limit-class results |
| `images/R2_crash_fencing_orphans.png` | Crash, fencing and orphan results |
| `images/R3_api_key_precedence.png` | API key precedence results |
| `images/R4_proof_metadata.png` | The proof bench on the metadata task |
| `images/R5_transport_flags.png` | Transport and flag matrix |
| `images/R6_parallel.png` | Parallel three-at-a-time results |
| `images/R8_write_fence.png` | Write-fence red team results |

These images contain no video frames, so they are not held under the archive's MiniMax-H3 publication note.

## Sources

Public documentation cited in the expert reports:

- Claude Code headless mode: https://code.claude.com/docs/en/headless
- Claude Code errors: https://code.claude.com/docs/en/errors
- Claude Code cost tracking: https://code.claude.com/docs/en/agent-sdk/cost-tracking
- Claude Code costs: https://code.claude.com/docs/en/costs
- Claude Code command-line reference: https://code.claude.com/docs/en/cli-reference
- Claude Code environment variables: https://code.claude.com/docs/en/env-vars
- Anthropic support, subscription usage: https://support.claude.com/en/articles/15036540
- Anthropic API pricing: https://platform.claude.com/docs/en/about-claude/pricing
- Anthropic API credits for subscribers: https://platform.claude.com/docs/en/about-claude/api-credits-for-subscribers
- OpenAI Agents SDK: https://openai.github.io/openai-agents-python/
- OpenAI Agents SDK, handoffs: https://openai.github.io/openai-agents-python/handoffs/
- OpenAI Agents SDK, models: https://openai.github.io/openai-agents-python/models/
- OpenAI Agents SDK, results: https://openai.github.io/openai-agents-python/results/
- OpenAI Agents SDK, running agents: https://openai.github.io/openai-agents-python/running_agents/
- OpenAI Agents SDK package: https://pypi.org/project/openai-agents/
- OpenAI API pricing: https://developers.openai.com/api/docs/pricing
- OpenAI API rate limits: https://developers.openai.com/api/docs/guides/rate-limits
- OpenAI Codex non-interactive mode: https://learn.chatgpt.com/docs/non-interactive-mode
- Temporal with the OpenAI Agents SDK: https://docs.temporal.io/develop/python/integrations/openai-agents
- Temporal announcements: https://temporal.io/blog/announcing-openai-agents-sdk-integration and https://temporal.io/blog/announcing-openai-agents-sdk-partnership
- Strands Agents, Anthropic provider: https://strandsagents.com/latest/documentation/docs/user-guide/concepts/model-providers/anthropic/
- Strands Agents, structured output: https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/structured-output/
- Strands Agents, session management: https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/session-management/
- Strands Agents, retry strategies: https://strandsagents.com/docs/user-guide/sdk/agents/retry-strategies/
- Huey task queue: https://huey.readthedocs.io/en/latest/
- Huey storage backends (package docs): https://tessl.io/registry/tessl/pypi-huey/2.5.0/files/docs/storage-backends.md
- Community write-ups and issue reports on limit retries and durable queues:
  - https://aident.ai/blog/fix-claude-code-max-budget-usd-subscription
  - https://claudeissues.com/issue/86272-headless-claude-p-reports-youve-hit-your-session-limit-while-the-account-is-at-1
  - https://dev.to/aobaworks/claude-code-rate-limit-reached-retry-setup-for-cron-jobs-1ioi
  - https://dev.to/minnzen/building-a-durable-message-queue-on-sqlite-for-ai-agent-orchestration-335m
  - https://github.com/error0702/agent-limit-retry
  - https://github.com/majorcontext/harness/pull/684
  - https://vanja.io/your-agents-eat-your-subscription/
  - https://www.theregister.com/ai-ml/2026/05/14/anthropic-tosses-agents-into-the-api-billing-pool/5240748

Pages cited by name only in the expert reports, with no URL, are not listed.
