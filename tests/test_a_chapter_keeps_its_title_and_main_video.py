"""Owner 2026-10-11: each chapter is TWO videos -- its title (the animated card)
and its main video (the chapter without the card).  The Short is main + title +
black, as it always was.  The book's long video is title FIRST, then main,
chapter after chapter.  Both pieces are cut out of the Short the channel
carries, so nothing is re-rendered and an existing book can be re-joined."""
from __future__ import annotations

from pathlib import Path

import pytest

from studio import book_compilation as bc


def test_the_main_video_is_the_short_up_to_its_title_card():
    assert bc.main_frames(master_frames=3125, card_frames=108, chip_frames=6) == 3011


def test_a_short_shorter_than_its_card_is_refused():
    with pytest.raises(ValueError):
        bc.main_frames(master_frames=100, card_frames=108, chip_frames=6)


def test_the_title_and_main_are_frame_ranges_of_the_short():
    assert bc.pieces(main=3011, card=108) == {"title": (3011, 3119), "main": (0, 3011)}


def test_a_piece_is_cut_by_frame_and_its_sound_by_the_same_seconds():
    argv = bc.cut_argv(Path("in.mp4"), (3011, 3119), Path("t.mp4"), fps=24)
    vf, af = argv[argv.index("-vf") + 1], argv[argv.index("-af") + 1]
    assert "trim=start_frame=3011:end_frame=3119" in vf and "setpts=PTS-STARTPTS" in vf
    assert "atrim=start=125.458333:end=129.958333" in af
    assert argv[-1] == "t.mp4"


def test_the_book_runs_title_then_main_for_every_chapter():
    chapters = [(Path("t1"), Path("m1")), (Path("t2"), Path("m2"))]
    assert bc.title_first(chapters) == [Path("t1"), Path("m1"), Path("t2"), Path("m2")]
