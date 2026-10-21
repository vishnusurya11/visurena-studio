"""The sandbox builder and its checkpoints (DESIGN 1.3; 2026-10-21_ep02_proof P1).

Built from tests/fixtures stand-ins only: the layout of 1.1, the sandbox codex
99991021000000 copied by SELECT with a queued ep02 row, a 1-commit git repo, the
manifest; the golden copy is reused; a checkpoint restores byte for byte."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
from contextlib import closing
from pathlib import Path

import pytest

from studio import settings
from studio.rehearsal import sandbox
from tests.proof_sandbox_fixture import codex_ids, env_for, tiny_sandbox

BOOK = f"{sandbox.SANDBOX_CODEX}_{sandbox.SLUG}"


def tree(root: Path) -> dict[str, str]:
    """relative path -> sha256 of every file under root."""
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def test_the_layout_of_1_1_is_built(tmp_path):
    box = tiny_sandbox(tmp_path)
    for rel in (f"library/{BOOK}/analysis/scenes.json", f"library/{BOOK}/refs/pins.json",
                "library/.autopilot", "library/.device", "library/.vlm_cache", "comfy/input", "comfy/output",
                "comfy/temp", "tmp", "db/visurena_studio.db", "rehearsal.json"):
        assert (box / rel).exists(), rel
    assert box.parent == tmp_path / "rehearsals" and box.name == "t1"


def test_the_sandbox_db_holds_the_codex_by_select_and_the_queue_row(tmp_path):
    box = tiny_sandbox(tmp_path)
    assert codex_ids(box / "db" / "visurena_studio.db") == [sandbox.SANDBOX_CODEX]
    with closing(sqlite3.connect(box / "db" / "visurena_studio.db")) as conn:
        row = conn.execute("SELECT c.name, w.stage, w.unit, w.number, w.state FROM codex c "
                           "JOIN work_orders w ON w.codex_id = c.id").fetchone()
    assert row == ("The Strange Case of Dr Jekyll and Mr Hyde", "episode", "ep02", 2, "queued")


def test_the_git_repo_has_one_commit_and_a_clean_tree(tmp_path):
    git = tiny_sandbox(tmp_path) / "git"
    log = subprocess.run(["git", "log", "--oneline"], cwd=git, capture_output=True, text=True, check=True)
    porcelain = subprocess.run(["git", "status", "--porcelain"], cwd=git, capture_output=True, text=True)
    assert len(log.stdout.splitlines()) == 1 and porcelain.stdout == ""


def test_the_manifest_loads_through_settings(tmp_path):
    box = tiny_sandbox(tmp_path, comfy_host="http://127.0.0.1:18188")
    manifest = json.loads((box / "rehearsal.json").read_text(encoding="utf-8"))
    assert {"comfy_host", "recordings", "real_library", "real_roots", "scale", "faults", "run_id", "fakes",
            "codex", "episode"} <= set(manifest)
    assert settings.rehearsal(env=env_for(box)) == manifest
    assert manifest["codex"] == sandbox.SANDBOX_CODEX and manifest["run_id"] == "t1"


def test_the_golden_copy_is_made_once_and_reused(tmp_path, monkeypatch):
    tiny_sandbox(tmp_path, run_id="a")
    copies = []
    monkeypatch.setattr(sandbox, "copy_records", lambda *a, **k: copies.append(a))
    second = tiny_sandbox(tmp_path, run_id="b")
    assert copies == [] and (second / "library" / BOOK / "analysis" / "scenes.json").exists()


def test_a_run_id_is_never_built_twice(tmp_path):
    tiny_sandbox(tmp_path, run_id="same")
    with pytest.raises(FileExistsError):
        tiny_sandbox(tmp_path, run_id="same")


def test_a_checkpoint_restores_byte_for_byte(tmp_path):
    box = tiny_sandbox(tmp_path)
    before = {top: tree(box / top) for top in sandbox.CHECKPOINTED}
    sandbox.checkpoint(box, "after_02")
    (box / "library" / BOOK / "analysis" / "scenes.json").write_text("changed", encoding="utf-8")
    (box / "library" / BOOK / "episodes" / "ep02").mkdir(parents=True)
    (box / "library" / BOOK / "episodes" / "ep02" / "plan.json").write_text("{}", encoding="utf-8")
    (box / "comfy" / "output" / "x.png").write_bytes(b"\x89PNG")
    sandbox.restore(box, "after_02")
    assert {top: tree(box / top) for top in sandbox.CHECKPOINTED} == before
    assert not (box / "library" / BOOK / "episodes").exists()


def test_a_missing_checkpoint_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        sandbox.restore(tiny_sandbox(tmp_path), "after_09")


def test_the_default_base_is_on_the_nvme_temp(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert sandbox.default_base() == tmp_path / "Temp" / "visurena_rehearsal"


def test_copy_records_copies_named_files_and_folders_and_skips_the_absent(tmp_path):
    src, dest = tmp_path / "src", tmp_path / "dest"
    (src / "refs").mkdir(parents=True)
    (src / "refs" / "a.json").write_text("{}", encoding="utf-8")
    (src / "uploads.jsonl").write_text("", encoding="utf-8")
    assert sandbox.copy_records(src, dest, ("refs", "uploads.jsonl", "absent")) == ["refs", "uploads.jsonl"]
    assert (dest / "refs" / "a.json").is_file() and (dest / "uploads.jsonl").is_file()


def test_the_cli_builds_checkpoints_and_restores(tmp_path, monkeypatch, capsys):
    from scripts.proof import sandbox as cli
    from tests.proof_sandbox_fixture import real_book, real_db
    monkeypatch.setattr(cli, "REAL_BOOK", real_book(tmp_path))
    monkeypatch.setattr(cli, "REAL_DB", real_db(tmp_path))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "appdata"))
    assert cli.main(["build", "cli1", "--no-fakes"]) == 0
    box = Path(capsys.readouterr().out.splitlines()[0])
    assert box == tmp_path / "appdata" / "Temp" / "visurena_rehearsal" / "cli1"
    assert json.loads((box / "rehearsal.json").read_text(encoding="utf-8"))["fakes"] is False
    assert cli.main(["checkpoint", str(box), "after_02"]) == 0 and cli.main(["restore", str(box), "after_02"]) == 0


def test_the_cli_guard_passes_untouched_and_fails_a_touch(tmp_path, monkeypatch):
    from scripts.proof import sandbox as cli
    watched = tmp_path / "watched.txt"
    watched.write_text("x", encoding="utf-8")
    monkeypatch.setattr(cli.guard, "named_paths", lambda: [watched])
    snap = tmp_path / "before.json"
    assert cli.main(["guard-snapshot", str(snap)]) == 0 and cli.main(["guard-check", str(snap)]) == 0
    watched.write_text("xy", encoding="utf-8")
    assert cli.main(["guard-check", str(snap)]) == 1
