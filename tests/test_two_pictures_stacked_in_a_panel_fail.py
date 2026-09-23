"""Two pictures stacked in one panel are caught by the gutter line between them.

Tier-4 calibration agent, 2026-09-23, on 127 published panels (ep05-ep09):
the share of a full row or column standing 18 luma above or below both
neighbours 4 px away reads 1.000 on ep07 S12, S13 and S14 (one grid, all
visibly stacked) and at most 0.748 on the 124 clean panels (ep09 S07, a real
chalk cross). Wall 0.90: 0.10 of margin each side.
"""
import numpy as np

from studio import panel_dq


def texture(h=512, w=512, seed=1):
    rng = np.random.default_rng(seed)
    return (np.clip(rng.normal(90, 12, (h, w, 3)), 0, 255)).astype(np.uint8)


def test_a_full_width_gutter_between_two_pictures_reads_stacked():
    frame = texture()
    frame[254:258, :, :] = 250
    assert panel_dq.stacked(frame) > 0.9


def test_a_picture_with_no_gutter_does_not():
    assert panel_dq.stacked(texture()) < 0.5


def test_the_verdict_flags_a_stacked_panel():
    row = panel_dq.verdict(faces=[], planned=0, sharp=1.0, ink=0.0, tiled=0.0, stacked=1.0)
    assert "stacked" in row["flags"] and not row["passed"]
    assert panel_dq.verdict(faces=[], planned=0, sharp=1.0, ink=0.0, tiled=0.0, stacked=0.75)["passed"]
