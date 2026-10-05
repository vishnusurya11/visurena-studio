"""The Viewer draws a picture from the 320 thumb at once, then the 1024 WebP -- never the
full-size PNG on the stage (SPEC_v3 Images; panel ruling 1.5).  The original stays one link
away ("Open the original").  Text checks on viewer.js, $0."""
from pathlib import Path

JS = (Path(__file__).parent.parent / "studio" / "command_center" / "static" / "viewer" / "viewer.js").read_text(encoding="utf-8")


def test_thumb_urls_reach_the_1024_width():
    assert ">= 1024 ? 1024" in JS


def test_an_image_item_loads_the_1024_thumb_on_the_stage():
    assert "kind === 'image' && book ? URLS.thumb(unit, out.rel, 1024)" in JS


def test_the_original_is_still_one_link_away():
    assert "'Open the original ↗'" in JS and "a.href = URLS.lib(L.unit, L.rel)" in JS
