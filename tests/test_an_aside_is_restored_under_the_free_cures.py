"""ep21 (2026-10-08 05:49Z): the ladder deferred on a 17-word style line; on
the relaunch, plan_repair --from-aside validated the RAW aside before any cure
and refused, so the one-line cure never ran and the climb started over from
nothing.  The restore runs the free pre-contract cures first."""
from __future__ import annotations

import importlib

from studio import house_style


def test_a_restored_aside_has_its_style_line_trimmed_and_its_button_beat():
    pr = importlib.import_module("scripts.episode.plan_repair")
    doc = {"where": "a ruined villa in Mortlake", "light": "grey daylight through the kitchen doorway, dust in the air, deep shadow",
           "shots": [], "lines": []}
    out = pr.restored(dict(doc))
    assert not house_style.style_faults(out["where"], out["light"])


def test_a_cure_that_raises_never_breaks_the_restore(monkeypatch):
    pr = importlib.import_module("scripts.episode.plan_repair")

    def boom(doc):
        raise RuntimeError("x")
    monkeypatch.setattr(pr.pc, "button_beat", boom)
    assert pr.restored({"where": "Woking", "light": "noon sun", "shots": [], "lines": []})["where"] == "Woking"
