"""A look lives on its own story track (Jekyll ch10, C1_L §3 "story time is not
narrative order").

timeline.json splits Jekyll and Hyde into tracks: `main` ch1-9 and `flashback`
ch10 (Jekyll's confession, the years before ch1).  A chapter-keyed span runs to
the next span, so every ch10 shot got the latest main-track look (Jekyll deathly
sick).  Now each span is cut to the chapters of its own track: a flashback
chapter wears its own quoted looks, else the base; a main look resumes when the
main track does.
"""
from __future__ import annotations

import json

from scripts.refs import looks_table
from studio import look_timeline
from studio.continuity_spec import CharacterLooks, Look, Span, StoryTime
from tests.test_episode_writer import FakeModel

JEKYLL = {1: "main", **{c: "main" for c in range(2, 10)}, 10: "flashback"}


def span(look, chapter, scene=None, until=None):
    return Span(look=look, start=StoryTime(chapter=chapter, scene=scene),
                until=StoryTime(chapter=until) if until else None)


def card(*spans) -> CharacterLooks:
    looks = {s.look: Look(made_by="base" if i == 0 else "fresh") for i, s in enumerate(spans)}
    return CharacterLooks(base=spans[0].look, body="A man.", looks=looks, timeline=list(spans))


def test_a_main_look_does_not_run_into_the_flashback():
    looks = card(span("well", 1), span("sick", 5))
    clipped = looks.model_copy(update={"timeline": look_timeline.on_track(looks.timeline, JEKYLL)})
    assert [clipped.look_id_at(c) for c in (4, 5, 9, 10)] == ["well", "sick", "sick", "well"]


def test_a_flashback_look_stands_in_its_own_chapter():
    looks = card(span("own", 1), span("clothes", 9, 6), span("clothes_again", 10, 7))
    timeline = look_timeline.on_track(looks.timeline, JEKYLL)
    clipped = CharacterLooks.model_validate({**looks.model_dump(), "timeline": [s.model_dump() for s in timeline]})
    assert [clipped.look_id_at(10, 1), clipped.look_id_at(10, 7), clipped.look_id_at(9, 6)] == \
        ["own", "clothes_again", "clothes"]


def test_a_main_look_resumes_when_the_main_track_does():
    tracks = {1: "main", 2: "main", 3: "main", 4: "past", 5: "main"}
    timeline = look_timeline.on_track([span("young", 1), span("old", 2)], tracks)
    looks = CharacterLooks(base="young", body="A man.", looks={"young": Look(made_by="base"), "old": Look()},
                           timeline=timeline)
    assert [looks.look_id_at(c) for c in (1, 3, 4, 5)] == ["young", "old", "young", "old"]


def test_a_book_without_tracks_keeps_its_timeline():
    spans = [span("well", 1), span("sick", 5)]
    assert look_timeline.on_track(spans, {}) == spans


def test_tracks_are_read_from_the_books_timeline(tmp_path):
    (tmp_path / "analysis").mkdir()
    (tmp_path / "analysis" / "timeline.json").write_text(json.dumps({"tracks": {
        "main": {"chapters": [1, 2]}, "flashback": {"chapters": [3]}}}), encoding="utf-8")
    assert look_timeline.tracks_of(tmp_path) == {1: "main", 2: "main", 3: "flashback"}
    assert look_timeline.tracks_of(tmp_path / "nowhere") == {}


def test_the_look_table_writes_per_track_spans(tmp_path):
    (tmp_path / "analysis" / "characters").mkdir(parents=True)
    (tmp_path / "analysis" / "characters" / "jekyll.json").write_text(json.dumps(
        {"id": "jekyll", "profile": {"physical": "Iron-grey hair; clean-shaven."}}), encoding="utf-8")
    (tmp_path / "analysis" / "timeline.json").write_text(json.dumps({"tracks": {
        "main": {"chapters": list(range(1, 10))}, "flashback": {"chapters": [10]}}}), encoding="utf-8")
    (tmp_path / "analysis" / "chapters").mkdir()
    (tmp_path / "analysis" / "chapters" / "ch_05.json").write_text(json.dumps(
        {"text": "The doctor sat by the fire, looking deathly sick."}), encoding="utf-8")
    draft = {"looks": [{"look_id": "well", "start_chapter": 1, "top": "frock coat"},
                       {"look_id": "sick", "start_chapter": 5, "face": "pale", "quote": "deathly sick"}]}
    looks_table.build(tmp_path, ["jekyll"], _agent=FakeModel(draft))
    table = look_timeline.load(tmp_path).characters["jekyll"]
    assert table.look_id_at(9) == "sick" and table.look_id_at(10) == "well"
