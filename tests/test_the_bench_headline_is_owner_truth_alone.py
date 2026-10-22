"""The bench's headline is owner truth alone (fleet H ruling A2, A5, A13).

- A2: the false-refusal interval is built on the raw count of refused pass
  rows; the weighted share (owner 1 / agent 0.75 / default 0.5) is printed
  beside it, never rounded back into a fake count.
- A5: headline recall and false refusals come from owner rows only.  Agent,
  default and synthetic rows are the ladder agreeing with itself: they go to
  an "internal consistency" table, and adding them leaves the headline alone.
  A panel of a redrawn storyboard that no check of its own refused is no
  fault row.
- A13: a refusal counts once per (artefact, rule): two rows on one take, or
  three landmark words on one take, are one refusal and one retake.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.calibration import harvest_labels as hl  # noqa: E402
from studio import judge_bench as jb  # noqa: E402
from studio.casebook import Row  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures" / "judge_bench"


def take(path, verdict="pass", by="default", cls=None):
    return Row(codex="c", unit="ep01", kind="take", path=path, verdict=verdict, fault_class=cls, verdict_by=by)


def refuses(row):
    return {"refused": True, "classes": ["over_push"], "values": {}}


def test_the_false_refusal_interval_counts_rows_not_weights():
    rows = [take("a.mp4", by="owner"), take("b.mp4"), take("c.mp4"), take("d.mp4", by="agent")]
    picky = jb.run(rows, lambda r: {"refused": r.path in ("b.mp4", "c.mp4"), "classes": [], "values": {}})
    fr = jb.false_refusals(picky)
    assert (fr.k, fr.n) == (2, 4) and fr.point == 0.5
    assert fr.weighted == round(1.0 / 2.75, 4)
    assert (fr.low, fr.high) == jb.wilson(2, 4)


def test_adding_agent_and_default_rows_leaves_the_owner_headline_unchanged():
    owner = [r for r in jb.load_rows(FIXTURES, "take") if r.verdict_by == "owner"]
    alone = jb.headline(jb.run(owner, refuses))
    crowded = jb.headline(jb.run(jb.load_rows(FIXTURES, "take") + [take("z.mp4", by="agent")], refuses))
    assert alone == crowded
    assert alone["false_refusals"]["n"] == 1 and alone["recall"]["n"] == 2


def test_the_report_puts_the_ladder_in_its_own_table():
    text = jb.report(jb.run(jb.load_rows(FIXTURES, "take"), refuses), "fixture", "abcdef01")
    head, tail = text.split("internal consistency", 1)
    assert "false refusals on owner rows" in head and "recall on all rows" in tail
    assert "weighted share" in tail


def test_a_refusal_counts_once_per_artefact_and_rule():
    twice = [take("T01.mp4", by="owner"), take("T01.mp4", by="agent"), take("T02.mp4")]
    outcomes = jb.run(twice, lambda r: {"refused": True, "classes": ["landform", "landform", "landform"], "values": {}})
    assert jb.distinct_refusals(outcomes) == {("c", "T01.mp4", "landform"), ("c", "T02.mp4", "landform")}
    assert jb.gpu_minutes(outcomes) == 2 * jb.GPU_MINUTES_PER_REFUSAL
    assert jb.flag_rate(outcomes)["per_unit"] == {"c/ep01": 2}


def test_a_redrawn_storyboards_panel_that_nothing_refused_is_no_fault_row():
    dq = [{"shot": 0, "flags": [], "sharp": 1.0}, {"shot": 1, "flags": ["clone"], "sharp": 1.0}]
    content = [{"shot": 0, "passed": True, "faults": []}, {"shot": 1, "passed": True, "faults": []}]
    rows = hl.panel_rows("c", "ep01", dq, content, {}, "src", "v1", "storyboard_prev_v1", refused=True)
    assert [r.path for r in rows] == ["episodes/ep01/storyboard_prev_v1/shot_01.png"]
    assert rows[0].verdict == "fault" and rows[0].verdict_by == "agent"
    kept = hl.panel_rows("c", "ep01", dq, content, {}, "src", "v1")
    assert len(kept) == 2 and {r.verdict for r in kept} == {"pass"}
