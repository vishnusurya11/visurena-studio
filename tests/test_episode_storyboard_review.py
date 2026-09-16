"""The review sheet is one row per shot: panel, take start, take end."""
import importlib.util
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ep_board_script", ROOT / "scripts" / "episode" / "storyboard.py")
sb = importlib.util.module_from_spec(spec)
sys.modules["ep_board_script"] = sb
spec.loader.exec_module(sb)


def test_contact_lays_out_three_tiles_per_row(tmp_path):
    tiles = []
    for name in ("a", "b", "c"):
        Image.new("RGB", (768, 1344), name and "grey").save(tmp_path / f"{name}.png")
        tiles.append(tmp_path / f"{name}.png")
    out = sb.contact([tuple(tiles), tuple(tiles)], tmp_path / "review.png")
    assert Image.open(out).size == (3 * 268, 2 * 452)


def test_a_white_gutter_on_an_edge_is_trimmed_before_conforming(tmp_path):
    from PIL import Image

    from studio import episode_gutter as gutter
    panel = Image.new("RGB", (600, 1000), (40, 40, 40))
    panel.paste((255, 255, 255), (0, 970, 600, 1000))       # a white gutter at the bottom
    trimmed = sb.strip_white_edges(panel)
    # the guard's own cut: the 30 rows of paper plus its MARGIN
    assert trimmed.size == (600, 1000 - 30 - gutter.MARGIN)
    panel.save(tmp_path / "p.png")
    out = sb.conform(tmp_path / "p.png", tmp_path / "o.png", box=(0, 0, 600, 1000))
    import numpy as np
    bottom = np.asarray(Image.open(out).convert("L"))[-8:].mean()
    assert bottom < 100
