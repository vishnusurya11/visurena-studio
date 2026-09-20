"""A deliverable's name is attached to a finished file, never to a growing one.

MEASURED 2026-09-20 (WotW ep05, and ep04 before it): `master_r2v.mp4` was found
truncated at 133 MB with no moov atom while another chain read it.  The encode
that makes a master is `-preset slow -crf 14` over three minutes of picture, and
it was given the master's own path as its output -- so for those minutes the
deliverable's name pointed at a headerless stump, and a reader could not tell
that from a broken cut.

`os.replace` is one step on NTFS and on POSIX: the reader sees the old file or
the new one.  That is the whole brick.
"""
from __future__ import annotations

import os
from pathlib import Path


def scratch_for(final: Path, work: Path) -> Path:
    """Where the writer writes: the work room, under the final name's extension.

    The extension is kept because ffmpeg picks its muxer off it."""
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    return work / f"publishing_{Path(final).name}"


def publish(made: Path, final: Path) -> Path:
    """Attach `final`'s name to the finished file, in one step."""
    made, final = Path(made), Path(final)
    if not made.exists():
        raise FileNotFoundError(f"nothing to publish as {final}: {made} was never written")
    final.parent.mkdir(parents=True, exist_ok=True)
    os.replace(made, final)
    return final
