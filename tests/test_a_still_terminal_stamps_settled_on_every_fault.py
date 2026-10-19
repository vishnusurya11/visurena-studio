"""K5: `terminal()` stamps fault.evidence['settled'] in {still, keep_best, high} on EVERY fault of
the eye verdict, so assemble's kept_of (P09) can name each kept take instead of one episode-wide
word (ep01: one narration still hid every other kept take)."""
from __future__ import annotations

from types import SimpleNamespace

from studio import take_ladder as tl
from studio.judges.verdict import Fault, Verdict


def plan_of(dialogue_shot=None):
    lines = [SimpleNamespace(kind="dialogue", shot=dialogue_shot)] if dialogue_shot is not None else []
    return SimpleNamespace(lines=lines, turn=lambda: SimpleNamespace(index=98),
                           button=lambda: SimpleNamespace(shot=99))


def verdict(*faults):
    return Verdict(judge="take_eye", version="1", passed=False, confidence=1.0, reads=1, faults=list(faults))


def test_every_fault_carries_its_takes_settled_word(tmp_path):
    home = tmp_path / "ep01"
    (home / "storyboard").mkdir(parents=True)
    (home / "storyboard" / "shot_03.png").write_bytes(b"png")
    (home / "takes" / "r2v").mkdir(parents=True)
    v = verdict(Fault(kind="content", where="T03"), Fault(kind="warp", where="T07"),
                Fault(kind="clones", where="T08"), Fault(kind="gait", where="T08"))
    out = tl.terminal(home, plan_of(dialogue_shot=8), v, order=[3, 7, 8])
    got = {(f.where, f.kind): f.evidence["settled"] for f in out.faults}
    assert got[("T03", "content")] == "still"
    assert got[("T07", "warp")] == "keep_best"
    assert got[("T08", "clones")] == "high" and got[("T08", "gait")] == "high"
    assert all("settled" in f.evidence for f in out.faults)


def test_the_mark_keeps_the_faults_own_evidence(tmp_path):
    home = tmp_path / "ep01"
    (home / "takes" / "r2v").mkdir(parents=True)
    out = tl.terminal(home, plan_of(), verdict(Fault(kind="warp", where="T07", evidence={"value": 1.9})), order=[7])
    assert out.faults[0].evidence == {"value": 1.9, "settled": "keep_best"}
