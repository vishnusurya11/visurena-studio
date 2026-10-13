"""A cut between two spoken lines breathes (Jekyll ep01 review, 2026-10-13).

SOUND.md R3: the Jekyll narration had a median gap between lines of 0.52 s
against WotW's 1.03 -- 13.4 s of gaps in all against 24-26.  The commonest gap
was a cut with no hold: two HANDLEs, 0.50 s, between one shot's last line and
the next shot's first.  WotW reached 1.03 the same way it reached its pauses:
holds the PLAN wrote.  So the floor lives in the plan, where a breath costs a
line and never the 174 s wall (a timeline-level pad pushed the owner-shipped
Scarlet ep10 to 178 s and its plan stopped loading):

- G-PACE counts the voiced->voiced cuts whose holds leave the next line under
  LINE_GAP_S, and faults a plan where more than a quarter of them do;
- its cure (`breathe`) gives those shots a beat first, then the pause floor,
  then cuts a line if the breaths push the plan over budget."""
from __future__ import annotations

from studio import plan_cures as pc
from studio import plan_gates as pg
from studio.episode_spec import HANDLE
from tests.test_hole_gate_measures_like_step05 import RATE, episode_with_wordless_run


def test_the_floor_is_point_nine_and_a_cut_needs_point_four_of_hold():
    assert pg.LINE_GAP_S == 0.9
    assert round(pg.CUT_HOLD_S, 6) == round(pg.LINE_GAP_S - 2 * HANDLE, 6) == 0.4


def test_a_voiced_cut_with_no_hold_is_breathless():
    ep = episode_with_wordless_run()
    cuts = pg.breathless_cuts(ep)
    assert ep.shots[0].index in cuts and ep.shots[1].index in cuts


def test_a_cut_into_a_wordless_shot_or_after_a_hold_is_not():
    ep = episode_with_wordless_run()
    cuts = set(pg.breathless_cuts(ep))
    held = ep.shots[-3]
    assert held.beat_s == 1.5 and held.index not in cuts
    for s, n in zip(ep.cut_shots(), ep.cut_shots()[1:]):
        if not ep.lines_of(n.index):
            assert s.index not in cuts


def test_the_same_count_reads_a_plan_dict():
    ep = episode_with_wordless_run()
    assert pg.breathless_cuts(ep.model_dump()) == pg.breathless_cuts(ep)


def test_g_pace_faults_a_plan_that_never_breathes_at_a_cut():
    rows = [r for r in pg.pace_faults(episode_with_wordless_run()) if "cuts where" in r]
    assert len(rows) == 1 and "G-PACE plan" in rows[0]


def test_the_cure_table_sends_it_to_breathe():
    row = next(r for r in pg.pace_faults(episode_with_wordless_run()) if "cuts where" in r)
    assert pc.cure_for(row) == "breathe"


def test_breathe_gives_the_breathless_cuts_their_hold():
    doc = episode_with_wordless_run().model_dump()
    before = len(pg.breathless_cuts(doc))
    doc = pc.breathe_cuts(doc, RATE)
    assert len(pg.breathless_cuts(doc)) < before
    for s in doc["shots"]:
        assert float(s.get("beat_s") or 0) <= pc.MAX_BEAT_S
