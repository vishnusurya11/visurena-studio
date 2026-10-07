"""The brain: one Claude Agent SDK session on a leash (decision 2026-10-06, Layer 2).

The supervisor (studio/autopilot.py) owns the loop; this module owns one TURN of
judgment: a brief with repo-relative paths in, a structured Verdict out, the cost
ledgered as the delta of the session's running total.  Two rungs, both unattended:
triage mid-run reads and answers (retry | cure(order) | park); the fixer between
episodes edits code and tests, and its commit stands only through the ratchet
(studio/ratchet.py).  Both run `dontAsk` -- an unlisted tool is denied, never a
prompt -- and a PreToolUse hook refuses any write that resolves under library/, any
shell route into it, every sign script, `git push|reset|amend` and `uv add|remove`:
data is written by the runner and its judges, never by hand.

The supervisor trusts the verdict JSON, the verdict file and `git rev-parse HEAD`,
never prose.  Nothing here imports a department; Strands keeps every department
call.  A test drives `turn` through a fake Transport; no test spends.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, HookMatcher, RateLimitEvent, ResultMessage
from pydantic import BaseModel

from studio import registry, spend

ROOT = Path(__file__).resolve().parents[1]
"""The repo root: the writer session's cwd."""

TRIAGE_MODEL = "claude-sonnet-5-5"
FIXER_MODEL = "claude-opus-5-5"
ORDER_KINDS = frozenset({"redo", "retry", "requeue"})
ENV = {"PYTHONUTF8": "1", "CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH": "1"}
READ_TOOLS = ["Read", "Glob", "Grep",
              "Bash(uv run --no-sync pytest *)",
              "Bash(uv run --no-sync python scripts/episode/plan_check.py *)",
              "Bash(git log *)", "Bash(git diff *)"]
NEVER = ["WebSearch", "WebFetch", "AskUserQuestion", "mcp__*"]
EDIT_TOOLS = ("Edit", "Write", "NotebookEdit")
TRIAGE_DENY = [*EDIT_TOOLS, *NEVER]
FIXER_TOOLS = [*READ_TOOLS, "Edit", "Write", "Bash(git add *)", "Bash(git commit *)",
               "Workflow(fix-parked)"]
FIXER_DENY = ["Edit(/library/**)", *NEVER]
WRITERS = "Write|Edit|NotebookEdit|Bash"
DENY_REASON = ("library/ data is written by the runner and its judges, never by hand, and the "
               "history is never rewritten: fix the code with its test and let the supervisor relaunch")
STOP_REASON = ("You edited code but did not run `uv run --no-sync pytest -q` on the touched tests; "
               "run it, then stop.")
_BASH_DENY = re.compile(
    r"\bsed\s+-i\b[^\n;|&]*\blibrary[/\\]"
    r"|\btee\b[^\n;|&]*\blibrary[/\\]"
    r"|>{1,2}\s*['\"]?\S*\blibrary[/\\]"
    r"|\bsign_[a-z_]*\.py\b"
    r"|\bgit\s+(?:push|reset)\b|\bgit\s+commit\b.*--amend"
    r"|\buv\s+(?:add|remove)\b")
_DRIVE = re.compile(r"[A-Za-z]:[\\/](?:[^\s'\"<>|]*?[\\/])?visurena_studio[\\/]|[A-Za-z]:[\\/]")


class BrainFailed(Exception):
    """The session ended without a verdict the supervisor may act on."""


class RateLimited(Exception):
    """The subscription window is shut; `resets_at` is when it opens (epoch seconds)."""

    def __init__(self, resets_at: float | None):
        super().__init__(f"rate limited until {resets_at}")
        self.resets_at = resets_at


class Verdict(BaseModel):
    """What one turn answers.  `order` is {kind, step_id} for a cure; `finding_row` is
    one tracker table row `| F? | Seen | Cost | Change | State |`; `proposed_diff` is
    text the fixer may later apply; `commit` is the SHA a fix landed on, if any."""
    response: Literal["retry", "cure", "park", "relaunch"]
    order: dict | None = None
    reason: str
    finding_row: str
    proposed_diff: str = ""
    commit: str | None = None


