"""ep21, 2026-10-08 07:30-07:40Z: step 05 rewrote the signed plan (respot, then
the measured-hole trim) without recording a cure; the re-run was refused at
step 06, the signature was left lapsed by unrecorded links, and the next
launch's step 02 -- with no takes yet to hold it in report mode -- re-planned a
31-shot signed plan over its voices and timeline.  Every downstream rewrite of
plan.json is recorded as a cure, so step 02's resigned() can carry the
signature over the chain when the battery is clean."""
from __future__ import annotations

import json
from types import SimpleNamespace

from scripts.episode import step_05_timeline as step
from studio import episode_home, plan_cures, plan_provenance, plan_verdict


def _home(tmp_path):
    book = tmp_path / "book"
    plan = episode_home.plan_path(book, 7)
    plan.parent.mkdir(parents=True)
    plan.write_text(json.dumps({"shots": [{"index": 0, "coda_s": 2.0}], "lines": []}), encoding="utf-8")
    return book, plan


def test_a_trim_is_recorded_as_a_cure(tmp_path, monkeypatch):
    book, plan = _home(tmp_path)
    before = plan_verdict.plan_sha8(plan)
    monkeypatch.setattr(episode_home, "write_plan", lambda path, doc: path.write_text(json.dumps(doc), encoding="utf-8"))

    def trim(doc, placed):
        doc["shots"][0]["coda_s"] = 0.5
        return 1
    monkeypatch.setattr(plan_cures, "trim_measured_holes", trim)
    ctx = SimpleNamespace(book_dir=book, number=7)
    assert step.trimmed(ctx, {"shots": []}) == 1
    chain = plan_provenance.chain(plan.parent, before, plan_verdict.plan_sha8(plan))
    assert chain == ["trim_measured_holes"]


def test_nothing_trimmed_records_nothing(tmp_path, monkeypatch):
    book, plan = _home(tmp_path)
    monkeypatch.setattr(plan_cures, "trim_measured_holes", lambda doc, placed: 0)
    ctx = SimpleNamespace(book_dir=book, number=7)
    assert step.trimmed(ctx, {"shots": []}) == 0
    assert not (plan.parent / plan_provenance.CURES_FILE).exists()


def test_a_respot_writes_only_when_a_cut_moved_and_records_it(tmp_path, monkeypatch):
    import importlib
    respot = importlib.import_module("scripts.episode.respot")
    book, plan = _home(tmp_path)
    raw = plan.read_bytes()
    monkeypatch.setattr(episode_home, "write_plan", lambda path, doc: path.write_text(json.dumps(doc, indent=1), encoding="utf-8"))
    doc = json.loads(raw)
    assert respot.commit_plan(plan, doc, 0) is False and plan.read_bytes() == raw     # nothing moved: no write
    before = plan_verdict.plan_sha8(plan)
    doc["shots"][0]["cuts"] = [{"at_s": 1.5}]
    assert respot.commit_plan(plan, doc, 1) is True
    assert plan_provenance.chain(plan.parent, before, plan_verdict.plan_sha8(plan)) == ["respot"]
