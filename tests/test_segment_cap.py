"""A take holds at most two segments, because the third one is where it breaks.

OWNER 2026-09-13, pointing at the master: "blurred man at 17 seconds".  At 17 s
the picture is supposed to be Watson reading the note; instead the take has cut
itself to an invented wide of the sitting room with a smeared second figure
standing at the right edge.  `sitting_room.crowd` is empty -- nothing asked for
another person.

That take is T02, and it scores 4/100, the worst in the episode.  It is also one
of only two takes in the episode carrying THREE segments.

MEASURED over all 22 takes of episode 3:

    1 segment    7/9  pass   mean 76.7
    2 segments   7/11 pass   mean 79.3
    3 segments   0/2  pass   mean 23.5      <- T02 4.0, T11 43.0

Both three-segment takes fail, and they are the two worst takes in the episode.
This repeats the earlier measurement (3+ segment takes failed 6 of 6) on fresh
data, which makes it 8 of 8.  The cap was proposed then and never built.

WHY THREE IS THE BREAK.  Every segment after the first is a cut the model has to
place itself, on its own clock, from a pin.  With two segments it has one cut to
get right.  With three it has two, and once it is early on the first it is
adrift for the rest -- T02 lands 1 of 3 and then invents a fourth cut of its
own, and it is in that invented shot, which no panel describes, that the extra
figure appears.  A picture nothing specifies is a picture the model fills in.

The cap cannot split a SHOT: a shot with two sub-shots is three segments by
itself and has to stay whole.  So the rule is "never START a third segment in a
take that already has two", not "every take has two".
"""
from studio.episode_takes import SEGMENT_CAP, groups, segments_in

# Episode 3's real sitting room: shot 2 carries one sub-shot, shot 3 none.
SHOT = lambda i, secs, cuts=(), setup="sitting_room": {
    "index": i, "seconds": secs, "setup": setup, "cuts": list(cuts)}
SITTING = [SHOT(0, 5.46), SHOT(1, 8.17), SHOT(2, 5.71, [2.77]), SHOT(3, 5.96)]


def test_a_shot_with_no_sub_shots_is_one_segment():
    assert segments_in([SHOT(3, 5.96)]) == 1


def test_a_shot_with_one_sub_shot_is_two_segments():
    assert segments_in([SHOT(2, 5.71, [2.77])]) == 2


def test_the_cap_is_two():
    assert SEGMENT_CAP == 2


def test_the_three_segment_take_that_scored_four_is_split():
    """T02 was [2, 3] -- two segments from shot 2 plus one from shot 3."""
    assert [3, 4] not in groups(SITTING)
    assert [2, 3] not in groups(SITTING)


def test_shot_two_keeps_its_own_sub_shot_and_takes_no_passenger():
    runs = groups(SITTING)
    assert [2] in runs and all(segments_in([s for s in SITTING if s["index"] in r]) <= SEGMENT_CAP
                               for r in runs)


def test_every_shot_still_appears_exactly_once_and_in_order():
    runs = groups(SITTING)
    assert [i for run in runs for i in run] == [0, 1, 2, 3]


def test_two_plain_shots_still_travel_together():
    """The cap removes the third segment, not the second: a take of two plain
    shots is the 2-segment case that passes 7 of 11."""
    assert groups([SHOT(0, 4.0), SHOT(1, 4.0)]) == [[0, 1]]


def test_a_shot_that_is_three_segments_on_its_own_stays_whole():
    """A cap that cannot be met by splitting must not drop or loop; a shot is
    indivisible, so it forms its own take and the cap yields to it."""
    fat = SHOT(9, 9.0, [3.0, 6.0])
    assert groups([fat]) == [[9]]
    assert groups([SHOT(8, 4.0), fat]) == [[8], [9]]


def test_the_seconds_budget_still_closes_a_run():
    assert groups([SHOT(0, 7.0), SHOT(1, 7.0)], budget=12.0) == [[0], [1]]


def test_a_take_still_never_crosses_a_setup():
    rows = [SHOT(0, 3.0), SHOT(1, 3.0, setup="cab")]
    assert groups(rows) == [[0], [1]]


def test_a_run_of_plain_shots_packs_two_at_a_time():
    rows = [SHOT(i, 3.0) for i in range(4)]
    assert groups(rows) == [[0, 1], [2, 3]]


def test_no_run_ever_exceeds_the_cap_on_the_whole_episode_shape():
    rows = SITTING + [SHOT(4, 7.08, setup="cab"), SHOT(5, 5.79, [2.5], setup="cab")]
    for run in groups(rows):
        picked = [s for s in rows if s["index"] in run]
        assert len(run) == 1 or segments_in(picked) <= SEGMENT_CAP
