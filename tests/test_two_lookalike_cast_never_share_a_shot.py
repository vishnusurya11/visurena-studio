"""G-ALIKE (owner 2026-10-28, ep05 deleted: "same characters duplicated multiple times ... they
are hard checks .. things like that can't be ignored").

Jekyll and Utterson share a shot in ep03 and ep05, and H3 drew Jekyll as a second Utterson (ep05
shots 3 and 15; ep03 shot 19). Their look rows agree on everything a face read sees -- a man,
grey hair, no facial hair -- and differ only in clothes (top hat / bowler, frock coat /
overcoat), which the video model swaps. LOOK's trait-card lookalike row saw it and was ADVISORY.

Two cast whose rows agree on figure, hair colour (grey and white are one notch) and facial hair
refuse any shot that stages both, at the plan, before a line is voiced. Replayed over Jekyll's 12
co-staged pairs it fires on that pair only."""
from __future__ import annotations

import json

from studio import cast_alike

UTTERSON = ("male", "grey", "none")
JEKYLL = ("male", "grey", "none")
GUEST = ("male", "dark", "beard")
LANYON = ("male", "white", "sideburns")
HOUSEKEEPER = ("female", "grey", "none")


def test_a_man_with_the_same_hair_and_face_is_alike():
    assert cast_alike.alike(UTTERSON, JEKYLL)


def test_grey_and_white_hair_are_one_notch():
    assert cast_alike.alike(("male", "grey", "none"), ("male", "white", "none"))


def test_hair_facial_hair_or_figure_tells_them_apart():
    assert not cast_alike.alike(UTTERSON, GUEST)
    assert not cast_alike.alike(UTTERSON, LANYON)
    assert not cast_alike.alike(UTTERSON, HOUSEKEEPER)


def test_an_unread_marker_never_refuses():
    assert not cast_alike.alike(("male", "", "none"), ("male", "", "none"))


def test_a_shot_staging_both_refuses_and_names_them():
    marks = {"gabriel_john_utterson": UTTERSON, "henry_jekyll": JEKYLL, "mr_guest": GUEST}
    shots = [{"index": 3, "faces": ["henry_jekyll", "gabriel_john_utterson"]},
             {"index": 19, "faces": ["gabriel_john_utterson", "mr_guest"]}]
    got = cast_alike.faults(shots, marks)
    assert len(got) == 1 and got[0].startswith("G-ALIKE shot 3:")
    assert "gabriel_john_utterson" in got[0] and "henry_jekyll" in got[0]


def test_the_marks_come_from_the_books_rows(tmp_path):
    (tmp_path / "refs").mkdir()
    (tmp_path / "refs" / "looks.json").write_text(json.dumps({"characters": {
        "utterson": {"base": "base", "looks": {"base": {"markers": {"hair_colour": "grey", "facial_hair": "none"}}}}}}))
    (tmp_path / "refs" / "refs.json").write_text(json.dumps({"refs": [{"entity_id": "utterson", "gender": "male"}]}))
    assert cast_alike.marks(tmp_path) == {"utterson": ("male", "grey", "none")}


def test_a_book_with_no_look_rows_has_no_marks(tmp_path):
    assert cast_alike.marks(tmp_path) == {}


def test_g_alike_is_a_tier_one_row_step_06_repeats():
    from studio import plan_tags
    assert "G-ALIKE" in plan_tags.BUILDER and "takes_r2v" in plan_tags.BUILDER["G-ALIKE"]
    lines = ["G-ALIKE      : 1", "    G-ALIKE shot 3: 'a' and 'b' read as one person"]
    assert plan_tags.builder_lines(lines) == lines


def test_step_06_refuses_the_same_pair(tmp_path, monkeypatch):
    import pytest
    from types import SimpleNamespace
    from scripts.episode import takes_r2v
    monkeypatch.setattr(cast_alike, "marks", lambda book: {"u": UTTERSON, "j": JEKYLL})
    episode = SimpleNamespace(shots=[SimpleNamespace(index=3, faces=["j", "u"])])
    with pytest.raises(SystemExit, match="G-ALIKE shot 3"):
        takes_r2v.refuse_alike(tmp_path, episode)
