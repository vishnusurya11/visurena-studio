# SDK ARCHITECT — the watcher-that-thinks on the Claude Agent SDK (Python)

Date 2026-10-06. Every claim below was checked today against code.claude.com/docs/en/agent-sdk/*,
platform.claude.com, PyPI JSON, the SDK's GitHub source, and this machine.

## 0. The brick

The brain is ONE function: `verdict = brain_turn(book, n, evidence)` where `evidence` is the
drive ledger + log tail and `verdict` is validated JSON `{action: DONE|RELAUNCH|BLOCKED, ...}`.
Python owns the loop (launch drive.py detached, watch, ledger, notify, sleep on rate limit,
call brain_turn, act on verdict). The SDK session owns judgment and code edits only. Nothing
else is new: `drive.py`/`episode.py`/stepwise/Strands stay exactly where they are.

Boundary (repo invariant respected):
- Strands = models + department agents INSIDE `studio/` (studio/llm.py, plan_ladder.py ...). Untouched.
- stepwise / `scripts/episode/drive.py` + `episode.py` = DAG, ledger, gates, clock. Untouched.
- Agent SDK = the layer ABOVE drive.py: `scripts/episode/brain.py` (new). It never imports a
  department, never writes `library/` data, only (a) runs read-only diagnostics, (b) edits code +
  tests, (c) commits, (d) returns the verdict. The Python scheduler, not the brain, launches
  `drive.py` (detached) so no 5-hour run ever sits inside a Bash tool call (Bash tool timeout
  max 600 s).

## 1. Package, minimal call, options

**Package**: `claude-agent-sdk` on PyPI. Latest 0.2.163 (uploaded 2026-09-30), `requires_python>=3.10`,
deps `anyio>=4`, `jsonschema>=4.20`, `mcp>=1.23,<3`. Changelog: 0.2.163 "Updated bundled Claude
CLI to version 2.1.286". No Node.js is required; the SDK spawns a native `claude` binary
(`anyio.open_process`, stream-json over stdin/stdout). Prompts, hooks and agents go over stdin
(the initialize request), NOT argv; only `system_prompt`/`--model`/`--max-turns` etc. are argv.
Sources: code.claude.com/docs/en/agent-sdk/python, /agent-sdk/quickstart,
raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/_internal/transport/subprocess_cli.py

**WINDOWS WHEEL FACT (decides the pin)** — PyPI file lists, checked per version:
0.2.159 (2026-09-23) and earlier ship `win_amd64.whl` (bundled `claude.exe`, CLI 2.1.281);
0.2.160–0.2.163 and 0.2.157 ship NO Windows wheel (macOS + manylinux + sdist only). On this box
`uv pip install --dry-run claude-agent-sdk==0.2.163` resolves the sdist (pure Python, builds fine)
→ no `_bundled/claude.exe` → the SDK falls back to `shutil.which("claude")` → the winget
`claude.exe` (native .exe, accepted; `.cmd` npm shims are refused since 0.2.124).
Pin choice:
- `claude-agent-sdk==0.2.159` → self-contained (bundled claude.exe 2.1.281; the SDK PREFERS the
  bundled copy over PATH, so winget version is irrelevant). Recommended for a scheduler job.
- `claude-agent-sdk==0.2.163` → newest SDK, depends on the machine's `claude.exe` (now 2.1.286 —
  see §6 disclosure). Either is fine; do not float.

**Minimal headless call that runs this repo's `episode` agent + `.claude/skills/episode`**
(`setting_sources=["project"]` loads `.claude/agents/*.md`, `.claude/skills/*`, project CLAUDE.md;
deliberately NOT `"user"`: `~/.claude/CLAUDE.md` says "ASK BEFORE YOU SCOPE … wait for the answers",
which in `dontAsk` mode becomes a dead stop; `~/.claude/settings.json` also sets `"model": "opus"`):

```python
# scripts/episode/brain.py  (shape; every function gets its test first, 10-20 lines)
from pathlib import Path
from claude_agent_sdk import (ClaudeAgentOptions, ClaudeSDKClient, HookMatcher,
                              ResultMessage, RateLimitEvent, ResultError, ProcessError)
from pydantic import BaseModel
from typing import Literal

ROOT = Path(__file__).resolve().parents[2]

class Verdict(BaseModel):
    action: Literal["DONE", "RELAUNCH", "BLOCKED"]
    reason: str
    commit: str | None = None          # sha the fix landed on, if any
    files_changed: list[str] = []
    needs_owner: bool = False          # BLOCKED + a question the owner must answer

def options(book: str, n: int, session_id: str | None) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        cwd=str(ROOT),
        model="claude-opus-5-5",                 # see §5; alias "opus" also resolves here
        fallback_model="claude-sonnet-5-5",
        effort="high",
        permission_mode="dontAsk",               # never prompts; unlisted => denied, not asked
        allowed_tools=["Read", "Glob", "Grep", "Edit", "Write", "Skill", "Agent",
                       "Bash(uv run *)", "Bash(uv sync *)", "Bash(git *)",
                       "Bash(nvidia-smi *)", "Bash(curl *)"],
        disallowed_tools=["WebSearch", "WebFetch", "AskUserQuestion",
                          "Edit(/library/**)",   # all file-writing tools + sed/tee/> in Bash
                          "Read(//**/.credentials.json)"],
        setting_sources=["project"],             # .claude/agents, .claude/skills, CLAUDE.md
        skills=["episode"],                      # exact names only; adds Skill tool
        system_prompt={"type": "preset", "preset": "claude_code",
                       "append": BRAIN_MANDATE},     # short; argv on Windows caps ~32 KB,
                                                     # use {"type":"file","path":...} if long
        output_format={"type": "json_schema", "schema": Verdict.model_json_schema()},
        max_turns=60,
        max_budget_usd=6.0,                      # list-price estimate; works on subscription too
        resume=session_id,                       # None on the first turn of an episode
        hooks={
            "PreToolUse": [HookMatcher(matcher="Write|Edit|NotebookEdit|Bash",
                                       hooks=[deny_library_writes])],
            "PostToolUse": [HookMatcher(hooks=[audit_tool_call])],
            "Stop": [HookMatcher(hooks=[refuse_stop_without_tests])],
        },
        env={"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8",
             "CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH": "1",
             "CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS": "2",
             "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"},
        stderr=lambda line: log_stderr(line),    # ProcessError.stderr is fixed text; this is real
    )

