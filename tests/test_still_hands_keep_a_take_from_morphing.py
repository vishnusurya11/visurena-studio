"""Still hands (owner 2026-10-30: "trial then adopt"; Jekyll ep06 morph audit).

ep06 morphed on 14 of 28 shots, worst where fingers worked a small object (6 of 7): a seal broken with both thumbs,
a page lifted and turned, an envelope set down, a packet pushed into a safe, fingers working the chair leather (a
black starburst grew out of the coat).  Trial, the seven hand-work takes re-rendered both ways, 2 seeds, judged
blind: the original action scored 1.43 mean (7 of 14 noticeable, 2 stop-level), still hands with a face beat 0.71
(3 of 14, none stop-level).  The writer is told so; a plan that still asks fingers to work an object is named as
an advisory, so the next episode measures whether the brief reached the plan."""
from types import SimpleNamespace

from studio import plan_brief, plan_gates


def shot(index, motion, faces=("gabriel_john_utterson",), changed=""):
    return SimpleNamespace(index=index, motion=motion, changed=changed, frame="", faces=list(faces))


EP06 = [
    shot(6, "The camera holds a locked-off frame on the doctor's face; he grips the leather arm of the chair as he "
            "speaks; his fingers tighten and work on the leather."),
    shot(15, "The camera tilts up from the leather to the face as he lifts the top page into the window light; his "
             "free hand turns the next page over on the desk."),
    shot(17, "The camera pulls back from the candle flame as he sets the sealed envelope before him."),
    shot(18, "The camera holds a locked-off frame as he breaks his dead friend's red wax seal with both thumbs."),
    shot(22, "The camera holds a locked-off frame as he pushes the packet into the inmost corner of the safe."),
    shot(11, "The camera holds a locked-off frame on his face as he turns his face toward the red fire."),
    shot(26, "The camera holds a locked-off frame on his face as he lowers his eyes as he speaks."),
    shot(9, "The camera pushes in toward his face as he keeps up a trembling hand before his chest."),
    shot(16, "The camera tracks sideways past the letter as the slanting lines of ink pass beneath the lens.", faces=()),
]


def test_the_brief_tells_the_writer_to_keep_hands_still():
    said = " ".join(plan_brief.PICTURE_RULES)
    assert "hands stay still" in said and "insert" in said


def test_fingers_working_an_object_are_named():
    found = plan_gates.handwork_advisories(SimpleNamespace(shots=EP06))
    assert [int(f.split()[2].rstrip(":")) for f in found] == [6, 15, 17, 18, 22]


def test_a_face_beat_or_an_empty_hand_gesture_is_not():
    calm = [s for s in EP06 if s.index in (11, 26, 9)]
    assert plan_gates.handwork_advisories(SimpleNamespace(shots=calm)) == []


def test_a_shot_with_no_one_in_it_is_not_read():
    assert plan_gates.handwork_advisories(SimpleNamespace(shots=[shot(16, "he breaks the seal", faces=())])) == []