# --- the brief -------------------------------------------------------------------

def _relative(text: str) -> str:
    """Repo-relative: a drive-lettered prefix up to the repo folder is dropped, any
    other drive letter becomes a root, so the brief reads the same on every machine."""
    return _DRIVE.sub(lambda m: "" if "visurena_studio" in m.group(0) else "/", text)


def brief(home_rel: str, log_tail: str, deferred_faults: list[str], learnings_tail: list[dict],
          spent_usd: float, allowed_orders: list[str]) -> str:
    """The evidence one turn reads, relative paths only."""
    lines = [f"Episode home: {home_rel} (paths are repo-relative; nothing under library/ is written by hand)",
             f"Spent so far on this episode: ${spent_usd:.2f}",
             "Allowed orders (kind, episode step id): " + ", ".join(allowed_orders),
             "Deferred faults:", *(f"- {fault}" for fault in deferred_faults),
             "Last learnings rows:", *(f"- {json.dumps(row, sort_keys=True)}" for row in learnings_tail),
             "Log tail:", log_tail,
             "Answer the Verdict JSON only: response retry | cure (with order) | park | relaunch, "
             "reason, finding_row (| F? | Seen | Cost | Change | State |), proposed_diff."]
    return _relative("\n".join(lines))


# --- the hooks -------------------------------------------------------------------

def _deny(reason: str) -> dict:
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                   "permissionDecisionReason": reason}}


def _under_library(repo: Path, cwd: str | None, target: str) -> bool:
    """A tool path, resolved against the session's cwd, that lands under library/."""
    if not target:
        return False
    path = Path(target)
    if not path.is_absolute():
        path = Path(cwd or repo) / path
    return path.resolve().is_relative_to((repo / "library").resolve())


def _bash_writes_library(command: str) -> bool:
    return bool(_BASH_DENY.search(command))


def deny_library_writes(repo: Path):
    """The PreToolUse hook for both rungs: path-resolving on the file tools, pattern
    matching on Bash.  Returns {} to allow."""
    async def hook(input_data: dict, tool_use_id: str | None, context: object) -> dict:
        tool, args = input_data.get("tool_name"), input_data.get("tool_input") or {}
        if tool == "Bash":
            bad = _bash_writes_library(args.get("command", ""))
        else:
            target = args.get("file_path") or args.get("notebook_path") or ""
            bad = _under_library(repo, input_data.get("cwd"), target)
        return _deny(DENY_REASON) if bad else {}
    return hook


@dataclass
class FixerState:
    """What the fixer's session has done so far, kept by the PostToolUse audit."""
    edited: bool = False
    tested: bool = False


def audit_tool_call(state: FixerState):
    """PostToolUse: an edit wants the suite run again; a pytest run satisfies it."""
    async def hook(input_data: dict, tool_use_id: str | None, context: object) -> dict:
        tool, args = input_data.get("tool_name"), input_data.get("tool_input") or {}
        if tool in EDIT_TOOLS:
            state.edited, state.tested = True, False
        elif tool == "Bash" and "pytest" in args.get("command", ""):
            state.tested = True
        return {}
    return hook


def refuse_stop_without_tests(state: FixerState):
    """Stop: block once when code was edited and pytest did not run since;
    `stop_hook_active` means we already blocked, so let it stop (the loop guard)."""
    async def hook(input_data: dict, tool_use_id: str | None, context: object) -> dict:
        if input_data.get("stop_hook_active"):
            return {}
        if state.edited and not state.tested:
            return {"decision": "block", "reason": STOP_REASON}
        return {}
    return hook


# --- the options -----------------------------------------------------------------

