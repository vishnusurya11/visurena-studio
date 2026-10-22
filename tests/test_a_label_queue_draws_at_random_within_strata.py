"""The owner's label queue is a seeded random draw within strata (fleet H ruling A17, skeptic F2).

Strata, from the casebook's harvested rows of SHIPPED artefacts only:
- `R:<gate>`: shipped takes a HARD gate refused (a hard row not ok); a soft
  deduction is no refusal and makes no stratum;
- `R-panel:<flag>`: shipped panels a panel check refused;
- `P` / `P-panel`: shipped takes / panels nothing refused -- the only view of misses.

Each stratum is drawn at random with its own seeded stream, then the draw is
de-duplicated per artefact: a take two gates refused is one item that names
both strata, and its `p_select` is its true inclusion probability across every
stratum it belongs to, 1 - prod(1 - n_h / N_h).  The P share is held at 20 %
or more -- a convention, printed as one.  The same seed gives the same queue.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.calibration import label_queue as lq  # noqa: E402
from studio.casebook import Row  # noqa: E402


def gate(name, ok, hard=True):
    return {"name": name, "value": 1.0, "ok": ok, "hard": hard, "note": "", "penalty": 0.0}


def take(i, gates, by="default", folder=""):
    return Row(codex="c", unit=f"ep{i % 4:02d}", kind="take", path=f"episodes/ep{i % 4:02d}/takes/r2v/{folder}T{i:02d}.mp4",
               sha8=f"{i:08d}", verdict="pass", verdict_by=by, machine={"take_dq": {"gates": gates}})


def panel(i, flags):
    return Row(codex="c", unit="ep01", kind="panel", path=f"episodes/ep01/storyboard/shot_{i:02d}.png", verdict="pass",
               verdict_by="default", machine={"panel_dq": {"shot": i, "flags": flags}, "panel_content": {"passed": True}})


def rows():
    out = [take(i, [gate("warp", False)]) for i in range(0, 6)]
    out += [take(i, [gate("warp", False), gate("frozen-whole", False)]) for i in range(6, 9)]
    out += [take(i, [gate("zoom", False, hard=False)]) for i in range(9, 30)]
    out += [take(99, [gate("warp", False)], by="agent", folder="attempts/")]
    return out + [panel(i, ["clone"] if i < 3 else []) for i in range(10)]


def test_strata_come_from_hard_refusals_of_shipped_artefacts():
    strata = lq.strata(rows())
    assert set(strata) == {"R:warp", "R:frozen-whole", "P", "R-panel:clone", "P-panel"}
    assert len(strata["R:warp"]) == 9 and len(strata["R:frozen-whole"]) == 3 and len(strata["P"]) == 21
    assert not any("attempts/" in key[1] for members in strata.values() for key in members)


def test_a_take_two_gates_refused_is_one_item_with_its_true_inclusion_probability():
    queue = lq.build(rows(), seed=7, per_gate=3, p_size=10, panel_size=4)
    keys = [(q["codex"], q["path"]) for q in queue]
    assert len(keys) == len(set(keys))
    both = [q for q in queue if set(q["strata"]) == {"R:warp", "R:frozen-whole"}]
    for q in both:
        assert q["p_select"] == pytest.approx(1 - (1 - 3 / 9) * (1 - 3 / 3))
    assert all(0.0 < q["p_select"] <= 1.0 for q in queue)


def test_the_random_share_is_held_at_a_fifth_or_more():
    queue = lq.build(rows(), seed=7, per_gate=3, p_size=1, panel_size=0)
    share = sum("P" in q["strata"] for q in queue) / len(queue)
    assert share >= lq.RANDOM_FLOOR == 0.20


def test_the_same_seed_gives_the_same_queue():
    assert lq.build(rows(), seed=3) == lq.build(rows(), seed=3)
    assert lq.build(rows(), seed=3) != lq.build(rows(), seed=4)


def test_the_summary_prints_each_stratum_and_the_conventions():
    text = lq.summary(lq.build(rows(), seed=7, per_gate=3, p_size=10, panel_size=4), lq.strata(rows()))
    assert "R:warp: drew 3 of 9" in text and "convention" in text
