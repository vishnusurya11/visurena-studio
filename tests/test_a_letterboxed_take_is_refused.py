"""G-FRAME (2026-09-29): a take drawn letterboxed inside the square is refused.
ep14 T26, a silent insert: the video model put a widescreen picture inside the
square frame -- 54 of 256 rows black at the top and as many at the bottom --
from a full-frame panel, and every take row passed it; the edit gate saw only
a dark segment.  The Sherlock line measured plates for this (plate_gate); the
take never was."""
from PIL import Image

from studio import take_frame
from studio.take_verdict import Gate


def square(bars: int = 0) -> Image.Image:
    im = Image.effect_noise((256, 256), 60).convert("RGB")
    if bars:
        black = Image.new("RGB", (256, bars), (0, 0, 0))
        im.paste(black, (0, 0))
        im.paste(black, (0, 256 - bars))
    return im


def test_a_full_frame_take_passes_and_a_letterboxed_one_is_refused_hard():
    ok = take_frame.row_of([square(), square()])
    assert isinstance(ok, Gate) and ok.name == "letterbox" and ok.ok
    bad = take_frame.row_of([square(54), square(54), square()])
    assert not bad.ok and bad.hard and bad.value == 2


def test_a_thin_border_is_not_a_letterbox():
    assert take_frame.row_of([square(5)]).ok


def test_the_move_type_rung_skips_a_take_it_has_no_substitute_for():
    """ep14 (2026-09-29): the rung met T20 with only a letterbox and content faults,
    none in its cause table, and `next()` crashed step 09 after four retakes."""
    from studio import take_ladder
    from studio.judges.verdict import Fault
    doc = {"shots": [{"index": 20, "motion": "The camera pans from the houses to the carriage", "at_rest": ""}]}
    before = dict(doc["shots"][0])
    out = take_ladder.move_type(doc, 20, [Fault(kind="letterbox", where="T20"), Fault(kind="content", where="T20")])
    assert out["shots"][0] == before
