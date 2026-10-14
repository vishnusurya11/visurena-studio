"""G-PRESENT and the scene's present cast (Jekyll ep01 HEL, owner 2026-10-14):
"the first shot doesn't have the actual characters in the scene, so in the
second shot the character magically appears ... Every shot needs to have all
characters involved in the references."

A SCENE is a run of consecutive shots on one setup.  Whoever is in the picture
anywhere in it is in its first shot, unless the plan marks his ENTRANCE
(`enters`, with an arrival in the motion).  A wide or full shot frames the whole
place, so it shows everyone present unless the plan marked an EXIT.  Measured on
ep01: shot 5 (the girl, no entrance after the wide of shot 3), shot 12 (the
lawyer, absent from the scene's opener 11), shot 19 (the lawyer, absent from the
opener 18).  $0."""
from __future__ import annotations

from types import SimpleNamespace

from studio import plan_gates, scene_cast

NAMES = {"enfield": "richard_enfield", "utterson": "gabriel_john_utterson", "hyde": "edward_hyde"}


def shot(i, setup, size, faces=(), frame="", motion="the camera holds", enters=(), exits=(), cuts=()):
    return SimpleNamespace(index=i, setup=setup, size=size, faces=list(faces), frame=frame,
                           at_rest="", end="", motion=motion, enters=list(enters),
                           exits=list(exits), cuts=list(cuts))


def ep(*shots):
    return SimpleNamespace(shots=list(shots))


def test_a_scene_is_a_run_of_consecutive_shots_on_one_setup():
    shots = [shot(0, "a", "wide"), shot(1, "a", "close"), shot(2, "b", "wide"), shot(3, "a", "wide")]
    assert [[s.index for s in run] for run in scene_cast.scenes(shots)] == [[0, 1], [2], [3]]


def test_in_frame_is_faces_cut_faces_and_whoever_the_picture_names():
    cut = SimpleNamespace(faces=["edward_hyde"], frame="", at_rest="", end="")
    s = shot(0, "a", "medium", ["richard_enfield"], frame="Over Mr. Utterson's shoulder", cuts=[cut])
    assert scene_cast.in_frame(s, NAMES) == ["richard_enfield", "edward_hyde", "gabriel_john_utterson"]


def test_a_person_who_appears_after_the_opener_is_refused():
    """ep01 shots 11 -> 12: a medium of Enfield alone, then the lawyer stands in the arch."""
    got = plan_gates.present_faults(ep(shot(11, "pavement", "medium", ["richard_enfield"]),
                                       shot(12, "pavement", "medium", ["gabriel_john_utterson",
                                                                       "richard_enfield"])), NAMES)
    assert len(got) == 1 and got[0].startswith("G-PRESENT shot 12:")
    assert "gabriel_john_utterson" in got[0] and "shot 11" in got[0]


def test_the_opener_that_names_him_in_its_words_holds_him():
    """A reverse over his shoulder establishes him: the opener's prose names him."""
    got = plan_gates.present_faults(ep(shot(0, "a", "medium_close", ["richard_enfield"],
                                            frame="Medium close over Mr. Utterson's shoulder"),
                                       shot(1, "a", "close", ["gabriel_john_utterson"])), NAMES)
    assert got == []


def test_a_marked_entrance_with_an_arrival_passes():
    """ep01 shot 5: the girl runs in down the cross street after the wide."""
    got = plan_gates.present_faults(ep(shot(3, "x", "wide", ["edward_hyde"]),
                                       shot(5, "x", "medium", ["child"], enters=["child"],
                                            motion="The camera holds; the girl runs in down the cross street")),
                                    NAMES)
    assert got == []


def test_an_entrance_the_motion_does_not_show_is_refused():
    got = plan_gates.present_faults(ep(shot(3, "x", "wide", ["edward_hyde"]),
                                       shot(5, "x", "medium", ["child"], enters=["child"],
                                            motion="The camera holds; the girl stands at the railing")),
                                    NAMES)
    assert len(got) == 1 and "arrival" in got[0]


