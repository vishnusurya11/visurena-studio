"""Which gate consumed each VL reply (2026-10-21_ep02_proof 2.3, 2.4, R3).

A wrapper AROUND (never instead of) comfy.run_text and comfy.cached_text: the real call runs,
and the OUTERMOST read appends one <sandbox>/vl_consumers.jsonl row {prompt_id, ask, caller,
via, cache, error}.  `prompt_id` is what comfy.submit returned inside the read (None on a cache
hit), `ask` the workflow name, `caller` the qualname of the first function outside studio.comfy
that asked.  P5 joins the rows to the fake engine's engine_log.jsonl by prompt id, so a gate that
passed on a canned (unread) reply is named."""
from __future__ import annotations

import contextvars
import functools
import sys
from pathlib import Path
from typing import Callable, Mapping

from studio.rehearsal import fakes

SKIPPED = frozenset({"studio.comfy", __name__, "functools", "contextlib"})
"""Modules whose frames are the read itself, never its consumer."""
_OPEN: contextvars.ContextVar[tuple] = contextvars.ContextVar("vl_reads", default=())


def caller(depth: int = 2) -> str:
    """module.qualname of the first frame outside the read's own modules."""
    frame = sys._getframe(depth)
    while frame is not None and frame.f_globals.get("__name__") in SKIPPED:
        frame = frame.f_back
    if frame is None:
        return "?"
    return f"{frame.f_globals.get('__name__', '?')}.{frame.f_code.co_qualname}"


def noting(submit: Callable) -> Callable:
    """comfy.submit that hands its prompt id to every read in progress."""
    @functools.wraps(submit)
    def call(*args, **kwargs):
        prompt_id = submit(*args, **kwargs)
        for read in _OPEN.get():
            read.append(prompt_id)
        return prompt_id
    return call


def cache_state(via: str, ids: list) -> str | None:
    return None if via != "cached_text" else ("miss" if ids else "hit")


def logged(read: Callable, via: str, box: Path) -> Callable:
    """`read` with one row per outermost call (an inner run_text of a cached_text is not a row)."""
    @functools.wraps(read)
    def call(name, *args, **kwargs):
        ids: list = []
        outer, token = not _OPEN.get(), _OPEN.set(_OPEN.get() + (ids,))
        who, failed = caller(), None
        try:
            return read(name, *args, **kwargs)
        except BaseException as exc:
            failed = type(exc).__name__
            raise
        finally:
            _OPEN.reset(token)
            if outer:
                fakes.log(box, "vl_consumers", {"prompt_id": ids[-1] if ids else None, "ask": name, "caller": who,
                                                "via": via, "cache": cache_state(via, ids), "error": failed})
    return call


def wrap(comfy, box: Path) -> Callable[[], None]:
    undo = [fakes.set_attr(comfy, "submit", noting(comfy.submit)),
            fakes.set_attr(comfy, "run_text", logged(comfy.run_text, "run_text", box)),
            fakes.set_attr(comfy, "cached_text", logged(comfy.cached_text, "cached_text", box))]
    return lambda: [u() for u in reversed(undo)]


def install(manifest: Mapping, box: Path) -> None:
    fakes.on_import("studio.comfy", lambda comfy: wrap(comfy, box))
