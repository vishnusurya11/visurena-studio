"""An unused LoadImage slot is not empty -- it holds ComfyUI's `example.png`.

MEASURED 2026-09-20. The owner asked why a doll in a pink dress with yellow
butterfly wings kept walking into the War of the Worlds storyboards. It was
not a word in any prompt. The multi-reference Qwen graph ships SIX LoadImage
nodes, every one of them defaulted to `example.png` -- which IS that doll --
and the driver cleared only the first three. Slots 4, 5 and 6 stayed wired
into the text encoder, so a grid staged with one location wide was read by
the encoder as one common and three dolls.

Three prompt theories died against this: the word "crown", the seed, and the
empty-cast clause. None of them could have been right. The doll's own
background is a green mound against blue sky, which is why it surfaced on the
panels that described a hummock -- composition, not prose.
"""
from __future__ import annotations

import pytest

from studio.ref_slots import stage_only


def graph_with(n_slots: int) -> dict:
    """The shape of image_qwen_image_2_1_edit_multi: N LoadImage, one encoder."""
    graph = {"5": {"class_type": "TextEncodeQwenImage21", "inputs": {"prompt": ""}}}
    for i in range(1, n_slots + 1):
        graph[str(100 + i)] = {"class_type": "LoadImage", "inputs": {"image": "example.png"}}
        graph["5"]["inputs"][f"images.image_{i}"] = [str(100 + i), 0]
    return graph


def test_every_unused_slot_goes_not_just_the_first_three():
    graph = stage_only(graph_with(6), {"101": "wide_night.png"})
    left = [k for k in graph if graph[k].get("class_type") == "LoadImage"]
    assert left == ["101"], f"unused LoadImage survived: {left}"


def test_the_encoder_stops_reading_every_slot_it_no_longer_has():
    graph = stage_only(graph_with(6), {"101": "wide_night.png"})
    reads = [k for k in graph["5"]["inputs"] if k.startswith("images.image_")]
    assert reads == ["images.image_1"]


def test_no_example_png_survives_anywhere():
    graph = stage_only(graph_with(6), {"101": "wide_night.png", "102": "sheet.png"})
    held = [v["inputs"]["image"] for v in graph.values()
            if v.get("class_type") == "LoadImage"]
    assert "example.png" not in held


def test_a_slot_the_graph_does_not_have_is_refused():
    with pytest.raises(KeyError):
        stage_only(graph_with(3), {"104": "wide.png"})


def test_the_staged_slots_keep_their_images():
    graph = stage_only(graph_with(6), {"101": "a.png", "103": "b.png"})
    assert graph["101"]["inputs"]["image"] == "a.png"
    assert graph["103"]["inputs"]["image"] == "b.png"
