"""The master path is only ever created by a RENAME of a finished file.

MEASURED 2026-09-20, WotW ep05: two chains touched one episode at once, and
`master_r2v.mp4` was found truncated at 133 MB with no moov atom -- unplayable,
while a reader was reading it.  The same thing truncated ep04's master mid-QC.

It is not a ffmpeg bug and not a disk fault.  `tail()` passed
`episode_home.master_path(...)` straight to ffmpeg as its output, and that
encode is `-preset slow -crf 14` over three minutes of 1536x1536 picture: for
those minutes the deliverable's own name points at a growing, headerless file.
`trim()` then did `master.write_bytes(...)`, a second window of the same kind.
Any reader arriving inside either window -- QC, the publisher, the owner's
player -- sees a broken master and cannot tell it from a broken cut.

The brick: a writer writes into the WORK room; the master's name is attached to
a file that is already complete, by one `os.replace`, which NTFS does in a
single step.  A reader then sees either the previous master or the new one, and
never a fraction of either.
"""
from pathlib import Path

import pytest


def test_publish_moves_the_finished_file_onto_the_name(tmp_path):
    from studio.finished_file import publish
    made = tmp_path / "work" / "final.mp4"
    made.parent.mkdir()
    made.write_bytes(b"whole film")
    master = tmp_path / "cut" / "master_r2v.mp4"
    master.parent.mkdir()
    assert publish(made, master) == master
    assert master.read_bytes() == b"whole film"
    assert not made.exists(), "the scratch copy is consumed, not left to be mistaken for a master"


def test_the_previous_master_stands_until_the_new_one_is_whole(tmp_path):
    """A reader between the two assembles reads the OLD master, not a stump."""
    from studio.finished_file import publish
    master = tmp_path / "master_r2v.mp4"
    master.write_bytes(b"yesterday's film")
    made = tmp_path / "final.mp4"
    made.write_bytes(b"today's film")
    assert master.read_bytes() == b"yesterday's film"   # while the encode ran
    publish(made, master)
    assert master.read_bytes() == b"today's film"


def test_a_failed_encode_leaves_the_master_untouched(tmp_path):
    """The encode writes its own name; if it dies there is nothing to publish."""
    from studio.finished_file import publish
    master = tmp_path / "master_r2v.mp4"
    master.write_bytes(b"yesterday's film")
    with pytest.raises(FileNotFoundError):
        publish(tmp_path / "never_written.mp4", master)
    assert master.read_bytes() == b"yesterday's film"


def test_scratch_for_never_names_the_master(tmp_path):
    from studio.finished_file import scratch_for
    master = tmp_path / "cut" / "master_r2v.mp4"
    work = tmp_path / "work"
    made = scratch_for(master, work)
    assert made != master
    assert made.parent == work
    assert made.suffix == master.suffix, "ffmpeg picks its muxer off the extension"


def test_assemble_never_hands_the_master_name_to_ffmpeg():
    """The regression itself: `tail`'s output must not be the master path.

    Read off the source, because the fault is one argument at one call site and
    a mock of ffmpeg would prove only that the mock was called."""
    import inspect

    from scripts.episode import assemble
    body = inspect.getsource(assemble.main)
    assert "episode_home.master_path" in body
    call = body[body.index("out = tail("):body.index("trim(out")]
    assert "master_path" not in call, (
        "tail() is writing straight to the deliverable's name; it must encode "
        "into the work room and publish by rename")


def test_trim_does_not_rewrite_the_master_in_place():
    import inspect

    from scripts.episode import assemble
    body = inspect.getsource(assemble.trim)
    assert "master.write_bytes" not in body, (
        "a second in-place write to the master, the same window as the first")
