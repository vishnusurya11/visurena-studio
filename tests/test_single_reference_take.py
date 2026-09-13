"""A take with ONE reference stages one picture, not the same one twice.

Episode 3's T15 is a single insert on a blood smear: no face is readable, and
the take has no cell wide enough to place a plate against, so its whole
reference list is one cell. `graph_for` assumed at least two and died on
`paths[1]` with IndexError.

Staging `paths[0]` into both template slots would run, and would be wrong: the
prompt defines `<Picture 1>` alone, and the graph would hand the model the same
cell twice as if it were two pictures. The second slot is removed instead.
"""
import importlib.util
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location("takes_r2v", "scripts/episode/takes_r2v.py")
tr = importlib.util.module_from_spec(spec)
sys.modules["takes_r2v"] = tr
spec.loader.exec_module(tr)


def graph():
    """The two staged slots exactly as the template wires them."""
    return {
        "18": {"class_type": "LoadImage", "inputs": {"image": "a.png"}},
        "19": {"class_type": "LoadImage", "inputs": {"image": "b.png"}},
        "8": {"class_type": "MiniMaxH3ReferenceToVideo",
              "inputs": {"ref_image_size": "match",
                         "ref_images.ref_image_0": ["18", 0],
                         "ref_images.ref_image_1": ["19", 0]}},
    }


def test_the_second_slot_and_its_loader_are_removed():
    got = tr.drop_second_slot(graph(), "8")
    assert "ref_images.ref_image_1" not in got["8"]["inputs"]
    assert "19" not in got


def test_the_first_slot_is_untouched():
    got = tr.drop_second_slot(graph(), "8")
    assert got["8"]["inputs"]["ref_images.ref_image_0"] == ["18", 0]
    assert got["18"]["inputs"]["image"] == "a.png"
    assert got["8"]["inputs"]["ref_image_size"] == "match"


def test_calling_it_twice_is_harmless():
    """A graph that has already lost its second slot is left alone."""
    once = tr.drop_second_slot(graph(), "8")
    assert tr.drop_second_slot(once, "8") == once
