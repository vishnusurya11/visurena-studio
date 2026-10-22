"""The grid negative is dead text, so the graph sends none and the lint warns on every negation (craft ruling A20).

`grids.graph_for` samples at cfg 1.0, and ComfyUI skips the unconditioned pass at cfg 1.0
(comfy/samplers.py, the cfg-1 optimisation), so the long NEGATIVE never reached Qwen: the SKILL's "the grid
negative ... read[s] it" was false.  A graph at cfg 1.0 now carries negative_prompt "" so nobody tunes a dead
string again, and `grid_lint.warnings` names each no / not / never / without the drawer reads as a noun
(outside the fixed UNWRITTEN sentence).  A warning, never a refusal: rewording the guards is bench T21-c.
Fixture: ep01 s09's prompt as the production builder writes it today (its two binding negations)."""
from __future__ import annotations

from scripts.episode import grids
from studio import grid_lint
from studio.storyboard_grid import UNWRITTEN

S09_BINDING = ("The people in <image1> and <image2> are never dressed alike.\n\n" + UNWRITTEN + "\n\n"
               "One full-frame illustration, edge to edge, with no lettering anywhere.")


def graph(monkeypatch, **kw) -> dict:
    template = {k: {"inputs": {}} for k in ("3", "5", "6", "7", "9")}
    monkeypatch.setattr(grids, "load_workflow", lambda name: (template, None))
    monkeypatch.setattr(grids, "stage_only", lambda graph, slots: None)
    return grids.graph_for("p", {}, 1, 1, 7, "g", **kw)


def test_a_cfg_one_graph_carries_no_negative(monkeypatch):
    said = graph(monkeypatch, negative="text, watermark")
    assert said["7"]["inputs"]["cfg"] == 1.0
    assert said["5"]["inputs"]["negative_prompt"] == ""


def test_the_house_negative_is_not_sent_either(monkeypatch):
    assert graph(monkeypatch)["5"]["inputs"]["negative_prompt"] == ""


def test_neg_warns_on_each_negation_outside_unwritten():
    warned = [w for w in grid_lint.warnings(S09_BINDING) if w.startswith("NEG")]
    assert len(warned) == 1 and "2 negations" in warned[0]
    assert "never dressed alike" in warned[0] and "no lettering" in warned[0]


def test_the_unwritten_sentence_alone_warns_nothing():
    assert grid_lint.warnings(UNWRITTEN) == []


def test_a_warning_never_refuses():
    assert grid_lint.faults(S09_BINDING) == []
