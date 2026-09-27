"""A claim the shot's own verified span backs is not invented (ep13, 2026-09-26).

The critic takes the UNION of its readings, so one flaky reading invents a
fault: the same ep13 plan passed, then failed on 'Horsell Common' because the
reader quoted the narration line instead of the chapter -- while the shot's own
`source` span (checked against the chapter by G-SOURCE) says "upon Horsell
Common".  A claim whose head noun stands in one of its shot's verified spans is
backed; a claim nothing on the shot supports is still invented."""
from __future__ import annotations

from types import SimpleNamespace as NS

from studio.judges import plan as pj

CHAPTER = "the Martians retreated to their original position upon Horsell Common; I lay down in the shadow of a hedge."


def reading(*claims):
    return NS(claims=list(claims))


def test_a_misquoted_claim_the_shot_span_backs_is_not_invented():
    claim = pj.Claim(shot=1, kind="place", claim="Horsell Common", span="they fell back to Horsell Common")
    spans = {1: ["the Martians retreated to their original position upon Horsell Common"]}
    assert pj.invented([reading(claim)], CHAPTER, {1}, spans) == {}


def test_a_claim_nothing_on_the_shot_backs_is_still_invented():
    claim = pj.Claim(shot=5, kind="prop", claim="floating reed", span="")
    spans = {5: ["I contrived to paddle, as well as my parboiled hands would allow"]}
    assert (5, "floating reed") in pj.invented([reading(claim)], CHAPTER, {5}, spans)


def test_the_head_noun_decides():
    assert pj.backed(pj.Claim(shot=10, kind="place", claim="hawthorn hedge"), ["in the shadow of a hedge"])
    assert not pj.backed(pj.Claim(shot=10, kind="place", claim="stone wall"), ["in the shadow of a hedge"])
