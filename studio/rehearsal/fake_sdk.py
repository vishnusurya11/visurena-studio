"""The Claude seam of a rehearsal: the SDK TRANSPORT (2026-10-21_ep02_proof 2.3, 2.4; R3, R9).

`install_into(brain)` rebinds brain.ClaudeSDKClient to RehearsalClient, a subclass that ALWAYS
passes a ReplayTransport (the fence refuses a client built without one).  So brain.turn,
brain.ask_structured and through them every `llm.structured` tier run their REAL parsing,
receipt, usage, RateLimited and BrainFailed code; only the bytes the CLI would have sent are
replayed.  An ask is answered, in order, by:
  fault        manifest `sdk_faults` [{"on": k, "kind": "rate_limit"|"error"}] on the k-th ask
  exact        a recorded stream <sdk_streams>/<schema title>/<prompt sha>.jsonl
  substituted  the episode writer's Draft parts folded from the manifest's `writer_plan`
  canned       the schema's REFUSING instance (canned_refusals.yaml); no row -> an error result
Every answer is one <sandbox>/sdk_log.jsonl row with its label (section 0's brick)."""
from __future__ import annotations

import hashlib
import importlib
import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, Callable, Mapping

import anyio
import yaml
from claude_agent_sdk import ClaudeSDKClient
from claude_agent_sdk._internal.transport import Transport

from studio.rehearsal import fakes

CANNED = Path(__file__).with_name("canned_refusals.yaml")
MODEL = "claude-rehearsal"
CANNED_MARK = "CANNED: no recorded answer for this ask (rehearsal)"
_SOURCE: list[Callable[[dict], list[dict]] | None] = [None]
_TABLE: list[dict | None] = [None]


# ---- the stream-json rows the CLI writes ------------------------------------------

def result_row(structured, *, usage: Mapping | None = None, **over) -> dict:
    """A `result` the way the CLI writes it (modelUsage camelCase)."""
    used = dict(usage or {"inputTokens": 1000, "outputTokens": 200, "cacheReadInputTokens": 0,
                          "cacheCreationInputTokens": 0, "costUSD": 0.0})
    row = {"type": "result", "subtype": "success", "duration_ms": 10, "duration_api_ms": 8, "is_error": False,
           "num_turns": 1, "session_id": "rehearsal", "total_cost_usd": 0.0, "structured_output": structured,
           "modelUsage": {MODEL: used}}
    return {**row, **over}


def rate_limit_row(resets_at: float) -> dict:
    return {"type": "rate_limit_event", "uuid": "rehearsal", "session_id": "rehearsal",
            "rate_limit_info": {"status": "rejected", "resetsAt": resets_at, "rateLimitType": "five_hour"}}


def error_row(subtype: str = "error_during_execution", why: str = "rehearsal fault") -> dict:
    return result_row(None, subtype=subtype, is_error=True, result=why)


# ---- the recorded streams ------------------------------------------------------------

def prompt_sha(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]


def stream_path(root: Path, title: str, prompt: str) -> Path:
    return Path(root) / title / f"{prompt_sha(prompt)}.jsonl"


def save_stream(root: Path, title: str, prompt: str, stream: list[dict]) -> Path:
    path = stream_path(root, title, prompt)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(m) + "\n" for m in stream), encoding="utf-8")
    return path


def load_stream(root: Path, title: str, prompt: str) -> list[dict] | None:
    path = stream_path(root, title, prompt)
    if not path.is_file():
        return None
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def ask_of(options, message: Mapping) -> dict:
    """What one user message asks: the schema (title and JSON) from the options, the prompt text."""
    fmt = getattr(options, "output_format", None) or {}
    schema = fmt.get("schema") if isinstance(fmt, dict) else None
    content = (message.get("message") or {}).get("content")
    prompt = content if isinstance(content, str) else json.dumps(content, sort_keys=True)
    return {"title": (schema or {}).get("title", ""), "schema": schema, "prompt": prompt,
            "model": getattr(options, "model", None)}


# ---- canned: the schema's refusing instance -------------------------------------------

def canned_table() -> dict:
    """canned_refusals.yaml, read once per process."""
    if _TABLE[0] is None:
        _TABLE[0] = yaml.safe_load(CANNED.read_text(encoding="utf-8"))
    return _TABLE[0]


def schema_class(spec: str):
    """`package.module:Class` -> the class."""
    module, _, name = spec.partition(":")
    return getattr(importlib.import_module(module), name)


def titles_of(row: Mapping) -> list[str]:
    return list(row.get("titles") or [row["schema"].rpartition(":")[2]])


def same_schema(row: Mapping, schema: Mapping | None) -> bool:
    """A row whose class's JSON schema is the asked one (two classes may share a title)."""
    try:
        return schema is None or schema_class(row["schema"]).model_json_schema() == dict(schema)
    except Exception:                                   # noqa: BLE001 -- an unimportable row never answers
        return False


def canned_row(ask: Mapping) -> dict | None:
    """The refusing row for this ask's schema: by title, told apart by the schema when titles repeat."""
    rows = [r for r in canned_table()["refusals"] if ask.get("title") in titles_of(r)]
    if len(rows) > 1:
        rows = [r for r in rows if same_schema(r, ask.get("schema"))] or rows[:0]
    return rows[0] if rows else None


