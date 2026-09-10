"""A take prompt is the official H3 Start Frame skeleton with the measured short body."""
from studio import episode_take_prompt as take
from studio.episode_spec import Shot


def shot(motion="Tracking beside the hand; the stick plants once; Stamford looks back."):
    return Shot(index=0, section="hook", t_start=0, t_end=5.0, setup="c", size="close",
                frame="Close on the hand.", motion=motion)


def test_the_prompt_has_the_official_four_parts_in_order():
    text = take.build(None, shot())
    heads = ["For the target video, at 0.00 seconds", "integrated_multimodal_description: [Shot 1]",
             "overall_soundscape:", "non_diegetic_music: N/A"]
    positions = [text.index(h) for h in heads]
    assert positions == sorted(positions) and text.count("\n\n") == 3


def test_beats_are_placed_in_order_with_prose_not_timestamps():
    text = take.build(None, shot())
    assert "At the start of the shot, Tracking beside the hand." in text
    assert "Halfway through the shot, the stick plants once." in text
    assert "In the final part of the shot, Stamford looks back." in text
    assert " seconds, " not in text and "00:0" not in text


def test_the_body_names_only_the_panel_the_beats_the_lock_and_the_rules():
    text = take.build(None, shot())
    assert "Close on the hand." in text and "nothing outside the panel's frame" in text
    assert "Nobody speaks" in text and len(text) < 1400


def test_a_single_clause_motion_spans_the_whole_shot():
    assert "Through the whole shot, Holds." in take.build(None, shot("Holds."))


def test_a_speaking_shot_carries_the_dialogue_tag_and_lip_movement():
    from studio.episode_spec import Episode, Line, Setup
    sh = Shot(index=0, section="hook", setup="c", size="medium_close", faces=["stamford"],
              frame="Medium close-up of Stamford.", motion="He speaks; his eyes flick away.")
    ep = Episode.model_construct(shots=[sh], lines=[Line(index=0, kind="dialogue", speaker="stamford",
                                                          text="You must not blame me.", shot=0)])
    text = take.build(ep, sh)
    assert "(S1)" in text and "<d>[English] You must not blame me.</d>" in text
    assert "natural lip movement" in text and "Nobody speaks" not in text
    assert "Stamford's voice, close and dry" in text
