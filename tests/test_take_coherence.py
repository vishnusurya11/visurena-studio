"""G-COHERENCE -- a take that abandons its storyboard MID-TAKE fails the way a
frozen one does.

Episode 9 scored 28/28 at 100.0 while 62 % of its frames matched no pinned cell
(docs/analysis/ep08_ep09_why_worse.md): `drift` reads the END frame only and
`foreign` only knows OTHER takes' pictures.  Everything here is synthetic
(no repo asset, no ffmpeg, no GPU) except the last test, which reads episodes
7 and 9 from `library/` when they are on disk and is skipped when they are not.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from studio import take_coherence as tc

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "library" / "20260822113400_a-study-in-scarlet" / "episodes"
SIZE = 256


def picture(seed: int, size: int = SIZE) -> np.ndarray:
    """A grey picture with STRUCTURE: hard-edged rectangles and discs of random
    tone, plus a fine grain.  (A field of soft blobs is the wrong fixture: at
    48x84 any zoom crop of one such field matches any other above 0.5.)"""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:size, 0:size]
    img = np.full((size, size), rng.uniform(40, 200))
    for _ in range(40):
        cx, cy = rng.uniform(0, size, 2)
        w, h, tone = rng.uniform(size / 16, size / 3), rng.uniform(size / 16, size / 3), rng.uniform(0, 255)
        if rng.uniform() < 0.5:
            img[(np.abs(x - cx) < w / 2) & (np.abs(y - cy) < h / 2)] = tone
        else:
            img[((x - cx) ** 2 + (y - cy) ** 2) < (w / 2) ** 2] = tone
    return np.clip(img + rng.normal(0, 3, img.shape), 0, 255).astype(np.uint8)


def hold(pic: np.ndarray, n: int, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return np.clip(pic[None].astype(np.int16) + rng.integers(-2, 3, (n, *pic.shape)), 0, 255).astype(np.uint8)


def push_in(pic: np.ndarray, n: int, zoom: float = 1.8) -> np.ndarray:
    im, s = Image.fromarray(pic), pic.shape[0]
    out = []
    for k in range(n):
        z = 1 + (zoom - 1) * k / max(n - 1, 1)
        c = int(s / z)
        out.append(np.asarray(im.crop(((s - c) // 2, (s - c) // 2, (s - c) // 2 + c, (s - c) // 2 + c)).resize((s, s))))
    return np.stack(out)


def morph(a: np.ndarray, b: np.ndarray, n: int) -> np.ndarray:
    t = np.linspace(0, 1, n)[:, None, None]
    return ((1 - t) * a + t * b).astype(np.uint8)


def pan(big: np.ndarray, n: int, step: int = 2 * tc.DOWN) -> np.ndarray:
    return np.stack([big[:SIZE, k * step:k * step + SIZE] for k in range(n)])


def cells(*pics: np.ndarray) -> dict[str, Image.Image]:
    return {f"Q0{k}_0.png": Image.fromarray(p) for k, p in enumerate(pics)}


# ---- the four numbers ---------------------------------------------------------

def test_a_held_take_is_coherent():
    a = picture(1)
    m = tc.measure(hold(a, 40), cells(a))
    assert m["offboard_share"] == 0.0 and m["last_vs_cell"] > 0.9
    assert m["hard_cut"] < 5 and m["nonrigid"] < 5


def test_a_push_in_on_the_cell_stays_on_board():
    """A dolly is a re-framing of the board, not an abandonment: measured on
    ep06, a plain cosine to the static cell called 60 % of a fine episode's
    frames off-board; against the cell's own zoom crops, 0 %."""
    a = picture(2)
    m = tc.measure(push_in(a, 40, zoom=1.8), cells(a))
    assert m["offboard_share"] <= 0.10
    assert m["last_vs_cell"] >= 0.5


