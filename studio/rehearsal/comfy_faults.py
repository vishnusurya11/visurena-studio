"""The faults the fake ComfyUI injects, each fired by a submit counter (2026-10-21_ep02_proof
DESIGN 2.2, scenarios F1, F1b, F9, F10, F11, F13, F16).

A fault row is `{kind, on: "submit#k", workflow?, detail?, text?}` or the design's sentence
`"<kind> on submit#k of workflow W"`.  The counter is per workflow; a row with no workflow counts
every submit.  The kinds:

  crash        the job is accepted, then the engine drops every connection for `detail` seconds
               (default 1) and comes back EMPTY: the job is forgotten (comfy.EngineLost)
  lost         accepted, then the engine never answers again; a restart cannot revive it (F1b)
  hang         accepted and running for ever; /interrupt is ignored until a restart (F9)
  exec_error   the job ends in an execution_error with TRANSIENT text (HostBuffer): retried once
  exec_fatal   an execution_error with NON-transient text (out of memory): never retried (F16)
  unreadable   a text job answers a reply every reader's readable() refuses (F11)
  corrupt      the output is broken: zero_byte, truncated, no_audio or wrong_frames (F13)
  rejected     every output fails validation: HTTP 400 prompt_outputs_failed_validation, nothing
               queued; `detail` names the broken input as <node>.<input> (GPU transcript, case B)
  partial_accept  one output still validates: HTTP 200 WITH node_errors, the valid outputs run and
               the job ends `success` with no picture (GPU transcript, case A)

The error texts are the client's own retry class (`comfy.TRANSIENT`) and ComfyUI's
out-of-memory wording.  NO studio log in the repo holds a recorded OOM, so FATAL_ERROR's
`source` says so; a manifest row's `text` replaces either text with a recorded one."""
from __future__ import annotations

import re
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

KINDS = ("crash", "lost", "hang", "exec_error", "exec_fatal", "unreadable", "corrupt", "rejected", "partial_accept")
CORRUPTIONS = ("zero_byte", "truncated", "no_audio", "wrong_frames")
VIDEO_ONLY = ("no_audio", "wrong_frames")
SENTENCE = re.compile(r"^\s*(\w+)\s+(?:on|at)\s+submit#(\d+)(?:\s+of\s+workflow\s+(\S+))?\s*$")
ON = re.compile(r"^submit#(\d+)$")

TRANSIENT_ERROR = {"node_type": "LoadVideo", "exception_type": "RuntimeError",
                   "exception_message": "HostBuffer.read_file_slice error",
                   "source": "comfy.TRANSIENT and the drive-log wording the client's retry tests carry"}
FATAL_ERROR = {"node_type": "SamplerCustomAdvanced", "exception_type": "torch.OutOfMemoryError",
               "exception_message": "Allocation on device 0 would exceed allowed memory. (out of memory)\n"
                                    "Currently allocated     : 22.61 GiB\nRequested               : 1.27 GiB",
               "source": "ComfyUI's OOM wording; no recorded OOM exists in the repo (a manifest `text` replaces it)"}
UNREADABLE_TEXT = "I am unable to make out the picture clearly enough to answer."
"""Prose a real VL model gives: no JSON, no list, so every studio reader's `readable()` refuses it."""


@dataclass(frozen=True)
class Fault:
    kind: str
    at: int
    workflow: str | None = None
    detail: str | None = None
    text: str | None = None


def parse(spec: Any) -> Fault:
    """A Fault from a manifest row or the design's sentence; an unknown kind or corruption raises."""
    if isinstance(spec, Fault):
        return spec
    if isinstance(spec, str):
        hit = SENTENCE.match(spec)
        if not hit:
            raise ValueError(f"cannot read the fault {spec!r}: '<kind> on submit#k [of workflow W]'")
        spec = {"kind": hit.group(1), "on": f"submit#{hit.group(2)}", "workflow": hit.group(3)}
    on = ON.match(str(spec.get("on", "")))
    fault = Fault(spec.get("kind", ""), int(on.group(1)) if on else 0, spec.get("workflow"),
                  None if spec.get("detail") is None else str(spec["detail"]), spec.get("text"))
    return checked(fault)


def checked(fault: Fault) -> Fault:
    if fault.kind not in KINDS:
        raise ValueError(f"unknown fault kind {fault.kind!r}; one of {KINDS}")
    if fault.at < 1:
        raise ValueError(f"a fault fires on submit#k with k >= 1, not {fault.at}")
    if fault.kind == "corrupt" and fault.detail not in CORRUPTIONS:
        raise ValueError(f"a corrupt fault names one of {CORRUPTIONS}, not {fault.detail!r}")
    return fault


