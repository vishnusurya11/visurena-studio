"""The grid prompt's fixed wording says what the picture holds, and each fault class is a lint rule (craft ruling A21).

The wave's census over ep01's 22 drawn grid prompts (docs: r1_storyboard_prompts D6): a street called "this exact
room ... the same walls, furniture, windows" (16), "The air is thick with thin fog" (22), a doubled stop at a
template join (7), Hyde's coat deleted from his chest-up binding while the panel grips his "coat collar" (s09:
BELOW_CHEST read "knee" in "knee-length ... coat" and dropped the garment), "a reference sheet of one man seen from
several angles" on a staged one-figure crop (every binding), the walk-on clause on the named pair (night_door:
"The two men are two different individuals"), and "head and shoulders fill the centre" under a FOCUS on a fist.
Fixtures: tests/fixtures/craft/grids/ (delivered ep01 prompts), tests/fixtures/shot_framework/refs/looks.json."""
from __future__ import annotations

import json
from pathlib import Path

from studio import book_look, grid_lint
from studio import storyboard_grid as sg

FIX = Path(__file__).parent / "fixtures"
GRIDS = FIX / "craft" / "grids"


def delivered(name: str) -> str:
    return (GRIDS / f"{name}.txt").read_text(encoding="utf-8")


def hyde() -> dict:
    looks = json.loads((FIX / "shot_framework" / "refs" / "looks.json").read_text(encoding="utf-8"))
    layers = looks["characters"]["edward_hyde"]["looks"]["base"]["layers"]
    return {"name": "Edward Hyde", "ref": 2, "noun": "man", "clothes": sg.clothes_of(layers)}


def shot(body: str = "A green door in a blank wall.", size: str = "MEDIUM CLOSE") -> dict:
    return {"size": size, "body": body, "cut": "the whole door", "who": [], "extras": 0}


def test_hydes_chest_up_binding_keeps_his_coat():
    said = sg._binding(hyde(), chest=True)
    assert "wide floppy brim; black double-breasted coat, white shirt." in said


def test_a_chest_up_binding_still_drops_what_is_below_the_chest():
    assert sg._items({"clothes": ["black trousers, black boots", "grey coat"]}, False, True) == ["grey coat"]


def test_the_binding_says_the_staged_crop_is_one_man():
    said = sg._binding(hyde())
    assert "<image2> shows one man, drawn exactly once in each picture." in said
    assert "several angles" not in said


def test_an_outdoor_room_is_a_place_not_furniture():
    said = sg.grid_prompt_v2([shot()], 1, 1, ([], "a by-street"), [], 1, room=1, outdoors=True)
    assert "this exact place" in said and "furniture" not in said


def test_an_indoor_room_keeps_its_walls():
    assert "furniture" in sg.grid_prompt_v2([shot()], 1, 1, ([], "a study"), [], 1, room=1)


def test_a_described_place_ending_in_a_stop_is_said_with_one():
    said = sg.grid_prompt_v2([shot()], 1, 1, ([1], "A door in a recess at the right."), [], 1)
    assert ".." not in said


def test_the_air_holds_the_atmosphere():
    said = book_look.ATMOSPHERE_AIR.format(atmosphere="thin fog, haze")
    assert said.startswith(" The air holds thin fog, haze") and "thick with" not in said


def test_the_named_pair_gets_no_walk_on_clause():
    assert sg.varied_group("the two men face each other under the lamp", named=2) == ""
    assert sg.varied_group("three labourers lean on the rail", named=2).startswith("The three labourers")


def test_a_fist_focus_states_only_the_cut():
    body = "THE FOCUS OF THE PICTURE IS the man's black-gloved fist on the coat collar at the CENTRE."
    assert sg.framing("medium_close", True, body) == "the panel cuts the figure at the middle of the chest"


def test_a_face_focus_keeps_the_whole_cut():
    body = "THE FOCUS OF THE PICTURE IS the lawyer's gaunt, unsmiling face at the CENTRE."
    assert sg.framing("close", True, body) == sg.PEOPLED_CUT["close"]


def rules(text: str, outdoors: bool = False) -> set[str]:
    return {f.split()[0] for f in grid_lint.faults(text, outdoors=outdoors)}


def test_the_lint_names_every_class_on_the_delivered_s09():
    assert {"WORN", "SHEET", "AIR", "FOCUS"} <= rules(delivered("ep01_grid_night_corner_1x1_s09"))


def test_the_lint_names_the_twin_clause_and_the_outdoor_room():
    text = delivered("ep01_grid_night_door_2x2")
    assert "TWIN" in rules(text)
    room = "<image3> is this exact room, already drawn: every panel is set in it, with the same walls."
    assert "ROOM" in rules(room, outdoors=True) and "ROOM" not in rules(room)


def test_the_lint_names_a_double_stop():
    assert "STOP" in rules("The picture is set at <image1>: a recess at the right..")
    assert "STOP" not in rules("He waits... then turns.")
