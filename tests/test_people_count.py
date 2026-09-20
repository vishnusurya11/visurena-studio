"""A take must not grow people: more big faces than the shot planned is a clone."""
from studio.people_count import BIG_FACE, clones, summarise_people


def test_a_big_face_beyond_the_plan_is_a_clone():
    # two faces at a third of frame height where one person was planned
    assert clones([0.33, 0.30], planned=1) == 1
    assert clones([0.33], planned=1) == 0


def test_small_faces_are_a_crowd_and_never_clones():
    assert clones([0.33, 0.04, 0.05, 0.03], planned=1) == 0
    assert BIG_FACE > 0.05


def test_a_shot_that_plans_nobody_tolerates_a_crowd_but_not_a_hero_face():
    assert clones([0.02, 0.03], planned=0) == 0
    assert clones([0.40], planned=0) == 1


def test_summarise_reports_the_worst_frame_and_how_many_frames_cloned():
    out = summarise_people([[0.3], [0.3, 0.31], [0.3, 0.33, 0.30]], planned=1)
    assert out["clone_frames"] == 2 and out["worst_extra"] == 2
