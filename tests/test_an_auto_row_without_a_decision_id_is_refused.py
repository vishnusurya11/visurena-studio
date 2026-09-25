"""An `auto` row is a retirement, and a retirement is a decision with a date:
a row without an id, with a malformed id, or with an id DECISIONS.md does not
carry is refused when read.  `shadow` is a field, never a state."""
from __future__ import annotations

import pytest

from studio import gate_policy


def gates(tmp_path, row: str):
    path = tmp_path / "gates.yaml"
    path.write_text("gates:\n  episode:\n    EYE_PANELS: " + row + "\n", encoding="utf-8")
    decisions = tmp_path / "DECISIONS.md"
    decisions.write_text("Decision id: `2026-09-24-a-decided-thing`\n", encoding="utf-8")
    return path, decisions


def test_auto_without_a_decision_is_refused(tmp_path):
    path, decisions = gates(tmp_path, "{ state: auto, judge: panel_eye@1 }")
    with pytest.raises(SystemExit, match="decision"):
        gate_policy.of("episode", "EYE_PANELS", path=path, decisions=decisions)


def test_a_malformed_id_is_refused(tmp_path):
    path, decisions = gates(tmp_path, "{ state: auto, judge: panel_eye@1, decision: because-i-said }")
    with pytest.raises(SystemExit, match="YYYY-MM-DD"):
        gate_policy.of("episode", "EYE_PANELS", path=path, decisions=decisions)


def test_an_id_absent_from_decisions_md_is_refused(tmp_path):
    path, decisions = gates(tmp_path, "{ state: auto, judge: panel_eye@1, decision: 2026-09-24-never-written }")
    with pytest.raises(SystemExit, match="DECISIONS.md"):
        gate_policy.of("episode", "EYE_PANELS", path=path, decisions=decisions)


def test_a_decided_auto_row_is_read(tmp_path):
    path, decisions = gates(tmp_path, "{ state: auto, judge: panel_eye@1, decision: 2026-09-24-a-decided-thing }")
    policy = gate_policy.of("episode", "EYE_PANELS", path=path, decisions=decisions)
    assert policy.state == "auto" and policy.judge == "panel_eye@1"


def test_a_human_row_needs_no_decision(tmp_path):
    path, decisions = gates(tmp_path, "{ state: human }")
    assert gate_policy.of("episode", "EYE_PANELS", path=path, decisions=decisions).state == "human"


def test_shadow_is_a_field_not_a_state(tmp_path):
    path, decisions = gates(tmp_path, "{ state: shadow, judge: panel_eye@1 }")
    with pytest.raises(SystemExit, match="state"):
        gate_policy.of("episode", "EYE_PANELS", path=path, decisions=decisions)
