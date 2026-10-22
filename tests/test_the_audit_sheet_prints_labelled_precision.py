"""The audit sheet says, per gate, how far its flags are worth trusting (fleet H ruling A13, A16).

Above the flagged cards, one table: each gate's terminal rows, its faults
counted once per (artefact, rule) -- three landmark words on one panel are
one -- and its labelled precision: the owner's casebook rows on the
artefacts the gate flagged, k faults of n, with the one-sided 95 %
Clopper-Pearson lower bound; "unlabelled" when the owner has looked at none.
The flagged-takes headline counts takes that shipped over a hard refusal and
says that soft deductions are not counted there (fleet H skeptic M2).
"""
from __future__ import annotations

import json

from scripts.audit import sheet
from studio import audit_rows, casebook, intervals
from studio.casebook import Row

WORDS = ("arch", "barn", "bridge")


def book(tmp_path):
    home = tmp_path / "book"
    faults = [{"kind": "landmark", "where": "shot_00", "note": f"{w} drawn where the place names none"} for w in WORDS]
    faults.append({"kind": "landmark", "where": "shot_03", "note": "lake drawn where the place names none"})
    audit_rows.append(home, {"unit": "ep01", "gate": "EYE_PANELS", "judge": "judge:panel_eye@1", "sha8": "c7e3eb93",
                             "artefact": "episodes/ep01/storyboard/eye_c7e3eb93.json", "faults": faults,
                             "terminal": "flag"})
    return home


def owner(home, path, verdict, cls=None):
    casebook.append_owner(home / "casebook", Row(codex="c", unit="ep01", kind="panel", path=path, verdict=verdict,
                                                 fault_class=cls, verdict_by="owner"))


def test_a_rule_counts_once_per_artefact():
    faults = [{"kind": "landmark", "where": "shot_00"}] * 3 + [{"kind": "landmark", "where": "shot_03"}]
    row = audit_rows.AuditRow(unit="ep01", gate="EYE_PANELS", judge="j", faults=faults, terminal="flag")
    assert sheet.distinct_faults([row]) == 2


def test_a_gate_nobody_labelled_prints_unlabelled(tmp_path):
    home = book(tmp_path)
    page = sheet.write(home, "ep01").read_text(encoding="utf-8")
    assert "labelled precision" in page and "unlabelled" in page
    assert "<td class=n>4</td><td class=n>2</td>" in page


def test_a_labelled_gate_prints_k_of_n_and_its_bound(tmp_path):
    home = book(tmp_path)
    owner(home, "episodes/ep01/storyboard/shot_00.png", "fault", "landform")
    owner(home, "episodes/ep01/storyboard/shot_03.png", "pass")
    owner(home, "episodes/ep01/storyboard/shot_07.png", "fault", "landform")
    page = sheet.write(home, "ep01").read_text(encoding="utf-8")
    assert f"1/2 (one-sided 95 % CP lower {intervals.cp_lower(1, 2):.2f})" in page


def test_the_flagged_takes_headline_keeps_soft_deductions_apart(tmp_path):
    home = book(tmp_path)
    work = home / "episodes" / "ep01" / "takes" / "work"
    work.mkdir(parents=True)
    (work / "flagged_takes.json").write_text(json.dumps([{"take": 3, "seconds_in_master": 4.0, "rows": ["warp"],
                                                          "notes": [], "severity": "normal"}]), encoding="utf-8")
    page = sheet.write(home, "ep01").read_text(encoding="utf-8")
    assert "1 shipped over a hard refusal" in page and "soft deductions are not counted here" in page
