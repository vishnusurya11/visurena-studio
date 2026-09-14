"""A TAKE is a run of consecutive shots inside one H3 budget, every shot's
panel anchored at its own start frame and the next take's first panel
anchored at the last frame (owner, 2026-09-10: one frame per ten seconds
repeats; give the model three)."""
from studio import episode_takes as tk

PLACED = [{"index": 0, "t_start": 0.0, "t_end": 3.0, "seconds": 3.0},
          {"index": 1, "t_start": 3.0, "t_end": 8.0, "seconds": 5.0},
          {"index": 2, "t_start": 8.0, "t_end": 12.0, "seconds": 4.0},
          {"index": 3, "t_start": 12.0, "t_end": 23.0, "seconds": 11.0},
          {"index": 4, "t_start": 23.0, "t_end": 26.0, "seconds": 3.0}]


def test_groups_fill_the_budget_and_stop_at_the_segment_cap():
    """This used to assert `[[0, 1, 2], [3], [4]]` -- three panels in one take,
    per the owner's 2026-09-10 "give the model three".

    SUPERSEDED BY MEASUREMENT, 2026-09-13, over all 22 takes of episode 3:
    1-segment takes pass 7/9 (mean 76.7), 2-segment 7/11 (79.3), 3-segment
    0/2 (23.5) -- and the two 3-segment takes are the two worst in the episode.
    With the earlier 6-of-6 result that is 8 of 8. `SEGMENT_CAP` now closes a run
    at two, so shots 0-2 no longer travel together. See `test_segment_cap.py`."""
    assert tk.groups(PLACED, budget=12.0) == [[0, 1], [2], [3], [4]]


def test_a_shot_longer_than_the_budget_still_gets_its_own_take():
    assert tk.groups(PLACED[3:4], budget=5.0) == [[3]]


def test_anchors_are_every_panel_at_its_start_frame_plus_the_next_panel_last():
    take = tk.take(PLACED, [0, 1, 2], following=3, fps=24)
    assert take["seconds"] == 12.0
    assert take["anchors"] == [(0, 0), (1, 72), (2, 192), (3, take["frames"] - 1)]


def test_the_last_take_has_no_following_panel():
    take = tk.take(PLACED, [4], following=None, fps=24)
    assert take["anchors"] == [(4, 0)]


def test_frames_cover_the_take_plus_the_handle_on_the_h3_grid():
    take = tk.take(PLACED, [0, 1, 2], following=3, fps=24)
    assert take["frames"] % 17 == 5 and take["frames"] >= 24 * 12.25


def test_a_take_never_crosses_a_setup():
    placed = [dict(p, setup="corridor" if p["index"] < 2 else "lab") for p in PLACED]
    assert tk.groups(placed, budget=12.0) == [[0, 1], [2], [3], [4]]


def test_a_shot_with_sub_shots_gives_the_take_its_cut_frames():
    placed = [dict(p) for p in PLACED]
    placed[1]["cuts"] = [6.0, 7.0]        # absolute, inside shot 1 (3.0 .. 8.0)
    take = tk.take(placed, [0, 1, 2], following=None, fps=24)
    assert take["cuts"] == [(1, 1, 144), (1, 2, 168)]
    assert tk.take(PLACED, [0, 1, 2], following=None, fps=24)["cuts"] == []


def test_every_cell_is_pinned_once_at_its_start():
    """Task force 2026-09-11: any end pin (the start cell again, or a drawn END cell) is
    reached in about a second and then HELD; pins are soft conditioning rows, and two of
    them say 'nothing changes'.  So the take builder pins each cell once, at its start."""
    assert not hasattr(tk, "end_pins")
    placed = [{"index": 3, "t_start": 10.0, "seconds": 4.0, "cuts": [12.5]}, {"index": 4, "t_start": 14.0, "seconds": 3.0, "cuts": []}]
    take = tk.take(placed, [3, 4], following=None)
    assert take["anchors"] == [(3, 0), (4, 96)] and take["cuts"] == [(3, 1, 60)]


def test_pins_land_on_token_starts_of_the_17_frame_blocks():
    """Verified in the model source (2026-09-11): FRAME_PER_TOKEN = (1,4,4,4,4), so a
    token starts at 17k + {0,1,5,9,13}; the old '1 mod 4' rule was wrong past frame 17."""
    assert [tk.grid_frame(f) for f in (0, 1, 2, 5, 6, 13, 14, 16, 17, 18, 22, 108)] == [0, 1, 5, 5, 9, 13, 17, 17, 17, 18, 22, 111]


def test_a_pin_can_also_snap_to_the_token_start_nearest_its_whole_second():
    """Spec 3.20.  `grid_frame` snaps FORWARD, which put T01's cut 0.208 s after the
    00:03 the text states; `near_grid` snaps to the nearest token start to the whole
    second instead (frame 76 -> 73 = 3.042 s).  It is not wired in: a backward snap
    moves the picture cut BEFORE the voice cut, and audio-first is the owner's
    non-negotiable rule.  Ties go forward for the same reason."""
    assert tk.near_grid(76) == 73 and tk.grid_frame(76) == 77
    assert tk.near_grid(0) == 0 and tk.near_grid(188) == 192
    assert tk.near_grid(102) == 98                      # a tie at 94/98 goes forward
