"""The PLAN signature: a verdict file bound to the plan's sha8.

A verdict written for one plan does not sign a rewritten one; the sha in the
file and the sha of the bytes on disk have to agree, and only APPROVE counts.
"""
from __future__ import annotations

import json

from studio import plan_verdict


def _plan(tmp_path, body="{\"a\": 1}"):
    plan = tmp_path / "plan.json"
    plan.write_text(body, encoding="utf-8")
    return plan


def test_the_sha8_is_eight_hex_characters_of_the_bytes(tmp_path):
    plan = _plan(tmp_path)
    got = plan_verdict.plan_sha8(plan)
    assert len(got) == 8 and int(got, 16) >= 0
    assert got == plan_verdict.plan_sha8(plan)


def test_the_verdict_sits_beside_the_plan(tmp_path):
    plan = _plan(tmp_path)
    assert plan_verdict.verdict_path(plan) == tmp_path / "plan.verdict.json"


def test_no_verdict_file_means_not_current(tmp_path):
    assert plan_verdict.current(_plan(tmp_path)) is False


def test_sign_writes_the_four_fields_and_the_plan_is_then_current(tmp_path):
    plan = _plan(tmp_path)
    out = plan_verdict.sign(plan, "read it; the turn lands", date="2026-09-24")
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert set(doc) == {"plan_sha8", "verdict", "note", "date"}
    assert doc["verdict"] == "APPROVE" and doc["note"] == "read it; the turn lands"
    assert doc["date"] == "2026-09-24" and doc["plan_sha8"] == plan_verdict.plan_sha8(plan)
    assert plan_verdict.current(plan) is True


def test_sign_dates_today_when_no_date_is_given(tmp_path):
    doc = json.loads(plan_verdict.sign(_plan(tmp_path), "ok").read_text(encoding="utf-8"))
    assert len(doc["date"]) == 10 and doc["date"][4] == "-"


def test_a_verdict_for_another_sha_is_stale(tmp_path):
    plan = _plan(tmp_path)
    plan_verdict.sign(plan, "signed the first draft")
    plan.write_text("{\"a\": 2}", encoding="utf-8")
    assert plan_verdict.current(plan) is False


def test_only_approve_signs(tmp_path):
    plan = _plan(tmp_path)
    plan_verdict.verdict_path(plan).write_text(json.dumps(
        {"plan_sha8": plan_verdict.plan_sha8(plan), "verdict": "REJECT", "note": "", "date": ""}),
        encoding="utf-8")
    assert plan_verdict.current(plan) is False


def test_a_missing_plan_is_never_current(tmp_path):
    assert plan_verdict.current(tmp_path / "plan.json") is False


def test_the_cli_signs_the_plan_of_a_book_and_prints_the_path(tmp_path, monkeypatch, capsys):
    from scripts.episode import sign_plan
    book = tmp_path / "20260901000001_book"
    plan = book / "episodes" / "ep03" / "plan.json"
    plan.parent.mkdir(parents=True)
    plan.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(sign_plan.episode_home, "book_dir", lambda codex: book)
    assert sign_plan.main(["sign_plan.py", "20260901000001", "3", "the button is right"]) == 0
    assert plan_verdict.current(plan)
    assert str(plan.with_name("plan.verdict.json")) in capsys.readouterr().out


def test_the_cli_refuses_without_a_note():
    from scripts.episode import sign_plan
    import pytest
    with pytest.raises(SystemExit):
        sign_plan.main(["sign_plan.py", "20260901000001", "3"])