def test_a_morph_to_another_picture_is_off_board():
    a, b = picture(3), picture(4)
    frames = np.concatenate([hold(a, 10), morph(a, b, 20), hold(b, 30)])
    m = tc.measure(frames, cells(a))
    assert m["offboard_share"] > 0.5
    assert m["last_vs_cell"] < 0.2


def test_a_hard_cut_inside_a_single_anchor_take_is_read_at_its_frame():
    """ep07 T13 57.8, ep08 T28 81.8, ep09 T11 32.7 -- all scored 100."""
    a, b = picture(5), picture(6)
    m = tc.measure(np.concatenate([hold(a, 20), hold(b, 20)]), cells(a))
    assert m["hard_cut"] > 30 and m["hard_cut_at"] == 20


def test_the_one_cut_at_a_two_anchor_pin_is_forgiven_and_one_elsewhere_is_not():
    a, b = picture(7), picture(8)
    frames = np.concatenate([hold(a, 20), hold(b, 20)])
    on_pin = tc.measure(frames, cells(a, b), anchors=[["Q00_0.png", 0], ["Q01_0.png", 20 + tc.PIN_TOL]])
    off_pin = tc.measure(frames, cells(a, b), anchors=[["Q00_0.png", 0], ["Q01_0.png", 20 + tc.PIN_TOL + 1]])
    assert on_pin["hard_cut"] < 30
    assert off_pin["hard_cut"] > 30


def test_a_pure_pan_is_rigid_and_a_morph_is_not():
    big = picture(9, size=SIZE + 200)[:SIZE]
    rigid = tc.measure(pan(big, 30), cells(big[:, :SIZE]))
    assert rigid["raw_diff"] > 4 * rigid["nonrigid"] and rigid["nonrigid"] < 2
    a, b = picture(10), picture(11)
    churn = tc.measure(morph(a, b, 30), cells(a))
    assert churn["nonrigid"] > 0.8 * churn["raw_diff"]


def test_one_frame_does_not_crash_and_reads_as_no_motion():
    a = picture(12)
    m = tc.measure(hold(a, 1), cells(a))
    assert m["hard_cut"] == 0.0 and m["nonrigid"] == 0.0 and m["offboard_share"] == 0.0


def test_the_last_frame_is_read_against_the_last_pinned_cell():
    a, b = picture(13), picture(14)
    frames = np.concatenate([hold(a, 20), hold(b, 20)])
    m = tc.measure(frames, cells(a, b), anchors=[["Q00_0.png", 0], ["Q01_0.png", 20]])
    assert m["last_vs_cell"] > 0.9
    assert m["last_cell"] == "Q01_0.png"


def test_the_pinned_cells_are_the_anchors_and_the_staged_end_pictures():
    rec = {"anchors": [["Q03_0.png", 0], ["Q04_0.png", 51]],
           "refs": ["char-x.png", "plate_y.png", "Q03_0.png", "Q04_0.png", "Q04_0E.png"]}
    assert tc.pinned_names(rec) == ["Q03_0.png", "Q04_0.png", "Q04_0E.png"]
    assert tc.last_pinned(rec) == "Q04_0E.png"
    assert tc.last_pinned({"anchors": [["Q03_0.png", 0], ["Q04_0.png", 51]], "refs": []}) == "Q04_0.png"


def test_a_missing_pinned_cell_is_an_error_not_a_pass(tmp_path):
    with pytest.raises(FileNotFoundError):
        tc.load_cells(tmp_path, ["Q00_0.png"])


# ---- the rows in the verdict --------------------------------------------------

def test_the_constants_are_the_calibrated_ones():
    assert (tc.OFFBOARD_HARD, tc.OFFBOARD_ADVISORY) == (0.40, 0.20)   # pushes and holds; a pan gets OFFBOARD_HARD_PAN 0.60
    assert (tc.LAST_HARD, tc.LAST_ADVISORY) == (0.20, 0.40)
    assert (tc.CUT_HARD, tc.CUT_ADVISORY, tc.PIN_TOL) == (30.0, 20.0, 6)
    assert tc.NONRIGID_ADVISORY == 7.0 and tc.NONRIGID_WIDE == 6.0 and tc.ON_BOARD == 0.50


