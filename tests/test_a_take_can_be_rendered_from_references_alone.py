"""A take built from the LOCATION PLATE and the CAST CARDS, with no storyboard cell.

WHY THIS MODE EXISTS.  On 2026-09-17 the paid image API that draws the storyboard
sheets had no credits left, so no episode can have its cells drawn.  Everything
upstream of the sheets -- the plan, the plates, the cast cards, the measured voice
-- is free and already on disk.  `--from-refs` runs the experiment that asks
whether those alone carry a take: the model is shown WHO is in it and WHERE it is,
and told the shot in words.

It is not the normal path and it never becomes one by default.  `FROM_REFS` is
off unless the flag is on the command line, and with it off every assertion the
existing files make about the reference order, the pinned cells and the strip
still holds.

THE ONE RULE THAT CHANGES: the plate is ALWAYS staged here.  `places_the_plate`
withholds it from a take of nothing but tight cells, and that rule answers a
fault which needs cells to happen -- the plate leaked because it was the only
WHOLE picture beside a close-up cell (episode 2, 13 of 14 foreign frames).  With
no cells at all, obeying it would leave a close-only take with nothing but faces,
and an insert take with no readable face with ZERO references, which `graph_for`
cannot stage (`paths[0]` is read unconditionally).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from studio import episode_home, h3_anchors

spec = importlib.util.spec_from_file_location(
    "takes_r2v", ROOT / "scripts" / "episode" / "takes_r2v.py")
tr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tr)

from tests.test_episode_spec import episode as plan_episode  # noqa: E402


def world(tmp_path):
    """A book with one cast card and one plate, and the ep01 boards beside them.

    No cell is drawn anywhere under it -- that is the whole point of the mode."""
    book = tmp_path / "book"
    (book / "refs" / "characters").mkdir(parents=True)
    (book / "refs" / "characters" / "char-a.png").write_bytes(b"")
    boards = episode_home.boards_dir(book, 1)
    (boards / "plates").mkdir(parents=True)
    (boards / "plates" / "plate_lab.png").write_bytes(b"")
    episode_home.write_json(book / "refs" / "refs.json",
                            {"refs": [{"entity_id": "a", "kind": "character",
                                       "physical": "A small man."}]})
    return book, boards


def take_of_shot_zero() -> dict:
    return {"shots": [0], "placed": [{"index": 0, "t_start": 0.0}], "t_start": 0.0,
            "frames": 100, "seconds": 4.17}


MEASURED = {0: {"at": 0.5, "seconds": 3.0, "rel_path": "audio/ep01/lines/L000.wav"}}


@pytest.fixture
def built(monkeypatch):
    """`ro.build` recorded, never run: the prompt builder is another agent's file
    and it spends nothing, but this mode is defined by WHAT IT IS TOLD."""
    said = {}

    def fake(*args, **kwargs):
        said.update(kwargs)
        said["args"] = args
        return "PROMPT"

    monkeypatch.setattr(tr.ro, "build", fake)
    return said


class TestTheSwitch:
    def test_the_mode_is_off_until_the_flag_asks_for_it(self):
        """The normal path is the default: an ordinary command line must not
        silently render an episode without its storyboard."""
        assert tr.FROM_REFS is False
        tr._set_from_refs(["takes_r2v.py", "book", "1"])
        assert tr.FROM_REFS is False

    def test_the_flag_turns_it_on(self, monkeypatch):
        monkeypatch.setattr(tr, "FROM_REFS", False)
        tr._set_from_refs(["takes_r2v.py", "book", "1", "--from-refs"])
        assert tr.FROM_REFS is True
        tr._set_from_refs(["takes_r2v.py", "book", "1"])   # left as we found it

    def test_it_reads_its_own_flag_and_not_the_end_pin_one(self, monkeypatch):
        """`--ends` and `--from-refs` are separate controls parsed side by side."""
        monkeypatch.setattr(tr, "FROM_REFS", True)
        tr._set_from_refs(["takes_r2v.py", "book", "1", "--ends"])
        assert tr.FROM_REFS is False


class TestTheReferences:
    def test_they_are_the_cast_sheets_then_the_plate(self, tmp_path):
        book, boards = world(tmp_path)
        refs = tr.refs_from_cards(book, boards, ["a"], "lab", "indoor", ["medium"])
        assert [p.name for p in refs] == ["char-a.png", "plate_lab.png"]

    def test_a_take_of_nothing_but_closes_stages_its_face_alone(self, tmp_path):
        """MEASURED on ep14's first references-only run: staging the plate on a
        tight take put the room at frame 0 -- T20 (medium close) opened on it at
        cosine 0.999 and dissolved into an invented library, T21 (insert) opened
        on it and hard-cut into the shot at frame 14. That is episode 2's fault
        with no cell in it, and `places_the_plate` is the rule that answers it."""
        book, boards = world(tmp_path)
        refs = tr.refs_from_cards(book, boards, ["a"], "lab", "", ["close", "insert"])
        assert [p.name for p in refs] == ["char-a.png"]

    def test_a_take_with_no_readable_face_still_stages_one_picture(self, tmp_path):
        """An insert take declares no face.  Zero references is an IndexError in
        `graph_for`, which reads `paths[0]` before it counts anything."""
        book, boards = world(tmp_path)
        assert [p.name for p in tr.refs_from_cards(book, boards, [], "lab", "", ["insert"])] == \
            ["plate_lab.png"]

    def test_the_faces_come_before_the_plate_in_first_appearance_order(self, tmp_path):
        book, boards = world(tmp_path)
        refs = tr.refs_from_cards(book, boards, ["b", "a"], "lab", "", ["wide"])
        assert [p.name for p in refs] == ["char-b.png", "char-a.png", "plate_lab.png"]


class TestTheCard:
    def test_it_pins_nothing_and_names_only_the_sheets_and_the_plate(self, tmp_path, monkeypatch, built):
        book, _ = world(tmp_path)
        monkeypatch.setattr(tr, "FROM_REFS", True)
        monkeypatch.setattr(tr, "reference_strip",
                            lambda *a: pytest.fail("the strip opens every cell; there are none"))
        card = tr.card(book, plan_episode(), 1, take_of_shot_zero(), MEASURED)
        assert card["anchors"] == []
        # the fixture shot is a CLOSE, so its plate is dropped (see refs_from_cards)
        assert card["refs"] == ["char-a.png"]

    def test_it_does_not_refuse_the_cells_that_were_never_drawn(self, tmp_path, monkeypatch, built):
        """The missing-cell refusal is the gate this mode exists to walk past."""
        book, _ = world(tmp_path)
        monkeypatch.setattr(tr, "FROM_REFS", True)
        card = tr.card(book, plan_episode(), 1, take_of_shot_zero(), MEASURED)
        assert card["prompt"] == "PROMPT"

    def test_everything_that_is_not_a_picture_is_unchanged(self, tmp_path, monkeypatch, built):
        book, _ = world(tmp_path)
        monkeypatch.setattr(tr, "FROM_REFS", True)
        card = tr.card(book, plan_episode(), 1, take_of_shot_zero(), MEASURED)
        assert card["index"] == 0 and card["shots"] == [0] and card["frames"] == 100
        assert card["seconds"] == round(100 / tr.FPS, 2) and card["lane"] == "dialogue"
        assert card["audio"] == [("L000.wav", 0.5)] and card["faces"] == ["a"]

    def test_the_mode_line_does_not_claim_a_cell_it_never_staged(self, tmp_path, monkeypatch, built):
        book, _ = world(tmp_path)
        monkeypatch.setattr(tr, "FROM_REFS", True)
        card = tr.card(book, plan_episode(), 1, take_of_shot_zero(), MEASURED)
        assert "no storyboard cell" in card["mode"] and "nothing pinned" in card["mode"]
        assert "pinned cell" not in card["mode"] and "weak_reference" not in card["mode"]
        assert "--from-refs" in card["mode"]

    def test_the_normal_path_still_refuses_a_cell_that_is_not_on_disk(self, tmp_path, monkeypatch, built):
        """With the switch off the gate is exactly where it was."""
        book, boards = world(tmp_path)
        (boards / "cells").mkdir(parents=True)
        monkeypatch.setattr(tr, "FROM_REFS", False)
        monkeypatch.setattr(tr, "reference_strip", lambda *a: boards / "ref_take_00.png")
        with pytest.raises(SystemExit, match="sequence cell Q00_0.png missing"):
            tr.card(book, plan_episode(), 1, take_of_shot_zero(), MEASURED)


class TestWhatThePromptIsTold:
    def test_the_plate_is_staged_and_the_cells_are_not(self):
        assert tr.staged_facts(["medium"], from_refs=True, faces=["a"]) == {"has_plate": True,
                                                                           "cells_staged": False}

    def test_a_tight_take_with_a_face_is_told_its_plate_is_not_staged(self):
        assert tr.staged_facts(["close"], from_refs=True, faces=["a"]) == {"has_plate": False,
                                                                          "cells_staged": False}

    def test_a_faceless_take_is_told_its_plate_is_staged(self):
        """It is: `refs_from_cards` keeps it, because nothing else would be."""
        assert tr.staged_facts(["insert"], from_refs=True, faces=[]) == {"has_plate": True,
                                                                        "cells_staged": False}

    def test_the_normal_path_still_asks_whether_a_cell_places_the_plate(self):
        """And says nothing about cells: `build`'s own default is the staged one,
        so the seven built episodes are told exactly what they were told before."""
        assert tr.staged_facts(["close", "insert"], from_refs=False) == {"has_plate": False}
        assert tr.staged_facts(["medium", "close"], from_refs=False) == {"has_plate": True}

    def test_the_card_hands_those_facts_to_the_builder(self, tmp_path, monkeypatch, built):
        book, _ = world(tmp_path)
        monkeypatch.setattr(tr, "FROM_REFS", True)
        tr.card(book, plan_episode(), 1, take_of_shot_zero(), MEASURED)
        assert built["has_plate"] is False and built["cells_staged"] is False
        assert built["refs"] == 1


class TestThePins:
    def test_every_segment_is_pinned_at_its_own_start_frame(self):
        ep = plan_episode()
        anchors = tr.cell_anchors([ep.shot(0)], take_of_shot_zero())
        assert anchors == [("Q00_0.png", 0)]

    def test_a_cell_pinned_twice_is_refused(self):
        with pytest.raises(SystemExit, match="pinned twice"):
            tr.refuse_double_pins([("Q00_0.png", 0), ("Q00_0.png", 40)], 0)

    def test_a_single_pin_of_each_cell_passes(self):
        assert tr.refuse_double_pins([("Q00_0.png", 0), ("Q00_1.png", 40)], 0) is None

    def test_a_missing_cell_is_named_with_the_step_that_draws_it(self, tmp_path):
        with pytest.raises(SystemExit, match="run seq_boards.py first"):
            tr.refuse_missing_cells(tmp_path, [("Q00_0.png", 0)], 0)

    def test_cells_on_disk_pass(self, tmp_path):
        (tmp_path / "Q00_0.png").write_bytes(b"")
        assert tr.refuse_missing_cells(tmp_path, [("Q00_0.png", 0)], 0) is None


class TestTheStaleCellGate:
    def test_a_cell_from_an_older_numbering_still_stops_the_normal_run(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tr, "FROM_REFS", False)
        monkeypatch.setattr(tr.sq, "stale_cells", lambda _b: ["Q19_0E.png"])
        with pytest.raises(SystemExit, match="Q19_0E.png"):
            tr.refuse_stale_cells(tmp_path)

    def test_the_no_cell_mode_does_not_ask(self, tmp_path, monkeypatch):
        """A gate calibrated on a world where cells are staged.  Here none is, so
        no cell on disk can reach the render and an old one refuses nothing."""
        monkeypatch.setattr(tr, "FROM_REFS", True)
        monkeypatch.setattr(tr.sq, "stale_cells",
                            lambda _b: pytest.fail("no cell is staged; none is judged"))
        assert tr.refuse_stale_cells(tmp_path) is None

    def test_a_clean_board_passes(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tr, "FROM_REFS", False)
        monkeypatch.setattr(tr.sq, "stale_cells", lambda _b: [])
        assert tr.refuse_stale_cells(tmp_path) is None


class TestTheGraph:
    def test_a_take_with_no_anchors_still_gets_its_audio_guide(self):
        """`graph_for` hands `c["anchors"]` straight to `h3_anchors.anchored`.
        With no cell pinned the chain is the audio guide alone, and the guider
        must still be rewired to it -- an unanchored wav is a silent take."""
        graph = {"1": {"class_type": "MiniMaxH3ReferenceToVideo", "inputs": {}},
                 "2": {"class_type": "VAELoader", "inputs": {}},
                 "3": {"class_type": "VAELoader", "inputs": {}},
                 "4": {"class_type": "BasicGuider", "inputs": {"conditioning": ["1", 0]}}}
        out = h3_anchors.anchored(graph, [], ("voice_00.wav", 0))
        guide = out[out["4"]["inputs"]["conditioning"][0]]
        assert guide["class_type"] == "MiniMaxH3AddGuide"
        assert guide["inputs"]["positive"] == ["1", 0]   # straight off the base node
        assert "audio" in guide["inputs"]
