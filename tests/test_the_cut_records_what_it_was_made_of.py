"""G5.6 provenance has never run on any episode, because nothing writes its input.

`edit_gate.provenance` asks whether the take files on disk are still the ones the
master was cut from.  It can only answer that against a manifest recorded AT CUT
TIME -- as its own docstring says, "a manifest read off the same files it is
compared to can never be stale".

`edit_gate.py` states that `assemble.py` writes it as `work/cut.json`.  It does
not.  `assemble`'s only manifest is `work/gutter.json`.  `find library -name
cut.json` returns nothing across episodes 1 to 5.

So the chain reads: `cut_json()` -> None -> `provenance()` -> `{"measured":
False, "stale_takes": []}` -> `edit_integrity`'s `"ok": ... and not
prov["stale_takes"]` -> an empty list is falsy -> **ok** -> `qc.verdict`'s
`.get("ok", True)` -> passes -> `youtube_publish` reads only `qc["passed"]` ->
publishes.  A reader of that report concludes the master is provably made of the
take files on disk.  It has never been checked once.

Two rungs, both of the same shape as the dead publish gate and the take gate
that measured zero frames:

  * `qc.edit_report` returns `{"ok": True, "measured": False}` when a take file
    is missing.  `migrate_layout.repoint`'s own docstring names this exact fault
    -- "reports `measured: False` -- which the ladder has been reading as a
    pass" -- and then fixed only the records, not the reader.
  * `qc.verdict` reads `report.get("edit", {}).get("ok", True)`, so an absent
    edit block is a pass too.

A gate may say the master is bad, and may say it could not read something.  It
may not say nothing and be taken for a pass.
"""
import json
from pathlib import Path

from scripts.episode import assemble
from studio import edit_gate


def a_take(tmp_path: Path, name: str, size: int = 32) -> dict:
    (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / name).write_bytes(b"x" * size)
    return {"index": 0, "rel_path": name}


# ---- assemble writes the manifest ------------------------------------------

def test_the_cut_manifest_is_written(tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    records = [a_take(tmp_path, "takes/r2v/T00.mp4", 11),
               a_take(tmp_path, "takes/r2v/T01.mp4", 22)]
    records[1]["index"] = 1
    out = assemble.write_cut_manifest(work, records, tmp_path)
    assert out.name == "cut.json" and out.exists()


def test_the_manifest_records_each_takes_size_in_bytes(tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    records = [a_take(tmp_path, "takes/r2v/T00.mp4", 11)]
    assemble.write_cut_manifest(work, records, tmp_path)
    got = json.loads((work / "cut.json").read_text(encoding="utf-8"))
    assert got["T00"]["bytes"] == 11 and got["T00"]["rel_path"] == "takes/r2v/T00.mp4"


def test_assemble_calls_it_with_names_that_exist():
    """AN INSPECTION ASSERTION IS NOT A BEHAVIOURAL ONE.  The first version of
    this test only checked that the string "write_cut_manifest" appeared in
    `main`, and the call I had written passed it `sheet` -- a name that does not
    exist in that scope.  The test passed; the assemble died with NameError after
    25 takes were rendered and the room had been made.

    Compiling the function is the cheapest check that every name it reads is
    bound, and it costs no GPU."""
    import ast
    import builtins
    import inspect
    import textwrap

    src = textwrap.dedent(inspect.getsource(assemble.main))
    assert "write_cut_manifest" in src
    tree = ast.parse(src)
    fn = tree.body[0]
    loaded = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    stored = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
    args = {a.arg for a in fn.args.args + fn.args.kwonlyargs}
    known = stored | args | set(vars(assemble)) | set(dir(builtins))
    unbound = loaded - known
    assert not unbound, f"main reads names nothing binds: {sorted(unbound)}"


# ---- and provenance can then actually answer -------------------------------

def test_an_unchanged_take_is_not_stale(tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    assemble.write_cut_manifest(work, [a_take(tmp_path, "takes/r2v/T00.mp4", 11)], tmp_path)
    manifest = json.loads((work / "cut.json").read_text(encoding="utf-8"))
    assert edit_gate.provenance([], tmp_path, manifest) == {"measured": True, "stale_takes": []}


def test_a_take_re_rendered_since_the_cut_is_stale(tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    assemble.write_cut_manifest(work, [a_take(tmp_path, "takes/r2v/T00.mp4", 11)], tmp_path)
    manifest = json.loads((work / "cut.json").read_text(encoding="utf-8"))
    (tmp_path / "takes/r2v/T00.mp4").write_bytes(b"y" * 99)      # re-rolled after the cut
    assert edit_gate.provenance([], tmp_path, manifest)["stale_takes"] == ["T00"]


def test_a_take_deleted_since_the_cut_is_stale(tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    assemble.write_cut_manifest(work, [a_take(tmp_path, "takes/r2v/T00.mp4", 11)], tmp_path)
    manifest = json.loads((work / "cut.json").read_text(encoding="utf-8"))
    (tmp_path / "takes/r2v/T00.mp4").unlink()
    assert edit_gate.provenance([], tmp_path, manifest)["stale_takes"] == ["T00"]


# ---- and an unmeasured edit is not a pass ----------------------------------

def test_an_unmeasured_edit_block_does_not_pass():
    from scripts.episode import qc
    report = {"lufs_ok": True, "tp_ok": True, "missing_cuts": [], "lines": [],
              "edit": {"ok": True, "measured": False, "note": "not measured: 2 take files missing"}}
    assert qc.verdict(report) is False


def test_a_measured_and_clean_edit_passes():
    from scripts.episode import qc
    report = {"lufs_ok": True, "tp_ok": True, "missing_cuts": [], "lines": [],
              "edit": {"ok": True, "measured": True}}
    assert qc.verdict(report) is True


def test_an_absent_edit_block_does_not_pass():
    """`.get("edit", {}).get("ok", True)` made a missing block a pass twice over."""
    from scripts.episode import qc
    report = {"lufs_ok": True, "tp_ok": True, "missing_cuts": [], "lines": []}
    assert qc.verdict(report) is False
