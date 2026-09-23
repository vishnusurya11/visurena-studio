"""Making an episode public re-checks the machine gates on the file that was uploaded.

Publish audit, 2026-09-23: every episode goes up private (an unverified API
project forces it) and youtube_privacy.py then flips it public, asking only
--approved. ep07-ep09 went public 6-7 s after the insert with no gate run at
the flip. The owner's standing instruction is that an upload goes public, so
the human sign-off stays waived; but the flip must never publish what the
private upload itself would have refused, as the takes and QC stand NOW.
"""
from studio.youtube_publish import public_refusals

ROW = {"episode": 9, "video_id": "abc", "sha8": "f00dbeef"}


def test_a_clean_episode_goes_public():
    assert public_refusals({"passed": True, "sha8": "f00dbeef"}, [], ROW) == []


def test_qc_about_another_file_refuses():
    got = public_refusals({"passed": True, "sha8": "12345678"}, [], ROW)
    assert got and "12345678" in got[0] and "f00dbeef" in got[0]


def test_a_failed_qc_or_take_refuses():
    assert public_refusals({"passed": False, "sha8": "f00dbeef"}, [], ROW)
    assert public_refusals({"passed": True, "sha8": "f00dbeef"}, ["T18 (content: 7 figures)"], ROW)
