"""Storyboards reviewer, iteration 3: seq_lab_1 drew three panels of four, so
Q15_0 was a crop of Q11_1 (correlation 0.963) and the master jumped back to
the doorway two-shot.  Two pinned cells of different shots may not match."""
from PIL import Image

from studio import episode_seq_board as sq


def seg(shot, sub=0):
    return {"shot": shot, "sub": sub, "end": False}


def test_one_floor_over_every_pair_no_pair_skipped(tmp_path):
    """MEASURED over the 40 cells of iteration 4: the highest LEGITIMATE pair anywhere
    is 0.584 (two bench close-ups) and same-shot sub-shot pairs top out at 0.47, while
    the copies sit at 0.821, 0.890 and 0.951. One floor at 0.70 over every pair, with
    no relation skipped, is simpler and catches all of them."""
    a = Image.radial_gradient("L").resize((90, 160)).convert("RGB")
    b = Image.linear_gradient("L").resize((90, 160)).convert("RGB")
    paths = []
    for k, im in enumerate((a, a, b)):
        p = tmp_path / f"c{k}.png"; im.save(p); paths.append(p)
    assert sq.ALIKE == 0.70
    assert sq.duplicates(paths, [seg(2), dict(seg(2), sub=1), seg(3)]) == [("Q02_0", "Q02_1")]


def test_two_cells_of_different_shots_that_match_are_duplicates(tmp_path):
    a = Image.radial_gradient("L").resize((90, 160)).convert("RGB")
    b = Image.linear_gradient("L").resize((90, 160)).convert("RGB")
    paths = []
    for k, im in enumerate((a, a, b)):
        p = tmp_path / f"c{k}.png"; im.save(p); paths.append(p)
    assert sq.duplicates(paths, [seg(11, 1), seg(15), seg(13)]) == [("Q11_1", "Q15_0")]


def test_an_end_cell_that_copies_its_own_start_is_a_duplicate(tmp_path):
    """Owner 2026-09-11: no two panels on a sheet may be the same picture. The first
    gate skipped same-shot pairs, so Q02_0E (0.951 to its own start) passed."""
    a = Image.radial_gradient("L").resize((90, 160)).convert("RGB")
    b = Image.linear_gradient("L").resize((90, 160)).convert("RGB")
    paths = []
    for k, im in enumerate((a, a, b)):
        p = tmp_path / f"c{k}.png"; im.save(p); paths.append(p)
    same_shot = [dict(seg(2), end=False), dict(seg(2), end=True), dict(seg(3), end=False)]
    assert sq.duplicates(paths, same_shot) == [("Q02_0", "Q02_0E")]
    # A WHOLLY different END picture is now refused too, and this line used to
    # assert the opposite ("a real END frame changes the picture, so it passes").
    # It was measured wrong: an END is the same picture after ONE SIMPLE CAMERA
    # MOVE, so a radial gradient beside a linear one is not a real END frame, it
    # is the RE-STAGE the render cannot travel. 9 of episode 2's 12 start/END
    # pairs looked like this (median 0.307, minimum -0.019) and seven takes then
    # failed the drift gate for failing to reach their own END cell.
    # `end_pair_verdict` judges the pair in a band; only the middle passes.
    assert sq.duplicates([paths[0], paths[2]], [dict(seg(2)), dict(seg(2), end=True)]) \
        == [("Q02_0", "Q02_0E")]