def test_a_later_wide_that_drops_a_present_person_is_advised():
    """Advice, not a refusal: Scarlet ep08 shot 14 is a wide of the sky over the rock."""
    e = ep(shot(0, "a", "medium", ["richard_enfield", "gabriel_john_utterson"]),
           shot(1, "a", "wide", ["gabriel_john_utterson"]))
    assert plan_gates.present_faults(e, NAMES) == []
    got = plan_gates.present_advisories(e, NAMES)
    assert len(got) == 1 and "richard_enfield" in got[0] and got[0].startswith("G-PRESENT-WIDE shot 1:")


def test_a_marked_exit_releases_the_wide():
    e = ep(shot(0, "a", "medium", ["richard_enfield", "gabriel_john_utterson"], exits=["richard_enfield"],
                motion="The camera holds; Mr. Enfield walks away up the street"),
           shot(1, "a", "wide", ["gabriel_john_utterson"]))
    assert plan_gates.present_faults(e, NAMES) == [] and plan_gates.present_advisories(e, NAMES) == []


def test_a_return_after_an_exit_is_a_new_entrance():
    e = ep(shot(0, "a", "medium", ["richard_enfield", "gabriel_john_utterson"], exits=["richard_enfield"],
                motion="The camera holds; Mr. Enfield walks away up the street"),
           shot(1, "a", "medium", ["gabriel_john_utterson", "richard_enfield"]))
    assert [f.split(":")[0] for f in plan_gates.present_faults(e, NAMES)] == ["G-PRESENT shot 1"]


def test_a_closer_framing_may_single_one_person_out():
    """A medium or a close-up frames the others out; it never makes anyone appear."""
    got = plan_gates.present_faults(ep(shot(0, "a", "wide", ["richard_enfield", "gabriel_john_utterson"]),
                                       shot(1, "a", "medium", ["richard_enfield"]),
                                       shot(2, "a", "close", ["gabriel_john_utterson"])), NAMES)
    assert got == []


def test_a_new_scene_on_the_same_setup_starts_clean():
    """ep01 shot 22: the button returns to the door with the lawyer alone."""
    got = plan_gates.present_faults(ep(shot(0, "door", "wide", ["richard_enfield", "gabriel_john_utterson"]),
                                       shot(1, "street", "wide", ["gabriel_john_utterson"]),
                                       shot(2, "door", "wide", ["gabriel_john_utterson"])), NAMES)
    assert got == []


def test_over_the_ceiling_the_closest_readable_faces_win_in_first_appearance_order():
    """Three people, two slots: the man only ever a speck in a wide loses."""
    shots = [shot(0, "a", "wide", ["a", "b", "c"]), shot(1, "a", "close", ["c"]),
             shot(2, "a", "medium", ["b"])]
    assert scene_cast.pick(["a", "b", "c"], shots, 2) == ["b", "c"]
    assert scene_cast.pick(["a", "b", "c"], shots, 3) == ["a", "b", "c"]


def test_the_battery_counts_g_present_hard_before_anything_is_drawn(tmp_path, monkeypatch):
    from scripts.episode import plan_check
    bad = ep(shot(11, "p", "medium", ["richard_enfield"]),
             shot(12, "p", "medium", ["gabriel_john_utterson", "richard_enfield"]))
    monkeypatch.setattr(plan_check, "rendered", lambda book, number: False)
    assert plan_check.present_gate(bad, tmp_path, 1, NAMES) == 1
    monkeypatch.setattr(plan_check, "rendered", lambda book, number: True)
    assert plan_check.present_gate(bad, tmp_path, 1, NAMES) == 0


def test_the_contract_carries_entrances_and_exits_and_defaults_them_empty():
    from studio.episode_spec import Shot
    s = Shot(index=5, section="friction", setup="x", size="medium", frame="Medium of the girl",
             motion="The camera holds; the girl runs in down the cross street", enters=["child"])
    assert s.enters == ["child"] and s.exits == []
    assert Shot(index=0, section="hook", setup="x", size="wide", frame="Wide", motion="The camera holds").enters == []


def test_a_common_noun_is_never_read_as_a_person():
    """WotW's narrator row claims "first" and "person": "Each person in the picture
    is a different man" would put the narrator in every shot it opens."""
    names = {"first": "narrator", "person": "narrator", "boy": "newspaper_boy", "ogilvy": "ogilvy"}
    assert scene_cast.named("Each person at the first rank, a boy, and Ogilvy", names) == ["ogilvy"]
