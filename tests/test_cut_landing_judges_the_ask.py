"""A gate may only demand a precision the instruction can express.

`cut_landing` measured `landed - pin` against [-4, +6] frames.  But the model is
never told the pin.  It is told a STAMP, and `episode_ref_official.stamp` rounds
to whole seconds -- "OWNER 5.14 ... MiniMax's own examples read whole seconds".
A shot pinned at frame 137 is asked for at 00:06, which is frame 144.  A model
that obeys perfectly lands at 144 and the gate reports +7 and refuses it.

MEASURED over all 15 of episode 3's internal pins, 2026-09-13, by taking each
pin, rounding it the way `stamp` does and landing exactly there:

    7 of 15 cannot pass even with PERFECT obedience
    worst: pin 85 -> told 00:04 -> frame 96 -> +11 (twice), pin 81 -> -9 (twice)

Whole-second stamps bound obedience to +-12 frames before the model does
anything at all, so [-4, +6] was measuring the plan's own rounding.

The repair is not a looser tolerance -- that would stop catching the real
misses, which ran +34 to +54.  It is that the target is a RANGE.  The plan wants
the pin; the words ask for `stated_frame(pin)`; both are obedient landings, and
anything between them is too.  `delta` is the distance to that span and is 0
inside it, so [-4, +6] keeps meaning what it says while measuring only what the
model controls.  `pin` is still what the picture is matched against.
"""
from studio.cut_landing import MAX_EARLY, MAX_LATE, landing, stated_frame, verdict


def frames(n: int, own: str, score: float = 0.9) -> list[dict]:
    return [{"own": own, "own_s": score, "foreign": False, "other": ""} for _ in range(n)]


def timeline(target: str, land_at: int, total: int = 300) -> list[dict]:
    out = frames(land_at, "Q02_0.png") + frames(total - land_at, target)
    return out


ANCHORS = [["Q02_0.png", 0], ["Q03_0.png", 137]]


# ---- the stamp is the ask -------------------------------------------------

def test_a_pin_is_asked_for_at_its_rounded_second():
    assert stated_frame(137) == 144      # 5.71 s -> "00:06" -> frame 144
    assert stated_frame(85) == 96        # 3.54 s -> "00:04" -> frame 96
    assert stated_frame(81) == 72        # 3.38 s -> "00:03" -> frame 72


def test_a_pin_already_on_a_second_asks_for_itself():
    assert stated_frame(144) == 144


# ---- perfect obedience passes ---------------------------------------------

def test_landing_exactly_where_the_stamp_said_is_obedience():
    """Episode 3's take 2: pinned 137, told 00:06, a model that lands on 144."""
    rows = landing(timeline("Q03_0.png", 144), ANCHORS)
    assert rows[0]["delta"] == 0
    assert verdict(rows)["passed"]


def test_every_episode_3_pin_becomes_passable_when_obeyed():
    """All seven that could not pass before, landing on the frame they were told."""
    for pin in (137, 85, 81, 77, 175, 68, 94):
        anchors = [["Q00_0.png", 0], ["Q03_0.png", pin]]
        rows = landing(timeline("Q03_0.png", stated_frame(pin), total=pin + 200), anchors)
        assert verdict(rows)["passed"], (pin, rows[0]["delta"])


# ---- a real miss is still a miss ------------------------------------------

def test_a_cut_thirty_four_frames_late_is_still_refused():
    rows = landing(timeline("Q03_0.png", stated_frame(137) + 34), ANCHORS)
    assert not verdict(rows)["passed"]


def test_a_cut_that_never_lands_is_still_refused():
    rows = landing(frames(300, "Q02_0.png"), ANCHORS)
    assert rows[0]["landed"] is None and not verdict(rows)["passed"]


def test_the_tolerance_is_unchanged():
    """The repair moves the origin, it does not widen the window."""
    assert (MAX_EARLY, MAX_LATE) == (4, 6)


def test_one_frame_past_the_late_bound_is_refused():
    rows = landing(timeline("Q03_0.png", stated_frame(137) + MAX_LATE + 1), ANCHORS)
    assert not verdict(rows)["passed"]


def test_the_row_still_reports_the_pin_it_was_planned_at():
    """The plan's own rounding loss stays visible; it is just not the model's fault."""
    rows = landing(timeline("Q03_0.png", 144), ANCHORS)
    assert rows[0]["pin"] == 137 and rows[0]["asked"] == 144


def test_landing_exactly_on_the_pin_is_also_obedience():
    """The trap in judging against the ask ALONE: a pin at 81 is asked for at
    frame 72, so a cut that lands on 81 -- exactly where the plan wanted it --
    would read +9 and be refused.  Both ends of the span are right."""
    anchors = [["Q00_0.png", 0], ["Q03_0.png", 81]]
    rows = landing(timeline("Q03_0.png", 81), anchors)
    assert rows[0]["delta"] == 0 and verdict(rows)["passed"]


def test_anywhere_between_the_pin_and_the_ask_is_obedience():
    anchors = [["Q00_0.png", 0], ["Q03_0.png", 81]]
    for at in range(72, 82):
        rows = landing(timeline("Q03_0.png", at), anchors)
        assert rows[0]["delta"] == 0, (at, rows[0])


def test_early_of_the_whole_span_is_measured_from_its_near_end():
    anchors = [["Q00_0.png", 0], ["Q03_0.png", 81]]
    rows = landing(timeline("Q03_0.png", 72 - 5), anchors)
    assert rows[0]["delta"] == -5 and not verdict(rows)["passed"]
