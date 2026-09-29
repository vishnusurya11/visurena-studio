"""ep14 (2026-09-29): shot 20 carries two cues 0.6 s apart -- hooves, then cabs
rattling behind.  The presence measure compared each cue's peak with the median
of the second before it; for the cabs that second was full of hooves, and the
cue read 2.4 dB (the hooves 13.7) and failed QC.  A cue that starts while an
earlier one sounds is measured against the quiet before the earlier one."""
from types import SimpleNamespace

from studio import episode_sound


def cue(start, seconds):
    return SimpleNamespace(start=start, seconds=seconds)


def test_an_overlapping_cue_takes_the_baseline_of_the_first():
    spans = [(121.858, 1.5), (122.458, 1.2)]
    assert episode_sound.baseline_start(spans, 1) == 121.858
    assert episode_sound.baseline_start(spans, 0) == 121.858


def test_a_cue_after_the_first_has_ended_keeps_its_own_baseline():
    spans = [(10.0, 1.0), (13.0, 1.0)]
    assert episode_sound.baseline_start(spans, 1) == 13.0


def test_a_chain_of_overlaps_reaches_the_earliest():
    spans = [(5.0, 2.0), (6.5, 2.0), (8.0, 1.0)]
    assert episode_sound.baseline_start(spans, 2) == 5.0
