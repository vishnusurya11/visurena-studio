"""ep19, 2026-10-07 19:14Z: step 13's upload died on Google OAuth ('invalid_grant:
Token has been expired or revoked') and the table had no row for it, so the
stop went to the brain as an unclassified Traceback.  No order can mint a
token: the stop PARKS, and the reason names the command and the one human
click OAuth allows."""
from __future__ import annotations

from studio import autopilot

TAIL = """Traceback (most recent call last):
  File "scripts/publish/youtube_upload.py", line 135, in send
google.auth.exceptions.RefreshError: ('invalid_grant: Token has been expired or revoked.', {'error': 'invalid_grant'})
"""


def test_a_refresh_error_parks_and_names_the_mint_command():
    kind, reason, order = autopilot.classify(TAIL, set())
    assert kind == "park" and order is None
    assert reason.startswith("youtube_token_expired") and "youtube_auth.py" in reason


def test_an_ordinary_traceback_still_goes_to_the_brain():
    kind, reason, _ = autopilot.classify("Traceback (most recent call last):\nKeyError: 'host'\n", set())
    assert kind == "brain" and reason.startswith("failed:")
