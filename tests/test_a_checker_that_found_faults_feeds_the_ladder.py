"""A take checker that FOUND faults feeds the ladder; one that crashed refuses.

ep12, 2026-09-25: the take ladder's retake rung re-checked six takes; T10 failed
take_content_check (exit 1), run_script made that a refusal, and step 09 died
inside the ladder that exists to handle exactly that fault. Exit 1 is also a
crash, so it passes only when every take has its verdict file.
"""
from pathlib import Path
from types import SimpleNamespace

import pytest

from studio import take_ladder


def ctx_with(tmp_path, rc: int):
    room = tmp_path / "takes" / "r2v"
    room.mkdir(parents=True)
    (room / "T10.mp4").write_bytes(b"take")
    logged = []

    def run_script(script, *extra, gpu=False, clock=None):
        if rc:
            raise SystemExit(f"REFUSED: {script} exit {rc}")
        return 0

    return SimpleNamespace(home=tmp_path, run_script=run_script,
                           log=lambda msg, **kw: logged.append(msg)), room, logged


def test_faults_found_with_every_verdict_on_disk_pass_on(tmp_path):
    ctx, room, logged = ctx_with(tmp_path, 1)
    (room / "T10.content.json").write_text("{}", encoding="utf-8")
    take_ladder.measured(ctx, "scripts/episode/take_content_check.py", "take_content", ".content.json")
    assert logged and "faults found" in logged[0]


def test_a_take_left_without_a_verdict_still_refuses(tmp_path):
    ctx, _, _ = ctx_with(tmp_path, 1)
    with pytest.raises(SystemExit):
        take_ladder.measured(ctx, "scripts/episode/take_content_check.py", "take_content", ".content.json")


def test_any_other_exit_code_refuses(tmp_path):
    ctx, room, _ = ctx_with(tmp_path, 2)
    (room / "T10.content.json").write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit):
        take_ladder.measured(ctx, "scripts/episode/take_content_check.py", "take_content", ".content.json")
