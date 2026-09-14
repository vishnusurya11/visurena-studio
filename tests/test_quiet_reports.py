"""Two numbers the pipeline printed that were not true.

  Q1 THE LONGEST SILENCE IS NOT THE LONGEST INTERIOR SILENCE.  `qc.main` passes
     `until=max(l["at"] for l in lines)` -- the last line's START -- so the final
     `until - end` is NEGATIVE and `max()` throws the tail away.  MEASURED on
     episode 3: the reported longest gap is 2.03 s; the real longest silence is
     the 3.26 s run-out from 158.74 s to the 162.00 s end of picture, and the
     music bed in that stretch sits at -45.6 LUFS.  The one hole a viewer is
     most likely to notice is the one the report cannot see.

  Q2 A CLAMPED LIFT MUST SAY SO.  `bed_gain_db` returns `min(want, MAX_LIFT)`
     and the caller prints "+6.0 dB to reach -25.6 LUFS", which is false whenever
     the clamp fires.  MEASURED on episode 3: `bed.wav` is -33.63 LUFS, wants
     +8.03 dB, gets +6.00, and lands at -27.83 -- 2.2 dB under its own target,
     with one printed line saying otherwise.  The skill's own rule says a bed far
     under target is a failed generation; this one shipped because the only
     sentence a human reads claimed it had not.
"""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def qc():
    return load("qc_mod", "scripts/episode/qc.py")


@pytest.fixture(scope="module")
def asm():
    return load("asm_mod", "scripts/episode/assemble.py")


# ---- Q1  the tail is a gap too ---------------------------------------------

LINES = [{"at": 0.5, "seconds": 4.0}, {"at": 6.0, "seconds": 3.0}]


def test_the_lead_in_before_the_first_line_is_not_a_hole(qc):
    """By design: `end` starts at the first line, so the 0.25 s handle and the
    title-card lead are not silence the viewer is waiting through."""
    assert qc.longest_gap([{"at": 3.0, "seconds": 1.0}], 5.0) == 1.0


def test_the_run_out_after_the_last_line_counts(qc):
    """Episode 3's shape: the last line ends well before the picture does."""
    assert qc.longest_gap(LINES, 12.26) == 3.26


def test_the_run_out_wins_when_it_is_the_longest(qc):
    """Reported 2.03 s while a 3.26 s silence sat at the end of the episode."""
    assert qc.longest_gap(LINES, 12.26) > qc.longest_gap(LINES, 9.0)


def test_an_interior_gap_still_wins_when_it_is_longer(qc):
    assert qc.longest_gap(LINES, 9.1) == 1.5


def test_a_duration_at_the_last_line_s_end_gives_no_tail_gap(qc):
    assert qc.longest_gap(LINES, 9.0) == 1.5


# ---- Q2  the clamp speaks ---------------------------------------------------

def test_an_ordinary_bed_reports_the_lift_it_got(asm):
    assert asm.bed_shortfall_db(-30.0) == 0.0


def test_a_bed_too_quiet_to_reach_target_reports_the_shortfall(asm):
    """ep03: -33.63 LUFS wants +8.03, gets +6.00, lands 2.03 dB short."""
    assert asm.bed_shortfall_db(-33.63) == pytest.approx(2.03, abs=0.01)


def test_the_gain_is_still_clamped(asm):
    assert asm.bed_gain_db(-33.63) == asm.BED_MAX_LIFT_DB


def test_an_unmeasurable_bed_claims_no_shortfall(asm):
    """It fell back to the fixed trim; there is no target to fall short of."""
    assert asm.bed_shortfall_db(None) == 0.0
