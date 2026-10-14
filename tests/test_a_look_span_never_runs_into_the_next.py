"""A drafted look span that runs into the next one is opened, never a refusal.

Jekyll's look table rebuild (2026-10-13): the look writer closed Lanyon's base
look at chapter 6 while his fallen look starts at chapter 6 scene 3, and the table
refused the whole book ("spans 'ruddy_dapper' and 'pale_aged' overlap").  An open
span already runs until the next one starts, so a closed span that reaches its
successor is opened; spans that start together still refuse.
"""
from __future__ import annotations

from studio import look_timeline
from studio.continuity_spec import Span, StoryTime, overlaps


def span(look, start, until=None, scene=None):
    return Span(look=look, start=StoryTime(chapter=start, scene=scene),
                until=StoryTime(chapter=until) if until else None)


def test_a_closed_span_that_runs_into_the_next_is_opened():
    spans = look_timeline.unrun([span("ruddy", 2, 6), span("pale", 6, scene=3)])
    assert spans[0].until is None and overlaps(spans) == ""


def test_a_span_closed_before_the_next_is_kept():
    spans = look_timeline.unrun([span("ruddy", 2, 5), span("pale", 6)])
    assert spans[0].until == StoryTime(chapter=5)


def test_the_order_is_story_time():
    spans = look_timeline.unrun([span("pale", 6), span("ruddy", 2, 9)])
    assert [s.look for s in spans] == ["ruddy", "pale"] and spans[0].until is None