async def brain_turn(book: str, n: int, evidence: str, session_id: str | None) -> tuple[Verdict, ResultMessage]:
    async with ClaudeSDKClient(options=options(book, n, session_id)) as client:
        await client.query(PROMPT.format(book=book, n=n, evidence=evidence))
        result = None
        async for m in client.receive_response():
            if isinstance(m, RateLimitEvent) and m.rate_limit_info.status == "rejected":
                raise RateLimited(m.rate_limit_info.resets_at)        # scheduler sleeps
            if isinstance(m, ResultMessage):
                result = m
    if result is None or result.subtype != "success" or result.structured_output is None:
        raise BrainFailed(result)                 # subtype error_max_turns / error_max_budget_usd / ...
    if result.terminal_reason not in (None, "completed"):
        raise BrainFailed(result)                 # docs: check terminal_reason BEFORE subtype
    return Verdict.model_validate(result.structured_output), result
```

Permission facts behind those choices (code.claude.com/docs/en/agent-sdk/permissions):
- Evaluation order: hooks → deny rules → ask rules → permission mode → allow rules → canUseTool.
  A hook deny wins even in `bypassPermissions`; `allowed_tools` does NOT constrain `bypassPermissions`.
- `dontAsk`: "Any call that would otherwise prompt is denied … canUseTool is never called". That is
  the "never prompts" mode. (`bypassPermissions` also never prompts but approves everything.)
- If `permission_mode` is omitted the session may start in `auto` (classifier) — always set it.
- `Edit(path)` governs Write/NotebookEdit too and the Bash file commands Claude Code recognises
  (`sed`, `tee`, `cat`, `> file` redirections). It does NOT cover a Python script that opens files
  itself — which is exactly right: `uv run python episode.py` may write `library/`, a hand
  `sed -i library/.../plan.json` may not. `/library/**` with one leading slash anchors at the
  primary working directory for CLI/session rules; Windows paths are normalised to POSIX before
  matching (`C:\x` → `/c/x`).
- Bash allow rules are prefix-as-written: `Bash(uv run *)` ≡ `Bash(uv run:*)`.

Hook shapes (code.claude.com/docs/en/agent-sdk/hooks, /docs/en/hooks). Python callback is
`async def f(input_data, tool_use_id, context) -> dict`; input has `session_id, cwd,
hook_event_name, tool_name, tool_input`; return `{}` to allow:

```python
LIB = ROOT / "library"
BLOCKED_BASH = re.compile(r"(^|[\s;&|])(sed\s+-i|tee|mv|cp|rm|python\s+-c)\b.*library[/\\]|>\s*\S*library[/\\]|sign[_a-z]*\.py")

async def deny_library_writes(input_data, tool_use_id, context):
    tool, args = input_data["tool_name"], input_data["tool_input"]
    bad = False
    if tool in ("Write", "Edit", "NotebookEdit"):
        p = Path(args.get("file_path") or args.get("notebook_path") or "")
        bad = p.is_absolute() and p.resolve().is_relative_to(LIB)
    elif tool == "Bash":
        bad = bool(BLOCKED_BASH.search(args.get("command", "")))
    if not bad:
        return {}
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
            "permissionDecisionReason": "library/ data is written by the runner and its judges, "
                                        "never by hand; fix the code and relaunch drive.py"}}

async def refuse_stop_without_tests(input_data, tool_use_id, context):
    if input_data.get("stop_hook_active"):          # already blocked once: let it stop (loop guard)
        return {}
    if state.edited_code and not state.ran_pytest:  # set by audit_tool_call (PostToolUse)
        return {"decision": "block", "reason": "You edited code but did not run `uv run pytest -q` "
                                               "on the touched tests; run it, then stop."}
    return {}
```
Note: hooks and `agents` are re-sent on every process start (initialize request), so pass them on
every resume. Python SDK has PreToolUse/PostToolUse/PostToolUseFailure/UserPromptSubmit/Stop/
SubagentStart/SubagentStop/PreCompact/PermissionRequest/Notification; SessionStart/End are
TypeScript-only (shell-command hooks in `.claude/settings.json` work via `setting_sources`).

## 2. Authentication / billing — exact

Machine today (`claude auth status`): `loggedIn: true, authMethod: claude.ai, subscriptionType: max`,
NO `ANTHROPIC_API_KEY` in the environment; credentials at `%USERPROFILE%\.claude\.credentials.json`
(docs: Windows storage location, "inherit the access controls of your user profile directory").

The SDK's subprocess is the Claude Code CLI, so it uses the CLI's credential precedence
(code.claude.com/docs/en/authentication, "Authentication precedence"):
1 cloud provider vars → 2 `ANTHROPIC_AUTH_TOKEN` → 3 `ANTHROPIC_API_KEY` ("In non-interactive
mode (-p), the key is always used when present") → 4 `apiKeyHelper` → 5 `CLAUDE_CODE_OAUTH_TOKEN`
→ 6 Anthropic profile/WIF → 7 subscription OAuth from `/login`.

Two documented ways to run the brain:
- **API key (what the SDK docs tell you to use)**: `$env:ANTHROPIC_API_KEY = "sk-ant-…"` in the
  scheduler's environment only (PowerShell; or Task Scheduler → job env; or pass it in
  `ClaudeAgentOptions(env={...})` which is merged over the inherited env in Python). Billed per
  token at list price; `ResultMessage.total_cost_usd` then approximates the bill. Interactive
  sessions keep the subscription because the key is scoped to the job's env.
  Quickstart note, verbatim: "Unless previously approved, Anthropic does not allow third party
  developers to offer claude.ai login or rate limits for their products, including agents built on
  the Claude Agent SDK. Use the API key authentication methods described in this document instead."
- **Subscription (documented for your own automation)**: env-vars page, verbatim:
  `CLAUDE_CODE_OAUTH_TOKEN` — "OAuth access token for claude.ai authentication. Alternative to
  /login for SDK and automated environments. Takes precedence over keychain-stored credentials.
  Generate one with `claude setup-token`." Authentication page: "This token authenticates with your
  Claude subscription and requires a Pro, Max, Team, or Enterprise plan. It can only make model
  requests." One-year token; set `$env:CLAUDE_CODE_OAUTH_TOKEN`. With no env var at all the
  subprocess simply reads the same `.credentials.json` as your terminal (precedence 7). Cost: $0
  marginal, counted against the Max 5-hour / 7-day windows; the SDK emits `RateLimitEvent`
  (`rate_limit_type` in `five_hour|seven_day|seven_day_opus|seven_day_sonnet|overage`, `status`
  `allowed|allowed_warning|rejected`, `resets_at` epoch) — the scheduler sleeps until `resets_at`.
  `total_cost_usd` is still filled from the bundled price table (a list-price equivalent, not a bill).
  Which of the two the owner picks is his call (the "third party … products" sentence is about
  offering login to others; I am not grading it).

## 3. Resume across process restarts; cost ledger per episode

- `ResultMessage.session_id` is on every result (success or error). Also in
  `SystemMessage(subtype="init").data["session_id"]`.
- `ClaudeAgentOptions(resume=<id>)` restores the full conversation from
  `%USERPROFILE%\.claude\projects\<encoded-cwd>\<id>.jsonl`. Encoded cwd = non-alphanumerics → `-`;
  for this repo that is `d--Projects-KingdomOfViSuReNa-alpha-visurena-studio` (directory exists, 11
  transcripts). Resume works after a process restart, same machine; since CLI 2.1.223 the lookup
  is cross-directory. `continue_conversation=True` = most recent session in cwd (ambiguous when
  the owner also uses the repo interactively — use `resume` with the stored id).
- `fork_session=True` + `resume` branches without touching the original.
- Persist per episode in `library/<book>/episodes/epNN/brain.jsonl` (relative path, production_id
  convention): `{ts, turn, session_id, action, reason, commit, total_cost_usd, model_usage}`.
- Cost fields (code.claude.com/docs/en/agent-sdk/cost-tracking): `total_cost_usd` (client-side
  ESTIMATE from a bundled price table; "Do not bill end users … from these fields"), `usage`
  (main loop only; excludes subagents), `model_usage` → per model `{inputTokens, outputTokens,
  cacheReadInputTokens, cacheCreationInputTokens, costUSD, contextWindow, thinkingTokens, ...}`.
  Since CLI 2.1.277 a RESUMED call's `total_cost_usd` includes the session's earlier spend — so
  ledger the DELTA per turn (`total - previous total`), never the sum of resumed results.
  `max_budget_usd` counts only the call's own spend (restored totals don't count).
- Error contract: single-shot `query()` yields the error result THEN raises `ResultError`
  (subclass of `ProcessError`, fields `subtype, errors, result, api_error_status, terminal_reason,
  session_id, data`) — catch it after capturing session_id. Subtypes: `success | error_max_turns |
  error_max_budget_usd | error_during_execution | error_max_structured_output_retries`. Docs: "check
  terminal_reason before subtype" — an API failure on the last request reports `subtype:"success"`
  with `terminal_reason:"api_error"`. A session crash emits `error_during_execution` with zeroed cost.
- Live progress: `AssistantMessage` per content block (`message_id` shared across one API turn —
  dedupe on it; per-step `output_tokens` is a placeholder, read output from the result).
  `include_partial_messages=True` for token deltas if the UI wants them.

## 4. Structured verdict (Python decides, no prose parsing)

`output_format={"type":"json_schema","schema": Verdict.model_json_schema()}` → the SDK validates
and re-prompts on mismatch; result lands in `ResultMessage.structured_output` (dict). Treat
`subtype=="success" and structured_output is None` as failure (documented case). Schema is
JSON-Schema draft-07; keep it flat (the `Verdict` above). Pydantic 2.13.4 is already in the venv.
Documented against `query()`; `ClaudeAgentOptions` is the same object for `ClaudeSDKClient`, the
CLI flag is `--json-schema`, result per turn — confirm on the first real turn.

## 5. Model per role + cost per watcher session

Current IDs (platform.claude.com/docs/en/about-claude/models/overview, today):
`claude-fable-5-1` $10/$50 per MTok (cache read 2.5%), `claude-opus-5-5` $4/$20 (cache read 5%,
default effort medium), `claude-sonnet-5-5` $2/$10 (cache read 10%), `claude-haiku-4-5` $1/$5.
Claude Code aliases on the Anthropic API today: `opus`→Opus 5.5, `sonnet`→Sonnet 5.5,
`fable`→Fable 5.1, `default`→Opus 5.5 (code.claude.com/docs/en/model-config). Pin full IDs.

Roles:
- Monitor rung (read the ledger/log tail, decide RELAUNCH vs escalate, no code): `claude-sonnet-5-5`, effort `medium`, max_turns 15.
- Diagnose-and-fix rung (deferral root cause, test-first fix, commit): `claude-opus-5-5`, effort `high`; `fallback_model="claude-sonnet-5-5"`.
- Fable 5.1 only when Opus returns BLOCKED twice on the same unit (long-horizon reasoning; 2.5× Opus price).
- Subagents the brain spawns (e.g. `episode` from .claude/agents): `CLAUDE_CODE_SUBAGENT_MODEL=claude-sonnet-5-5`; depth 1, concurrency 2 via env above.

Cost per watcher session (modelled: 40 turns growing to ~100k context ≈ 2.4M cache-read tokens,
0.1M cache writes at 1.25×, 0.1M uncached input, 60k output; the 200k/80-turn case ≈ 3.5–4×):
- Sonnet 5.5: ≈ $1.5 (50k-ctx) … ≈ $5–6 (200k-ctx)
- Opus 5.5:   ≈ $2.6 … ≈ $9–10
- Fable 5.1:  ≈ $6 … ≈ $20–25
So per episode (1 monitor turn + 1–2 fix turns): ~$3–12 at API prices; $0 marginal on Max, bounded
by the 5-hour window. `max_budget_usd` is the hard cap either way.

## 6. Windows pitfalls + exact pins

1. **No Windows wheel on 0.2.160–0.2.163** (see §1). Pin `claude-agent-sdk==0.2.159` for a
   bundled `claude.exe`, or `==0.2.163` + rely on PATH `claude.exe`. `_find_cli` order: package
   `_bundled/claude.exe` → `shutil.which("claude")` (must be .exe/.com; `.cmd/.bat` refused) →
   `%USERPROFILE%\.local\bin\claude.exe` (the native installer's path; not present here).
   `cli_path=` skips discovery entirely.
2. **Disclosure**: while probing winget I ran `winget upgrade --id Anthropic.ClaudeCode --exact`
   intending a version query; it UPGRADED the CLI 2.1.158 → 2.1.286 (the SDK's paired version,
   no repo files touched). Open a new shell before relying on it.
3. CLI pairing matters: several documented behaviours need CLI ≥ 2.1.2xx (resume cost restore
   2.1.277, Stop-hook timeout = no-decision 2.1.273, invalid schema fails loudly 2.1.205, cross-dir
   resume 2.1.223). 2.1.158 had none of them.
4. Argv cap ≈ 32 KB on Windows: `system_prompt` string goes on argv → keep `append` short or use
   `{"type":"file","path":...}`. Prompts/hooks/agents go over stdin (no cap).
5. `resume`/`session_id` values are rejected if they contain `&|<>^%!"` (cmd.exe hardening) — UUIDs are fine.
6. UTF-8: the SDK's own pipe is JSON; the hazard is child processes (drive.py already does
   `utf8_console()`; set `PYTHONUTF8=1` in `env` for everything the Bash tool spawns). Bash tool on
   Windows = Git Bash (`CLAUDE_CODE_GIT_BASH_PATH` if not on PATH). `LongPathsEnabled=1` here.
7. Process tree: `ClaudeSDKClient.disconnect()` kills `claude.exe` only; Bash-tool children can
   outlive it (memory: kill by CommandLine match). Hence the scheduler, not the brain, owns
   `drive.py` (Popen with `CREATE_NEW_PROCESS_GROUP|DETACHED_PROCESS`, log to file, poll `drive.jsonl`).
8. Never start the watcher from inside an interactive Claude session (env carries
   `CLAUDE_CODE_SESSION_ID`, `CLAUDE_CODE_ENTRYPOINT`…; SDK strips only `CLAUDECODE`). Launch from
   plain PowerShell or Task Scheduler as the same Windows user (so `.credentials.json` is readable).
9. `uv add` strips the music/voice groups (memory) → `uv sync --all-groups` after. Put the SDK in
   its own group so the GPU pipeline venv is unchanged:
   ```toml
   [dependency-groups]
   brain = ["claude-agent-sdk==0.2.159", "pydantic==2.13.4"]
   ```
   Transitives the lock will carry (0.2.163 dry-run on this box): `mcp==2.3.0`, `anyio==4.15.1`,
   `jsonschema==4.26.0`, `pywin32==312`.
10. Tests never spend: `ClaudeSDKClient(transport=FakeTransport())` — `Transport` ABC has
    `connect/write/read_messages/close/is_ready/end_input`; a fake yields canned stream-json
    dicts ending in a `result` with `structured_output`. Tests cover: verdict parsing, the deny
    hook (library path, sed/redirect, sign script), the Stop guard loop-breaker, ledger delta
    arithmetic, rate-limit sleep. Live run is `@pytest.mark.local`-style opt-in only.

## 7. Scheduler loop (the comfort of Python)

```
brain_drive.py <book> <n>:
  home = episodes/epNN; sid = last session_id from brain.jsonl (or None)
  loop (max K brain turns, wall clock ≤ EPISODE_CEILING):
    launch drive.py detached; wait on drive.jsonl 'end' row or SILENCE_S silence (existing constants)
    if outcome == completed: ledger DONE; notify; exit 0
    evidence = ledger tail + last drive_runNN.log tail + git log -3 + nvidia-smi
    try: verdict, result = await brain_turn(book, n, evidence, sid); sid = result.session_id
    except RateLimited as r: notify; sleep until r.resets_at; continue
    except (ResultError, ProcessError) as e: ledger; notify; sid = e.session_id or sid; retry once, then BLOCKED
    ledger(verdict, cost delta); notify(verdict.reason)
    RELAUNCH → next iteration (drive.py itself refuses a dirty tree, so the brain must have committed)
    BLOCKED → notify owner with needs_owner; exit 1
```
Deliverable of a run: `library/<book>/episodes/epNN/cut/master_iterN.mp4` reported by drive.py as
today; the brain's artifact is `brain.jsonl` + commits.
