r"""Every shot in episodes 4-6 is the same length, and no gate can see it.

A viewer watching all six masters end to end, 2026-09-15:

> "Episodes 4, 5 and 6 have no editorial rhythm. They are a shot every six
>  seconds, start to finish."

MEASURED from `placed.json`, shot seconds:

    ep    shots  median   IQR      on-screen cuts   internal cuts
    01      23    6.38   1.33           53                17
    02      25    6.50   2.25           44                17
    03      25    6.58   1.31           38                12
    04      24    5.67   1.26           25                 0
    05      25    6.42   1.31           26                 0
    06      26    6.02   0.94           27                 0

THIS IS A FIX THAT CREATED A NEW PROBLEM. "One line per shot, zero internal
cuts" was right and is staying: 7 of episode 3's 15 internal cuts could not land
even with perfect obedience, because a whole-second stamp bounds the model to
+-12 frames. But those cuts were the ONLY source of rhythm variation the
pipeline had. Remove them and the only thing left that varies a shot's length is
its line -- and the sync rule says `shot.seconds = HANDLE + line + HANDLE +
beat + coda`, so SHOT LENGTH IS LINE LENGTH.

And the lines do not vary. Word counts per line:

    ep    n   median   IQR   min-max
    01   23     13     4.0    8-18
    02   25     14     6.0    4-18      <- the widest, and rated best as writing
    03   25     13     2.0    8-17
    04   24     12     2.0    7-16
    05   24     15     1.0   14-17      <- every line 14 to 17 words
    06   26     16     2.0   10-18

Episode 5's twenty-four lines are all between 14 and 17 words. Episode 6 has no
picture-only shot at all. Nothing in the pipeline asked for that; it is what
happens when every line is written to sit just under the 18-word wall.

SO THE GATE IS ON THE HALF THE WRITER CONTROLS. If a plan has no internal cuts,
its LINES have to carry the rhythm, and a plan whose line lengths cluster is a
plan that will cut like a metronome however good its pictures are.

ADVISORY, NOT A REFUSAL, and the reason is honest: the evidence for the
consequence is one reviewer's judgement plus a distribution, not a scored
outcome. The distribution is not in doubt -- an IQR of 1.0 word over 24 lines is
a metronome by arithmetic -- but nothing measures what it COSTS, so it prints
loudly and refuses nothing. See the note in the episode skill.
"""
import pytest

from studio.episode_spec import RHYTHM_IQR, line_rhythm


def lines(*counts: int) -> list[dict]:
    return [{"index": i, "kind": "narration", "text": " ".join(["w"] * n)}
            for i, n in enumerate(counts)]


EP05 = lines(14, 15, 15, 16, 14, 17, 15, 16, 15, 14, 16, 15, 17, 15, 14, 16,
             15, 15, 16, 14, 17, 15, 16, 15)
EP02 = lines(4, 6, 8, 9, 11, 12, 13, 13, 14, 14, 15, 15, 16, 16, 16, 17, 17,
             18, 18, 12, 10, 7, 14, 16, 5)


def test_episode_fives_lines_are_a_metronome():
    got = line_rhythm(EP05, cuts=0)
    assert got["iqr"] <= 1.5 and got["flat"] is True


def test_episode_twos_lines_are_not():
    got = line_rhythm(EP02, cuts=0)
    assert got["iqr"] >= 3.0 and got["flat"] is False


def test_the_report_names_the_spread():
    got = line_rhythm(EP05, cuts=0)
    assert got["shortest"] == 14 and got["longest"] == 17


def test_a_plan_with_internal_cuts_carries_its_rhythm_elsewhere():
    """Episodes 1 to 3 have flat-ish lines AND 12-17 internal cuts, and a viewer
    sees 38-53 cuts. The cuts are the rhythm there, so the line spread is not
    the whole story and the gate says nothing."""
    assert line_rhythm(EP05, cuts=14)["flat"] is False


def test_one_internal_cut_is_not_a_rhythm():
    assert line_rhythm(EP05, cuts=1)["flat"] is True


def test_a_short_line_among_long_ones_widens_it():
    """The cheapest fix: write one line of six words."""
    before = line_rhythm(EP05, cuts=0)["iqr"]
    after = line_rhythm(EP05 + lines(5, 6, 6, 7), cuts=0)["iqr"]
    assert after > before


def test_a_picture_only_shot_is_not_a_line():
    """Episode 6 has none; episode 1 has one. They are how a plan gets a beat
    that is not the length of a sentence."""
    assert line_rhythm(lines(15, 15, 15), cuts=0)["lines"] == 3


def test_too_few_lines_to_judge_says_so():
    got = line_rhythm(lines(12, 14), cuts=0)
    assert got["flat"] is False and got["note"]


def test_no_lines_at_all_is_not_a_metronome():
    assert line_rhythm([], cuts=0)["flat"] is False


def test_the_wall_is_the_measured_one():
    """ep02 6.0 and ep01 4.0 sit above it; ep03/04/06 at 2.0 and ep05 at 1.0
    below. The line is drawn where the two on-screen rhythms separate."""
    assert RHYTHM_IQR == 3.0
