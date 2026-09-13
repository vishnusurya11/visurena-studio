"""G3 (cell side) and its take-side twin: did the END cell move, does the route
grow, and did the take make a picture the plan never asked for.  Synthetic
images and arrays only -- no sheet is drawn, no take is decoded, nothing spends.
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw

from studio import geo_gate as gg


def test_the_thresholds_are_the_measured_populations():
    """review8/geography.md, measured on iterations 3 and 4: a pinned cut steps
    20-60 while a moving wide peaks at 14; a walk END cell that froze reads
    0.82-0.89 against its start cell and one that moved 0.34-0.62; the far
    landmark holds within 2 % over a static hold and shrinks 9 % on a settle;
    floor slide on a real tracking walk is 25-49 px/s against 12 for a crawl."""
    assert (gg.CUT, gg.CUT_RATIO) == (20.0, 4.0)
    assert gg.END_MOVED == 0.75 and gg.WALK == 20.0
    assert (gg.SHRINK, gg.GROW, gg.ROUTE_STEP) == (0.25, 1.3, 0.3)


def test_a_hard_cut_is_a_spike_above_the_floor_and_the_neighbourhood():
    e = np.full(96, 2.0)
    e[47] = 45.0                       # one pinned cut at frame 48 -> 2.0 s
    assert gg.cuts_from_energy(e) == [2.0]
    busy = np.full(96, 12.0)
    busy[47] = 30.0                    # a moving wide: 30 is not 4x its surroundings
    assert gg.cuts_from_energy(busy) == []


def test_unplanned_cuts_are_those_with_no_pin_within_the_tolerance():
    assert gg.unplanned_cuts([2.0, 4.75, 9.25], [0, 45, 49, 117, 121, 253]) == [9.25]


def test_extra_pictures_counts_cuts_beyond_the_plans_cell_changes():
    anchors = [("Q07_0.png", 0), ("Q07_0E.png", 45), ("Q08_0.png", 49), ("Q08_0E.png", 117),
               ("Q08_1.png", 121), ("Q08_1.png", 253)]
    assert gg.transitions(anchors) == 2
    assert gg.extra_pictures([2.0, 4.75, 9.25], anchors) == 1
    assert gg.extra_pictures([2.0, 5.0], anchors) == 0


def cell(x: int) -> Image.Image:
    im = Image.new("L", (96, 168), 40)
    ImageDraw.Draw(im).rectangle([x, 60, x + 20, 140], fill=220)
    return im


def test_a_walk_end_cell_must_show_a_different_instant():
    """Four of the five END cells of iteration 4 repeated their start (0.821-0.951)
    and the three takes pinned to them froze.  The two that moved read 0.62 and 0.339."""
    assert gg.end_moved(cell(30), cell(30)) is False
    assert gg.end_moved(cell(30), cell(70)) is True


def test_landmark_must_not_shrink_and_must_grow_when_the_route_advances():
    sizes = ["wide", "full", "full", "close"]
    assert gg.landmark_track([100, 90, 300, 20], [0.0, 0.1, 0.9, 0.9], sizes) == {"shrunk": [], "flat": []}
    assert gg.landmark_track([266, 261], [0.0, 0.5], ["wide", "full"]) == {"shrunk": [], "flat": [1]}
    assert gg.landmark_track([267, 177], [0.05, 0.5], ["medium", "full"]) == {"shrunk": [1], "flat": []}


def test_direction_is_read_from_the_text_and_a_change_without_a_turn_breaks():
    assert gg.direction_of("Medium from behind at the corridor's near end") == "away"
    assert gg.direction_of("Medium from the door, facing them: walking toward the camera") == "toward"
    assert gg.direction_of("Tracking beside at walking pace") == "beside"
    segs = [{"size": "medium", "path": 0.1, "frame": "from behind", "motion": "Tracking behind"},
            {"size": "insert", "path": 0.6, "frame": "two hands", "motion": "Static"},
            {"size": "medium", "path": 0.9, "frame": "facing them, toward the camera", "motion": "Tracking back ahead"}]
    assert gg.direction_breaks(segs) == [(2, "away", "toward")]
    segs[2]["frame"] += "; they turn from the bench"
    assert gg.direction_breaks(segs) == []


def test_floor_slide_reads_a_sliding_texture_and_not_a_hold():
    rng = np.random.default_rng(0)
    tex = rng.integers(0, 255, (336, 192 + 200)).astype(np.float32)
    moving = np.stack([tex[:, i * 2:i * 2 + 192] for i in range(48)])   # 2 px per frame = 48 px/s
    still = np.repeat(tex[None, :, :192], 48, axis=0)
    assert gg.walk_moves(gg.floor_slide(moving)) is True
    assert gg.floor_slide(still) == 0.0
    assert gg.walk_moves(12.0) is False                                 # a close that crawls


def test_the_sheet_verdict_names_every_end_cell_that_copied_its_start(tmp_path):
    """G3: the cell gate's END rule, run over a setup's drawn cells."""
    for name, im in (("Q07_0.png", cell(30)), ("Q07_0E.png", cell(30)),
                     ("Q12_0.png", cell(30)), ("Q12_0E.png", cell(70))):
        im.convert("RGB").save(tmp_path / name)
    assert gg.frozen_end_cells(tmp_path, ["Q07_0.png", "Q07_0E.png", "Q12_0.png", "Q12_0E.png"]) == ["Q07_0E.png"]
