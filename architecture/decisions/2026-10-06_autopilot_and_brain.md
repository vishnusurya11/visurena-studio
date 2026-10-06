# The autopilot: a Python supervisor that never stops, and a Claude brain it calls on a leash

**Date:** 2026-10-06 · **Status:** APPROVED (owner, 2026-10-06: "Approve"; defaults
taken for the sub-choices he left open: subscription login for the brain, ep19 parks and
ep20 starts, the CLI upgrade stays) · asked as: "I need brain of Claude with agent sdk ..
but the comfort of python jobs to make sure they are triggered and monitored and not
stopped in middle"; and: "when I say approve I need the design of how this works, not the
actual episode or script — that should be autonomous" · **Debate:** four specialists,
reports under [research/2026-10-06_autopilot/](research/2026-10-06_autopilot/) (SDK
architect, ops engineer, skeptic, repo integrator) · **Tracker:**
[../plan/2026-10-06_autopilot_build.md](../plan/2026-10-06_autopilot_build.md).

## The problem, measured

The pipeline is already a Python job: `scripts/episode/drive.py <book> <n>` runs steps
01–13 to a public Short and refuses, defers or crashes by rule. What is NOT a job is the
layer above it — the interactive Claude session that watches the log, reads a deferral,
writes a code fix and its test, commits, relaunches, and picks the next chapter. That
session ends its turn and the work stops. ep19 sat for hours between launches four times
today for exactly that reason (`episodes/ep19/drive.jsonl`: four `start` rows on four SHAs).

The same ledger shows what the hand-driven "brain" bought on ep19: 4 launches, 3
deferrals, 11 writer calls, $3.10 against a $3.00 wall, zero pictures. Of the twenty
findings in the self-curing tracker (F1–F20), **none needed judgment at runtime**: 11
landed as code, 4 are proposed code, 4 are process, 1 was the owner's hand (standing.json).
Nine of them were *diagnosed* by a Claude session reading a parked run — the fix was a
commit, which the repo's own rule forbids on a live episode ("one episode, one commit").

So the pain is **session lifetime**, not judgment. The design puts the lifetime in Python
and gives the judgment a short, fenced leash.

## The four positions, and where they split

| point | SDK architect | ops engineer | skeptic | integrator | ruling |
|---|---|---|---|---|---|
| who owns the loop | Python scheduler; SDK session is one call | Task Scheduler re-arms a long-lived `autopilot.py run` | the supervisor half alone solves the pain | a pure `loop()` like `episode_drive.drive` | **unanimous: Python owns launch, watch, ledger, notify, next chapter** |
| the brain may fix code mid-episode | yes, with caps, test-first, commit | yes, 3 attempts, $5 wall | **no** — hit rate ~1 useful fix per 2 tries, each a coin-flip to add a false gate; "one episode one commit" | no — triage only: retry / cure order / park | **split → ruled: no code change on a live episode. The brain triages mid-run; it FIXES only between episodes, under a mechanical ratchet (§4)** |
| brain spend | `max_budget_usd`, $3–12/episode at API prices, $0 marginal on Max | $5 separate wall | inside the $3, $1 cap | rows in the same `usage` table count against the $3 with zero new code | **own cap, same ledger: `stage='brain'` rows, $1.00 list-equivalent per episode, outside the $3 media wall** |
| waiting on the owner | BLOCKED + `needs_owner` | PARKED row, move on; one deliberate wait: a dirty tree | every brake self-acting | block = stop + report | **owner ruling applied: PARKED is a record, never a wait; the series moves on the same tick** |
| the $3 wall when hit | — | signed plan → relaunch once past step 02; else park | park | catch `OverBudget` in the ladder so it is a terminal, not a crash | **both: the catch (code) and the policy (supervisor)** |

## The design

### Layer 1 — `autopilot`, the supervisor (deterministic, Python, no model)

A long-lived loop, re-armed by Windows Task Scheduler (task `visurena-autopilot`,
AtStartup + AtLogOn + every 5 min, `MultipleInstances=IgnoreNew`, no time limit — the
shape `studio-foreman` already runs on this box). Not a service: session 0 has no Claude
login, YouTube token or Telegram creds. Every tick is a pure function of disk:

