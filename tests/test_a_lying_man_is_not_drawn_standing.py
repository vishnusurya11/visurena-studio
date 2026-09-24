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
