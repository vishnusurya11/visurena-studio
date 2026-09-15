r"""The storyboard was told "same camera" and then told to move the camera.

`CAMERA_MOVE` strips the camera clause off a motion before the sheet prompt is
built, so a still panel is never asked to draw a move. It anchors on a bare
camera verb at the START of the line:

    ^(static|tracking|track|push|pull|tilt|pan|handheld|locked|dolly|crane)\b[^;]*;

Episode 1 wrote `"Static shot; Stamford speaks..."` and it matched 23 of 23.
Every plan since episode 2 writes `"The camera pushes in on his face across the
whole shot; his head turns..."`, which begins with "The" and inflects the verb,
so it matches NOTHING:

    ep01 23/23 · ep02 0/25 · ep04 0/24 · ep06 0/26

So `still()` strips nothing and `moved_clause()` returns the CAMERA CLAUSE as
the END panel's one named change. Verified in the paid prompt on disk,
`ep06/boards/sheets/seq_window_street_0.prompt.txt`:

    "PANEL 3 ONE ACTION LATER, from the same camera. What a viewer sees at a
     different place than in panel 3: The camera pushes in on his face across
     the whole shot. Draw that finished and at rest, at its new place..."

One sentence tells the drawer the camera is unchanged and that the change is a
camera push. It obeyed the second, and ALL SEVEN of episode 6's END panels came
back re-staged -- 0.330, 0.253, 0.321, 0.315, 0.407, 0.176 and -0.007 against
their own start cells, every one under the 0.45 floor, all retired, leaving one
END cell in the whole episode.

AND THE CAMERA-MOVE RULE IS WHAT TRIGGERED IT. Before episode 6 only 7 to 13
motions per plan led with the camera; episode 6 leads with it on 26 of 26, so
every END panel got a camera instruction where earlier episodes got a subject
action. The fix that took stillness to zero broke the destination panels,
through a regex that has been wrong since episode 2 and cost nothing until the
prose changed shape.
"""
from studio.episode_seq_board import CAMERA_MOVE, moved_clause, still

EP01 = "Static shot; Stamford speaks the line to the man in front of him."
EP06 = ("The camera pushes in on his face across the whole shot, travelling a forearm; "
        "his head turns a thumb's width to follow something; his shoulders come round.")
LEAD = ("his hand comes up to the pipe as the camera pushes in a hand's breadth across "
        "the whole shot; his chin lifts; his shoulders come down.")


def test_the_old_shape_still_matches():
    """Episode 1's 23 of 23 must keep working."""
    assert CAMERA_MOVE.match(EP01)


def test_the_modern_shape_matches_too():
    assert CAMERA_MOVE.match(EP06)


def test_the_camera_clause_is_stripped_from_the_panel():
    got = still(EP06)
    assert "camera" not in got.lower() and "his head turns" in got


def test_the_end_panel_change_is_not_a_camera_move():
    """`moved_clause` returned "The camera pushes in on his face across the whole
    shot" as the END panel's one named change, in a prompt that also said "from
    the same camera"."""
    got = moved_clause(EP06)
    assert "camera" not in got.lower()


def test_the_change_is_the_subject_action():
    assert "head turns" in moved_clause(EP06)


def test_a_subject_first_head_keeps_its_action():
    """41 of episode 2's 42 motions put the subject first with the camera
    trailing. The subject half is the panel's content and must survive."""
    got = still(LEAD)
    assert "his hand comes up to the pipe" in got and "camera" not in got.lower()


def test_no_shipped_motion_leaks_a_camera_to_the_drawer():
    """Asserted on the OUTCOME, not the route. Two different mechanisms handle
    the two shapes -- `CAMERA_MOVE` cuts a camera-first head, `CAMERA_LEAD` cuts
    a trailing "as the camera ..." -- and a test that pinned the route claimed
    the subject-first shape must match `CAMERA_MOVE`, which it never did and
    never needed to."""
    for said in (EP01, EP06, LEAD,
                 "The camera tracks a hand's breadth to the right across the whole shot; x; y.",
                 "The camera pulls back off the newspapers across the whole shot; a hand comes in; z.",
                 "The camera cranes up a hand's breadth over the chair back; his hand comes out; w."):
        assert "camera" not in still(said).lower(), said


def test_a_motion_with_no_camera_clause_is_untouched():
    said = "The folded paper slides across the white cloth; his eyes go to it; his chin lifts."
    assert still(said) == said
