"""A shot that lays its one person down is failed when the picture stands him up.

ep10 shot 18 asked for the landlord "lying back on the sand"; the panel drew an
upright portrait against the fence, the lane and the houses behind him. H3 then
reconciled the two by turning the world around his face until sand filled the
frame -- the take passed every gate. The reader names the main figure's posture
from a closed list; the judging is done here, against the shot's own words.
"""
from studio import panel_content as pc
from studio.panel_content import Seen


def test_the_shot_asks_for_a_posture_only_when_one_family_is_named():
    assert pc.asked_posture("lying back on the sand with his eyes closed") == "lying"
    assert pc.asked_posture("crouches in the furze at the edge of the pool") == "low"
    assert pc.asked_posture("sits on the bottom stair of the hall") == "sitting"
    assert pc.asked_posture("walks up the lane") is None
    # the narrator kneels by the landlord who lies: two families, no one answer
    assert pc.asked_posture("kneels beside the landlord lying at the fence") is None


def test_a_lying_man_read_standing_fails():
    got = pc.posture_fault(Seen(people=1, posture="standing"), "lying back on the sand", planned=1)
    assert got and "lying" in got


def test_a_lying_man_read_lying_passes():
    assert not pc.posture_fault(Seen(people=1, posture="lying"), "lying back on the sand", planned=1)


def test_crouching_and_kneeling_are_one_family():
    assert not pc.posture_fault(Seen(people=1, posture="kneeling"), "crouches in the furze", planned=1)


def test_an_unread_posture_fails_only_where_one_was_asked():
    assert pc.posture_fault(Seen(people=1, posture=""), "lying back on the sand", planned=1)
    assert not pc.posture_fault(Seen(people=1, posture=""), "walks up the lane", planned=1)


def test_two_people_are_not_judged_for_one_posture():
    assert not pc.posture_fault(Seen(people=2, posture="standing"), "lying back on the sand", planned=2)


def test_the_reader_is_asked_for_the_posture():
    assert '"posture"' in pc.ASK
    assert pc.parse('{"landform": "flat", "people": 1, "lookalikes": 0, "text": false, '
                    '"hour": "night", "posture": "Lying", "subjects": []}').posture == "lying"


def test_a_word_inside_a_bound_tag_is_not_a_posture():
    """ep13 shot 24: the curate's row says his curls are 'lying on a low forehead',
    and the panel of him springing to his feet was refused as a man not lying down."""
    prose = ("Medium close on the curate (crisp, almost flaxen curls cut short and lying on a low "
             "forehead, soot-smudged shirt sleeves) springing to his feet, one hand raised.")
    assert pc.asked_posture(prose) is None


def test_the_keypoint_posture_is_not_judged_where_it_cannot_be_read(monkeypatch):
    """ep13's panel judge, read against the board by eye: a man lying flat seen
    from straight above read 'standing' (2D keypoints are the same), six seated
    figures read 'low', and a chest-up medium close read 'standing' with no legs
    in frame.  Sitting accepts low; a close framing or a top-down camera is not
    judged for posture at all."""
    from studio.judges import panel_eye as pe
    pts = object()
    monkeypatch.setattr(pe.keypoints, "posture", lambda p: "low")
    assert pe.posture_fault(pts, "he sits in the grass", 1, "shot_15", size="medium") is None
    monkeypatch.setattr(pe.keypoints, "posture", lambda p: "standing")
    assert pe.posture_fault(pts, "he sits in the grass", 1, "shot_19", size="medium_close") is None
    assert pe.posture_fault(pts, "lying on his back, high angle, looking down on him", 1, "shot_09",
                            size="medium") is None
    assert pe.posture_fault(pts, "he sits in the grass", 1, "shot_21", size="medium") is not None
