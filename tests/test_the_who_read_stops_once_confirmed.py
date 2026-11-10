"""Jekyll ep07 retro S10: G-WHO read every extracted frame of a take even after CONFIRM frames had
already agreed on the fault; the third read could not change the verdict.  It stops once CONFIRM who
lines are in.  It never stops on clean frames: the last read can still come back unreadable, a kept
fault, so a take that fails today still fails."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "episode"))
import take_content_check as tcc  # noqa: E402

WHO = "who: 2 figures read as 'gabriel_john_utterson'; the shot casts one"
SHOT = SimpleNamespace(faces=["a", "b"], size="medium")
READS = [SimpleNamespace(people=2)] * 3


def run(monkeypatch, said: list):
    asked = []

    def read(path, seed):
        asked.append(seed)
        got = said[len(asked) - 1]
        if isinstance(got, Exception):
            raise got
        return got
    monkeypatch.setattr(tcc, "read_who_frame", read)
    monkeypatch.setattr(tcc.fw, "applies", lambda *a: True)
    monkeypatch.setattr(tcc.fw, "fault", lambda figures, staged: WHO if figures == "bad" else "")
    return tcc.who_faults_for(SHOT, READS, Path("."), "T07", {}), asked


def test_two_agreeing_frames_end_the_reads(monkeypatch):
    out, asked = run(monkeypatch, ["bad", "bad", "bad"])
    assert out == [WHO, WHO] and len(asked) == 2


def test_clean_frames_read_every_frame_and_keep_an_unread(monkeypatch):
    out, asked = run(monkeypatch, ["ok", "ok", tcc.pc.Unreadable("no answer")])
    assert len(asked) == 3 and out == ["unread: who no answer"]


def test_one_fault_then_clean_reads_on(monkeypatch):
    out, asked = run(monkeypatch, ["bad", "ok", "ok"])
    assert len(asked) == 3 and out == [WHO]
