"""The eye that counts is the newest whose sha8 names the take files on disk NOW: a retaken
take moves the fingerprint, so the old verdict stops admitting anything."""
from __future__ import annotations

import os

from scripts.episode import assemble
from tests.test_a_still_terminal_does_not_hide_the_other_kept_takes import fault, sign


def test_a_retaken_take_orphans_the_old_verdict(tmp_path):
    sign(tmp_path, [fault("T01", "keep_best")])
    (tmp_path / "T02.mp4").write_bytes(b"retaken")
    assert assemble.kept_of(tmp_path) == {}


def test_the_verdict_of_the_current_set_is_read_not_the_newest_file(tmp_path):
    current = sign(tmp_path, [fault("T00", "keep_best")], names=("T00", "T01"))
    (tmp_path / "T01.mp4").write_bytes(b"retaken")
    sign(tmp_path, [fault("T01", "keep_best")], names=("T00", "T01"))        # the new set's eye
    os.utime(current, (4e9, 4e9))                                              # the old eye is the newer file
    assert set(assemble.kept_of(tmp_path)) == {1}
