"""A silent gap names the shot that owns it, not only its length.

MEASURED 2026-09-22 on ep08: QC reported "longest gap 6.81s (wall 6.0)" and
nothing else. The obvious lever was the shots on either side of it, so their
codas were trimmed; the number came down and shot 16 froze, twice. The gap
belonged to shot 17, the episode's one silent shot, lying inside it and
contributing its whole length by definition. Nobody was asked which shot the
gap was made of, so nobody answered.
"""
from studio.gap_owner import owner, shots_in


def shot(index, at, seconds):
    return {"index": index, "at": at, "seconds": seconds}


SHOTS = [shot(0, 0.0, 5.0), shot(1, 5.0, 4.0), shot(2, 9.0, 3.0), shot(3, 12.0, 6.0)]


def test_a_gap_lists_every_shot_it_touches():
    assert shots_in(SHOTS, 4.0, 10.0) == [0, 1, 2]


def test_a_gap_inside_one_shot_lists_that_shot_alone():
    assert shots_in(SHOTS, 5.5, 8.0) == [1]


def test_a_gap_touching_nothing_lists_nothing():
    assert shots_in(SHOTS, 40.0, 50.0) == []


def test_the_owner_is_the_silent_shot_inside_the_gap():
    got = owner(SHOTS, 4.0, 10.0, silent=[2])
    assert got.silent == [2]
    assert "shot 2" in got.said


def test_two_silent_shots_are_both_named():
    assert owner(SHOTS, 0.0, 12.0, silent=[1, 2]).silent == [1, 2]


def test_a_gap_with_no_silent_shot_says_so_and_names_the_neighbours():
    got = owner(SHOTS, 4.0, 10.0, silent=[])
    assert got.silent == []
    assert "no silent shot" in got.said
    assert "0, 1, 2" in got.said


def test_the_owner_never_names_a_shot_outside_the_gap():
    assert 3 not in owner(SHOTS, 4.0, 10.0, silent=[2, 3]).silent


# ---- where the longest hole IS, not only how long it is ---------------------

from studio.gap_owner import longest_span


def line(at, seconds):
    return {"at": at, "seconds": seconds}


def test_the_span_is_the_hole_between_two_lines():
    assert longest_span([line(0.0, 1.0), line(5.0, 1.0)], until=6.0) == (1.0, 5.0)


def test_the_span_can_be_the_run_out_after_the_last_line():
    assert longest_span([line(0.0, 1.0), line(2.0, 1.0)], until=9.0) == (3.0, 9.0)


def test_the_span_can_be_the_run_in_before_the_first():
    assert longest_span([line(7.0, 1.0)], until=8.0) == (0.0, 7.0)


def test_the_span_of_no_lines_is_the_whole_episode():
    assert longest_span([], until=4.0) == (0.0, 4.0)


def test_overlapping_lines_never_make_a_negative_hole():
    got = longest_span([line(0.0, 5.0), line(2.0, 1.0), line(9.0, 1.0)], until=10.0)
    assert got == (5.0, 9.0)


# ---- a placed shot says t_start/t_end, and only a line says `at` ------------
# MEASURED 2026-09-22: every test above passed on fixtures that gave a shot an
# `at`, and the first real placed.json raised KeyError. A green test is not
# evidence the code ever met the file it is for.

def placed(index, t_start, t_end):
    return {"index": index, "t_start": t_start, "t_end": t_end,
            "seconds": t_end - t_start}


REAL = [placed(0, 0.0, 6.54), placed(1, 6.54, 12.0), placed(2, 12.0, 18.2)]


def test_a_placed_shot_is_read_by_its_t_start_and_t_end():
    assert shots_in(REAL, 7.0, 13.0) == [1, 2]


def test_the_owner_reads_a_real_placed_shot():
    assert owner(REAL, 7.0, 13.0, silent=[1]).silent == [1]
