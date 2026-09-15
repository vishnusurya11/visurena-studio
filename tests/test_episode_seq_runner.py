"""The runner's gates, with story order underneath them.

The ladder gate used to read `cells[:geography]` -- it assumed the walk was
the first n panels of the sheet, which was true only while `split()` sorted
the geography first.  In story order the route panels are scattered, so the
gate reads the route panel NUMBERS the board hands it.  And a sheet that
fails twice no longer keeps the copy: an END cell left on disk becomes a
take's pin and freezes the render on the frame it repeats.
"""
import importlib.util
from pathlib import Path

from PIL import Image, ImageDraw

from studio.episode_spec import Setup

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ep_seq_boards", ROOT / "scripts" / "episode" / "seq_boards.py")
boards = importlib.util.module_from_spec(spec)
spec.loader.exec_module(boards)


def corridor(path: Path, door_px: int | None) -> Path:
    im = Image.new("L", (768, 1344), 60)
    if door_px:
        d = ImageDraw.Draw(im)
        d.rectangle((384 - door_px // 3, 500 - door_px // 2, 384 + door_px // 3, 500 + door_px // 2), fill=235)
    im.save(path)
    return path


def seg(path):
    return {"shot": 0, "sub": 0, "size": "medium", "path": path}


def test_the_ladder_gate_reads_the_route_panels_wherever_they_sit(tmp_path):
    cells = [corridor(tmp_path / "a.png", 90), corridor(tmp_path / "b.png", None),
             corridor(tmp_path / "c.png", 60)]
    group = [seg(0.1), seg(None), seg(0.5)]
    heights, regress = boards.ladder_check(cells, group, route=[1, 3])
    assert [h is None for h in heights] == [False, False] and heights[0] > heights[1]
    assert regress == [1]  # the far window shrank by a third between two places on the walk


def test_a_landmark_at_the_route_start_is_gated_the_other_way_round(tmp_path):
    """The gateway and the bench: the people walk AWAY from the landmark, so the
    honest strip SHRINKS and it is a landmark that grows which has let them arrive
    early.  Gated the old way, a correctly drawn gateway sheet failed twice and the
    strict retry asked it for the impossible."""
    gateway = Setup(described="The hospital gateway.", landmark="the stone arch of the gateway",
                    landmark_at="start", route="from the kerb under the arch to the corner")
    group = [seg(0.0), seg(0.5)]
    shrinking = [corridor(tmp_path / "g1.png", 90), corridor(tmp_path / "g2.png", 60)]
    assert boards.ladder_check(shrinking, group, [1, 2], gateway)[1] == []
    growing = [corridor(tmp_path / "h1.png", 60), corridor(tmp_path / "h2.png", 90)]
    assert boards.ladder_check(growing, group, [1, 2], gateway)[1] == [0]


def test_a_shrink_between_two_panels_at_the_same_place_is_framing(tmp_path):
    cells = [corridor(tmp_path / "a.png", 90), corridor(tmp_path / "c.png", 60)]
    group = [seg(0.5), seg(0.52)]
    assert boards.ladder_check(cells, group, route=[1, 2])[1] == []


def test_a_sheet_is_clean_only_when_every_gate_is_quiet():
    passing = {"regressions": [], "white_lines_in": [], "duplicates": []}
    assert boards.clean(passing) is True
    assert boards.clean(dict(passing, duplicates=[("Q02_0", "Q02_0E")])) is False
    assert boards.clean(dict(passing, white_lines_in=["Q02_0.png"])) is False


def test_an_end_cell_that_is_still_a_copy_after_the_retry_is_retired(tmp_path):
    """Owner 2026-09-11: a silently kept copy is worse than no END cell.

    THIS TEST USED TO WRITE THE CELLS IN THE BOARDS ROOT, which is where the
    code looked before cells moved to `boards/cells/` -- so it kept passing
    while the real tree stopped matching, and pinned the broken path in place.
    Episode 4 had seven copied END cells and `dropped_ends` came back empty.
    The cell is now MOVED to `boards/superseded/`, not unlinked: `sq.reaches`
    already refuses a copy as a destination, so deleting a drawn picture bought
    nothing.  See tests/test_drop_end_copies_finds_the_cells.py."""
    (tmp_path / "cells").mkdir()
    # A PICTURE, not a flat field. Two solid-black cells measure 0.00 against
    # each other, not 1.00, because `frame_match` mean-centres and a constant
    # image has no variance -- so the old fixture could never have produced the
    # "copy" verdict it was named for, and only passed while the reason string
    # was hardcoded.
    same = Image.effect_noise((48, 84), 40).convert("L")
    for name in ("Q02_0.png", "Q02_0E.png"):
        same.save(tmp_path / "cells" / name)
    dropped = boards.drop_end_copies(tmp_path, {"duplicates": [("Q02_0", "Q02_0E")]})
    # THE REASON IS MEASURED NOW, not one hardcoded word for two opposite faults.
    # `duplicates` flags a pair that is a COPY or a RE-STAGING, and the old string
    # said "still a copy" for both: all seven of episode 6's retired ENDs were
    # re-stagings (0.330 down to -0.007) and every one was logged as a copy.
    # These two cells are identical, so this one really is a copy.
    assert len(dropped) == 1 and dropped[0]["dropped_end"] == "Q02_0E"
    assert "copy" in dropped[0]["reason"] and "Q02_0" in dropped[0]["reason"]
    assert dropped[0]["similarity"] >= 0.8
    assert (tmp_path / "cells" / "Q02_0.png").exists()
    assert not (tmp_path / "cells" / "Q02_0E.png").exists()
    assert (tmp_path / "superseded" / "Q02_0E.png").exists()


def test_two_start_cells_that_match_are_left_on_disk_for_the_human(tmp_path):
    """Only an END cell has a start panel to fall back on; two matching start cells
    are a redraw the owner looks at, never a file this script deletes."""
    (tmp_path / "cells").mkdir()
    for name in ("Q11_1.png", "Q15_0.png"):
        Image.new("L", (8, 8), 0).save(tmp_path / "cells" / name)
    assert boards.drop_end_copies(tmp_path, {"duplicates": [("Q11_1", "Q15_0")]}) == []
    assert (tmp_path / "cells" / "Q11_1.png").exists()
    assert (tmp_path / "cells" / "Q15_0.png").exists()
