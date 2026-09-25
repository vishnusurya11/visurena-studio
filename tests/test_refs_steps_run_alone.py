"""Every refs step on its own: done() reads the disk, run() launches the script it
wraps through the context (a fake launch here), and step 01 refuses without the
chapter and cast it needs.  No GPU, no model, no library."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from agents.look_back import LookReading
from scripts.refs import step_01_canon as canon
from scripts.refs import step_02_sheets as sheets
from scripts.refs import step_03_voices as voices
from studio import cast_home, db
from studio.stage_run import StageContext

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def book(tmp_path):
    book = tmp_path / "book"
    (book / "refs").mkdir(parents=True)
    return book


def a_ctx(tmp_path, book, extra=(), launched=None):
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    codex = "20260901000001"
    if conn.execute("SELECT 1 FROM codex WHERE id = ?", (codex,)).fetchone() is None:
        db.insert_codex(conn, "Book", codex_id=codex)
    launch = (lambda cmd: launched.append(cmd) or 0) if launched is not None else (lambda cmd: 0)
    ctx = StageContext(conn, codex, book, "refs", unit="main", logs_root=tmp_path / "logs",
                       busy=lambda: False, hold=tmp_path / "HOLD", launch=launch)
    ctx.extra = list(extra)
    return ctx


def character(book, who, prompt="A man in a coat. Character sheet."):
    folder = book / "analysis" / "characters"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{who}.json").write_text(json.dumps(
        {"name": who, "profile": {"design": {"sheet_prompt": prompt}}}), encoding="utf-8")


# --- 01 canon ---------------------------------------------------------------

def test_step_01_refuses_without_a_chapter_and_a_cast(tmp_path, book):
    with pytest.raises(SystemExit, match="--chapter"):
        canon.run(a_ctx(tmp_path, book))
    with pytest.raises(SystemExit, match="--cast"):
        canon.run(a_ctx(tmp_path, book, ["--chapter=3"]))


def test_step_01_launches_cast_rows_with_the_chapter_and_every_cast_argument(tmp_path, book):
    launched = []
    ctx = a_ctx(tmp_path, book, ["--chapter=3", "--cast=a=Alpha:male,b"], launched)
    canon.run(ctx)
    assert launched[0][1:] == ["scripts/refs/cast_rows.py", ctx.codex_id, "3", "a=Alpha:male", "b"]
    assert json.loads((book / "refs" / "refs.json").read_text(encoding="utf-8"))["refs"] == []


def test_step_01_is_done_when_refs_json_is_stamped_for_the_chapter_with_the_cast(tmp_path, book):
    ctx = a_ctx(tmp_path, book, ["--chapter=3", "--cast=a,b=Beta:female"])
    assert canon.done(ctx) is False
    rows = [{"entity_id": "a", "kind": "character"}, {"entity_id": "b", "kind": "character"}]
    (book / "refs" / "refs.json").write_text(json.dumps({"chapter": 2, "refs": rows}), encoding="utf-8")
    assert canon.done(ctx) is False
    (book / "refs" / "refs.json").write_text(json.dumps({"chapter": 3, "refs": rows[:1]}), encoding="utf-8")
    assert canon.done(ctx) is False
    (book / "refs" / "refs.json").write_text(json.dumps({"chapter": 3, "refs": rows}), encoding="utf-8")
    assert canon.done(ctx) is True


def test_step_01_without_a_chapter_is_done_once_refs_json_exists(tmp_path, book):
    ctx = a_ctx(tmp_path, book)
    assert canon.done(ctx) is False
    (book / "refs" / "refs.json").write_text("{}", encoding="utf-8")
    assert canon.done(ctx) is True


# --- 02 sheets --------------------------------------------------------------

def test_step_02_is_done_only_when_every_pending_picture_is_on_disk(tmp_path, book):
    character(book, "narrator")
    ctx = a_ctx(tmp_path, book)
    assert sheets.done(ctx) is False
    picture = book / "refs" / "characters" / "narrator" / "sheet.png"
    picture.parent.mkdir(parents=True)
    picture.write_bytes(b"png")
    assert sheets.done(ctx) is True


def test_step_02_launches_build_pack_on_the_gpu_with_the_kind_and_only_flags_split(tmp_path, book):
    character(book, "narrator")
    launched = []
    ctx = a_ctx(tmp_path, book, ["--kind=characters", "--only=narrator,curate"], launched)
    sheets.run(ctx)
    assert launched[0][1:] == ["scripts/refs/build_pack.py", ctx.codex_id,
                               "--kind=characters", "--only=narrator", "--only=curate"]
    assert sheets.GPU is True


def test_step_02_look_back_is_advisory_it_warns_and_never_refuses(tmp_path, book, capsys):
    character(book, "narrator", "A man wearing a top hat, holding a cane.")
    ctx = a_ctx(tmp_path, book)
    asked = sheets.jobs(ctx)
    picture = book / "refs" / "characters" / "narrator" / "sheet.png"
    picture.parent.mkdir(parents=True)
    picture.write_bytes(b"png")
    look = lambda path, prompt: LookReading(seen=["a man", "a hat"], missing=["cane"], text=False)
    misses = sheets.advise(ctx, asked, look=look)
    assert misses and "cane" in misses[0]
    assert "WARNING" in capsys.readouterr().out
    logged = "".join(p.read_text(encoding="utf-8") for p in (tmp_path / "logs").rglob("*.log"))
    assert "cane" in logged


def test_step_02_look_back_skips_a_picture_that_was_not_drawn(tmp_path, book):
    character(book, "narrator")
    ctx = a_ctx(tmp_path, book)
    calls = []
    sheets.advise(ctx, sheets.jobs(ctx), look=lambda p, q: calls.append(p))
    assert calls == []


# --- 03 voices --------------------------------------------------------------

def test_step_03_is_done_when_every_card_has_its_design_clip(tmp_path, book):
    ctx = a_ctx(tmp_path, book)
    assert voices.done(ctx) is False
    card = cast_home.card(book, "narrator")
    card.parent.mkdir(parents=True)
    card.write_text("{}", encoding="utf-8")
    assert voices.done(ctx) is False
    clip = cast_home.clip(book, "narrator")
    clip.parent.mkdir(parents=True)
    clip.write_bytes(b"wav")
    assert voices.done(ctx) is True
    assert voices.done(a_ctx(tmp_path, book, ["--recast", "--only=narrator"])) is False


def test_step_03_gathers_the_homes_then_launches_cast_voices_with_its_flags(tmp_path, book):
    character(book, "narrator")
    launched = []
    ctx = a_ctx(tmp_path, book, ["--only=narrator", "--recast"], launched)
    voices.run(ctx)
    assert cast_home.card(book, "narrator").exists()
    assert launched[0][1:] == ["scripts/cast/cast_voices.py", ctx.codex_id, "--only=narrator", "--recast"]
    assert voices.GPU is True


# --- every step answers --help on its own -------------------------------------

@pytest.mark.parametrize("script", ["step_01_canon", "step_02_sheets", "step_03_voices", "step_04_verdict"])
def test_every_step_runs_alone_from_the_command_line(script):
    done = subprocess.run([sys.executable, str(ROOT / "scripts" / "refs" / f"{script}.py"), "--help"],
                          cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip()
