"""The Viewer's loading slot is a still placeholder that appears late (panel ruling 3.3, 3.9):
the board allows one infinite animation (the GPU card's dot), and a shimmer is not it."""
from pathlib import Path

VIEWER_CSS = Path(__file__).parent.parent / "studio" / "command_center" / "static" / "viewer" / "viewer.css"


def test_the_viewer_stylesheet_has_no_infinite_animation():
    assert "infinite" not in VIEWER_CSS.read_text(encoding="utf-8")


def test_the_loading_slot_waits_before_it_shows():
    css = VIEWER_CSS.read_text(encoding="utf-8")
    rule = css[css.index(".vw-skel{"):].split("}", 1)[0]
    assert "opacity:0" in rule and "300ms" in rule
