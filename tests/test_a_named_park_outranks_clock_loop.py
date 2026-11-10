"""Jekyll ep07 retro S2: ep07's run 19 died on an expired YouTube token, but `clock_loop` was
tested before the hand-back table, so the park said `clock_loop` and the finished episode
sat 6 days (11-04 -> 11-10) behind a reason nobody could act on.  A stop the table parks
by name parks by that name first; a clock_loop park names the last stop's cause."""
from __future__ import annotations

from studio import autopilot as ap
from studio.run_budget import EPISODE_CEILING_SECONDS
from tests.test_autopilot_derives_state_from_disk import signals

START = {"event": "start", "sha": "x"}
END = {"event": "end", "code": 1, "sha": "x", "clock_spent": True}
SPENT = [START, END, START, END, START, END]
TOKEN = ("google.auth.exceptions.RefreshError: ('invalid_grant: Token has been expired or revoked.', "
         "{'error': 'invalid_grant'})")
PEOPLE = "RuntimeError: REFUSED: G-PEOPLE: a fault on the ship-block list stands at shot_07"


def _derive(tail: str):
    return ap.derive(signals(drive_rows=SPENT, clock_spent_s=EPISODE_CEILING_SECONDS + 1, log_tail=tail), 7)


def test_an_expired_token_parks_by_its_name_on_a_spent_clock():
    got = _derive(TOKEN)
    assert got.state is ap.State.PARKED and got.reason.startswith("youtube_token_expired")


def test_a_clock_loop_park_names_the_last_stop():
    got = _derive(PEOPLE)
    assert got.state is ap.State.PARKED
    assert got.reason.startswith("clock_loop: refused:") and "G-PEOPLE" in got.reason and "shot_07" in got.reason


def test_named_park_is_none_for_a_stop_the_brain_reads():
    assert ap.named_park(signals(log_tail=PEOPLE), 7) is None