def test_the_churn_wall_is_size_aware_and_hard_on_a_wide():
    """MEASURED ep10 (analyst H): the wides the reviewer kept churned 3.12 /
    3.60 / 3.63; the three wide faults -- a second chimney, a second window,
    gate posts gone -- churned 6.43 (T20_fail1), 9.03 (T03_fail2), 10.82
    (T03_fail1) with off-board 0.00 and last-vs-cell 0.58-0.69: the cosine
    forgives a wide that changes everywhere a little.  ep05-07 wides max 5.73.
    Margin +0.43 above / -0.27 below on 20 wides; elsewhere 7.0 stays advisory
    (5.5 would buy T04/T20 at the price of T06, a KEEP at 6.56)."""
    m = {"offboard_share": 0.0, "last_vs_cell": 0.69, "hard_cut": 12.6, "nonrigid": 6.4}
    wide = {g.name: g for g in tc.rows(m, size="wide")}["churn"]
    assert not wide.ok and wide.hard and wide.penalty > 0 and wide.note == "6.4 wide"
    medium = {g.name: g for g in tc.rows(m, size="medium")}["churn"]
    assert medium.ok and not medium.hard and medium.penalty == 0.0
    adv = {g.name: g for g in tc.rows(m | {"nonrigid": 7.5}, size="medium")}["churn"]
    assert not adv.ok and not adv.hard and adv.penalty > 0
    kept = {g.name: g for g in tc.rows(m | {"nonrigid": 3.6}, size="wide")}["churn"]
    assert kept.ok and kept.penalty == 0.0 and kept.note == "3.6 wide"


def test_a_planned_exit_turns_the_last_frame_row_off():
    """ep10 T17: told to drop the fist out of the bottom of the frame, it ended
    on bare boards and last-vs-cell 0.20 cost it ten points for obeying."""
    m = {"offboard_share": 0.10, "last_vs_cell": 0.20, "hard_cut": 5.8, "nonrigid": 3.4}
    row = {g.name: g for g in tc.rows(m, exit=True)}["last-vs-cell"]
    assert row.value is None and row.ok and not row.hard and row.penalty == 0.0 and "exit" in row.note
    assert not {g.name: g for g in tc.rows(m)}["last-vs-cell"].ok


def test_measure_reports_the_last_on_board_frame_of_every_segment():
    """The zoom row caps an exit segment's read at its last on-board sample;
    the number comes from here, one per anchor span."""
    a, b, c = picture(15), picture(16), picture(17)
    frames = np.concatenate([hold(a, 20), hold(c, 10), hold(b, 20)])
    one = tc.measure(frames, cells(a))
    assert one["onboard_last"] == [19]
    two = tc.measure(frames, cells(a, b), anchors=[["Q00_0.png", 0], ["Q01_0.png", 30]])
    assert two["onboard_last"] == [19, 49]


def test_ep09_t02_shaped_numbers_fail_hard_on_off_board_and_last_frame():
    rows = {g.name: g for g in tc.rows({"offboard_share": 0.62, "last_vs_cell": 0.08, "hard_cut": 14.9, "nonrigid": 10.7})}
    assert not rows["coherence off-board"].ok and rows["coherence off-board"].hard
    assert not rows["last-vs-cell"].ok and rows["last-vs-cell"].hard
    assert rows["cut"].ok
    assert not rows["churn"].ok and not rows["churn"].hard and rows["churn"].penalty > 0


def test_an_unprompted_cut_is_hard_and_the_churn_is_only_advisory():
    rows = {g.name: g for g in tc.rows({"offboard_share": 0.10, "last_vs_cell": 0.70, "hard_cut": 32.7, "nonrigid": 9.0})}
    assert not rows["cut"].ok and rows["cut"].hard
    assert all(g.hard is False for g in [rows["churn"]])


