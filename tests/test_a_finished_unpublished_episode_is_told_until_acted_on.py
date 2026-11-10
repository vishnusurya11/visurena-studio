"""Jekyll ep07 retro S3 (brick 8 appendix): ep07's master was finished and signed for upload on
11-04, the upload died on an expired token, and the episode sat parked six days: `youtube_token_told`
was logged at every launch but proved only an attempt, and nothing told the owner again once it
parked.  A parked episode the chain carried to step 13 with standing approval is told every
NUDGE_EVERY_S until someone acts; a send that fails is tried again after RETRY_S."""
from __future__ import annotations

from studio import autopilot as ap

H = 3600.0
AT_13 = [{"event": "start"}, {"event": "run", "n": 19, "outcome": "failed", "step": "13"}, {"event": "end", "code": 1}]
AT_11 = [{"event": "start"}, {"event": "run", "n": 17, "outcome": "refused", "step": "11"}, {"event": "end", "code": 1}]


def due(rows=AT_13, standing=True, published=False, told=(), now=10 * H) -> bool:
    return ap.nudge_due(rows, standing, published, list(told), now)


def test_a_parked_master_at_publish_is_told_at_once():
    assert due()


def test_it_is_told_again_after_six_hours_and_not_before():
    assert not due(told=[(7 * H, True)])
    assert due(told=[(4 * H, True)])


def test_a_failed_send_is_tried_again_after_ten_minutes():
    assert not due(told=[(10 * H - 300, False)])
    assert due(told=[(10 * H - 700, False)])


def test_an_episode_that_stopped_before_publish_is_not_this_nudge():
    assert not due(rows=AT_11)


def test_a_held_or_published_episode_is_never_nudged():
    assert not due(standing=False)
    assert not due(published=True)
