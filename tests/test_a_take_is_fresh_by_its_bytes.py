"""A5 (fleet E, 2026-10-22): the lanes call a take fresh by its bytes, not its mtime.

take_overlap.fresh compared the dq verdict's mtime with the take's, so a take copied back with
the same bytes (a keep-aside restore) read as stale and went to the CPU lane again, and a take
whose bytes changed under an older mtime read as fresh.  The verdict's `take_sha8` is the key
(take_dq.cache_key writes it); a verdict without one keeps the mtime test."""
from __future__ import annotations

import json
import os
import shutil

from scripts.episode import take_dq
from studio import take_overlap

CODE = "c0de0001"


def landed_take(room, body: bytes = b"take bytes " * 64, stamp_sha: bool = True):
    take = room / "T05.mp4"
    take.write_bytes(body)
    doc = {"measures_sha8": CODE, "gates": {}}
    if stamp_sha:
        doc["take_sha8"] = take_dq.take_sha8(take)
    (room / "T05.dq.json").write_text(json.dumps(doc), encoding="utf-8")
    return take


def newer_than_its_verdict(take):
    later = take.with_suffix(".dq.json").stat().st_mtime + 30
    os.utime(take, (later, later))


def test_a_take_copied_back_with_the_same_bytes_is_fresh(tmp_path):
    take = landed_take(tmp_path)
    shutil.copyfile(take, tmp_path / "aside.mp4")
    shutil.copyfile(tmp_path / "aside.mp4", take)
    newer_than_its_verdict(take)
    assert take_overlap.fresh(take, CODE)


def test_a_take_with_one_flipped_byte_is_stale(tmp_path):
    take = landed_take(tmp_path)
    body = bytearray(take.read_bytes())
    body[7] ^= 0xFF
    stamp = take.stat().st_mtime
    take.write_bytes(bytes(body))
    os.utime(take, (stamp - 60, stamp - 60))              # older than its verdict, by the clock
    assert not take_overlap.fresh(take, CODE)


def test_a_verdict_without_a_byte_key_keeps_the_mtime_test(tmp_path):
    take = landed_take(tmp_path, stamp_sha=False)
    assert take_overlap.fresh(take, CODE)
    newer_than_its_verdict(take)
    assert not take_overlap.fresh(take, CODE)


def test_a_verdict_by_other_measuring_code_is_still_stale(tmp_path):
    take = landed_take(tmp_path)
    assert not take_overlap.fresh(take, "other000")
