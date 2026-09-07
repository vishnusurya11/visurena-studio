"""What the cue SUPPLIES to the editor: cut points, and the waits between them.

The numbers here are measured off run 19's shipped music, not chosen: cue-1002
gave 26 attacks over 113.8 s of material for a cut that needed 27 cuts, and
its longest wait without one ran 17.5 s -- 4.4x the editor's own MAX_SHOT.
"""
from __future__ import annotations

import numpy as np
import pytest

from studio import cue_supply
from studio.trailer_edit import MAX_SHOT


def clicks(at: list[float], seconds: float = 24.0, rate: int = 100) -> tuple[np.ndarray, np.ndarray]:
    """(times, dB) of a quiet bed with a loud stroke at each of `at`."""
    times = np.arange(int(seconds * rate)) / rate
    db = np.full(times.shape, -30.0)
    for when in at:
        db[int(when * rate)] = -6.0
    return times, db


class TestAttacks:
    def test_an_attack_is_a_rise_the_cut_grid_would_have_kept(self):
        """The same detector the editor cuts on: what it cannot see is not a
        cut point, however loud the sustain under it."""
        times, db = clicks([2.0, 5.0, 9.0])
        assert cue_supply.attacks(times, db) == pytest.approx([2.0, 5.0, 9.0], abs=0.05)

    def test_a_rise_under_the_threshold_is_no_cut_point(self):
        times, db = clicks([2.0])
        db[int(6.0 * 100)] = -28.0                      # a 2 dB push, under GRID_DB
        assert cue_supply.attacks(times, db) == pytest.approx([2.0], abs=0.05)


class TestWaits:
    def test_the_longest_wait_is_measured_inside_the_material_only(self):
        """A dropout the arc ASKED for is not the editor waiting: the cue is
        silent there because the cut is meant to be."""
        material = cue_supply.material(20.0, [(6.0, 14.0)])
        assert material == [(0.0, 6.0), (14.0, 20.0)]
        assert cue_supply.longest_wait([2.0, 5.0, 16.0], material) == pytest.approx(4.0)
        # ... and the 8 s hole is not charged to the editor: read straight
        # across it the wait from 5.0 to 16.0 would have been 11.0 s.
        assert cue_supply.longest_wait([2.0, 5.0, 16.0], [(0.0, 20.0)]) == pytest.approx(11.0)

    def test_a_wait_runs_from_the_last_attack_to_the_end_of_its_material(self):
        """Inside the cue, yes: the editor must hold one shot from its last cut
        point to the hole ahead of it."""
        assert cue_supply.longest_wait([1.0], [(0.0, 12.0)]) == pytest.approx(11.0)

    def test_the_run_out_after_the_last_attack_is_not_a_wait(self):
        """The cut ENDS on the hard out -- `trailer_edit` lands its last cut
        there and the card holds to the stop -- so the stretch after the final
        attack is the picture arriving, not the editor stranded.  A fixture cue
        failed the gate on 6.1 s of exactly this."""
        spans = cue_supply.to_last_attack([(0.0, 6.0), (14.0, 24.0)], [2.0, 5.0, 16.0])
        assert spans == [(0.0, 6.0), (14.0, 16.0)]
        # 0->2, 2->5, 5->6 inside the first stretch; 14->16 in the second.
        assert cue_supply.longest_wait([2.0, 5.0, 16.0], spans) == pytest.approx(3.0)

    def test_material_with_no_attack_at_all_waits_its_whole_length(self):
        assert cue_supply.longest_wait([], [(0.0, 9.0)]) == pytest.approx(9.0)


class TestSupply:
    def test_a_cue_that_strikes_every_bar_supplies_a_choice_for_every_shot(self):
        """MEASURED on beatmap.GRID_DB's own tuning: the detector is set at
        4.0 dB to yield "roughly 1.5 candidates per shot" -- so the supply is
        counted in shots of MAX_SHOT, not in bars."""
        times, db = clicks([float(t) for t in range(1, 24)])
        found = cue_supply.supply(times, db, bar=2.0, until=24.0, dropouts=[])
        assert found.count == 23
        assert found.per_bar == pytest.approx(23 / 12.0, abs=0.05)
        assert found.per_shot == pytest.approx(23 / 6.0, abs=0.05)
        assert found.longest_wait <= MAX_SHOT
        assert not found.starves

    def test_run_19s_shipped_cue_starves_the_editor(self):
        """cue-1002: an attack every 4.4 s and a 17.5 s hold. The editor may
        not run a shot past MAX_SHOT and may only cut on an attack, so it had
        to break the ceiling -- the 17.5 s span in run 19's plan.json."""
        times, db = clicks([2.0, 6.0, 23.5], seconds=24.0)
        found = cue_supply.supply(times, db, bar=2.9, until=24.0, dropouts=[])
        assert found.longest_wait == pytest.approx(17.5, abs=0.1)
        assert found.per_shot < cue_supply.CANDIDATES_PER_SHOT
        assert found.starves
        assert "17.5s" in found.why and "MAX_SHOT" in found.why

    def test_a_wait_inside_a_hold_is_the_cue_holding_not_the_editor_waiting(self):
        """`cue_qc.long_shots_on_holds` already says a long shot is right over a
        sustain or a trough -- the picture is meant to rest there.  So the
        ceiling binds only where the cue is playing at level: run 19's fixture
        cue waited 6.1 s, all of it inside the trough the ask rode down."""
        times, db = clicks([2.0, 5.0, 21.0], seconds=24.0)
        found = cue_supply.supply(times, db, bar=2.0, until=24.0, dropouts=[],
                                  holds=[(6.0, 20.0)])
        assert found.count == 3
        assert found.longest_wait == pytest.approx(3.0)      # 21.0 -> 24.0, past the hold
        assert not found.starves or found.per_shot < cue_supply.CANDIDATES_PER_SHOT

    def test_an_asked_dropout_does_not_starve_the_cue(self):
        """The arc cuts holes on purpose; a hole is not a wait."""
        times, db = clicks([2.0, 5.0, 17.0, 20.0, 23.0])
        found = cue_supply.supply(times, db, bar=2.0, until=24.0, dropouts=[(6.0, 16.0)])
        assert found.longest_wait <= MAX_SHOT
