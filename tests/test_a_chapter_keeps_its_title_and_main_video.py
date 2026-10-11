"""Owner 2026-10-11: each chapter is TWO videos -- its title (the animated card)
and its main video (the chapter without the card).  The Short is main + title +
black, as it always was.  The book's long video is title FIRST, then main,
chapter after chapter.  Both pieces are cut out of the Short the channel
carries, so nothing is re-rendered and an existing book can be re-joined."""
from __future__ import annotations

from pathlib import Path

import pytest

from studio import book_compilation as bc


def test_the_title_and_main_are_frame_ranges_of_the_short():
    assert bc.pieces(main=3011, card=108) == {"title": (3011, 3119), "main": (0, 3011)}


def test_a_piece_is_cut_by_frame_and_its_sound_by_the_same_seconds():
    argv = bc.cut_argv(Path("in.mp4"), (3011, 3119), Path("t.mp4"), fps=24, side=1536)
    vf, af = argv[argv.index("-vf") + 1], argv[argv.index("-af") + 1]
    assert "trim=start_frame=3011:end_frame=3119" in vf and "setpts=PTS-STARTPTS" in vf
    # every Short conformed to the book's square: Scarlet ep01 is 768x1344, ep02-08 768
    assert "scale=1536:1536:force_original_aspect_ratio=decrease,pad=1536:1536:-1:-1,setsar=1" in vf
    assert "atrim=start=125.458333:end=129.958333" in af
    assert argv[-1] == "t.mp4"


def test_the_card_starts_at_the_last_cut_before_the_black_tail():
    # Scarlet ep01 (an older card, 90 frames, ~2 s of black): cuts at 3866, 3940, 4036; black from 4126
    assert bc.card_start(cuts=[120, 3866, 3940, 4036], black_from=4126) == 4036


def test_a_short_with_no_cut_before_its_black_is_refused():
    with pytest.raises(ValueError):
        bc.card_start(cuts=[100], black_from=4126)


def test_a_time_is_a_frame_at_the_books_rate():
    assert bc.frame_at(168.166016, fps=24) == 4036


def test_the_book_runs_title_then_main_for_every_chapter():
    chapters = [(Path("t1"), Path("m1")), (Path("t2"), Path("m2"))]
    assert bc.title_first(chapters) == [Path("t1"), Path("m1"), Path("t2"), Path("m2")]
