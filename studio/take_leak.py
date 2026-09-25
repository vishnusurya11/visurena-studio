"""A head leak: the take opens on another STAGED picture -- a character
sheet, the location plate -- and lands on its panel some frames in.

Three owner-caught heads (8, 11 and 12 frames of a prop sheet or a plate
before the shot) were fixed by a HAND-WRITTEN `heads.json`: somebody read the
strip, counted, and typed the seconds.  This measures the same count: the
first HEAD_FRAMES frames against every picture the take's own graph loaded
(`take_currency.staged_images` -- the content-addressed names are the record
of which bytes rendered), by a patch embedding; the leak is the first frame
where a panel wins.  `write_head` puts the measured count into `heads.json`
through the one reader the cut and the edit gate share (`edit_gate.heads_in`),
only when the take still covers its shot.

The embedder is injected (`embed=`): DINOv3 through the `image_embed` ComfyUI
workflow in production, a thumbnail in the tests.  `dino_embed` is the
production default and no test may reach it (tests/conftest.py traps comfy).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

HEAD_FRAMES = 12
FPS = 24
FITTED_ON = "three owner-caught heads of 8-12 frames, no negatives benched: advisory; the cure costs no GPU"
EMBED_WORKFLOW = "image_embed"


def kinds(names: list[str]) -> dict[str, str]:
    """panel (a cell `Q..` or a `shot_NN`), plate (`plate` in the name), else a sheet."""
    out = {}
    for n in names:
        stem = Path(n).name.lower()
        out[n] = "panel" if stem.startswith(("q", "shot_")) else ("plate" if "plate" in stem else "sheet")
    return out


def cosines(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """(n, m) cosines between unit-normalised rows of a and b."""
    a = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-9)
    b = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-9)
    return a @ b.T


def embed_all(images: dict[str, np.ndarray], embed) -> dict[str, np.ndarray]:
    return {n: np.asarray(embed(img), dtype=float).ravel() for n, img in images.items()}


def landing(best: list[str], kind: dict[str, str], head: int) -> tuple[int, bool]:
    """(frames before a panel wins, whether it did within the head)."""
    for k, name in enumerate(best):
        if kind[name] == "panel":
            return k, True
    return head, False


def leak(frames, pictures: dict[str, np.ndarray], embed, head: int = HEAD_FRAMES) -> dict | None:
    """The head leak of a take's first `head` frames against its staged
    pictures; None when no panel was staged (nothing to land on)."""
    kind = kinds(list(pictures))
    if "panel" not in kind.values():
        return None
    vecs = embed_all(pictures, embed)
    names = sorted(vecs)
    sims = cosines(np.stack([np.asarray(embed(f), dtype=float).ravel() for f in frames[:head]]),
                   np.stack([vecs[n] for n in names]))
    best = [names[int(i)] for i in sims.argmax(axis=1)]
    frames_, covers = landing(best, kind, head)
    return {"frames": frames_, "seconds": head_seconds(frames_), "covers": covers, "best": best,
            "against": names, "fitted_on": FITTED_ON}


def head_seconds(frames: int, fps: int = FPS) -> float:
    return round(frames / fps, 3)


def staged_pictures(take: Path, inputs: Path) -> dict[str, np.ndarray]:
    """The pictures the take's graph loaded, read from ComfyUI's input dir
    (`inputs`); a staged name no longer on disk is left out."""
    from PIL import Image

    from studio.take_currency import staged_images

    out = {}
    for name in sorted(staged_images(take)):
        path = Path(inputs) / name
        if path.is_file():
            out[name] = np.asarray(Image.open(path).convert("RGB"))
    return out


def write_head(home: Path, index: int, got: dict | None) -> Path | None:
    """Merge the measured head into `<episode>/heads.json`; a zero leak clears
    the take's key; a head that does not cover the shot writes nothing."""
    if not got or not got.get("covers"):
        return None
    path = Path(home) / "heads.json"
    heads = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    heads.pop(str(index), None)
    if got["frames"] > 0:
        heads[str(index)] = got["seconds"]
    path.write_text(json.dumps(heads, indent=2), encoding="utf-8")
    return path


def row(got: dict | None):
    """Advisory: a leak is cured by a head cut, not a render (see FITTED_ON)."""
    from studio.take_verdict import Gate

    if not got:
        return Gate("leak", None, True, False, "not measured")
    n = got["frames"]
    if n == 0:
        return Gate("leak", 0, True, False, "opens on its panel")
    note = f"{n} frames of {kinds(got['best'][:1])[got['best'][0]]} before the panel" if got["covers"] \
        else f"{n}+ frames: never lands on the panel"
    return Gate("leak", n, False, False, note, min(40.0, 5.0 * n))


def dino_embed(image: np.ndarray) -> np.ndarray:
    """The production embedder: DINOv3 through the `image_embed` workflow.
    Stages the picture, runs the graph, parses the vector it prints."""
    import tempfile

    from PIL import Image

    from studio import comfy

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        Image.fromarray(np.asarray(image)).save(tmp.name)
        text = comfy.run_text(EMBED_WORKFLOW, {"image_1": comfy.stage_image(Path(tmp.name))})
    return np.array(json.loads(text), dtype=float).ravel()
