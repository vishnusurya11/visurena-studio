"""The write fence refuses BEFORE the write (DESIGN 2.6, R7; 2026-10-21_ep02_proof P1).

Tmp folders stand in as the real roots: a planted write into the VL cache, an ep01 attempt,
another book and the DB's -wal companion each raises RehearsalTripwire, leaves no file and
writes one tripwire.jsonl row.  Reads of a real root and writes in the sandbox pass."""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from studio.rehearsal import fence
from tests.proof_sandbox_fixture import env_for, stand_in_roots, tiny_sandbox

REPO = Path(__file__).resolve().parents[1]
JEKYLL = "20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde"


@pytest.fixture
def armed(tmp_path):
    """A fence armed on stand-in roots; disarmed after (the hook stays, inert)."""
    lib, dbdir, box = tmp_path / "real_library", tmp_path / "real_db", tmp_path / "box"
    for d in (lib / ".vlm_cache" / "ab", lib / JEKYLL / "episodes" / "ep01" / "takes" / "r2v" / "attempts",
              lib / "20260827135508_the-war-of-the-worlds" / "episodes", dbdir, box):
        d.mkdir(parents=True)
    (lib / JEKYLL / "plan.json").write_text("{}", encoding="utf-8")
    fence.install(fence.Fence.of(roots=(lib, dbdir), sandbox=box, repo=REPO))
    yield lib, dbdir, box
    fence.disarm()


def trips(box: Path) -> list[dict]:
    path = box / "tripwire.jsonl"
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


@pytest.mark.parametrize("rel", [".vlm_cache/ab/x.txt", f"{JEKYLL}/episodes/ep01/takes/r2v/attempts/x",
                                 "20260827135508_the-war-of-the-worlds/episodes/x.json"])
def test_a_planted_library_write_trips_before_the_file_exists(armed, rel):
    lib, _, box = armed
    with pytest.raises(fence.RehearsalTripwire):
        (lib / rel).write_text("x", encoding="utf-8")
    assert not (lib / rel).exists()
    assert trips(box)[-1]["event"] == "open" and rel.split("/")[-1] in trips(box)[-1]["reason"]


def test_the_db_wal_companion_and_any_connect_trip(armed):
    _, dbdir, box = armed
    with pytest.raises(fence.RehearsalTripwire):
        open(dbdir / "visurena_studio.db-wal", "ab")
    with pytest.raises(fence.RehearsalTripwire):
        sqlite3.connect(dbdir / "visurena_studio.db")
    with pytest.raises(fence.RehearsalTripwire):
        sqlite3.connect(f"file:{(dbdir / 'visurena_studio.db').as_posix()}?mode=ro", uri=True)
    assert not list(dbdir.iterdir())
    assert [t["event"] for t in trips(box)] == ["open", "sqlite3.connect", "sqlite3.connect"]


def test_renames_removes_dirs_and_copies_into_a_root_trip(armed):
    lib, _, box = armed
    src = box / "here.txt"
    src.write_text("x", encoding="utf-8")
    book = lib / JEKYLL
    for act in (lambda: os.replace(src, book / "y"), lambda: os.remove(book / "plan.json"),
                lambda: (book / "new").mkdir(), lambda: shutil.copyfile(src, book / "c"),
                lambda: shutil.copy2(src, book / "c2"), lambda: shutil.rmtree(book / "episodes"),
                lambda: (book / "plan.json").touch(), lambda: os.rmdir(lib / ".vlm_cache" / "ab")):
        with pytest.raises(fence.RehearsalTripwire):
            act()
    assert sorted(p.name for p in book.iterdir()) == ["episodes", "plan.json"] and src.exists()
    assert len(trips(box)) == 8


def test_reads_of_a_root_and_writes_in_the_sandbox_pass(armed):
    lib, _, box = armed
    assert (lib / JEKYLL / "plan.json").read_text(encoding="utf-8") == "{}"
    (box / "out" / "a").mkdir(parents=True)
    (box / "out" / "a" / "b.txt").write_text("ok", encoding="utf-8")
    sqlite3.connect(box / "sb.db").close()
    assert trips(box) == []


def test_a_mkdir_of_a_folder_already_there_passes_and_a_new_one_still_trips(armed):
    """Window 2 (2026-10-21 20:42 PDT): speechbrain's fetch runs `savedir.mkdir(exist_ok=True)` on
    ECAPA's own folder at every load, and the fence tripped step 04 on a mkdir that creates nothing."""
    lib, _, box = armed
    book = lib / JEKYLL
    (book / "episodes").mkdir(parents=True, exist_ok=True)
    os.makedirs(book / "episodes", exist_ok=True)
    assert trips(box) == []
    with pytest.raises(fence.RehearsalTripwire):
        (book / "episodes" / "ep02").mkdir(parents=True, exist_ok=True)
    assert not (book / "episodes" / "ep02").exists() and len(trips(box)) == 1


