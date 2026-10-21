"""The time-constant scale for hang and cap scenarios (2026-10-21_ep02_proof 2.7).

Under manifest.scale = k (a rehearsal's only), the printed list below is divided by k: each
constant in its defining module, in every module that imported it BY VALUE, in every default
argument bound to it at def time, and every wall of the step_caps table (stages.yaml caps).
tests/test_proof_scale_covers_every_importer.py greps studio/ and scripts/episode/ and fails on a
by-value use missing here.  What a scaled run proves is that a mechanism fires at its cap, never
the cap's value and never a time (section 5 refuses a scaled clock as time evidence).

A module run as a script (`python scripts/episode/drive.py`) is `__main__`, never imported by
name, so its own constants (drive.POLL_S) keep their value there; drive's silence wall is
episode_drive.SILENCE_S, read by attribute, and is scaled."""
from __future__ import annotations

import dataclasses
import importlib
from typing import Mapping

from studio.rehearsal import fakes

CONSTANTS: dict[str, tuple[str, ...]] = {
    "studio.comfy": ("RESTART_SECONDS", "STUCK_SECONDS", "QUEUE_SECONDS"),
    "studio.episode_drive": ("SILENCE_S",),
    "scripts.episode.drive": ("POLL_S",),
    "scripts.episode.autopilot": ("HUNG_S", "DEAD_BEAT_S", "LIVENESS_QUIET_S"),
    "studio.run_budget": ("EPISODE_CEILING_SECONDS", "OWNER_LIMIT_SECONDS"),
}
"""Defining module -> its scaled constants."""
IMPORTERS: dict[str, tuple[str, ...]] = {
    "studio.command_center.progress_view": ("EPISODE_CEILING_SECONDS", "OWNER_LIMIT_SECONDS"),
    "studio.episode_capacity": ("EPISODE_CEILING_SECONDS", "OWNER_LIMIT_SECONDS"),
    "studio.episode_run": ("EPISODE_CEILING_SECONDS", "OWNER_LIMIT_SECONDS"),
    "studio.repair_clock": ("EPISODE_CEILING_SECONDS", "OWNER_LIMIT_SECONDS"),
    "scripts.episode.step_09_shoot": ("EPISODE_CEILING_SECONDS",),
}
"""Module -> the constants it imported by value (`from studio.run_budget import ...`)."""
DEFAULTS: dict[str, dict[str, tuple[str, ...]]] = {
    "studio.comfy": {"stuck": ("patience",)},
    "studio.episode_run": {"EpisodeContext.__init__": ("ceiling",)},
    "studio.repair_clock": {"cap_for": ("ceiling",)},
}
"""Module -> function qualname -> its parameters whose default is a scaled constant."""
CAPTURES: dict[str, dict[str, tuple[str, str]]] = {
    "studio.plan_ladder": {"CLIMB_WALL_S": ("wall_s", "plan")},
}
"""Module -> module-level name computed at import -> the step_caps read that made it, re-read
from the scaled table (never divided, so an import after the patch is not scaled twice)."""


def home_of(name: str) -> str:
    return next(mod for mod, names in CONSTANTS.items() if name in names)


def original(name: str):
    """The constant's scaled value read from its home (it is divided there first)."""
    return getattr(importlib.import_module(home_of(name)), name)


def divide(mod, names: tuple[str, ...], k: float):
    undo = [fakes.set_attr(mod, n, getattr(mod, n) / k) for n in names]
    return lambda: [u() for u in reversed(undo)]


def follow(mod, names: tuple[str, ...], k: float):
    """An importer's copies set to the home's scaled values (never divided twice)."""
    undo = [fakes.set_attr(mod, n, original(n)) for n in names]
    return lambda: [u() for u in reversed(undo)]


def attr_path(mod, qualname: str):
    obj = mod
    for part in qualname.split("."):
        obj = getattr(obj, part)
    return obj


def defaults(mod, table: Mapping[str, tuple[str, ...]], home: str, k: float):
    """Each listed default set to the scaled value of the constant of the same module's import."""
    undo = []
    for qualname, params in table.items():
        func = attr_path(mod, qualname)
        for param in params:
            name = DEFAULT_OF[(home, qualname, param)]
            undo.append(fakes.set_default(func, param, original(name)))
    return lambda: [u() for u in reversed(undo)]


DEFAULT_OF = {("studio.comfy", "stuck", "patience"): "STUCK_SECONDS",
              ("studio.episode_run", "EpisodeContext.__init__", "ceiling"): "EPISODE_CEILING_SECONDS",
              ("studio.repair_clock", "cap_for", "ceiling"): "EPISODE_CEILING_SECONDS"}
"""(module, function, parameter) -> the constant its default is."""


def scaled_cap(make, k: float):
    """step_caps._cap whose wall is divided by k (every table, wall_s and step_wall_s read)."""
    def cap(name: str, row: dict):
        made = make(name, row)
        return dataclasses.replace(made, wall_s=made.wall_s / k)
    return cap


def recompute(mod, names: Mapping[str, tuple[str, str]]):
    """Each captured name set to its step_caps read again, now off the scaled table."""
    from studio import step_caps
    undo = [fakes.set_attr(mod, n, getattr(step_caps, read)(arg)) for n, (read, arg) in names.items()]
    return lambda: [u() for u in reversed(undo)]


def listing(k: float) -> list[str]:
    """The printed list: every scaled constant, its value and its scaled value."""
    out = []
    for home, names in CONSTANTS.items():
        try:
            mod = importlib.import_module(home)
        except Exception as why:                         # noqa: BLE001 -- a listing never fails a run
            out.append(f"{home}: not importable ({why})")
            continue
        out += [f"{home}.{n} {getattr(mod, n)} -> {getattr(mod, n) / k}" for n in names]
    return out + [f"studio.step_caps every wall_s / {k:g}"]


def install(manifest: Mapping, box) -> None:
    k = float(manifest.get("scale") or 1)
    if k == 1:
        return
    fakes.rebind("studio.step_caps", "_cap", lambda make: scaled_cap(make, k))
    for home, names in CONSTANTS.items():
        fakes.on_import(home, lambda mod, names=names: divide(mod, names, k))
    for mod_name, names in IMPORTERS.items():
        fakes.on_import(mod_name, lambda mod, names=names: follow(mod, names, k))
    for mod_name, table in DEFAULTS.items():
        fakes.on_import(mod_name, lambda mod, table=table, home=mod_name: defaults(mod, table, home, k))
    for mod_name, names in CAPTURES.items():
        fakes.on_import(mod_name, lambda mod, names=names: recompute(mod, names))
