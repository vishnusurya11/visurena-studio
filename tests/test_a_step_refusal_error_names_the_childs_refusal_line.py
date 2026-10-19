"""A step failure's RuntimeError carries the last REFUSED / CAP line the step printed (P12;
the brain parked blind on `REFUSED: say_lines.py exit 1` with no gate and no value)."""
import types

import pytest

from studio import db, step_runner
from studio.stage_run import StageContext


@pytest.fixture()
def conn(tmp_path):
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    return connection


def _ctx(conn, tmp_path):
    codex_id = db.insert_codex(conn, "Book", codex_id="20260901000001")
    return StageContext(conn, codex_id, tmp_path / "book", "episode", unit="ep01", number=1,
                        logs_root=tmp_path / "logs", busy=lambda: False,
                        hold=tmp_path / "RENDER_HOLD", launch=lambda cmd: 0)


def _step(run):
    return types.SimpleNamespace(STEP_ID="04", NAME="record", GPU=False, run=run, done=lambda c: False)


def test_the_error_names_the_last_refusal_line(conn, tmp_path):
    def run(c):
        print("CAP lines: 3/8 rounds, 10:02, kept best (0 advisories)")
        print("REFUSED: G-VOICE line 11 heard 'check' for 'cheque'")
        raise SystemExit("REFUSED: scripts/episode/say_lines.py exit 1")
    with pytest.raises(RuntimeError) as err:
        step_runner.run_steps(_ctx(conn, tmp_path), [_step(run)])
    text = str(err.value)
    assert "say_lines.py exit 1" in text and "G-VOICE line 11" in text


def test_a_cap_line_is_named_when_no_refusal_follows(conn, tmp_path):
    def run(c):
        print("CAP lines: 3/8 rounds, 10:02, kept best (0 advisories)")
        raise SystemExit("exit 1")
    with pytest.raises(RuntimeError, match="CAP lines: 3/8"):
        step_runner.run_steps(_ctx(conn, tmp_path), [_step(run)])


def test_a_clean_failure_text_is_unchanged(conn, tmp_path):
    def run(c):
        raise SystemExit("REFUSED: no panel verdict")
    with pytest.raises(RuntimeError) as err:
        step_runner.run_steps(_ctx(conn, tmp_path), [_step(run)])
    assert str(err.value) == "REFUSED: no panel verdict"


def test_the_outcome_carries_its_step(conn, tmp_path):
    out = step_runner.run_steps(_ctx(conn, tmp_path), [_step(lambda c: None)])
    assert out == "completed" and out.step == "04"
