"""P08 item 7: a take kept with a dropped cure class (warp Se-only, ledger 0/4; the input-borne
kinds the board owns) gets an audit_rows entry (take, class, scores) so the owner's flagged list
is a short watch-list, not a refusal."""
from __future__ import annotations

from types import SimpleNamespace

from studio import audit_rows, take_ladder as tl
from studio.judges.verdict import Fault, Verdict


def test_the_dropped_classes_are_named_with_their_scores():
    fs = [Fault(kind="warp", where="T21", evidence={"value": -0.64}, note="fail: S -0.64 Se 3.55 over 100% tracked"),
          Fault(kind="clones", where="T08"), Fault(kind="held", where="T05")]
    rows = tl.watch_rows(fs)
    assert {(r["take"], r["class"]) for r in rows} == {("T21", "warp_se"), ("T08", "clones")}
    warp = next(r for r in rows if r["take"] == "T21")
    assert warp["scores"] == {"S": -0.64, "Se": 3.55}


def test_an_s_fail_warp_is_not_a_dropped_class():
    f = Fault(kind="warp", where="T07", evidence={"value": 3.0}, note="fail: S 3.0 Se 1.0 over 90% tracked")
    assert tl.watch_rows([f]) == []


def test_terminal_for_appends_one_audit_row_for_the_watch_list(tmp_path):
    home = tmp_path / "ep01"
    (home / "takes" / "r2v").mkdir(parents=True)
    ctx = SimpleNamespace(home=home, book_dir=tmp_path, unit="ep01", log=lambda *a, **k: None)
    plan = SimpleNamespace(lines=[], turn=lambda: SimpleNamespace(index=98), button=lambda: SimpleNamespace(shot=99))
    v = Verdict(judge="take_eye", version="1", passed=False, confidence=1.0, reads=1,
                faults=[Fault(kind="warp", where="T21", evidence={"value": -0.6},
                              note="fail: S -0.6 Se 3.4 over 90% tracked")])
    tl.terminal_for(ctx, plan)(v)
    rows = audit_rows.load(tmp_path)
    assert len(rows) == 1 and rows[0].terminal == "watch"
    assert rows[0].faults[0]["class"] == "warp_se" and rows[0].faults[0]["take"] == "T21"