# ---- the writer's Draft parts from a target plan --------------------------------------

def draft_of(plan: Mapping) -> dict:
    """The plan in the writer's Draft shape: setups a named list, the code-set fields dropped."""
    from agents.episode_writer import Draft
    doc = {k: v for k, v in plan.items() if k in Draft.model_fields}
    doc["setups"] = [{"name": name, **setup} for name, setup in (plan.get("setups") or {}).items()]
    return doc


def draft_parts(plan: Mapping) -> dict[str, dict]:
    """Part model name -> that part's PART_TABLE fields of the plan (absent fields left out)."""
    from agents.episode_writer import PART_MODELS, PART_TABLE
    draft = draft_of(plan)
    return {model.__name__: {f: draft[f] for f in fields if f in draft}
            for (_, fields), model in zip(PART_TABLE, PART_MODELS)}


# ---- the source: fault, exact, substituted, canned -------------------------------------

class Library:
    """ask -> (label, stream), one sdk_log.jsonl row per ask (the k-th ask counts from 1)."""

    def __init__(self, box: Path, manifest: Mapping):
        self.box, self.asked = Path(box), 0
        self.streams = Path(manifest.get("sdk_streams") or Path(box) / "sdk_streams")
        self.faults = {int(f["on"]): f for f in manifest.get("sdk_faults") or ()}
        plan = manifest.get("writer_plan")
        self.parts = draft_parts(json.loads(Path(plan).read_text(encoding="utf-8"))) if plan else {}

    def __call__(self, ask: Mapping) -> list[dict]:
        self.asked += 1
        label, stream, row = self.fault(ask) or self.recorded(ask) or self.substituted(ask) or self.canned(ask)
        fakes.log(self.box, "sdk_log", {"n": self.asked, "label": label, "title": ask.get("title"),
                                        "prompt_sha": prompt_sha(ask.get("prompt", "")), "row": row})
        return stream

    def fault(self, ask: Mapping):
        fault = self.faults.get(self.asked)
        if fault is None:
            return None
        if fault["kind"] == "rate_limit":
            return "fault", [rate_limit_row(fault.get("resets_at", 0)), error_row()], "rate_limit"
        return "fault", [error_row(fault.get("subtype", "error_during_execution"))], fault["kind"]

    def recorded(self, ask: Mapping):
        stream = load_stream(self.streams, ask.get("title", ""), ask.get("prompt", ""))
        return ("exact", stream, None) if stream else None

    def substituted(self, ask: Mapping):
        part = self.parts.get(ask.get("title", ""))
        return ("substituted", [result_row(part)], "writer_plan") if part else None

    def canned(self, ask: Mapping):
        row = canned_row(ask)
        if row is None:
            return "canned", [error_row(why=f"{CANNED_MARK}; no refusing row for {ask.get('title')!r}")], None
        return "canned", [result_row(row["instance"])], row["schema"]


# ---- the transport and the client --------------------------------------------------------

class ReplayTransport(Transport):
    """The SDK's own seam: answers every control request with success and, on the user's
    message, yields the source's stream.  `rehearsal = True` is what the fence looks for."""

    rehearsal = True

    def __init__(self, source: Callable[[Mapping], list[dict]], options=None):
        self.source, self.options, self.writes, self._ready = source, options, [], False
        self._send, self._recv = anyio.create_memory_object_stream(256)

    async def connect(self) -> None:
        self._ready = True

    async def write(self, data: str) -> None:
        message = json.loads(data)
        self.writes.append(message)
        if message.get("type") == "control_request":
            await self._send.send({"type": "control_response", "response": {
                "subtype": "success", "request_id": message["request_id"], "response": {}}})
        elif message.get("type") == "user":
            for reply in self.source(ask_of(self.options, message)):
                await self._send.send(reply)

    async def read_messages(self) -> AsyncIterator[dict[str, Any]]:
        async with self._recv:
            async for message in self._recv:
                yield message

    async def close(self) -> None:
        self._ready = False
        await self._send.aclose()

    def is_ready(self) -> bool:
        return self._ready

    async def end_input(self) -> None:
        return None


def source() -> Callable[[Mapping], list[dict]]:
    """The installed Library; a client built before install_into refuses every ask."""
    return _SOURCE[0] or (lambda ask: [error_row(why="the rehearsal SDK source is not installed")])


class RehearsalClient(ClaudeSDKClient):
    """ClaudeSDKClient that ALWAYS passes a ReplayTransport (a rehearsal one given is kept)."""

    def __init__(self, options=None, transport=None):
        if not getattr(transport, "rehearsal", False):
            transport = ReplayTransport(source(), options)
        super().__init__(options=options, transport=transport)


def install_into(brain, manifest: Mapping, box: Path):
    """The patch fakes lands when studio.brain is imported; returns its undo."""
    _SOURCE[0] = Library(box, manifest)
    undo = fakes.set_attr(brain, "ClaudeSDKClient", RehearsalClient)

    def undone() -> None:
        undo()
        _SOURCE[0] = None
    return undone
