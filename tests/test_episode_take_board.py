"""A take's own storyboard: nine beats of the take's timeline, each a cell."""
from studio import episode_take_board as tb
from studio.episode_spec import Line, Shot

SHOTS = [Shot(index=11, section="spike", setup="lab", size="close", faces=[],
              frame="Close over Watson's coat and hand.", motion="Tilt down a hand's breadth; holds on the stick"),
         Shot(index=12, section="spike", setup="lab", size="medium_close", faces=["sherlock_holmes"],
              frame="Medium close-up of Holmes about to speak.", motion="Locked off; he speaks; a small tilt of the head")]
PLACED = [{"index": 11, "t_start": 92.96, "seconds": 4.25}, {"index": 12, "t_start": 97.21, "seconds": 3.71}]
LINES = [Line(index=17, kind="narration", speaker="john_watson", text="He looked at my hands.", shot=11),
         Line(index=18, kind="dialogue", speaker="sherlock_holmes", text="You have been in Afghanistan.", shot=12)]
AT = {17: (93.21, 3.75), 18: (97.46, 3.19)}


def test_six_beats_cover_the_take_and_name_the_active_shot():
    beats = tb.beats(SHOTS, PLACED, LINES, AT, seconds=7.96)
    assert len(beats) == 6
    assert beats[0]["t"] == 0.0 and beats[0]["shot"] == 11
    assert beats[-1]["shot"] == 12
    assert sum(1 for b in beats if b["shot"] == 11) == 3  # 4.25 of 7.96 s


def test_a_beat_says_how_far_into_its_shot_it_is_and_who_speaks():
    beats = tb.beats(SHOTS, PLACED, LINES, AT, seconds=7.96)
    assert "through the motion" in beats[1]["text"]
    assert "Close over Watson's coat and hand." in beats[1]["text"]
    during = beats[4]  # 6.37 s into the take, inside Holmes's line
    assert "Holmes" in during["text"] and "speaking" in during["text"]


def test_the_sheet_prompt_opens_with_the_camera_lock_and_lists_six_cells():
    beats = tb.beats(SHOTS[:1], PLACED[:1], LINES[:1], AT, seconds=4.25)
    text = tb.prompt(beats, "The lab.", ["sherlock_holmes"], {"sherlock_holmes": "Lean."},
                     landmark="the tall window", push=False, own_panels=2)
    assert text.startswith("ONE locked camera, six moments of one continuous shot.")
    assert "the tall window sits at the same place in every panel" in text
    assert "Image 1 is the exact framing" in text and "Image 3 is the empty location" in text
    assert "Image 4 is Sherlock Holmes" in text
    assert "Panel 1 (0.0 s):" in text and "Panel 6 (" in text and "Panel 7" not in text
    assert "3 by 2 grid of 6" in text


def test_a_named_push_gets_the_monotonic_variant_and_strict_prefixes():
    beats = tb.beats(SHOTS[:1], PLACED[:1], LINES[:1], AT, seconds=4.25)
    text = tb.prompt(beats, "The lab.", [], {}, landmark="the window", push=True, own_panels=1, strict=True)
    assert text.startswith("STRICT: identical framing")
    assert "pushes in evenly and by a small amount" in text
    assert tb.names_push("Push forward a hand's breadth following them; Stamford turns") is True
    assert tb.names_push("Locked off; he speaks") is False


def test_sub_shots_split_the_cells_per_segment_with_the_pin_first():
    from studio.episode_spec import SubShot
    shot = Shot(index=1, section="setup", setup="c", size="insert", frame="Hand on stick.", motion="Static; plants once",
                cuts=[SubShot(at_s=3.5, size="close", faces=["stamford"], frame="Stamford turns.", motion="Static"),
                      SubShot(at_s=7.0, size="medium", faces=["john_watson"], frame="Watson behind.", motion="Tracking")])
    placed = [{"index": 1, "t_start": 3.33, "seconds": 11.2, "cuts": [6.83, 10.33]}]
    beats = tb.beats([shot], placed, [], {}, seconds=11.2)
    assert [b["segment"] for b in beats] == [0, 0, 1, 1, 2, 2]
    assert beats[0]["t"] == 0.0 and beats[2]["t"] == 3.5 and beats[4]["t"] == 7.0
    assert "Stamford turns." in beats[2]["text"] and "Watson behind." in beats[4]["text"]
    text = tb.prompt(beats, "Corridor.", [], {}, landmark="the window", push=False, own_panels=1)
    assert text.startswith("3 locked cameras, one per shot")
    assert "Panels 1-2 are shot A" in text and "Panels 5-6 are shot C" in text


def test_allot_is_as_even_as_possible():
    assert tb.allot(2) == [3, 3] and tb.allot(3) == [2, 2, 2] and tb.allot(4) == [2, 2, 1, 1]


def test_a_two_shot_take_gets_two_locked_cameras_three_cells_each():
    beats = tb.beats(SHOTS, PLACED, LINES, AT, seconds=7.96)
    assert [b["segment"] for b in beats] == [0, 0, 0, 1, 1, 1]
    text = tb.prompt(beats, "The lab.", [], {}, landmark="the window", push=False, own_panels=2)
    assert text.startswith("2 locked cameras, one per shot")
