"""ep24 (2026-10-09 02:55Z): QC failed two masters running on one row -- 'a spade
biting into wet clay', shot 13, under a voice line: the mix measure 4.8 dB (the
voice masks it) and the stem -23.6 against its -20 target.  The lift skipped every
under-line row ('a masked measure moves 0.0 dB per lifted dB') while QC kept
failing it, so no recut could ever pass.  The STEM moves with the lift: an
under-line cue is lifted by its stem's deficit and judged, like a cue with no
baseline, against the level the plan asked for (the target less the lift)."""
from __future__ import annotations

from studio import episode_sound as es

ROW = {"shot": 13, "sound": "a spade biting into wet clay", "at": 71.875, "db": 4.8, "ok": False,
       "under_line": True, "stem_db": -23.6, "stem_target": -20.0, "stem_base": -20.0}


def test_an_under_line_cue_is_lifted_by_its_stem_deficit():
    lifts = es.lift_cures([ROW], {})
    assert lifts[es.lift_key(13, "a spade biting into wet clay")] == round(3.6 + es.LIFT_MARGIN_DB, 1)


def test_an_under_line_row_without_a_stem_measure_is_left_alone():
    bare = {k: v for k, v in ROW.items() if not k.startswith("stem_")}
    assert es.lift_cures([bare], {}) == {}


def test_a_stem_pinned_at_the_peak_ceiling_is_heard():
    """ep24 03:25Z: lifted +4.6, the spade rose only to -22.0 M -- its true peak
    sat at -3.43 against the -3.0 limiter.  A transient at the ceiling is as loud
    as a cue may be; asking more of its momentary loudness is the ruler's fault."""
    assert es.stem_judged(-22.0, target=-15.4, lift=4.6, limited=True) == (-20.0, True)
    assert es.stem_judged(-22.0, target=-15.4, lift=4.6, limited=False) == (-20.0, False)


def test_a_lifted_stem_is_judged_against_the_level_asked_for():
    # lifted +4.6: the sidecar target is now -15.4, the stem measures -19.0
    assert es.stem_judged(-19.0, target=-15.4, lift=4.6) == (-20.0, True)
    assert es.stem_judged(-23.6, target=-20.0, lift=0.0) == (-20.0, False)
