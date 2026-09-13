"""A storyboard sheet holds nine shots in reading order, names its references, and crops cleanly."""
from studio import episode_board as board
from studio.episode_spec import Shot


def shots(n):
    return [Shot(index=i, section="friction", t_start=i * 3.0, t_end=i * 3.0 + 3.0, setup="lab",
                 size="wide", carrier="wide", cast=["a"], frame=f"frame {i}", motion="m")
            for i in range(n)]


def test_shots_are_spread_evenly_over_the_fewest_sheets():
    assert [len(c) for c in board.chunks(shots(10))] == [5, 5]
    assert [len(c) for c in board.chunks(shots(7))] == [7]
    assert [len(c) for c in board.chunks(shots(9))] == [9]
    assert [len(c) for c in board.chunks(shots(19))] == [7, 7, 5]
    assert board.chunks(shots(10))[1][0].index == 5


def test_spare_panels_become_alternates_of_real_shots_never_black():
    alts = board.alternates(shots(7))
    assert [index for index, _ in alts] == [0, 1]
    assert "panel 1" in alts[0][1] and "panel 2" in alts[1][1]
    assert board.alternates(shots(9)) == []
    text = board.prompt(shots(7), "a lab", ["a"], {}, previous=False)
    assert "Panel 9:" in text and "plain black" not in text


def test_the_prompt_names_every_reference_panel_and_the_spares():
    text = board.prompt(shots(7), "a lab", ["john_watson", "stamford"],
                        {"john_watson": "a lean man"}, previous=True)
    assert "3 by 3 grid" in text and "left to right, top to bottom" in text
    assert "Image 2 is John Watson: a lean man" in text
    assert "Image 4 is the previous storyboard" in text
    assert "Panel 7: frame 6" in text and "Panel 8: Reverse angle" in text


def test_panel_boxes_follow_reading_order_and_trim_gutters():
    first, third, fourth, last = (board.panel_box(i) for i in (0, 2, 3, 8))
    assert first[0] > 0 and first[1] > 0
    assert third[2] < board.CANVAS[0] and third[1] == first[1]
    assert fourth[0] == first[0] and fourth[1] > first[3]
    assert last[2] < board.CANVAS[0] and last[3] < board.CANVAS[1]
    assert all(b[2] - b[0] > 640 and b[3] - b[1] > 980 for b in (first, third, fourth, last))


def test_a_single_panel_prompt_names_one_frame_and_no_grid():
    from studio.episode_spec import Shot
    from studio import episode_board as board
    shot = Shot(index=19, section="payoff", setup="lab", size="insert", frame="Two hands clasp.",
                motion="hold")
    text = board.panel_prompt(shot, "A lab.", ["sherlock_holmes"], {"sherlock_holmes": "Lean."})
    assert text.startswith("A single vertical 9:16 film frame")
    assert "no grid" in text and "Two hands clasp." in text
    assert "Image 3 is the previous storyboard sheet" in text
    assert "Panel 1" not in text
