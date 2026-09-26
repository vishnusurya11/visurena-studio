"""The drift guard (decision 2026-09-25, the Command Center): every `out:` the
registry declares for an episode or refs step is a path that step's own
`done()` reads as done.  For each step a tmp book gets the declared inputs
(the least `done()` needs), then the declared outputs with the least valid
content (a signed verdict where done() checks a signature, written by the
module's own signer); `done()` must say no with nothing on disk, no with the
inputs alone, and yes once the outputs are there -- and the files the step
would have written must be exactly what its `out:` globs match, so a glob that
names nothing, or an output nobody declared, fails here.  No script is
launched; no model, no GPU."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from studio import db, episode_clock, episode_home, eye_verdict, grid_layout, manifest, plan_verdict
from studio import refs_verdict, registry, step_runner, timeline_fresh
from studio import youtube_publish as yp
from studio.episode_spec import Episode
from studio.judges import master_eye
from studio.judges.verdict import Verdict
from studio.stage_run import StageContext
from tests.test_episode_writer import canned_plan

CODEX = "20260901000001"
UNIT = {"episode": ("ep04", 4), "refs": ("main", None)}
VACUOUS = {
    "refs/02": "sheets is done when nothing bound is missing: an empty book asks for no picture",
    "refs/03": "voices is done when nobody bound speaks: an empty book has no speaker",
}
"""Steps whose done() is vacuously true on an empty book; the inputs-alone test
still holds them to a no, and the outputs test to a yes."""


# ---- the book -------------------------------------------------------------------

def _ctx(tmp_path, stage: str) -> StageContext:
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    db.insert_codex(conn, "Book", codex_id=CODEX)
    unit, number = UNIT[stage]
    ctx = StageContext(conn, CODEX, tmp_path / "book", stage, unit=unit, number=number,
                       logs_root=tmp_path / "logs", busy=lambda: False, hold=tmp_path / "HOLD",
                       launch=lambda cmd: 0)
    ctx.home = episode_home.home(ctx.book_dir, number) if number else ctx.book_dir / "refs"
    ctx.extra = []
    return ctx


def _file(path: Path, data: bytes = b"bytes") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _json(path: Path, doc) -> Path:
    return episode_home.write_json(path, doc)


def _plan_doc() -> dict:
    """A plan the contract accepts whose one setup names a place."""
    plan = canned_plan(4)
    plan["setups"]["room"].update(location="yard", view="wide_establishing")
    return plan


def _lines_rows(plan: dict) -> list[dict]:
    return [{"index": line["index"], "seconds": 2.0} for line in plan["lines"]]


def _analysis(book: Path) -> None:
    _json(book / "analysis" / "scenes.json", {"scenes": []})
    _json(book / "analysis" / "characters" / "lead.json",
          {"name": "lead", "profile": {"design": {"sheet_prompt": "A man. Character sheet."}}})
    _json(book / "analysis" / "props" / "cup.json",
          {"name": "cup", "profile": {"design": {"sheet_prompt": "A cup. Prop sheet."}}})
    _json(book / "analysis" / "locations" / "yard.json", {"name": "yard"})


def _bible(book: Path, chapter: int | None = None) -> Path:
    rows = [{"entity_id": "lead", "kind": "character"}, {"entity_id": "cup", "kind": "prop"}]
    doc = {"refs": rows, **({"chapter": chapter} if chapter else {})}
    return _json(book / "refs" / "refs.json", doc)


def _sheets(book: Path) -> list[Path]:
    return [_file(book / "refs" / "characters" / "lead" / "sheet.png"),
            _file(book / "refs" / "props" / "cup" / "sheet.png")]


def _pack(book: Path) -> Path:
    rows = [{"path": "refs/characters/lead/sheet.png", "prompt": "x", "seed": 1},
            {"path": "refs/props/cup/sheet.png", "prompt": "y", "seed": 2}]
    return _file(book / "refs" / "pack.jsonl", "".join(json.dumps(r) + "\n" for r in rows).encode())


def _place(book: Path) -> Path:
    return _file(book / "refs" / "locations" / "yard" / "wide_establishing.png")


def _panels(home: Path, plan: dict) -> list[Path]:
    return [_file(home / "storyboard" / f"shot_{s['index']:02d}.png", b"p%d" % s["index"]) for s in plan["shots"]]


def _take(home: Path) -> Path:
    return _file(home / "takes" / "r2v" / "T01.mp4", b"take")


def _master(book: Path) -> Path:
    return _file(episode_home.master_path(book, 4, "r2v"), b"the cut")


def _rubric(home: Path, sha8: str) -> Path:
    passing = Verdict(judge="master_eye", version="1", passed=True, confidence=1.0, reads=3)
    return master_eye.write_rubric(home, sha8, passing)


# ---- episode: the inputs done() needs, then the outputs ---------------------------

def ep01_in(book, home):
    _json(book / "analysis" / "scenes.json", {"scenes": []})
    _bible(book)


def ep01_out(book, home):
    return [_bible(book, chapter=4)]


def ep02_in(book, home):
    _analysis(book)
    _json(book / "analysis" / "dq_rules.json", {})
    _json(book / "screenplay" / "feature" / "elements.json", [])
    _bible(book)


def ep02_out(book, home):
    plan = _json(home / "plan.json", _plan_doc())
    return [plan, plan_verdict.sign(plan, "holds", signed_by="judge:plan@1")]


def ep03_in(book, home):
    _json(home / "plan.json", _plan_doc())
    _analysis(book)


def ep03_out(book, home):
    return [_place(book)]


def ep04_in(book, home):
    _json(home / "plan.json", _plan_doc())
    _file(book / "cast" / "lead" / "voice" / "design.wav")


def ep04_out(book, home):
    plan = episode_home.read_json(home / "plan.json")
    wavs = [_file(home / "audio" / "lines" / f"L{l['index']:02d}.wav") for l in plan["lines"]]
    return wavs + [_json(home / "audio" / "lines" / "lines.json", _lines_rows(plan)),
                   _json(home / "review" / "speaker_check.json", {})]


def ep05_in(book, home):
    plan = _plan_doc()
    _json(home / "plan.json", plan)
    _json(home / "audio" / "lines" / "lines.json", _lines_rows(plan))


def ep05_out(book, home):
    plan = _plan_doc()
    stamp = timeline_fresh.fingerprint(Episode.model_validate(plan), _lines_rows(plan))
    return [_json(home / "placed.json", {"plan": stamp, "shots": []})]


def ep06_in(book, home):
    ep05_in(book, home)
    _json(home / "placed.json", {})


def ep06_out(book, home):
    return [_json(home / "takes" / "r2v" / "prompts.json", [])]


def ep07_in(book, home):
    _json(home / "plan.json", _plan_doc())
    _sheets(book)
    _place(book)


def ep07_out(book, home):
    plan = _plan_doc()
    rows = grid_layout.layout(plan["setups"], plan["shots"])
    grids = [_file(home / "storyboard" / "grids" / f"{grid_layout.name_of(4, row)}.png") for row in rows]
    return grids + [grid_layout.write(home, rows)]


def ep08_in(book, home):
    _json(home / "plan.json", _plan_doc())
    _file(home / "storyboard" / "grids" / "ep04_grid_room_3x2_a.png")


def ep08_out(book, home):
    plan = _plan_doc()
    panels = _panels(home, plan)
    rows = [{"shot": s["index"], "passed": True} for s in plan["shots"]]
    board = home / "storyboard"
    return panels + [_json(board / "panel_dq.json", rows), _json(board / "panel_content.json", rows),
                     _file(board / "contact.png"),
                     eye_verdict.sign(board, panels, "pass", "clean", signed_by="judge:panel_eye@1")]


def ep09_in(book, home):
    panels = _panels(home, _plan_doc())
    eye_verdict.sign(home / "storyboard", panels, "pass", "clean", signed_by="judge:panel_eye@1")
    _sheets(book)
    _file(home / "audio" / "lines" / "L00.wav")
    _json(home / "takes" / "r2v" / "prompts.json", [])


def ep09_out(book, home):
    take = _take(home)
    room = take.parent
    return [take, _json(room / "T01.dq.json", {}), _json(room / "T01.content.json", {}),
            eye_verdict.sign(room, [take], "pass", "moves", signed_by="judge:take_eye@1")]


def ep10_in(book, home):
    take = _take(home)
    eye_verdict.sign(take.parent, [take], "pass", "moves", signed_by="judge:take_eye@1")
    _json(home / "placed.json", {})
    _file(home / "audio" / "lines" / "L00.wav")


def ep10_out(book, home):
    return [_file(book / "title" / "ep04.mp4", b"card"), _master(book)]


def ep11_in(book, home):
    _master(book)
    _json(home / "plan.json", _plan_doc())
    _json(home / "placed.json", {})


def ep11_out(book, home):
    sha8 = yp.sha8(episode_home.master_path(book, 4, "r2v"))
    return [_json(home / "qc_r2v.json", {"passed": True, "sha8": sha8}), _rubric(home, sha8)]


def ep12_in(book, home):
    ep11_in(book, home)
    ep11_out(book, home)
    ep02_out(book, home)
    ep08_out(book, home)
    ep09_out(book, home)
    episode_clock.stamp(book, 4, "takes", 0, 10)


def ep12_out(book, home):
    sha8 = yp.sha8(episode_home.master_path(book, 4, "r2v"))
    return [_json(home / "manifest.json", {"qc": {"sha8": sha8}})]


# ---- refs ------------------------------------------------------------------------

def refs01_in(book, home):
    _analysis(book)


def refs01_out(book, home):
    return [_bible(book)]


def refs02_in(book, home):
    _analysis(book)
    _bible(book)


def refs02_out(book, home):
    return _sheets(book) + [_pack(book)]


def refs03_in(book, home):
    _json(book / "refs" / "refs.json", {"refs": [{"entity_id": "narrator", "kind": "character"}]})
    _json(book / "cast" / "narrator" / "character.json", {})
    _json(book / "episodes" / "ep01" / "plan.json", {"lines": [{"speaker": "narrator", "text": "x"}]})


def refs03_out(book, home):
    return [_file(book / "cast" / "narrator" / "voice" / "design.wav", b"wav")]


def refs04_in(book, home):
    _pack(book)
    _bible(book)
    _sheets(book)


def refs04_out(book, home):
    empty = manifest.UnitManifest(codex_id=CODEX, stage="refs", unit="main")
    return [refs_verdict.sign(book, "every face its own", signed_by="judge:look@1"),
            manifest.write_manifest(book, "refs", empty)]


MAKERS = {
    "episode/01": (ep01_in, ep01_out), "episode/02": (ep02_in, ep02_out), "episode/03": (ep03_in, ep03_out),
    "episode/04": (ep04_in, ep04_out), "episode/05": (ep05_in, ep05_out), "episode/06": (ep06_in, ep06_out),
    "episode/07": (ep07_in, ep07_out), "episode/08": (ep08_in, ep08_out), "episode/09": (ep09_in, ep09_out),
    "episode/10": (ep10_in, ep10_out), "episode/11": (ep11_in, ep11_out), "episode/12": (ep12_in, ep12_out),
    "refs/01": (refs01_in, refs01_out), "refs/02": (refs02_in, refs02_out),
    "refs/03": (refs03_in, refs03_out), "refs/04": (refs04_in, refs04_out),
}


# ---- the guard -------------------------------------------------------------------

def _every_step() -> list[str]:
    return [f"{stage}/{s['id']}" for stage in ("episode", "refs") for s in registry.steps(stage)]


def _params(skip_vacuous: bool = False) -> list:
    out = []
    for key in _every_step():
        marks = [pytest.mark.xfail(reason=VACUOUS[key], strict=True)] if skip_vacuous and key in VACUOUS else []
        out.append(pytest.param(key, id=key, marks=marks))
    return out


def _module(key: str):
    stage, step_id = key.split("/")
    return step_runner.import_step(stage, registry.step(stage, step_id))


def _rel(book: Path, path: Path) -> str:
    return Path(path).resolve().relative_to(book.resolve()).as_posix()


def test_every_episode_and_refs_step_has_a_maker_here():
    assert set(MAKERS) == set(_every_step())


@pytest.mark.parametrize("key", _params(skip_vacuous=True))
def test_nothing_on_disk_is_not_done(tmp_path, key):
    ctx = _ctx(tmp_path, key.split("/")[0])
    assert _module(key).done(ctx) is False


@pytest.mark.parametrize("key", _params())
def test_the_inputs_alone_are_not_done(tmp_path, key):
    ctx = _ctx(tmp_path, key.split("/")[0])
    MAKERS[key][0](ctx.book_dir, ctx.home)
    assert _module(key).done(ctx) is False


@pytest.mark.parametrize("key", _params())
def test_the_declared_outputs_are_exactly_what_done_reads(tmp_path, key):
    stage, step_id = key.split("/")
    ctx = _ctx(tmp_path, stage)
    seed, make = MAKERS[key]
    seed(ctx.book_dir, ctx.home)
    written = {_rel(ctx.book_dir, p) for p in make(ctx.book_dir, ctx.home)}
    declared = set(manifest.matched(ctx.book_dir, registry.outputs_of(stage, step_id, ctx.unit)))
    assert declared == written, f"{key}: out: names {declared - written or 'nothing extra'}; " \
                                f"the step writes {written - declared or 'nothing undeclared'}"
    assert _module(key).done(ctx) is True


@pytest.mark.parametrize("key", _params())
def test_every_declared_input_glob_names_a_file_the_step_reads(tmp_path, key):
    """An `in:` that matches nothing on a book the step can finish is a typo."""
    stage, step_id = key.split("/")
    ctx = _ctx(tmp_path, stage)
    seed, make = MAKERS[key]
    seed(ctx.book_dir, ctx.home)
    make(ctx.book_dir, ctx.home)
    for pattern in registry.inputs_of(stage, step_id, ctx.unit):
        assert manifest.matched(ctx.book_dir, [pattern]), f"{key}: in: {pattern} names nothing"