def _options(repo: Path, *, tools: list[str], denied: list[str], model: str, effort: str,
             turns: int, budget: float, hooks: dict, fallback: str | None = None) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        cwd=str(repo), model=model, fallback_model=fallback, effort=effort,
        permission_mode="dontAsk", allowed_tools=list(tools), disallowed_tools=list(denied),
        setting_sources=["project"], max_turns=turns, max_budget_usd=budget,
        output_format={"type": "json_schema", "schema": Verdict.model_json_schema()},
        env=dict(ENV), hooks=hooks)


def triage_options(repo: Path) -> ClaudeAgentOptions:
    """Mid-run: read, run the suite and plan_check, answer.  Never a write."""
    guard = HookMatcher(matcher=WRITERS, hooks=[deny_library_writes(repo)])
    return _options(repo, tools=READ_TOOLS, denied=TRIAGE_DENY, model=TRIAGE_MODEL,
                    effort="medium", turns=15, budget=1.0, hooks={"PreToolUse": [guard]})


def fixer_options(repo: Path, state: FixerState | None = None) -> ClaudeAgentOptions:
    """Between episodes: edit code and tests, commit on master, never push."""
    state = state or FixerState()
    hooks = {"PreToolUse": [HookMatcher(matcher=WRITERS, hooks=[deny_library_writes(repo)])],
             "PostToolUse": [HookMatcher(hooks=[audit_tool_call(state)])],
             "Stop": [HookMatcher(hooks=[refuse_stop_without_tests(state)])]}
    return _options(repo, tools=FIXER_TOOLS, denied=FIXER_DENY, model=FIXER_MODEL,
                    fallback=TRIAGE_MODEL, effort="high", turns=60, budget=3.0, hooks=hooks)


# --- the turn --------------------------------------------------------------------

def verdict_of(result: ResultMessage | None) -> Verdict:
    """The verdict is the result's structured output; anything else is a failure."""
    if result is None:
        raise BrainFailed("the session ended without a result")
    if result.terminal_reason not in (None, "completed"):
        raise BrainFailed(f"terminal_reason {result.terminal_reason}")
    if result.is_error or result.subtype != "success":
        raise BrainFailed(f"{result.subtype}: {result.errors or result.result}")
    if result.structured_output is None:
        raise BrainFailed("no structured output: the verdict is JSON, never prose")
    return Verdict.model_validate(result.structured_output)


def receipt_of(result: ResultMessage) -> dict:
    """What the ledger needs: input counts every token the model read, cached or not."""
    usage = {}
    for model, used in (result.model_usage or {}).items():
        usage[model] = {"input_tokens": int(used.get("inputTokens", 0))
                        + int(used.get("cacheReadInputTokens", 0))
                        + int(used.get("cacheCreationInputTokens", 0)),
                        "output_tokens": int(used.get("outputTokens", 0))}
    return {"session_id": result.session_id, "total_cost_usd": result.total_cost_usd,
            "model_usage": usage, "num_turns": result.num_turns}


async def turn(prompt: str, options: ClaudeAgentOptions, *, transport=None) -> tuple[Verdict, dict]:
    """One session, one prompt, one verdict.  `transport` is the SDK's seam for a
    fake; None spawns the bundled claude.exe."""
    result = None
    async with ClaudeSDKClient(options=options, transport=transport) as client:
        await client.query(prompt)
        async for message in client.receive_response():
            if isinstance(message, RateLimitEvent) and message.rate_limit_info.status == "rejected":
                raise RateLimited(message.rate_limit_info.resets_at)
            if isinstance(message, ResultMessage):
                result = message
    return verdict_of(result), receipt_of(result)


# --- the ledger and the clamp ----------------------------------------------------

def _tokens(model_usage: dict) -> tuple[int, int]:
    tokens_in = sum(int(u.get("input_tokens", 0)) for u in model_usage.values())
    tokens_out = sum(int(u.get("output_tokens", 0)) for u in model_usage.values())
    return tokens_in, tokens_out


