"""gates.yaml: every refs and episode gate is `auto`, names its judge, and carries
a decision id of the form YYYY-MM-DD-<slug> that appears literally in
docs/DECISIONS.md.  No row parks on a person."""
from __future__ import annotations

from studio import gate_policy

GATES = {"refs": {"LOOK"},
         "episode": {"PLAN", "LAYOUT", "EYE_PANELS", "EYE_TAKES", "MASTER", "RENDER"}}


def test_the_named_gates_are_all_there():
    doc = gate_policy.load()
    for stage, names in GATES.items():
        assert set(doc["gates"][stage]) == names, stage


def test_every_row_is_auto_with_a_decided_id():
    for stage, gate, row in gate_policy.rows(gate_policy.load()):
        assert row["state"] == "auto", f"{stage}/{gate}"
        assert gate_policy.DECISION_ID.match(row["decision"]), f"{stage}/{gate}: {row['decision']}"
        assert gate_policy.decided(row["decision"]), f"{stage}/{gate}: {row['decision']} not in DECISIONS.md"


def test_every_judged_row_names_its_judge_and_version():
    for stage, gate, row in gate_policy.rows(gate_policy.load()):
        if gate == "RENDER":
            continue
        name, _, version = row["judge"].partition("@")
        assert name and version.isdigit(), f"{stage}/{gate}: {row.get('judge')!r}"


def test_of_reads_every_row_without_refusing():
    for stage, gate, _row in gate_policy.rows(gate_policy.load()):
        policy = gate_policy.of(stage, gate)
        assert policy.state == "auto" and policy.decision


def test_a_gate_nobody_registered_is_human():
    assert gate_policy.of("episode", "NOT_A_GATE").state == "human"
