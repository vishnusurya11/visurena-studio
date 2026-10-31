"""One-picture edits run on Qwen-Image 2.1 (owner 2026-10-30: "make them qwen 2.1").

The place-state edit (scripts/refs/places.py) and the room emptier (step 07) ran on Qwen-Image-Edit 2511 with its
Lightning LoRA while every grid already drew on Qwen-Image 2.1.  Both now build the grids' own workflow with one
reference slot: the picture is <image1>, nothing else is staged (an unused slot holds ComfyUI's example doll), the
canvas keeps the source's size on the model's 16 px grid, and cfg stays 1.0 like the grids."""
from pathlib import Path

from PIL import Image

from studio import qwen21_edit as qe


def source(tmp_path, size=(1256, 840)) -> Path:
    path = tmp_path / "room.png"
    Image.new("RGB", size, (20, 20, 20)).save(path)
    return path


def test_the_graph_is_the_qwen_2_1_workflow_with_one_slot(tmp_path):
    g = qe.graph("Change only: every person is gone.", source(tmp_path), seed=7, prefix="t", staged="room_ab.png")
    assert g["1"]["inputs"]["unet_name"] == "qwen_image_2.1_int8_convrot.safetensors"
    loads = [k for k, n in g.items() if n.get("class_type") == "LoadImage"]
    assert loads == ["101"] and g["101"]["inputs"]["image"] == "room_ab.png"


def test_the_prompt_names_its_one_picture(tmp_path):
    g = qe.graph("Change only: every person is gone.", source(tmp_path), seed=7, prefix="t", staged="x.png")
    said = g["5"]["inputs"]["prompt"]
    assert said.startswith("Edit <image1>.") and said.endswith("every person is gone.")


def test_the_canvas_keeps_the_source_size_on_the_16px_grid(tmp_path):
    g = qe.graph("p", source(tmp_path, (1256, 840)), seed=7, prefix="t", staged="x.png")
    assert (g["6"]["inputs"]["width"], g["6"]["inputs"]["height"]) == (1248, 832)


def test_the_sampler_matches_the_grids(tmp_path):
    g = qe.graph("p", source(tmp_path), seed=11, prefix="t", staged="x.png")
    assert g["7"]["inputs"]["seed"] == 11 and g["7"]["inputs"]["cfg"] == 1.0 and g["5"]["inputs"]["negative_prompt"] == ""


def test_both_callers_use_it():
    from scripts.episode import step_07_board
    from scripts.refs import places
    assert step_07_board.EDIT == places.EDIT == qe.WORKFLOW
