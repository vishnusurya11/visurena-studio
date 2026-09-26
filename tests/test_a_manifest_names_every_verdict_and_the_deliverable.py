"""The manifest crosses the department boundary (decision 2026-09-25, the Command
Center): a department's last step writes one `manifest.json` at the unit's home,
pydantic `UnitManifest` -- the inputs and outputs the registry declares matched
on disk with their sha8, every verdict file with who signed it and the word as
it stands, the steps' latest events, the cost.  Paths are book-relative posix.
Nothing here launches a script or touches a model."""
from __future__ import annotations

import json

import pytest

from scripts.episode import step_12_deliver
from scripts.refs import step_04_verdict
from studio import db, episode_clock, episode_home, eye_verdict, manifest, plan_verdict, refs_verdict
from studio import youtube_publish as yp
from studio.judges import master_eye
from studio.judges.verdict import Verdict
from studio.stage_run import StageContext
from tests import look_fixtures as lf

CODEX = "20260901000001"


def _ctx(tmp_path, book, stage, **kw):
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    db.insert_codex(conn, "Book", codex_id=CODEX)
    ctx = StageContext(conn, CODEX, book, stage, logs_root=tmp_path / "logs", busy=lambda: False,
                       hold=tmp_path / "HOLD", launch=lambda cmd: 0, **kw)
    ctx.extra = []
    return ctx


@pytest.fixture()
def episode(tmp_path):
    """An episode unit with every verdict signed, a master, its QC and a clock row."""
    book = tmp_path / "book"
    ctx = _ctx(tmp_path, book, "episode", unit="ep04", number=4)
    ctx.home = episode_home.home(book, 4)
    home = ctx.home
    episode_home.write_json(book / "refs" / "refs.json", {"chapter": 4, "refs": []})
    plan = episode_home.write_json(home / "plan.json", {"number": 4})
    plan_verdict.sign(plan, "the plan holds", signed_by="judge:plan@1")
    panel = home / "storyboard" / "shot_01.png"
    panel.parent.mkdir(parents=True)
    panel.write_bytes(b"panel")
    eye_verdict.sign(home / "storyboard", [panel], "pass", "clean", signed_by="judge:panel_eye@1")
    take = home / "takes" / "r2v" / "T01.mp4"
    take.parent.mkdir(parents=True)
    take.write_bytes(b"take")
    eye_verdict.sign(take.parent, [take], "flagged", "kept best", signed_by="judge:take_eye@1",
                     terminal="keep_best")
    master = episode_home.master_path(book, 4, "r2v")
    master.parent.mkdir(parents=True)
    master.write_bytes(b"the cut")
    sha8 = yp.sha8(master)
    episode_home.write_json(home / "qc_r2v.json", {"passed": True, "sha8": sha8})
    master_eye.write_rubric(home, sha8, Verdict(judge="master_eye", version="1", passed=True,
                                                confidence=1.0, reads=3, terminal="flag"))
    episode_clock.stamp(book, 4, "takes", 0, 10)
    ctx.tracker.event("11", "completed")
    return ctx


def test_sha8_is_the_first_eight_hex_of_sha256_the_verdicts_already_use(tmp_path):
    f = tmp_path / "f.bin"
    f.write_bytes(b"bytes")
    assert manifest.sha8_of(f) == yp.sha8(f) == plan_verdict.plan_sha8(f)
    assert len(manifest.sha8_of(f)) == 8


def test_every_verdict_is_named_with_its_signer_its_word_and_its_rung(episode):
    m = manifest.manifest_for(episode, "episode")
    rows = {v.gate: v for v in m.verdicts}
    assert list(rows) == ["PLAN", "EYE_PANELS", "EYE_TAKES", "MASTER"]
    assert rows["PLAN"].signed_by == "judge:plan@1" and rows["PLAN"].word == "APPROVE"
    assert rows["PLAN"].path == "episodes/ep04/plan.verdict.json"
    assert rows["EYE_PANELS"].word == "pass" and rows["EYE_PANELS"].terminal == ""
    assert rows["EYE_TAKES"].word == "flagged" and rows["EYE_TAKES"].terminal == "keep_best"
    assert rows["EYE_TAKES"].path.startswith("episodes/ep04/takes/r2v/eye_")
    assert rows["MASTER"].signed_by == "judge:master_eye@1" and rows["MASTER"].terminal == "flag"
    assert all("\\" not in v.path and not v.path.startswith("/") for v in m.verdicts)


