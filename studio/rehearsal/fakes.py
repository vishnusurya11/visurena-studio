"""The rehearsal's fakes (2026-10-21_ep02_proof 2.3, package P4): `install(manifest)` is called by
`activate.install()` in EVERY rehearsal process, after the fence is armed.

Seam policy: fake at the OUTERMOST boundary, so every line of studio code in front of it runs.
Each fake module registers patches here; a patch lands the moment its module is imported (now,
if it already is) through the fence's import hook, so installing costs no import:
  fake_sdk      the Claude SDK transport (brain.ClaudeSDKClient always passes ReplayTransport)
  fake_workers  the face detect / anime id / whisper workers at the process boundary, memo-fed
  fake_publish  YouTube refuses by default; Telegram captured; the engine launch to fake_comfy
  vl_consumers  a log AROUND comfy.run_text / cached_text naming the gate that read each reply
  scale         the hang and cap time constants divided by manifest.scale
plus VISURENA_MASTER_UPSCALE=lanczos (the CPU path; av3 is never exercised).

`uninstall()` undoes every patch (tests only: a rehearsal process keeps its fakes to its exit)."""
from __future__ import annotations

import importlib
import inspect
import json
import os
import time
from pathlib import Path
from typing import Any, Callable, Mapping

from studio import settings
from studio.rehearsal import fence

MODULES = ("fake_workers", "fake_publish", "vl_consumers", "scale")
"""Installed in order after the SDK seam; each exposes install(manifest, box)."""
UPSCALE = ("VISURENA_MASTER_UPSCALE", "lanczos")
_UNDO: list[Callable[[], None]] = []
_GEN = [0, False]
"""[install generation, live]: a patch still pending from an earlier install never lands."""


def on_import(module: str, patch: Callable[[Any], Callable[[], None] | None]) -> None:
    """patch(module) when `module` is imported (now, if it is); the undo it returns is kept."""
    gen = _GEN[0]

    def landed(mod) -> None:
        if _GEN[1] and _GEN[0] == gen:
            undo = patch(mod)
            if undo is not None:
                _UNDO.append(undo)
    fence.patch_on_import(module, landed)


def set_attr(obj, attr: str, value) -> Callable[[], None]:
    """obj.attr = value; the undo puts the old value back."""
    old = getattr(obj, attr)
    setattr(obj, attr, value)
    return lambda: setattr(obj, attr, old)


def rebind(module: str, attr: str, make: Callable[[Any], Any]) -> None:
    """module.attr = make(old value) when `module` is imported."""
    on_import(module, lambda mod: set_attr(mod, attr, make(getattr(mod, attr))))


def set_default(func, param: str, value) -> Callable[[], None]:
    """Rebind one parameter's default (bound by value at def time); the undo restores it."""
    kind = inspect.signature(func).parameters[param].kind
    if kind is inspect.Parameter.KEYWORD_ONLY:
        old = dict(func.__kwdefaults__)
        func.__kwdefaults__ = {**old, param: value}
        return lambda: setattr(func, "__kwdefaults__", old)
    names = [p.name for p in inspect.signature(func).parameters.values()
             if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
    old = func.__defaults__
    at = names.index(param) - (len(names) - len(old))
    func.__defaults__ = old[:at] + (value,) + old[at + 1:]
    return lambda: setattr(func, "__defaults__", old)


def log(box: Path, name: str, row: Mapping) -> None:
    """Append one row to <sandbox>/<name>.jsonl (the sandbox is never a real root)."""
    with open(Path(box) / f"{name}.jsonl", "a", encoding="utf-8") as out:
        out.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "pid": os.getpid(), **row}) + "\n")


def module(name: str):
    return importlib.import_module(f"studio.rehearsal.{name}")


def _upscale() -> None:
    key, value = UPSCALE
    old = os.environ.get(key)
    os.environ[key] = value
    _UNDO.append(lambda: os.environ.__setitem__(key, old) if old is not None else os.environ.pop(key, None))


def install(manifest: Mapping, box: Path | None = None) -> Path:
    """Every fake for this rehearsal process; returns the sandbox the fakes log into."""
    box = box or settings.sandbox()
    if box is None:
        raise RuntimeError("fakes.install needs a sandbox: VISURENA_LIBRARY names none in this process")
    box = Path(box)
    _GEN[0], _GEN[1] = _GEN[0] + 1, True
    on_import("studio.brain", lambda brain: module("fake_sdk").install_into(brain, manifest, box))
    for name in MODULES:
        module(name).install(manifest, box)
    _upscale()
    return box


def uninstall() -> None:
    """Undo every patch, newest first (tests only)."""
    _GEN[1] = False
    while _UNDO:
        _UNDO.pop()()
