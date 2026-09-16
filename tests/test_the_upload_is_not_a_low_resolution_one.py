r"""The master is delivered at the size YouTube gives a good transcode to.

Every episode so far was rendered, cut AND UPLOADED at H3's native 768x768.
That is 0.59 megapixels, below every tier YouTube treats as high definition, so
the upload is transcoded at the bitrate of its tier and the detail is thrown
away on the way to the viewer. The local master is not the problem -- it is
CRF 17, near-lossless, and episode 8's is the highest-bitrate master in the
series at 2983 kb/s against 1885 and 2084 for episodes 6 and 7.

EPISODE 8 IS WHERE IT SHOWED, and the measurement says why. Sampled across each
delivered master:

    ep06 interiors   detail 5.03   flat-area 37.7 %   mean luma  69.0
    ep07 interiors   detail 5.60   flat-area 37.7 %   mean luma  55.5
    ep08 desert      detail 6.93   flat-area 34.3 %   mean luma 100.9

(detail = mean absolute Laplacian, the high-frequency energy a codec has to
spend bits on.) Episode 8 carries 38 % more fine detail than episode 6 and is
46 % brighter. Both punish a thin transcode: detail smears, and the banding that
hides in a dark parlour is plain in a pale sky. The first episode that is mostly
wide exteriors is the first episode where the upload size hurts.

So the deliverable is scaled up before the final encode. This adds NO detail --
Lanczos cannot invent any -- it stops the detail that IS there from being
discarded by a transcode tier chosen on pixel count. That is the whole claim,
and it is worth stating plainly rather than calling it an improvement in
quality.

The render pipeline is untouched: cells, takes and cuts stay at H3's 768. Only
the last encode changes.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from studio import canvas


def test_the_delivery_size_is_above_the_high_definition_line():
    for aspect in ("1:1", "9:16"):
        w, h = canvas.deliver(aspect)
        assert min(w, h) >= 1080, (aspect, w, h)


def test_it_is_a_whole_multiple_of_the_render_size():
    """An integer factor resamples cleanly; 768 -> 1080 is 1.406 and rings."""
    for aspect in ("1:1", "9:16"):
        rw, rh = canvas.size(aspect)
        dw, dh = canvas.deliver(aspect)
        assert dw % rw == 0 and dh % rh == 0, (aspect, (rw, rh), (dw, dh))
        assert dw // rw == dh // rh


def test_the_shape_is_unchanged():
    for aspect in ("1:1", "9:16"):
        rw, rh = canvas.size(aspect)
        dw, dh = canvas.deliver(aspect)
        assert rw * dh == rh * dw, (aspect, (rw, rh), (dw, dh))


def test_both_sides_are_even_for_yuv420():
    for aspect in ("1:1", "9:16"):
        w, h = canvas.deliver(aspect)
        assert w % 2 == 0 and h % 2 == 0


def test_the_render_canvas_itself_did_not_move():
    """The whole pipeline is pinned to H3's fixed point; only the last encode
    changes. If this fails, something scaled the RENDER and not the delivery."""
    assert canvas.size("1:1") == (768, 768)
