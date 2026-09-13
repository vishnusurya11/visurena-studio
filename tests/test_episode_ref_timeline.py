"""The take prompt for a multi-shot r2v take: one segment per shot with its
seconds, the voice line at its time, and who is on camera."""
from studio import episode_ref_prompt as rp
from studio.episode_spec import Line, Shot

SHOTS = [Shot(index=3, section="friction", setup="corridor", size="full", faces=[],
              frame="Two backs walking away.", motion="Locked off; they walk; both heads stay forward"),
         Shot(index=4, section="friction", setup="corridor", size="close", faces=["stamford"],
              frame="Close on Stamford turning to speak.", motion="Handheld; he turns")]
PLACED = [{"index": 3, "t_start": 24.0, "seconds": 4.0}, {"index": 4, "t_start": 28.0, "seconds": 3.0}]
LINES = [Line(index=5, kind="narration", speaker="john_watson", text="I did not know him.", shot=3),
         Line(index=6, kind="dialogue", speaker="stamford", text="You must not blame me.", shot=4)]
AT = {5: (24.25, 2.0), 6: (28.25, 2.4)}


def test_segments_carry_seconds_frame_motion_and_the_voice_at_its_time():
    body = rp.timeline_body(SHOTS, PLACED, LINES, AT, seconds=7.0)
    assert "From 0.00 to 4.00 seconds [Shot 1]" in body
    assert "Two backs walking away." in body
    assert "From 0.25 to 2.25 seconds the narrator's voice, off-screen" in body
    assert "I did not know him." in body
    assert "nobody on screen speaks" in body
    assert "From 4.00 to 7.00 seconds [Shot 2]" in body
    assert "Stamford (S1) speaks" in body and "<d>[English] You must not blame me.</d>" in body
    assert "From 4.25 to 6.65 seconds" in body


def test_a_shot_with_no_face_says_who_is_not_shown():
    body = rp.timeline_body(SHOTS[:1], PLACED[:1], LINES[:1], AT, seconds=4.0)
    assert "no face is readable" in body


def test_pictures_without_cast_number_the_sheet_first():
    text = rp.pictures([], {})
    assert text.startswith("<Picture 1> is the storyboard sheet")
    assert "<Picture 2> is the empty location" in text
