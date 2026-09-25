"""A word pasted into a clean picture is a synthetic lettering fault.

The generator only: it changes the pixels inside the box it reports, leaves
the rest alone, and hands back a casebook row marked `synthetic` with the
box as its region -- so a lettering judge can be shown a fault the owner
never had to find.
"""
import numpy as np
from PIL import Image

from studio import synth_faults


def clean(size=(128, 96)):
    rng = np.random.default_rng(3)
    return Image.fromarray(rng.integers(40, 90, (size[1], size[0], 3), dtype=np.uint8))


def test_the_word_changes_only_its_box():
    before = clean()
    after, box = synth_faults.paste_text(before, "WORD", at=(10, 20))
    a, b = np.asarray(before).astype(int), np.asarray(after).astype(int)
    x, y, w, h = box
    assert (a[y:y + h, x:x + w] != b[y:y + h, x:x + w]).any()
    outside = np.ones(a.shape[:2], bool)
    outside[y:y + h, x:x + w] = False
    assert (a[outside] == b[outside]).all()


def test_the_row_is_synthetic_lettering_with_the_box_as_region():
    _, box = synth_faults.paste_text(clean(), "WORD", at=(10, 20))
    row = synth_faults.row("00000000000000", "ep01", "panel", "casebook/synth/shot_00_lettering.png",
                           "lettering", region=box)
    assert row.verdict_by == "synthetic" and row.verdict == "fault"
    assert row.fault_class == "lettering" and row.region == list(box)
    assert row.source == "studio/synth_faults.py"