def test_a_disarmed_fence_refuses_nothing(tmp_path):
    fence.disarm()
    (tmp_path / "x.txt").write_text("x", encoding="utf-8")
    assert fence.armed() is None


CHILD = r'''
import os, sys, json, tempfile
sys.path.insert(0, sys.argv[1])
import studio                                  # the variable is not set yet: a no-op
os.environ["VISURENA_LIBRARY"] = sys.argv[2]
from studio import settings
import importlib; importlib.reload(settings)
from studio.rehearsal import activate
off = '"TaskName","Next Run Time","Status"\n"\\visurena-autopilot","N/A","Disabled"\n'
activate.install(env=os.environ, schtasks=lambda: off, series=lambda: [])
print(json.dumps({"tmp": tempfile.gettempdir()}), flush=True)
open(sys.argv[3], "w")
'''


def test_activate_arms_the_fence_in_a_child_process(tmp_path):
    box = tiny_sandbox(tmp_path)
    planted = stand_in_roots(tmp_path)[0] / "planted.txt"
    clean = {k: v for k, v in os.environ.items() if k != "VISURENA_LIBRARY"}
    out = subprocess.run([sys.executable, "-c", CHILD, str(REPO), env_for(box)["VISURENA_LIBRARY"], str(planted)],
                         capture_output=True, text=True, cwd=REPO, env=clean, timeout=120)
    assert out.returncode != 0 and "RehearsalTripwire" in out.stderr, out.stderr[-2000:]
    assert json.loads(out.stdout.splitlines()[0])["tmp"] == str(box / "tmp")
    assert not planted.exists() and len(trips(box)) == 1


def test_an_extended_length_path_into_a_root_trips(armed):
    lib, _, box = armed
    target = lib / JEKYLL / "y.txt"
    for prefix in ("\\\\?\\", "\\\\.\\"):     # \\?\ and \\.\ open the same file as its plain path
        with pytest.raises(fence.RehearsalTripwire):
            open(prefix + str(target), "w")
    assert not target.exists() and len(trips(box)) == 2


def test_a_junction_from_the_sandbox_into_a_root_trips(armed):
    _winapi = pytest.importorskip("_winapi")
    lib, _, box = armed
    fence.disarm()
    _winapi.CreateJunction(str(lib / JEKYLL), str(box / "door"))
    fence.install(fence.Fence.of(roots=(lib, armed[1]), sandbox=box, repo=REPO))
    with pytest.raises(fence.RehearsalTripwire):
        (box / "door" / "through.txt").write_text("x", encoding="utf-8")
    assert not (lib / JEKYLL / "through.txt").exists()
    fence.disarm()                      # removing the junction itself also resolves into the root
    os.rmdir(box / "door")


GRANDCHILD = r'''
import os, sys, json, subprocess
sys.path.insert(0, sys.argv[1])
import studio                                  # the variable is not set yet: a no-op
os.environ["VISURENA_LIBRARY"] = sys.argv[2]
from studio.rehearsal import activate
off = '"TaskName","Next Run Time","Status"\n"\\visurena-autopilot","N/A","Disabled"\n'
activate.install(env=os.environ, schtasks=lambda: off, series=lambda: [])
code = f"open({sys.argv[3]!r}, 'w').write('x')"
out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=sys.argv[4], timeout=120)
print(json.dumps({"rc": out.returncode, "err": out.stderr[-1500:]}), flush=True)
'''


def test_a_python_child_that_never_imports_studio_is_still_fenced(tmp_path):
    """The rehearsal boot path rides PYTHONPATH: a bare `python -c` child arms before its code."""
    box = tiny_sandbox(tmp_path)
    planted = stand_in_roots(tmp_path)[0] / "grandchild.txt"
    clean = {k: v for k, v in os.environ.items() if k not in ("VISURENA_LIBRARY", "PYTHONPATH")}
    out = subprocess.run([sys.executable, "-c", GRANDCHILD, str(REPO), env_for(box)["VISURENA_LIBRARY"],
                          str(planted), str(tmp_path)], capture_output=True, text=True, cwd=REPO, env=clean,
                         timeout=240)
    assert out.returncode == 0, out.stderr[-2000:]
    child = json.loads(out.stdout.splitlines()[-1])
    assert child["rc"] != 0 and "RehearsalTripwire" in child["err"], child
    assert not planted.exists() and trips(box)[-1]["event"] == "open"
