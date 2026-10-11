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


def test_the_card_starts_at_the_biggest_change_before_the_black_tail():
    # MEASURED: Scarlet ep01's older 90-frame card (4036: 0.42, an earlier cut 3940: 0.39);
    # WotW ep01's dark picture into the dark card scored only 0.24 -- under any fixed threshold
    assert bc.card_start(scores={3940: 0.39, 3959: 0.01, 4036: 0.42}, black_from=4126, card_frames=107) == 4036
    assert bc.card_start(scores={3664: 0.08, 3711: 0.24, 502: 0.75}, black_from=3818, card_frames=107) == 3711


def test_a_short_with_no_change_before_its_black_is_refused():
    with pytest.raises(ValueError):
        bc.card_start(scores={100: 0.9, 4100: 0.02}, black_from=4126, card_frames=107)


def test_a_time_is_a_frame_at_the_books_rate():
    assert bc.frame_at(168.166016, fps=24) == 4036


def test_the_book_runs_title_then_main_for_every_chapter():
    chapters = [(Path("t1"), Path("m1")), (Path("t2"), Path("m2"))]
    assert bc.title_first(chapters) == [Path("t1"), Path("m1"), Path("t2"), Path("m2")]


def test_every_piece_is_tagged_bt709_so_the_main_title_joins_it():
    argv = bc.cut_argv(Path("in.mp4"), (0, 10), Path("t.mp4"), fps=24, side=1536)
    for flag, value in (("-color_primaries", "bt709"), ("-color_trc", "iec61966-2-1"), ("-colorspace", "bt709")):
        assert argv[argv.index(flag) + 1] == value


def test_the_card_starts_at_the_change_nearest_where_its_length_puts_it():
    """WotW ep06/10/20 and Scarlet ep12 shipped with seconds of picture inside the
    'title': a hard cut in the picture outscored the cut into the card."""
    scores = {3892: 0.55, 3958: 0.21, 4001: 0.02}                      # Scarlet ep12: picture cut, then the card
    assert bc.card_start(scores=scores, black_from=4065, card_frames=107) == 3958
    # no change near where today's card would start: an older card (Scarlet ep01) -> the biggest
    assert bc.card_start(scores={3940: 0.39, 4036: 0.42}, black_from=4126, card_frames=107) == 4036
