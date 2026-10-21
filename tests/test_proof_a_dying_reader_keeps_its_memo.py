"""A real worker that dies mid-fill keeps what it already read (final proof run 2026-10-21 15:50 PDT:
the CPU face detect worker died 11 min into `rehearse.py memos`, and fill_kind, which wrote the memo
only after its last item, lost every reading).  The memo is written after each reading, so the next
run resumes at the item that killed the worker instead of starting over."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.proof import fill_memos
from studio.rehearsal import fake_workers


def test_a_reader_that_dies_on_the_third_take_leaves_the_first_two_in_the_memo(tmp_path):
    takes = [tmp_path / f"T0{k}.mp4" for k in range(1, 4)]
    for k, take in enumerate(takes):
        take.write_bytes(bytes([k]))

    def see(take: Path) -> dict:
        if take == takes[2]:
            raise RuntimeError("the worker died")
        return {"0": []}
    with pytest.raises(RuntimeError, match="worker died"):
        fill_memos.fill(tmp_path / "memos", detect=takes, see=see, idle=lambda: True)
    memo = json.loads((tmp_path / "memos" / "detect.json").read_text(encoding="utf-8"))
    every = fake_workers.detect_every()
    assert sorted(memo) == sorted(fake_workers.detect_key(t, every) for t in takes[:2])
