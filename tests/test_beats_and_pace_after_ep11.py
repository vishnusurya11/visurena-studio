"""Two builder faults the ep11 dry build found.

A segment too short for a first beat (shot 5, a 1.5 s silent close packed
behind shot 4) made `beat_sentences` index an empty list. And the L8 pace
lint read "We ride tonight" inside the spoken line as a ride with no pace.
"""
import inspect

from studio import episode_ref_official as ro


def test_a_segment_too_short_for_a_beat_still_gets_its_tail():
    out = ro.beat_sentences("The camera pushes in across the whole shot, travelling a hand's breadth; "
                            "his jaw sets; his hand comes up to wipe his mouth", 0, 1)
    assert out and out[-1].endswith("continues to the last frame of the shot.")
    assert "wipe his mouth" in " ".join(out)


def test_a_gait_inside_the_spoken_line_is_not_a_walk():
    assert ro.unquoted('He says: "We ride tonight." The camera pushes in.') == "He says:  The camera pushes in."
    assert "unquoted" in inspect.getsource(ro.l8_pace)