class Faults:
    """The manifest's fault rows and the submit counters they fire on."""

    def __init__(self, specs=()):
        self.faults = [parse(s) for s in specs]
        self.counts: Counter = Counter()
        self.total = 0

    def on_submit(self, workflow: str | None) -> Fault | None:
        """Count this submit; the fault that fires on it, if any (the first row wins)."""
        self.counts[workflow] += 1
        self.total += 1
        for fault in self.faults:
            if fault.workflow is None:
                count = self.total
            else:
                count = self.counts[workflow] if fault.workflow == workflow else None
            if count == fault.at:
                return fault
        return None


def error_of(fault: Fault) -> dict:
    """The execution_error fields this fault reports."""
    base = dict(TRANSIENT_ERROR if fault.kind == "exec_error" else FATAL_ERROR)
    if fault.text:
        base["exception_message"] = fault.text
    return base


def message_text(error: dict) -> str:
    """What the client's error line says: `<node_type>: <exception_message>` (comfy._first_error)."""
    return f"{error.get('node_type')}: {error.get('exception_message')}"


def error_message(fault: Fault, prompt_id: str, node_id: str, now_ms: int, inputs: dict | None = None) -> list:
    """The ["execution_error", {...}] status message, in the engine's field set and forms: each of the
    failing node's inputs as a list of its repr, and the node ids with outputs as a list (SR-5)."""
    error = error_of(fault)
    return ["execution_error", {"prompt_id": prompt_id, "node_id": str(node_id), "node_type": error["node_type"],
                                "executed": [], "exception_message": error["exception_message"],
                                "exception_type": error["exception_type"],
                                "traceback": [f"rehearsal fake: {error['exception_type']} (no recorded traceback)\n"],
                                "current_inputs": {k: [str(v)] for k, v in (inputs or {}).items()},
                                "current_outputs": [str(node_id)], "timestamp": now_ms}]


REJECTED = {"type": "prompt_outputs_failed_validation", "message": "Prompt outputs failed validation",
            "details": "", "extra_info": {}}
"""The 400's `error` when no output of the graph validates (GPU transcript, error_invalid_graph case B)."""


def broken_input(fault: Fault, graph: dict) -> tuple[str, str]:
    """(node id, input name) a validation fault names as <node>.<input>; else the first node's first input."""
    if fault.detail and "." in fault.detail:
        node, name = fault.detail.rsplit(".", 1)
        return node, name
    node = next((n for n, spec in graph.items() if (spec or {}).get("inputs")), next(iter(graph)))
    return str(node), next(iter((graph[node] or {}).get("inputs") or {"input": None}))


def node_errors(fault: Fault, graph: dict, dependents: list[str]) -> dict:
    """The engine's `node_errors` for one missing required input and the outputs it starves."""
    node, name = broken_input(fault, graph)
    error = {"type": "required_input_missing", "message": "Required input is missing", "details": name,
             "extra_info": {"input_name": name}}
    return {node: {"errors": [error], "dependent_outputs": list(dependents),
                   "class_type": (graph.get(node) or {}).get("class_type")}}


def ffmpeg() -> str:
    """The pinned imageio-ffmpeg binary studio/take_zoom.ffmpeg_exe runs, never whatever PATH holds:
    a rehearsal with no ffmpeg on PATH must not answer HTTP 500, a fault the real engine never gives."""
    from studio.take_zoom import ffmpeg_exe
    return ffmpeg_exe()


def reencode(path: Path, args: list[str]) -> None:
    """Rewrite `path` through ffmpeg with `args` between input and output."""
    tmp = path.with_name(path.stem + ".corrupt" + path.suffix)
    subprocess.run([ffmpeg(), "-y", "-v", "error", "-i", str(path), *args, str(tmp)], check=True, capture_output=True)
    tmp.replace(path)


def corrupt(path: Path, how: str, frames: int) -> Path:
    """Break the sandbox copy `path` the named way; `frames` is the frame count it holds."""
    path = Path(path)
    if how in VIDEO_ONLY and path.suffix.lower() not in (".mp4", ".webm", ".mov", ".mkv"):
        raise ValueError(f"corrupt {how} needs a video output, not {path.name}")
    if how == "zero_byte":
        path.write_bytes(b"")
    elif how == "truncated":
        body = path.read_bytes()
        path.write_bytes(body[: max(1, len(body) // 2)])
    elif how == "no_audio":
        reencode(path, ["-c:v", "copy", "-an"])
    else:
        reencode(path, ["-frames:v", str(max(1, frames // 2)), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac"])
    return path
