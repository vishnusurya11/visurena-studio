"""Cutting the page: every beat for its written seconds, in written order.

ffmpeg is faked at its three seams -- extract, title_card, concat -- so what
is tested is the CUT's decisions, not the encoder.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from studio import script_cut
from studio.trailer_assemble import HEAD_TRIM
from studio.trailer_script import ScriptBeat, TrailerScript


def a_page(**kw) -> TrailerScript:
    beats = ([ScriptBeat(id=f"B{i:02d}", movement="M1", function="question", seconds=3.0,
                         see="blood on plaster", why="the crime") for i in range(5)]
             + [ScriptBeat(id=f"B{10 + i:02d}", movement="M2", function="escalation",
                           seconds=3.0, see="fog", why="the hunt") for i in range(9)]
             + [ScriptBeat(id=f"B{30 + i:02d}", movement="M3", function="escalation",
                           seconds=3.0, see="the arrest", why="the answer") for i in range(4)]
             + [ScriptBeat(id="B40", movement="M3", function="title", seconds=3.0,
                           card="A STUDY IN SCARLET", why="the logo"),
                ScriptBeat(id="B41", movement="M3", function="button", seconds=3.0,
                           card="EPISODE 1 OUT NOW", why="the next action")])
    fields = {"title": "A Study in Scarlet", "runtime": 60.0, "beats": beats}
    fields.update(kw)
    return TrailerScript(**fields)


@pytest.fixture()
def rendered(tmp_path):
    """A take on disk for every beat that needs one."""
    clips = tmp_path / "clips"
    clips.mkdir()
    for beat in a_page().beats:
        if not beat.card:
            (clips / f"{beat.id}.mp4").write_bytes(b"take")
    return clips


@pytest.fixture()
def fake_ffmpeg(monkeypatch):
    cuts, cards, joined = [], [], []
    monkeypatch.setattr(script_cut, "extract",
                        lambda video, start, seconds, out, w, h, fps, grade="":
                        cuts.append((video.name, start, seconds, w, h, grade)) or out)
    monkeypatch.setattr(script_cut, "title_card",
                        lambda text, out, seconds, w, h, fps, font=None:
                        cards.append((text, seconds)) or out)
    monkeypatch.setattr(script_cut, "concat",
                        lambda pieces, out: joined.append([p.name for p in pieces]) or out)
    return cuts, cards, joined


def test_every_beat_becomes_one_piece_of_picture_in_page_order(tmp_path, rendered, fake_ffmpeg):
    cuts, cards, joined = fake_ffmpeg
    page = a_page()
    script_cut.cut(page, rendered, tmp_path / "work", tmp_path / "picture.mp4")
    assert joined[0] == [f"{b.id}.mp4" for b in page.beats]
    assert len(cuts) == 18 and len(cards) == 2


def test_a_beat_is_cut_past_the_reference_leak_for_exactly_its_seconds(
        tmp_path, rendered, fake_ffmpeg):
    """The take renders longer than the beat plays; the cut starts after the
    leak the reference image bleeds into the first frames."""
    cuts, _, _ = fake_ffmpeg
    script_cut.cut(a_page(), rendered, tmp_path / "work", tmp_path / "picture.mp4")
    name, start, seconds, w, h, _ = cuts[0]
    assert name == "B00.mp4" and start == HEAD_TRIM and seconds == 3.0
    assert (w, h) == (768, 1344)


def test_a_beat_with_a_picture_AND_a_card_keeps_the_picture(tmp_path, rendered, fake_ffmpeg):
    """MEASURED on the first real cut: B01 is the body on the floor with the
    book's title over it -- the page names the title inside the first seven
    seconds.  Drawn as a card it became black with text, and the opening image,
    the one thing that decides whether a viewer stays, was thrown away."""
    cuts, cards, _ = fake_ffmpeg
    page = a_page()
    over = page.beats[0].model_copy(update={"card": "A STUDY IN SCARLET"})
    script_cut.cut(a_page(beats=[over] + page.beats[1:]), rendered,
                   tmp_path / "work", tmp_path / "picture.mp4")
    assert cards == [("A STUDY IN SCARLET", 3.0), ("EPISODE 1 OUT NOW", 3.0)]  # the card-only beats
    assert cuts[0][0] == "B00.mp4"                      # B00 was FILMED, not drawn
    assert "drawtext" in cuts[0][5]                     # with its title over it


def test_a_card_beat_is_drawn_not_filmed(tmp_path, rendered, fake_ffmpeg):
    _, cards, _ = fake_ffmpeg
    script_cut.cut(a_page(), rendered, tmp_path / "work", tmp_path / "picture.mp4")
    assert cards == [("A STUDY IN SCARLET", 3.0), ("EPISODE 1 OUT NOW", 3.0)]


def test_a_beat_with_no_take_stops_the_cut_and_names_it(tmp_path, rendered, fake_ffmpeg):
    """Better to say which beat is missing than to ship a trailer short of it."""
    (rendered / "B11.mp4").unlink()
    with pytest.raises(FileNotFoundError, match="B11"):
        script_cut.cut(a_page(), rendered, tmp_path / "work", tmp_path / "picture.mp4")
