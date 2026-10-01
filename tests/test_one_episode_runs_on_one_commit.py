"""Five-hour plan fix 7 (2026-09-30): one episode runs on one commit.  ep14
ran across 23 commits with 26 driver starts -- each relaunch rebuilt its setup
and climbed the same steps again.  The driver reads the commit the episode
STARTED on off drive.jsonl and says out loud when the code moved."""
from __future__ import annotations

import json

from studio import episode_drive


def rows(*shas: str) -> str:
    return "".join(json.dumps({"event": "start", "sha": s}) + "\n" for s in shas)


def test_the_first_recorded_commit_is_the_episodes_own():
    assert episode_drive.first_sha(rows("aaa111", "bbb222")) == "aaa111"
    assert episode_drive.first_sha("") is None
    assert episode_drive.first_sha("not json\n" + rows("ccc333")) == "ccc333"
