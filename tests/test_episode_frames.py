"""Every plate handed to the storyboard is 768x1344."""
import importlib.util
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ep_frames", ROOT / "scripts" / "episode" / "frames.py")
frames = importlib.util.module_from_spec(spec)
sys.modules["ep_frames"] = frames
spec.loader.exec_module(frames)


def test_a_landscape_image_is_cropped_not_stretched(tmp_path):
    src = tmp_path / "wide.png"
    Image.new("RGB", (1368, 768), "red").save(src)
    assert Image.open(frames.conform(src, tmp_path / "out.png")).size == (frames.W, frames.H)


def test_a_small_portrait_is_scaled_up_to_the_canvas(tmp_path):
    src = tmp_path / "small.png"
    Image.new("RGB", (384, 672), "blue").save(src)
    assert Image.open(frames.conform(src, tmp_path / "o.png")).size == (768, 1344)


def test_an_existing_sheet_is_reused_and_refs_json_untouched(tmp_path):
    (tmp_path / "refs" / "characters").mkdir(parents=True)
    sheet = tmp_path / "refs" / "characters" / "char-x.png"
    sheet.write_bytes(b"png")
    refs = tmp_path / "refs" / "refs.json"
    refs.write_text("{}")
    assert frames.sheet_for(tmp_path, "x") == sheet
    assert refs.read_text() == "{}"


def test_a_character_the_book_never_bound_gets_no_invented_body(tmp_path):
    """`frames.py` inventing a description is how "fair side-whiskers" entered
    a clean-shaven man's record: only `step_02_refs.py` may create a body,
    because it is the only thing that reads the render back."""
    import pytest

    (tmp_path / "refs" / "characters").mkdir(parents=True)
    with pytest.raises(SystemExit):
        frames.sheet_for(tmp_path, "stamford")
    assert not hasattr(frames, "STAMFORD")