def test_a_clean_take_carries_no_penalty():
    rows = tc.rows({"offboard_share": 0.0, "last_vs_cell": 0.9, "hard_cut": 4.0, "nonrigid": 2.0})
    assert all(g.ok and g.penalty == 0.0 for g in rows)
    assert [g.name for g in rows] == ["coherence off-board", "last-vs-cell", "cut", "churn"]


def test_an_unmeasured_take_says_so_and_fails_nothing():
    rows = tc.rows({})
    assert all(g.note == "not measured" and g.ok and not g.hard for g in rows)


# ---- calibration: the owner's eye ---------------------------------------------

def takes_of(ep: str):
    recs = json.loads((LIB / ep / "takes" / "r2v" / "shots.json").read_text())
    return [(r, LIB / ep / "takes" / "r2v" / f"T{r['index']:02d}.mp4") for r in recs]


def hard_fail(m: dict) -> bool:
    return any(g.hard and not g.ok for g in tc.rows(m))


def churns(m: dict) -> bool:
    """The churn advisory alone. The union of ALL advisories is not a verdict:
    off-board > 0.20 and last-vs-cell < 0.40 are common on episode 7, whose
    camera genuinely moves off its board without morphing, so ORing them
    flags 44 % of an episode the owner judged fine."""
    return m["nonrigid"] > tc.NONRIGID_ADVISORY


@pytest.mark.skipif(not (LIB / "ep09" / "takes" / "r2v" / "shots.json").exists(), reason="library not on disk")
def test_ep07_mostly_passes_and_ep09_mostly_fails():
    """The owner's judgement: episode 7 looked fine, episode 9 did not.

    On the HARD rungs alone, no honest threshold reaches 50 % of ep09 without
    failing a third of ep07 (calibration table in `take_coherence`); with the
    churn advisory on its own -- the rung the eye tracked -- ep07 3/25 and ep09
    8/28 at the 7.0 wall, measured at the shipped DOWN=2 grid."""
    hard, flagged = {}, {}
    for ep in ("ep07", "ep09"):
        ms = [tc.measure(tc.frames(v, min(r["placed_seconds"], 20.0)),
                         tc.load_cells(LIB / ep / "boards" / "cells", tc.pinned_names(r)), r["anchors"])
              for r, v in takes_of(ep)]
        hard[ep] = sum(map(hard_fail, ms)) / len(ms)
        flagged[ep] = sum(map(churns, ms)) / len(ms)
    assert hard["ep07"] <= 0.30 and hard["ep09"] >= 2 * hard["ep07"]
    assert flagged["ep07"] <= 0.20 and flagged["ep09"] >= 2 * flagged["ep07"]



def test_a_pan_gets_the_wider_off_board_wall():
    """MEASURED on episode 11 (2026-09-17): T08 read off-board 0.06 as a push and
    0.48 as a PAN of the same shot; the reviewer's kept pans T03 0.52 / T20 0.43
    sat over the 0.40 wall while the re-stagings sat at 0.64-0.70 (T13) and 0.66
    (T06).  A pan reveals picture beyond the cell by design."""
    m = {"offboard_share": 0.50, "last_vs_cell": 0.50, "hard_cut": 3.0, "nonrigid": 2.0}
    plain = {g.name: g for g in tc.rows(m)}
    panned = {g.name: g for g in tc.rows(m, panned=True)}
    assert plain["coherence off-board"].hard and not plain["coherence off-board"].ok
    assert not panned["coherence off-board"].hard and not panned["coherence off-board"].ok
    far = {g.name: g for g in tc.rows(dict(m, offboard_share=0.66), panned=True)}
    assert far["coherence off-board"].hard
    assert (tc.OFFBOARD_HARD, tc.OFFBOARD_HARD_PAN) == (0.40, 0.60)