def test_an_owner_signed_verdict_reads_as_the_owner(episode):
    plan_verdict.sign(episode.home / "plan.json", "looked")
    rows = {v.gate: v for v in manifest.manifest_for(episode, "episode").verdicts}
    assert rows["PLAN"].signed_by == "owner" and rows["PLAN"].word == "APPROVE"


def test_the_outputs_are_the_registrys_matched_on_disk_with_their_bytes_named(episode):
    m = manifest.manifest_for(episode, "episode")
    master = episode_home.master_path(episode.book_dir, 4, "r2v")
    by_path = {o.path: o for o in m.outputs}
    assert by_path["episodes/ep04/cut/master_r2v.mp4"].sha8 == yp.sha8(master)
    assert by_path["episodes/ep04/cut/master_r2v.mp4"].kind == "edit"
    assert by_path["episodes/ep04/plan.json"].kind == "plan"
    assert "episodes/ep04/manifest.json" not in by_path          # never names itself
    assert len(by_path) == len(m.outputs)                       # one row per file
    assert {i.path for i in m.inputs} >= {"refs/refs.json", "episodes/ep04/qc_r2v.json"}
    assert next(i for i in m.inputs if i.path == "refs/refs.json").sha8 == manifest.sha8_of(
        episode.book_dir / "refs" / "refs.json")


def test_the_steps_and_the_cost_come_from_the_ledger_and_the_clock(episode):
    m = manifest.manifest_for(episode, "episode")
    assert m.codex_id == CODEX and m.stage == "episode" and m.unit == "ep04"
    assert m.steps == {"11": "completed"}
    assert m.cost.wall_seconds == 10.0 and m.cost.usd == 0.0


def test_a_unit_with_nothing_on_disk_is_an_empty_manifest_not_an_error(tmp_path):
    ctx = _ctx(tmp_path, tmp_path / "book", "episode", unit="ep09", number=9)
    m = manifest.manifest_for(ctx, "episode")
    assert m.inputs == [] and m.outputs == [] and m.verdicts == [] and m.steps == {}
    assert m.cost.wall_seconds == 0.0 and m.cost.gpu_seconds == 0.0


def test_write_then_read_round_trips_at_the_units_home(episode):
    m = manifest.manifest_for(episode, "episode")
    path = manifest.write_manifest(episode.book_dir, "episodes/ep04", m, extra={"master": "x"})
    assert path == episode.home / "manifest.json"
    assert json.loads(path.read_text(encoding="utf-8"))["master"] == "x"
    assert manifest.read_manifest(episode.book_dir, "episodes/ep04") == m
    assert manifest.read_manifest(episode.book_dir, "episodes/ep05") is None


def test_the_home_is_where_the_deliverable_lives():
    assert manifest.home_of("episode", "ep04") == "episodes/ep04"
    assert manifest.home_of("refs", "main") == "refs"


def test_deliver_writes_the_contract_beside_what_it_always_wrote(episode, monkeypatch, capsys):
    monkeypatch.setattr(episode_home, "LIBRARY", episode.book_dir.parent)
    step_12_deliver.run(episode)
    doc = episode_home.read_json(episode.home / "manifest.json")
    assert doc["master"] == "book/episodes/ep04/cut/master_r2v.mp4" and doc["qc"]["passed"] is True
    got = manifest.read_manifest(episode.book_dir, "episodes/ep04")
    assert [v.gate for v in got.verdicts] == ["PLAN", "EYE_PANELS", "EYE_TAKES", "MASTER"]
    assert got.steps == {"11": "completed"}
    assert step_12_deliver.done(episode)


def test_the_refs_verdict_step_writes_the_bibles_manifest_after_the_sign(tmp_path):
    book = lf.a_book(tmp_path)
    lf.character(book, "a")
    ctx = lf.a_ctx(tmp_path, book, **lf.tools(reader=lf.reader_of({"a": "base"})))
    step_04_verdict.run(ctx)
    got = manifest.read_manifest(book, "refs")
    assert got.stage == "refs" and got.unit == "main"
    assert [(v.gate, v.signed_by, v.word) for v in got.verdicts] == [("LOOK", "judge:look@1", "APPROVE")]
    assert {o.path for o in got.outputs} >= {"refs/verdict.json", "refs/characters/a/sheet.png", "refs/pack.jsonl"}
    assert refs_verdict.current(book)["pack_sha8"] == refs_verdict.pack_sha8(book)   # the sign is untouched
