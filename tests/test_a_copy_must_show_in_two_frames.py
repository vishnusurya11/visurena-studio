"""A take's copy count must hold in two of its frames (Jekyll ep06 T23, run 23, 2026-10-29).

The reader called bareheaded Poole in tails and Utterson in a bowler and double-breasted coat "1 of them copies
of another" in one wide frame; `busiest` took the max over frames, the take failed as a people fault, and G-DEAD
would have refused the cut.  The people count keeps its max (a figure who walks in halfway is in the take); a
copy is a picture fault that persists, so it must show in two frames (the take's G-WHO rule, CONFIRM)."""
from studio.panel_content import Seen
from studio import take_content


def seen(lookalikes: int, people: int = 2) -> Seen:
    return Seen(landform="flat", people=people, lookalikes=lookalikes, text=False, hour="night", subjects=[],
                posture="standing")


def test_one_frame_calling_two_men_copies_is_not_a_copy():
    assert take_content.busiest([seen(1), seen(0), seen(0)]).lookalikes == 0


def test_two_frames_agreeing_is_a_copy():
    assert take_content.busiest([seen(1), seen(1), seen(0)]).lookalikes == 1


def test_a_single_read_keeps_its_count():
    assert take_content.busiest([seen(2)]).lookalikes == 2


def test_the_people_count_still_takes_the_fullest_frame():
    assert take_content.busiest([seen(0, people=3), seen(0, people=2), seen(0, people=2)]).people == 3
