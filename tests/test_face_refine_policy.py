"""The wide-shot face refine (owner 2026-10-17: "I like face improvements a lot in
wide shots, go ahead"): which takes are refined, who each face is, what it costs
on the episode clock, the prompt each crop renders with, and the gate that keeps
a refined crop or falls back to the unrefined take.  Pure policy: no file, no
GPU, no model (studio/face_refine.py)."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from studio import face_refine as fr
from studio.run_budget import EPISODE_SHARES, Budget

H = 768


def dq(passed=True, face=None):
    gates = [{"name": "face-at-end", "value": face, "ok": True, "hard": False}]
    return {"passed": passed, "gates": gates}


# ---- selection -----------------------------------------------------------------------

def test_a_face_at_end_share_is_read_in_render_pixels():
    assert fr.face_px(dq(face=0.05), H) == pytest.approx(38.4)


def test_an_unmeasured_face_has_no_pixels():
    assert fr.face_px(dq(face=None), H) is None and fr.face_px({}, H) is None


def test_a_wide_or_full_shot_wants_the_refine_whatever_its_face_measured():
    assert fr.wants(["wide"], 200.0) and fr.wants(["full"], None)


def test_a_closer_shot_wants_it_only_under_sixty_pixels():
    assert fr.wants(["medium"], 56.0) and not fr.wants(["medium"], 61.0)
    assert not fr.wants(["medium_close"], None)


def test_an_insert_never_wants_it():
    assert not fr.wants(["insert"], 20.0)


def test_a_take_is_selected_only_with_faces_and_a_passed_dq():
    card = {"index": 0, "shots": [0], "faces": ["utterson"]}
    assert fr.eligible(card, ["wide"], dq(), H)
    assert not fr.eligible(card, ["wide"], dq(passed=False), H)
    assert not fr.eligible(card | {"faces": []}, ["wide"], dq(), H)
    assert not fr.eligible(card, ["wide"], None, H)


def test_selection_reads_every_shot_of_the_take():
    cards = [{"index": 0, "shots": [0], "faces": ["a"]}, {"index": 1, "shots": [1, 2], "faces": ["a"]},
             {"index": 3, "shots": [3], "faces": ["a"]}]
    sizes = {0: "wide", 1: "medium", 2: "full", 3: "medium_close"}
    dqs = {0: dq(), 1: dq(), 3: dq(face=0.2)}
    assert fr.selected(cards, sizes, dqs, H) == [0, 1]


# ---- the clock -----------------------------------------------------------------------

def test_a_refine_is_priced_at_110_s_per_face_per_192_frames():
    assert fr.price(2, 192) == pytest.approx(220.0)
    assert fr.price(1, 96) == pytest.approx(55.0)


def test_no_faces_cost_nothing():
    assert fr.price(0, 192) == 0.0


def budget_at(spent_s: float) -> Budget:
    now = [0.0]
    b = Budget(5 * 3600, EPISODE_SHARES, clock=lambda: now[0], limit=6 * 3600)
    b.start("09")
    now[0] = spent_s
    return b


def test_a_refine_runs_when_the_reserve_holds_it_and_the_checks():
    assert not fr.cut(budget_at(3600.0), "09", 600.0)


def test_the_refine_is_cut_before_any_check_is():
    owed = budget_at(0).owed_after("09")
    b = budget_at(6 * 3600 - owed - 600.0)          # room for a 550 s check, not for a refine too
    assert fr.cut(b, "09", 300.0)
    assert not b.checks_cut("09", 550.0), "the same clock still runs the measuring check"


def test_no_budget_never_cuts():
    assert not fr.cut(None, "09", 10_000.0)


# ---- the cast a take staged ------------------------------------------------------------

PROMPT = ("subject_definitions:\n"
          "<Subject 1> is Mr. Utterson in <Picture 1>: Lank grey hair; black bowler hat. <Picture 1> defines this man alone; each shot keeps.\n"
          "<Subject 2> is the child in <Picture 2>: Fair hair in two plaits. <Picture 2> defines this girl alone.\n"
          "<Audio 1> is the take's complete audio track.\n\n"
          "detailed_description:\nHand-drawn 2D gothic anime, London, 1885.\n"
          "[Shot 1] The shot opens. <Subject 1> stands at the LEFT third. <Subject 2> waits at the RIGHT edge. <Subject 1> walks on to the RIGHT. "
          "<Subject 1> and <Subject 2> meet at the CENTRE.\n\noverall_soundscape: Open air.")


def test_subjects_are_read_off_the_card_prompt():
    got = fr.subjects(PROMPT)
    assert [(k, s.name, s.picture) for k, s in got.items()] == [(1, "Mr. Utterson", 1), (2, "the child", 2)]
    assert got[2].said.startswith("Fair hair in two plaits.")


def test_the_cast_names_each_subject_by_its_sheet_folder():
    refs = ["refs/characters/gabriel_john_utterson/sheet_front.png", "refs/characters/child/sheet_front.png",
            "episodes/ep01/storyboard/h3/shot_00.png"]
    cast = fr.cast_of(PROMPT, refs)
    assert [(p.who, p.sheet) for p in cast] == [("gabriel_john_utterson", refs[0]), ("child", refs[1])]


def test_a_subject_whose_picture_is_no_sheet_is_left_out():
    assert fr.cast_of(PROMPT, ["episodes/ep01/storyboard/h3/shot_00.png", "x.png"]) == []


def test_a_pronoun_follows_the_definition():
    cast = fr.cast_of(PROMPT, ["refs/characters/u/s.png", "refs/characters/c/s.png"])
    assert [fr.pronoun(p.said) for p in cast] == ["his", "her"]


def test_positions_come_only_from_a_sentence_naming_one_subject():
    assert fr.positions(PROMPT) == {1: 0.2, 2: 0.8}


def test_a_direction_of_travel_is_no_position():
    said = "detailed_description: <Subject 1> walks from LEFT to RIGHT. <Subject 2> runs on to the LEFT."
    assert fr.positions(said) == {}


def test_the_style_line_is_the_takes_own():
    assert fr.style_line(PROMPT) == "Hand-drawn 2D gothic anime, London, 1885."


# ---- matching a track to a person -------------------------------------------------------

def test_identity_and_position_both_count():
    assert fr.match_score(0.3, 0.2, 0.2) > fr.match_score(0.3, 0.8, 0.2)
    assert fr.match_score(0.3, 0.5, None) == pytest.approx(0.3)


def test_tracks_get_the_assignment_with_the_best_total():
    scores = {(0, "a"): 0.9, (0, "b"): 0.8, (1, "a"): 0.85, (1, "b"): 0.1}
    assert fr.assign(scores, [0, 1], ["a", "b"]) == {0: "b", 1: "a"}


def test_more_tracks_than_people_leaves_the_weakest_unrefined():
    scores = {(0, "a"): 0.2, (1, "a"): 0.7, (2, "a"): 0.4}
    assert fr.assign(scores, [0, 1, 2], ["a"]) == {1: "a"}


def test_a_match_under_the_floor_is_never_refined():
    assert fr.assign({(0, "a"): fr.MATCH_FLOOR - 0.01}, [0], ["a"]) == {}


# ---- the crop's prompt ---------------------------------------------------------------------

def test_the_crop_prompt_defines_only_its_one_person():
    p = fr.cast_of(PROMPT, ["refs/characters/u/s.png", "refs/characters/c/s.png"])[1]
    text = fr.crop_prompt(p, "Hand-drawn 2D gothic anime.", 3.75)
    assert "<Subject 1> is the child in <Picture 1>: Fair hair in two plaits." in text
    assert "<Subject 2>" not in text and "Mr. Utterson" not in text
    assert "One 3.75-second close-up" in text and "her head" in text
    assert "Hand-drawn 2D gothic anime." in text


# ---- the gate ------------------------------------------------------------------------------

def measures(**kw):
    base = dict(id_src=0.40, id_ref=0.45, seam=4.0, flick_src=3.0, flick_ref=3.1, faces_src=6, faces_ref=6)
    return fr.Measures(**(base | kw))


def test_a_refine_that_holds_every_measure_is_kept():
    assert fr.decide(measures()) == (True, "kept")


def test_an_identity_drop_falls_back():
    kept, why = fr.decide(measures(id_ref=0.40 - fr.ID_DROP - 0.01))
    assert not kept and "identity" in why


def test_a_seam_falls_back():
    kept, why = fr.decide(measures(seam=fr.SEAM_MAX + 0.1))
    assert not kept and "seam" in why


def test_new_flicker_falls_back():
    kept, why = fr.decide(measures(flick_ref=3.0 * fr.FLICKER_RATIO + fr.FLICKER_SLACK + 0.1))
    assert not kept and "flicker" in why


def test_a_changed_face_count_falls_back():
    assert not fr.decide(measures(faces_ref=7))[0]
    assert not fr.decide(measures(faces_ref=4))[0]


def test_one_missed_detection_is_not_a_count_change():
    assert fr.decide(measures(faces_ref=5))[0]


def test_an_identity_nobody_could_read_is_not_a_drop():
    assert fr.decide(measures(id_src=None, id_ref=None))[0]


def test_every_refusal_is_named():
    kept, why = fr.decide(measures(seam=99.0, faces_ref=0))
    assert not kept and "seam" in why and "faces" in why