def ledger(conn, codex_id: str, unit: str, step_id: str, model: str, prev_total: float,
           result: dict) -> float:
    """One usage row per turn, stage `brain`, costed as the DELTA of the session's
    running total (a resumed call's total includes the session's earlier spend).
    A turn with no total keeps the rate-table price.  Returns the new total."""
    tokens_in, tokens_out = _tokens(result.get("model_usage") or {})
    spend.record(conn, codex_id, "brain", step_id, "brain", model, tokens_in, tokens_out, unit=unit)
    total = result.get("total_cost_usd")
    if total is None:
        return prev_total
    delta = round(max(float(total) - prev_total, 0.0), 6)
    conn.execute("UPDATE usage SET cost_usd = ? WHERE id = (SELECT MAX(id) FROM usage)", (delta,))
    conn.commit()
    return float(total)


def episode_step_ids() -> set[str]:
    return {step["id"] for step in registry.steps("episode")}


def _clamped(verdict: Verdict, why: str) -> Verdict:
    return verdict.model_copy(update={"response": "park", "order": None,
                                      "reason": f"clamped: {why}; {verdict.reason}"})


def allowed(verdict: Verdict, step_ids: set[str]) -> Verdict:
    """An order the desk accepts, on a step the episode stage has; else park and say why."""
    order = verdict.order
    if order is None:
        return _clamped(verdict, "a cure names no order") if verdict.response == "cure" else verdict
    kind, step = order.get("kind"), str(order.get("step_id", ""))
    if kind not in ORDER_KINDS:
        return _clamped(verdict, f"order kind {kind!r} is not one of {sorted(ORDER_KINDS)}")
    if step not in step_ids:
        return _clamped(verdict, f"step {step!r} is not an episode step")
    return verdict


# --- the structured writer on the subscription (owner, 2026-10-07) --------------
# "don't use API for money -- use Claude, like how you used to supervise."  One
# session per structured call: no tools, the schema enforced by the SDK, nothing
# billed.  Every LLM tier in models.yaml routes here (studio/llm._SdkStructuredCaller).

WRITER_SYSTEM = ("You are a department of a film studio answering ONE structured brief. "
                 "Return only the JSON the schema asks for: no prose, no commentary, no questions.")


def writer_options(schema_model, *, model: str, effort: str = "medium", turns: int = 3) -> ClaudeAgentOptions:
    """A pure generation session: no tools, no project settings, the schema as the
    output format, a small turn cap (a re-prompt on schema mismatch is a turn)."""
    return ClaudeAgentOptions(
        cwd=str(ROOT), model=model, effort=effort, permission_mode="dontAsk",
        allowed_tools=[], disallowed_tools=["Bash", "Edit", "Write", "Read", "Glob", "Grep", "Agent", "WebSearch", "WebFetch"],
        setting_sources=[], max_turns=turns, system_prompt=WRITER_SYSTEM,
        output_format={"type": "json_schema", "schema": schema_model.model_json_schema()},
        env=dict(ENV))


async def ask_structured(prompt: str, schema_model, *, model: str, effort: str = "medium", transport=None):
    """One session, one prompt, one validated instance of `schema_model`; the
    receipt carries the SDK's usage so the ledger keeps the tokens at no cost."""
    result = None
    async with ClaudeSDKClient(options=writer_options(schema_model, model=model, effort=effort),
                               transport=transport) as client:
        await client.query(prompt)
        async for message in client.receive_response():
            if isinstance(message, RateLimitEvent) and message.rate_limit_info.status == "rejected":
                raise RateLimited(message.rate_limit_info.resets_at)
            if isinstance(message, ResultMessage):
                result = message
    if result is None or result.is_error or result.subtype != "success" or result.structured_output is None:
        raise BrainFailed(f"no structured answer: {getattr(result, 'subtype', None)} {getattr(result, 'result', '')!s:.200}")
    return schema_model.model_validate(result.structured_output), receipt_of(result)
