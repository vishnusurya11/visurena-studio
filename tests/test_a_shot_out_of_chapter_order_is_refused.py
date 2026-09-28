"""G-ORDER: the shots follow the chapter.

ep13 (2026-09-27): the curate's "What does it mean?" (paragraph 14) was patched
in front of the Martians' retreat (paragraph 1) to pass G-STORY's
first-dialogue wall; no gate read chapter order, and the owner asked why the
curate opens the episode.  A shot whose span sits more than ORDER_SLACK
paragraphs before the previous shot's is refused; an omitted shot is not in
the cut and is not read.
"""
from types import SimpleNamespace as S

from studio import plan_gates as pg

PARAS = [f"paragraph number {i} with its own words alpha{i} beta{i} gamma{i} delta{i}" for i in range(1, 21)]


def shot(i, para, setup="a"):
    return S(index=i, setup=setup, source=[f"alpha{para} beta{para} gamma{para} delta{para}"])


def test_a_flash_forward_is_refused():
    ep = S(shots=[shot(0, 14, "hedge"), shot(1, 1, "pit"), shot(2, 3, "pit")], omit=[])
    got = pg.order_faults(ep, PARAS)
    assert len(got) == 1 and "G-ORDER shot 1" in got[0]


def test_chapter_order_passes_with_a_small_step_back():
    ep = S(shots=[shot(0, 1), shot(1, 4), shot(2, 3), shot(3, 9)], omit=[])
    assert pg.order_faults(ep, PARAS) == []


def test_an_omitted_shot_is_not_read():
    ep = S(shots=[shot(0, 14, "hedge"), shot(1, 1, "pit"), shot(2, 3, "pit")], omit=[0])
    assert pg.order_faults(ep, PARAS) == []


def test_a_reorder_inside_one_scene_is_the_editor_s_choice():
    """ep13 shots 15-16: "What are we?" (paragraph 29) before the curate's lost
    church (21), both at the hedge -- a conversation's order, not a flash-forward."""
    ep = S(shots=[shot(0, 20, "hedge"), shot(1, 29, "hedge"), shot(2, 21, "hedge")], omit=[])
    assert pg.order_faults(ep, PARAS) == []