```
signals = drive.jsonl rows · drive exit code · plan.deferred.json · learnings.jsonl terminal rows
        · timing.jsonl sum · uploads.jsonl public rows · gpu.lock pid liveness · /system_stats · git porcelain
state   = derive(signals)        decide(state) -> one action        status.json names the state
```

States per episode: `IDLE → RUNNING → {PUBLISHED | NEEDS_BRAIN(reason) | WAIT_TREE}`;
`NEEDS_BRAIN → BRAIN_RUNNING → {RELAUNCH | PARKED(reason)}`. Twenty-five hand-back
points were enumerated with their on-disk signal (integrator §4): 8 are a plain retry,
5 are a cure the desk already accepts (`work_orders`: `redo 08`, `redo 10`, refs runner,
comfy restart), 1 is a wait (RENDER_HOLD — the owner's brake, never lifted by code),
4 fall to the brain, 11 park with a reason. **The one invariant, as a test:** after any
tick on any fixture, exactly one of {live drive pid, brain running, PARKED row, PUBLISHED
row, PAUSED, WAIT_TREE} holds and `status.json` names it. Silence is never a state.

- **Series:** ep N = chapter N (`source/chapters/ch_NN.json`, `book.json episodes`);
  `next_unit` = lowest chapter with no public `uploads.jsonl` row and no `parked.jsonl`
  row; `drive.py`'s own `mkdir` creates the unit — no registry edit. SERIES_COMPLETE
  at the last chapter, one Telegram.
- **PARKED** replaces every "ask the owner": a row in `library/<book>/autopilot/parked.jsonl`
  (episode, SHA, reason, evidence, the brain's finding), one Telegram, and the tick
  moves to N+1. `autopilot.py retry N` is the owner's optional act, never a wait.
- **The $3 media wall:** `OverBudget` becomes a ladder terminal, not a crash (6 lines in
  `plan_ladder.Desk.write`); `episode_drive.outcome()` learns the words `overbudget` and
  `escalated`. Policy: a signed `plan.json` and no aside → relaunch once resuming past
  step 02 (the rest of the chain is $0 local, with a `publish_reserve_usd 0.10` so step
  13's one metadata call survives); otherwise PARK(over_budget).
- **Engine:** a run whose log is quiet past 2× the step's budget while `/queue` shows the
  same prompt → kill the run tree by command line, restart ComfyUI, relaunch (resume
  skips done steps); cap 2 per episode → PARK(engine).
- **Observability:** `status.json` (series / episode / engine / brain), `events.jsonl`,
  rotating log; Telegram only on PUBLISHED, PARKED, SERIES_COMPLETE, and a dirty tree
  older than 6 h.
- **Not built:** a second runner, step calls, any plan/verdict/waiver writer, a new
  Telegram path.

### Layer 2 — `brain`, the Claude Agent SDK on a leash

`claude-agent-sdk==0.2.159` (the last version with a Windows wheel; it bundles its own
`claude.exe`, so the machine's CLI version is irrelevant), in its own `brain` dependency
group, `uv sync --all-groups` after. `permission_mode="dontAsk"` (unlisted tool → denied,
never a prompt), explicit `allowed_tools`, `disallowed_tools=["Edit(/library/**)", ...]`,
a PreToolUse hook that denies any write resolving under `library/`, any `sed`/redirect
into it, any sign script, `git push/reset/amend`, `uv add/remove`, and every
Higgsfield/Comfy generate tool. `setting_sources=["project"]` so the repo's CLAUDE.md,
`.claude/agents/episode.md` and the `episode` skill load (NOT `user`: the global
"ask before you scope" would dead-stop a session that cannot ask). The verdict is
`output_format=json_schema` → `ResultMessage.structured_output`; the supervisor trusts the
JSON, the verdict file and `git rev-parse HEAD`, never prose. `session_id` is kept per
episode so a restarted supervisor resumes the same conversation; cost is ledgered per
turn as the DELTA of `total_cost_usd` into the `usage` table (`stage='brain'`,
`unit='epNN'`, model priced in `models.yaml rates`).

**Two rungs, both unattended:**

| rung | when | may do | may not | model | caps |
|---|---|---|---|---|---|
| **Triage** (mid-run) | a NEEDS_BRAIN state the regex table could not class | read logs, plan, verdicts, run `plan_check`/`pytest -q` read-only; answer `{retry \| cure(order) \| park, finding_row, proposed_diff_text}` | write anything but its verdict file; the finding row is appended by the supervisor | Sonnet 5.5, effort medium | 1 session per stop, 15 turns, $1.00 per episode, 3 per day series-wide |
| **Fixer** (between episodes) | no drive live, tree clean, `parked.jsonl` has rows with a proposed diff | write the fix AND a test, run the suite, commit on master, re-queue the parked episodes once on that commit | edit `library/**`, verdicts, `gates.yaml`, `models.yaml`, `stages.yaml`, pyproject, `.claude/**`; touch any `terminal:`, `episode_ceiling_usd`, `MAX_*`/`*_CAP`/`*_WALL`/`*_SHARE` constant or `guard_spend` | Opus 5.5, effort high, fallback Sonnet | 1 commit per batch, 45 min, $3.00 list-equivalent per batch |

**The ratchet** (mechanical, run by the supervisor on the fixer's commit, never trusted
from the brain): (1) the commit adds ≥ 1 test file; the supervisor runs ONLY those tests
on `HEAD~1` (must fail) and on `HEAD` (must pass), else `git reset --hard HEAD~1`;
(2) `git diff --name-only HEAD~1` must stay inside the allow set, else revert;
(3) `plan_check` over the last three delivered plans may not report FEWER faults after
the fix unless each removed fault is asserted as a false positive in the new test;
(4) the forbidden-edit grep. This is `feedback_a_fix_that_changes_nothing` and
`feedback_constants_outlive_their_world` as code.

**Fixer scope, by class:** Python tracebacks in `studio/**` and `scripts/**`, and a
*missing cure* for a fault the table already names (objective red/green) — allowed.
A gate threshold, a judge, a cure's wording, a model tier — **report-only, forever**:
the repo's memory says the most frequent fault is a threshold that looked right. Those
episodes stay parked with the finding until the owner's next design change.

**Self-acting brakes on drift** (`feedback_gates_are_not_quality`): 2 consecutive parked
episodes, or 3 consecutive shipped with `terminal: flag` on MASTER → the fixer is
demoted to triage-only for the series, the series pins to the last SHA that shipped a
zero-terminal MASTER, parked episodes re-queue once on it. If that SHA parks 2 in a row,
the autopilot stops launching and says so in the receipt: a pipeline that cannot ship on
its best-known code has nothing left to try unattended. The owner's next design change
restarts it — the one touchpoint he approved.

### Where workflows sit (owner's question, 2026-10-06; verified against code.claude.com/docs/en/workflows)

The Agent SDK has the `Workflow` tool: a JavaScript script that holds the loop, branches on
results, needs no human mid-run, runs headless under a `Workflow(<name>)` allow rule in
`dontAsk` mode, and is resumable by session. Three documented limits put it INSIDE the
brain, not above it: (1) its lifetime is the session's — a crash or reboot needs a Python
process to relaunch the session and resume the run by `session_id`; (2) "no direct
filesystem or shell access from the workflow itself" — every tick of the state machine
would be a paid agent call to run `ls`, where `derive()` costs nothing and is pytest-able;
(3) in SDK/headless mode a run that hits the subscription usage limit fails the agent
instead of pausing — the supervisor sleeps on `RateLimitEvent`, a script cannot.
**Workflows dictate what agents run next; Python dictates what processes run next.**

So the fixer rung is a saved workflow, `.claude/workflows/fix-parked.js`: one fix agent per
parked finding in its own worktree → three skeptics try to refute each fix → only
survivors go to the ratchet → one commit per batch. The supervisor's allow list names
exactly that workflow. The subagents page cites the TypeScript SDK version that added the
tool; the Python SDK drives the same CLI, so this is confirmed on the first live turn,
with the plain `Agent` fan-out as the fallback.

### Auth and billing — the owner's one choice inside this approval

This box is logged into claude.ai Max; there is no `ANTHROPIC_API_KEY`. Two documented
routes for the brain's subprocess (the Claude Code CLI):

- **Subscription token:** `claude setup-token` → `CLAUDE_CODE_OAUTH_TOKEN` in the task's
  environment. Documented as "alternative to /login for SDK and automated environments",
  one year, $0 marginal, counted against the Max 5-hour/7-day windows; the SDK emits
  `RateLimitEvent` and the supervisor sleeps until `resets_at`. The quickstart's policy
  sentence ("Anthropic does not allow third party developers to offer claude.ai login …
  for their products") is about offering login to others; this is your own automation.
- **API key:** `ANTHROPIC_API_KEY` scoped to the task's env only; per-token at list price
  (Sonnet triage ≈ $0.30–1.50 a session, Opus fixer ≈ $2.6–10).

Recommendation: subscription token, with the brain's list-equivalent cost still ledgered
and capped so the numbers stay honest whichever route is live.

### ep19 under this design

ep19 has `plan.json` + `plan.deferred.json` (unsigned) and `unit_spent` $3.10 > $3.00 →
PARK(over_budget) on the first tick, Telegram once, autopilot launches ep20. ep19
re-queues once when a SHA ships a clean episode. The owner may `autopilot.py retry 19`
at any time (optional, never waited on); a higher ceiling for one episode is a config
act outside the autopilot.

## Build (opens as `plan/2026-10-06_autopilot_build.md` on approval)

| file | ~lines | contract |
|---|---|---|
| `studio/autopilot.py` | 150 | pure: `derive`, `decide`, `classify`, `next_unit`, `status` — every H-row a parametrised test case |
| `studio/engine_ops.py` | 50 | `alive`, `queue`, `kill_run_tree`, `restart` (the memory recipes as code) |
| `studio/brain.py` | 90 | `brief` (relative paths only), `options` (hooks, allow/deny), `turn` (one SDK session → `Verdict`), `ledger` (delta rows), `allowed` (clamps orders to registry step ids) |
| `studio/ratchet.py` | 60 | red-before-green on `HEAD~1`/`HEAD`, allow-set diff, last-3-plans fault count, forbidden-edit grep |
| `scripts/episode/autopilot.py` | 120 | CLI `run \| tick \| status \| install \| uninstall \| pause \| resume \| retry N \| park N --why` |
| `studio/plan_ladder.py`, `studio/episode_drive.py`, `scripts/episode/drive.py` | +13 | `OverBudget` → terminal; `overbudget`/`escalated` outcomes; `DRIVE_QUIET` |
| `models.yaml`, `pyproject.toml` | +4 | `tiers.brain`, `rates.claude-sonnet-5-5` / `claude-opus-5-5`; `brain` group pinned |
| tests (free: fake drive, fake transport, fake procs) | 14 files | `test_no_silent_stop`, derive-every-row, stale lock, crash×3, over-budget policy, dead clock, brain trusted by file+git only, hung engine ×2, next chapter, telegram-only-on-three, second instance exits, status keys, ratchet reverts a weakening fix, brief has no drive letter |

Every function 10–20 lines with its test first; no absolute path stored; Strands keeps
every department call; the SDK sits above `drive.py` and never imports a department.

## What the owner approves here

1. The two layers and the leash: Python owns the loop; the brain triages mid-run and
   fixes only between episodes, under the ratchet; gate/threshold/judge edits stay
   report-only.
2. PARKED replaces every wait; the series moves on; the drift brakes above.
3. The $3 media wall unchanged; brain cost ledgered separately, $1.00 triage / $3.00
   fixer list-equivalent caps.
4. Auth route: subscription token (recommended) or API key.
5. ep19 parks under the wall; ep20 starts.

## Disclosure

While verifying the SDK's CLI pairing, the SDK architect agent ran `winget upgrade
--id Anthropic.ClaudeCode --exact`, which upgraded this machine's Claude Code CLI
2.1.158 → 2.1.286. No repo file was touched. Open a new shell before relying on it;
say the word and it is rolled back. The pinned SDK bundles its own CLI, so the design
does not depend on this.
