"""Every rung a run takes is a learning.  The retrospect reads the file."""
import json

from studio.learnings import Learning, record, load, by_gate


def make(step="07", gate="identity", action="reroll", measured=0.61, attempt=1,
         terminal=False, frames=None):
    return Learning(step=step, gate=gate, measured=measured, threshold=0.75,
                    action=action, attempt=attempt, seconds=660.0, terminal=terminal,
                    frames=frames)


class TestRecord:
    def test_appends_one_json_line(self, tmp_path):
        path = tmp_path / "learnings.jsonl"
        record(path, make())
        record(path, make(attempt=2))
        lines = path.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 2
        assert json.loads(lines[1])["attempt"] == 2

    def test_has_a_utc_timestamp(self, tmp_path):
        path = tmp_path / "l.jsonl"
        record(path, make())
        assert json.loads(path.read_text(encoding="utf-8"))["ts"].endswith("Z")

    def test_round_trips(self, tmp_path):
        path = tmp_path / "l.jsonl"
        record(path, make())
        assert load(path)[0].gate == "identity"

    def test_a_cycle_row_keeps_its_frames(self, tmp_path):
        """The frame budget fits `a + b * frames` from cycle rows; a row that
        forgot its frames on re-read is a point on no line."""
        path = tmp_path / "l.jsonl"
        record(path, make(gate="cycle", measured=612.0, frames=243))
        assert load(path)[0].frames == 243

    def test_missing_file_loads_empty(self, tmp_path):
        assert load(tmp_path / "none.jsonl") == []


class TestRetrospect:
    def test_groups_by_step_and_gate_with_counts(self):
        rows = [make(), make(attempt=2), make(step="05", gate="similarity"),
                make(action="card", step="05", gate="similarity")]
        summary = by_gate(rows)
        assert summary[("07", "identity")]["count"] == 2
        assert summary[("05", "similarity")]["actions"] == {"reroll": 1, "card": 1}

    def test_terminal_rungs_are_counted_separately(self):
        rows = [make(action="reroll"), make(action="drop_beat", terminal=True)]
        assert by_gate(rows)[("07", "identity")]["terminal"] == 1
