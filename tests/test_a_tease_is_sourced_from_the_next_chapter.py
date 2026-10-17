"""A tease shot shows the NEXT chapter's first image (anime-TV grammar, 2026-10-17),
so its spans are found in the next chapter, never this one -- G-SOURCE judges a
tease against the next chapter's text, and stands down (never a pass of this
chapter) when there is none.  G-ORDER and G-COVER already skip a span this
chapter does not hold.  $0."""
from __future__ import annotations

from types import SimpleNamespace

from studio import plan_gates

THIS = "The lawyer shook hands on that, and walked on."
NEXT = "From that time forward, Mr. Utterson began to haunt the door in the by-street of shops."


def _ep(section: str):
    shot = SimpleNamespace(index=0, section=section, setup="door", source=["Mr. Utterson began to haunt the door"],
                           extras=0, frame="", motion="", at_rest="", end="", cuts=[])
    return SimpleNamespace(shots=[shot], setups={"door": SimpleNamespace(props=[])})


def test_a_tease_span_is_found_in_the_next_chapter():
    assert plan_gates.source_faults(_ep("tease"), THIS, after=NEXT) == []
    assert plan_gates.source_faults(_ep("runout"), THIS, after=NEXT)


def test_a_tease_with_no_next_chapter_is_not_judged_against_this_one():
    assert plan_gates.source_faults(_ep("tease"), THIS) == []
