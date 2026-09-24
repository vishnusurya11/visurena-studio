"""The cell gates: fixtures are the ep09 sentences that cost renders, and the
published sentences the gates must leave alone (plan-gate audit, 2026-09-23)."""


from studio.cell_gates import aimed_at, anchored_truck, hat_clash, in_cell, landmarks, BARE
from studio.episode_spec import Shot

GEO_TOWER = ("The burning church tower stands up the whole height of the frame at the CENTRE, its masonry "
             "going out of line at the CENTRE LEFT. Red flame fills the LEFT third and the RIGHT third "
             "behind it and dust lifts across the BOTTOM third.")


def shot(**kw):
    base = dict(index=0, section="setup", setup="s", size="insert", frame="f", motion="m")
    return Shot(**{**base, **kw})


# ---- G-AIM
def test_tilt_toward_a_ruin_the_cell_lacks_is_caught():  # ep09 shot 14 before 80bb79c
    s = shot(at_rest=GEO_TOWER, motion="x")
    head = ("The camera tilts down from the top of the tower to the ruin already in the picture until "
            "the falling masonry is in the middle of the frame, travelling a forearm")
    assert [p for _, p in aimed_at(head) if not in_cell(p, s)] == ["ruin"]


def test_pan_to_a_bridge_the_cell_lacks_is_caught():  # ep09 shot 18 before 6c70fe2
    s = shot(size="wide", at_rest="The scorched lawn fills the BOTTOM half. The summerhouse stands at the LEFT third.")
    head = "The camera pans to the left along the road until the railway bridge already in the picture is at the centre"
    assert not in_cell(aimed_at(head)[0][1], s)


def test_a_person_target_may_stand_in_the_frame_sentence():  # ep08 shot 7, published
    s = shot(size="medium", frame="Medium on a knot of five men under the platform lamps",
             at_rest="The pale platform runs from the BOTTOM edge away into the CENTRE.")
    head = "The camera pans to the right across the knot until the furthest man already in the picture is at the centre"
    assert in_cell(aimed_at(head)[0][1], s)


def test_face_and_head_are_one_target():  # ep09 shot 22
    s = shot(size="close", at_rest="His head fills the CENTRE of the frame.")
    assert in_cell("face", s)


def test_rises_from_names_the_camera_floor_not_a_target():  # ep09 shot 21
    head = "The camera rises from the road with small amplitude until the cart at the gate is inside the picture"
    assert aimed_at(head) == []


# ---- G-HAT
def test_boater_worn_by_tag_and_held_in_hand_clashes():  # ep09 shot 11 before 5933f8a
    text = ("Medium on the narrator, straw boater with a black band standing in the heather with his "
            "straw boater in one hand")
    assert hat_clash(text)[0] == {"boater"}


def test_another_mans_hat_off_beside_a_worn_boater_clashes():  # ep09 shot 20 before 5933f8a
    text = ("Medium on the narrator, straw boater with a black band speaking past another man, "
            "his hat off and held against his chest")
    assert hat_clash(text)[0] == {"boater"}


def test_a_different_named_hat_off_does_not_clash():  # ep09 shot 20 after 5933f8a
    text = ("Medium on the narrator, straw boater with a black band speaking past another man "
            "holding his own brown bowler off against his chest")
    assert hat_clash(text)[0] == set()


def test_a_cap_pushed_back_off_the_forehead_is_worn():  # ep08 shot 8, published
    assert hat_clash("in a brown cloth cap, his cap pushed back off his forehead")[0] == set()


def test_holding_a_hat_on_is_worn():  # ep03 shot 16, ep04 shot 5, published
    assert hat_clash("in the straw boater, one hand holding his boater on")[0] == set()


def test_bare_head_downgrades_to_advisory():  # ep05 shot 15, published
    assert BARE.search("the last light along one side of his bare head")


# ---- G-PLACE
def test_a_simile_and_a_direction_are_not_landmarks():  # ep06 shot 1, ep01 shot 22
    assert landmarks("bright as a lighthouse reflector, raised toward the railway beyond") == set()


def test_a_bridge_in_the_frame_is_a_landmark():
    assert landmarks("hussars riding under the brick railway bridge below") == {"bridge", "railway"}


# ---- G-ANCHOR
def test_truck_on_a_man_leaning_over_a_fence_fires():  # ep09 T02, owner 2026-09-23
    s = shot(size="medium", faces=["unnamed_neighbour"],
             frame="Medium on the neighbour leaning over the low paling fence with a handful of strawberries",
             motion="The camera tracks sideways to the right along the fence, a truck with small amplitude, "
                    "until the side gate already in the picture is at the centre; he laughs")
    assert anchored_truck(s) == "leaning over"


def test_truck_with_a_walking_man_at_his_own_pace_is_left_alone():  # ep08 T05, published
    s = shot(size="medium_close", faces=["x"], frame="Medium close on a boy walking along the platform, his hand resting on the rail",
             motion="The camera tracks with him along the platform at his own pace, a truck with small amplitude, "
                    "keeping him in the middle of the picture; he calls")
    assert anchored_truck(s) == ""


def test_push_in_on_a_leaning_man_is_left_alone():  # the remedy
    s = shot(size="medium", faces=["x"], frame="Medium on the neighbour leaning over the low paling fence",
             motion="The camera pushes in toward him with small amplitude, travelling one short stride; he laughs")
    assert anchored_truck(s) == ""


# ---- on the real plans
from studio import cell_gates, episode_home  # noqa: E402

WOTW = "20260827135508_the-war-of-the-worlds"


def test_the_owners_neighbour_shot_is_refused_by_the_real_ep09_plan():
    book = episode_home.book_dir(WOTW)
    found = cell_gates.faults(episode_home.load_plan(book, 9), cell_gates.pack_prompts(book))
    assert any(f.startswith("G-ANCHOR shot 2:") for f in found)


def test_the_place_pictures_are_read_by_location_and_view():
    got = cell_gates.pack_prompts(episode_home.book_dir(WOTW))
    assert "maybury_hill/wide_lawn_burning" in got and got["maybury_hill/wide_lawn_burning"]


# ---- G-LAID
def test_a_close_on_a_lying_man_from_low_over_him_is_caught():  # ep10 shot 18, published
    from studio.cell_gates import laid_unseen
    s = shot(size="close", faces=["landlord"], frame="Close on the landlord lying back on the sand",
             camera="low over him, two paces away, an 85mm lens")
    assert laid_unseen(s)


def test_looking_down_or_level_with_the_face_passes():
    from studio.cell_gates import laid_unseen
    for camera in ("above him looking down, two paces away", "on the ground level with his face, a 50mm lens"):
        s = shot(size="close", faces=["landlord"], frame="Close on the landlord lying on the sand", camera=camera)
        assert not laid_unseen(s)


def test_a_medium_or_a_two_shot_is_left_alone():  # ep07 4, ep10 17
    from studio.cell_gates import laid_unseen
    assert not laid_unseen(shot(size="medium", faces=["a"], frame="Medium on a man lying in the road",
                                camera="low over him"))
    assert not laid_unseen(shot(size="medium_close", faces=["a", "b"], camera="low in the lane",
                                frame="Medium close on the narrator kneeling by the landlord lying at the fence"))


def test_a_pan_across_a_seated_man_is_caught_too():  # ep11 T06, held 0.85 over 320 px
    s = shot(size="medium", faces=["narrator"],
             frame="Medium on the narrator sitting in his desk chair turned to the open window at night",
             motion="The camera pans from the dark bookshelves across to the open window already in the "
                    "picture until the window is at the centre; he goes on staring")
    assert anchored_truck(s) == "sitting in"
