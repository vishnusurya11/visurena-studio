"""A one-picture edit on Qwen-Image 2.1 (owner 2026-10-30: "make them qwen 2.1").

The grids' own workflow (`image_qwen_image_2_1_edit_multi`) with one reference slot: the picture is <image1>, every
other LoadImage is dropped (an unused slot holds ComfyUI's example doll and the encoder reads it), the canvas keeps
the source's size on the model's 16 px grid, and the sampler runs as the grids do (25 steps, cfg 1.0, no negative).
Callers: the place-state edit (scripts/refs/places.py) and the room emptier (step 07); both ran on Qwen-Image-Edit
2511 until 2026-10-30."""
from __future__ import annotations

import shutil
from pathlib import Path

WORKFLOW = "image_qwen_image_2_1_edit_multi"
CLIP = "qwen3vl_8b_fp8_scaled.safetensors"
"""The grids' encoder (scripts/episode/grids.CLIP)."""
SLOT = "101"
STEPS, CFG, GRID = 25, 1.0, 16


def canvas(source: Path) -> tuple[int, int]:
    from PIL import Image
    with Image.open(source) as im:
        w, h = im.size
    return w // GRID * GRID, h // GRID * GRID


def graph(prompt: str, source: Path, seed: int, prefix: str, staged: str) -> dict:
    """The edit's graph: `staged` is the source's name in ComfyUI's input folder."""
    from studio.comfy import load_workflow
    from studio.ref_slots import stage_only
    template, _ = load_workflow(WORKFLOW)
    g = {k: v for k, v in template.items()}
    g["3"]["inputs"]["clip_name"] = CLIP
    stage_only(g, {SLOT: staged})
    g["5"]["inputs"].update(prompt=f"Edit <image1>. {prompt}", negative_prompt="", resolution=1024)
    width, height = canvas(source)
    g["6"]["inputs"].update(width=width, height=height)
    g["7"]["inputs"].update(seed=seed, steps=STEPS, cfg=CFG)
    g["9"]["inputs"]["filename_prefix"] = prefix
    return g


def edit(prompt: str, source: Path, target: Path, seed: int, prefix: str = "qwen21_edit") -> None:
    """Draw the edit on the local GPU and land it at `target`."""
    from studio.comfy import stage_image, submit, wait
    made = wait(submit(graph(prompt, Path(source), seed, prefix, stage_image(Path(source)))), timeout=1800)
    Path(target).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(made[0], target)
