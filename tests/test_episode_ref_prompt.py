from studio import episode_ref_prompt as rp
from studio.episode_spec import Shot

SHOT = Shot(index=12, section="spike", setup="lab", size="medium_close", faces=["sherlock_holmes"],
            frame="Medium close-up of Holmes.", motion="Locked off; a small tilt of the head")


def test_pictures_bind_cast_then_sheet_then_plate_by_position():
    text = rp.pictures(["sherlock_holmes", "john_watson"], {"sherlock_holmes": "Lean, hawk-nosed."})
    assert text.startswith("<Picture 1> is Sherlock Holmes: Lean, hawk-nosed.")
    assert "<Picture 2> is John Watson" in text
    assert "<Picture 3> is the storyboard sheet" in text and "<Picture 4> is the empty location" in text


def test_the_speaking_body_lays_the_timeline_out_in_seconds():
    body = rp.speaking_body(SHOT, "sherlock_holmes", "How are you?", line_s=4.2, seconds=4.46)
    assert "At 0.00 seconds the shot begins exactly on the anchored first frame" in body
    assert "From 0.00 to 0.25 seconds Sherlock Holmes is silent" in body
    assert "From 0.25 to 4.45 seconds Sherlock Holmes (S1) speaks" in body
    assert "<d>[English] How are you?</d>" in body
    assert "From 4.45 seconds to the end" in body


def test_motion_clauses_are_spread_over_the_shot():
    assert rp.bands(SHOT, 4.0) == "Locked off for the whole shot. From 0.00 to 4.00 seconds a small tilt of the head."


def test_a_silent_body_forbids_lips():
    assert "Nobody speaks and no lips move" in rp.silent_body(SHOT, 4.0)
