"""An over-the-shoulder's near man, seen only from behind, is drawn from words, not his sheet (ep06 retro A).

Jekyll ep06 shots 24/25: "over the near shoulder of the lawyer toward the butler"; the grid staged Utterson's
face sheet AND Poole's, and the drawer copied Utterson into the butler's slot -- four draws of panel 24 gave one
right.  A man whose every appearance in the grid is his back or shoulder shows no face, so his face sheet is
nothing but a second face to copy; his hat, hair and coat are said in words (the binding a sheetless person
already gets) and the far man's sheet is the only face in the picture."""
from __future__ import annotations

from types import SimpleNamespace

from studio import back_view

SHOT_25 = SimpleNamespace(
    index=25, faces=["gabriel_john_utterson", "poole"], cuts=[],
    frame="Medium close over the near shoulder of the lawyer (lank grey hair, white at the sides) toward the butler "
          "on the threshold as he reports on his master.",
    at_rest="THE FOCUS OF THE PICTURE IS the butler's face at the CENTRE. The lawyer's black shoulder and the back "
            "of his grey hair fill the RIGHT third in the foreground.",
    end="The butler's face at the CENTRE, the lawyer's shoulder at the RIGHT third.", motion="", view="")
LAWYER = ["the lawyer", "Mr. Utterson", "utterson"]
BUTLER = ["the butler", "Poole", "poole"]


def test_the_near_shoulder_of_an_over_the_shoulder_is_back_only():
    assert back_view.back_only(LAWYER, [SHOT_25]) is True


def test_the_man_the_camera_looks_at_is_not():
    assert back_view.back_only(BUTLER, [SHOT_25]) is False


def test_a_man_seen_from_behind_in_one_cell_and_facing_in_another_keeps_his_sheet():
    facing = SimpleNamespace(index=26, faces=["gabriel_john_utterson"], cuts=[], frame="Close on the lawyer's face as he listens.",
                             at_rest="The lawyer's face at the CENTRE.", end="", motion="", view="")
    assert back_view.back_only(LAWYER, [SHOT_25, facing]) is False


def test_a_man_named_nowhere_is_not_back_only():
    assert back_view.back_only(["the doctor"], [SHOT_25]) is False


def test_from_behind_and_back_of_the_head_read_as_back_views():
    shot = SimpleNamespace(index=1, faces=["x"], cuts=[], frame="The doctor, seen from behind, at the window.",
                           at_rest="The back of the doctor's head at the LEFT.", end="", motion="", view="")
    assert back_view.back_only(["the doctor"], [shot]) is True


def test_the_grid_stages_no_sheet_for_a_back_only_man(monkeypatch, tmp_path):
    from scripts.episode import grids
    monkeypatch.setattr(grids, "people_in", lambda book, shots: ["gabriel_john_utterson", "poole"])
    monkeypatch.setattr(grids, "sheet_of", lambda book, w, look: tmp_path / f"{w}.png")
    monkeypatch.setattr(grids.cast_refs, "row", lambda book, w: {"name": w})
    monkeypatch.setattr(grids.continuity, "look_for", lambda setup, w, row: None)
    from studio import scene_cast
    monkeypatch.setattr(scene_cast, "pick", lambda who, shots, n: who)
    monkeypatch.setattr(grids, "person", lambda book, name, setup, aliases, names: ({"ref": None, "name": name, "entity": name},
                                                                                    tmp_path / f"{name}.png"))
    monkeypatch.setattr(grids, "name_tokens", lambda book: [])
    aliases = {"gabriel_john_utterson": ["the lawyer"], "poole": ["the butler"]}
    people, slots = grids.cast_of(tmp_path, [SHOT_25], aliases=aliases)
    staged = {p["entity"]: p["ref"] for p in people}
    assert staged == {"gabriel_john_utterson": None, "poole": 1} and list(slots) == ["101"]
