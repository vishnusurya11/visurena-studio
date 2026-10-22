"""No test may copy a file into the real `ComfyUI/input/`.

MEASURED 2026-10-21 (window 2 of the ep02 rehearsal): 426 `tmp*_cdc0bebf.png`
files sat in the real `ComfyUI/input/`, each byte-identical to
`synth_frames.picture(31)`.  `test_the_default_embedder_is_never_reached_by_a_test`
calls `take_leak.dino_embed`, which stages its picture BEFORE `run_text` trips,
and `comfy_trap` trapped only `run` and `run_text`.  Every full suite any
session ran wrote one more, and the rehearsal's A-real check read them as the
rehearsal's own writes.  `dino_embed` also left its temp png in %TEMP%.

The trap now points `comfy.COMFY_ROOT` at a session folder under the test's
temp root, so `stage_image` -- under any name a module imported it by -- lands
beside the tests and never in the engine's folder.
"""
from pathlib import Path

import numpy as np

from studio import comfy, settings
from studio import take_leak as lk
from studio.comfy import stage_image as bound_at_import

REAL = Path(settings.TODAY_COMFY_ROOT).resolve()


def outside_real(root: Path) -> bool:
    root = Path(root).resolve()
    return root != REAL and REAL not in root.parents


def test_a_test_sees_a_comfy_root_outside_the_real_engine():
    assert outside_real(comfy.COMFY_ROOT)


def test_a_staged_picture_lands_beside_the_tests(tmp_path):
    assert outside_real(comfy.COMFY_ROOT)            # checked first: a red run never writes to the engine
    pic = tmp_path / "a.png"
    pic.write_bytes(b"the panel")
    name = comfy.stage_image(pic)
    assert (comfy.COMFY_ROOT / "input" / name).read_bytes() == b"the panel"


def test_a_name_bound_at_import_stages_beside_the_tests_too(tmp_path):
    assert outside_real(comfy.COMFY_ROOT)
    pic = tmp_path / "b.png"
    pic.write_bytes(b"another panel")
    assert (comfy.COMFY_ROOT / "input" / bound_at_import(pic)).is_file()


def test_the_embedder_leaves_no_temp_picture_behind(tmp_path, monkeypatch):
    import tempfile
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    monkeypatch.setattr(comfy, "stage_image", lambda p: "staged.png")
    monkeypatch.setattr(comfy, "run_text", lambda *a, **k: "[1.0, 2.0]")
    got = lk.dino_embed(np.zeros((8, 8, 3), dtype=np.uint8))
    assert list(got) == [1.0, 2.0] and list(tmp_path.glob("*.png")) == []
