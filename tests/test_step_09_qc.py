"""Step 09 of the trailer stage: the master is measured, the floor decides.

`measure` and `recut` are the two seams -- one shells out to ffmpeg, the
other re-cuts the picture -- and both are replaced here, so the ladder is
tested on its own: a floor fail buys two recuts, then ships flagged.
"""
from __future__ import annotations

import json

import pytest

from scripts.trailer import step_09_qc as step
from studio import db
from studio.learnings import load
from studio.trailer_run import RunContext
from studio.trailer_stage_spec import QCReport


def report(lufs: float = -14.0, unbound: int = 0) -> QCReport:
    return QCReport(cuts=40, cuts_on_beat=0.85, cuts_on_downbeat=0.35, cuts_on_L0=1.0,
                    title_on_downbeat=True, integrated_lufs=lufs,
                    true_peak=-1.5, unbound_shots=unbound)


def fake_measure(reports: list[QCReport], calls: list[int]):
    """Each call writes qc.json the way qc.qc does and returns the next report."""
    def measure(ctx):
        found = reports[min(len(calls), len(reports) - 1)]
        calls.append(1)
        (ctx.out_dir / "qc.json").write_text(json.dumps(
            found.model_dump() | {"missing_cuts": [], "flags": found.flags,
                                  "floor_pass": found.floor_pass}), encoding="utf-8")
        return found
    return measure


@pytest.fixture()
def ctx(tmp_path, monkeypatch):
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    codex_id = db.insert_codex(conn, "Scarlet", codex_id="20260901000009")
    context = RunContext(conn, codex_id, tmp_path / "book", logs_root=tmp_path / "logs")
    context.out_dir.mkdir(parents=True)
    context.open_step("09")
    return context


def written(ctx) -> dict:
    return json.loads((ctx.out_dir / "qc.json").read_text(encoding="utf-8"))


class TestVerdict:
    def test_the_floor_is_loudness_peak_and_binding(self):
        assert step.verdict(report())[0]
        assert not step.verdict(report(lufs=-20.0))[0]
        assert not step.verdict(report(unbound=2))[0]
        assert "unbound" in step.verdict(report(unbound=2))[1]

    def test_flag_shipped_adds_a_sidecar_key_only(self, ctx):
        fake_measure([report()], [])(ctx)
        step.flag_shipped(ctx)
        assert written(ctx)["shipped_flagged"] is True
        assert QCReport.model_validate(written(ctx)).floor_pass

    def test_recut_asks_step_08(self, ctx, monkeypatch):
        from scripts.trailer import step_08_assemble
        asked: list[int] = []
        monkeypatch.setattr(step_08_assemble, "recut", lambda c, attempt: asked.append(attempt))
        step.recut(ctx, 2)
        assert asked == [2]


class TestStep:
    def test_floor_fail_recuts_then_ships_flagged(self, ctx, monkeypatch):
        calls, recuts = [], []
        monkeypatch.setattr(step, "measure", fake_measure([report(lufs=-20.0)], calls))
        monkeypatch.setattr(step, "recut", lambda c, attempt: recuts.append(attempt))
        step.run(ctx.codex_id, ctx)
        assert recuts == [1, 2] and len(calls) == 3
        assert written(ctx)["shipped_flagged"] is True and written(ctx)["floor_pass"] is False
        rows = load(ctx.learnings_path)
        assert [r.action for r in rows] == ["measure", "recut", "recut", "ship_flagged"]
        assert rows[-1].terminal and rows[0].gate == "floor" and "LUFS" in str(rows[0].measured)

    def test_a_recut_that_reaches_the_floor_ships_clean(self, ctx, monkeypatch):
        calls, recuts = [], []
        monkeypatch.setattr(step, "measure", fake_measure([report(lufs=-20.0), report()], calls))
        monkeypatch.setattr(step, "recut", lambda c, attempt: recuts.append(attempt))
        step.run(ctx.codex_id, ctx)
        assert recuts == [1] and "shipped_flagged" not in written(ctx)
        assert [r.action for r in load(ctx.learnings_path)] == ["measure"]

    def test_a_clean_master_is_not_recut(self, ctx, monkeypatch):
        calls, recuts = [], []
        monkeypatch.setattr(step, "measure", fake_measure([report()], calls))
        monkeypatch.setattr(step, "recut", lambda c, attempt: recuts.append(attempt))
        step.run(ctx.codex_id, ctx)
        assert recuts == [] and len(calls) == 1 and not ctx.learnings_path.exists()

    def test_measure_reads_the_master_in_the_out_dir(self, ctx, monkeypatch):
        from scripts.trailer import qc
        seen: list = []
        monkeypatch.setattr(qc, "qc", lambda out_dir: seen.append(out_dir) or report())
        assert step.measure(ctx).floor_pass and seen == [ctx.out_dir]
