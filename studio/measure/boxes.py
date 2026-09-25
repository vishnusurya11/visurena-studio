"""GroundingDINO boxes -> a hat worn or held, a landmark the place never named.

The `image_groundingdino_boxes` workflow takes ONE phrase and prints the boxes
it found as `[[[x1, y1, x2, y2], ...]]` in pixels (one list per image).  A hat
box over a head box is worn; one centred within reach of a wrist is held; a
picture that has both on its one planned person is the fault the plan gate
refuses in words (G-HAT) and no picture gate ever counted.  A landmark word
from `cell_gates.MAJOR` with a box and no mention in the place's words is
invented -- the retake class the plan gate G-PLACE checks only in prose.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from studio import cell_gates

WORKFLOW = "image_groundingdino_boxes"
BOX_THRESHOLD = 0.35
"""GroundingDINO box threshold for a single phrase; the research recipe's value."""
WORN = 0.5
"""The share of a hat box inside a head box that makes it worn."""
REACH = 1.5
"""A hat centred within this many face heights of a wrist is held."""
HEAD_UP = 0.8
"""A head box is the face box raised by this many face heights, for the crown."""


def parse(text) -> list[list[float]]:
    """The boxes in the workflow's text, flattened out of the per-image list."""
    data = json.loads(text) if isinstance(text, str) else text
    if data and isinstance(data[0], list) and (not data[0] or isinstance(data[0][0], (list, tuple))):
        data = data[0]
    return [[float(v) for v in box] for box in data]


def normalised(boxes: list[list[float]], size: tuple[int, int]) -> list[list[float]]:
    w, h = size
    return [[b[0] / w, b[1] / h, b[2] / w, b[3] / h] for b in boxes]


def head_box(face: dict, aspect: float) -> list[float]:
    """A YuNet face (`cx`, `cy`, `h` as fractions) grown upward into a head box;
    `aspect` is frame width over height, since a face box is square in pixels."""
    h = float(face["h"])
    w = h / aspect
    cx, cy = float(face["cx"]), float(face["cy"])
    return [cx - w / 2, cy - h / 2 - HEAD_UP * h, cx + w / 2, cy + h / 2]


def share_inside(box: list[float], other: list[float]) -> float:
    """The share of `box` that lies inside `other`."""
    area = max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1])
    if area <= 0:
        return 0.0
    ix = max(0.0, min(box[2], other[2]) - max(box[0], other[0]))
    iy = max(0.0, min(box[3], other[3]) - max(box[1], other[1]))
    return ix * iy / area


def centre(box: list[float]) -> tuple[float, float]:
    return ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)


def classify(hat: list[float], heads: list[list[float]], wrists: list[tuple[float, float]],
             face_h: float) -> str:
    """worn | held | loose."""
    if any(share_inside(hat, head) >= WORN for head in heads):
        return "worn"
    cx, cy = centre(hat)
    if any(math.hypot(cx - wx, cy - wy) <= REACH * face_h for wx, wy in wrists):
        return "held"
    return "loose"


def hats(boxes: list[list[float]], heads: list[list[float]], wrists: list[tuple[float, float]],
         face_h: float) -> list[dict]:
    """Every hat box with its state; all coordinates as fractions of the frame."""
    return [{"box": [round(v, 3) for v in b], "state": classify(b, heads, wrists, face_h)} for b in boxes]


def hat_fault(found: list[dict]) -> str | None:
    """A hat worn AND a hat held in one picture."""
    states = {h["state"] for h in found}
    return "a hat worn and a hat held" if {"worn", "held"} <= states else None


def invented(found: dict[str, list], place: str) -> list[str]:
    """Landmark words with a box that the place's words (or their kin) never name."""
    have = cell_gates.landmarks(place)
    return sorted(word for word, hits in found.items()
                  if hits and word not in have and not (cell_gates.KIN.get(word, set()) & have))


def detect_words(image, words: list[str], detect) -> dict[str, list]:
    """One detection per word; only the words with a box are kept."""
    return {word: hits for word in words if (hits := detect(image, word))}


def detector(run=None, threshold: float = BOX_THRESHOLD, timeout: float = 120.0):
    """`detect(image, word) -> boxes` through ComfyUI (or the injected `run`);
    a picture is staged once for every word asked of it."""
    from studio import comfy
    staged: dict[str, str] = {}

    def detect(image, word: str) -> list[list[float]]:
        name = staged.get(str(image)) or staged.setdefault(str(image), comfy.stage_image(Path(image)))
        values = {"image_1": name, "prompt": word, "threshold": threshold}
        return parse((run or comfy.run_text)(WORKFLOW, values, timeout))
    return detect
