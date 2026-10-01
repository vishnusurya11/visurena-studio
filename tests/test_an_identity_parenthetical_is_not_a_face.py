"""ep16 (2026-10-01): M6 flagged "the brother (grey eyes)'s forearm reaches
across the seat" -- a forearm is a limb, but the FEATURES scan read the cast
identity parenthetical "(grey eyes)" and accused correct work.  The constants
ride every clause by design (describe-cast-from-its-rows), so the scan must
strip parentheticals before looking for a face part.  $0: a regex."""
from __future__ import annotations

from studio.episode_spec import motion_faults


def codes(motion: str) -> set[str]:
    return {c for c, _ in motion_faults(motion)}


def test_an_identity_parenthetical_does_not_trip_m6():
    m = ("camera pushes in a quarter of the frame across the whole shot; "
         "the chaise rolls; the brother (grey eyes)'s forearm reaches across the seat.")
    assert "M6" not in codes(m)


def test_a_real_face_part_still_trips_m6():
    m = ("camera pushes in a quarter of the frame across the whole shot; "
         "the chaise rolls; the brother's eyes narrow against the dust.")
    assert "M6" in codes(m)
