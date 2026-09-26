"""The web process is a reader (decision 2026-09-25, the board): it never runs a
step, spawns a subprocess, writes a file under library/ or opens the DB for
writing.  Enforced by grep over the package: no `subprocess`, no `run_script`,
no SQL INSERT/UPDATE, and no import of a runner, a step script or a stage
module; the connection is opened `mode=ro`."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "studio" / "command_center"
SOURCES = sorted(PACKAGE.glob("*.py")) + [ROOT / "command_center.py"]
FORBIDDEN_WORDS = re.compile(r"\bsubprocess\b|\brun_script\b|\bINSERT\b|\bUPDATE\b|\bos\.system\b")
FORBIDDEN_IMPORTS = re.compile(
    r"^\s*(?:from|import)\s+(?:scripts|episode|refs|trailer|analysis|screenplay|studio\.py)\b"
    r"|^\s*from\s+studio\s+import\s+.*\b(?:episode_run|stage_run|step_runner|tracking|approval)\b"
    r"|^\s*(?:from|import)\s+studio\.(?:episode_run|stage_run|step_runner|tracking|approval)\b",
    re.MULTILINE)


@pytest.mark.parametrize("source", SOURCES, ids=lambda p: p.name)
def test_no_source_names_a_writer_or_a_runner(source):
    text = source.read_text(encoding="utf-8")
    assert not FORBIDDEN_WORDS.search(text), source.name
    assert not FORBIDDEN_IMPORTS.search(text), source.name


def test_the_connection_is_read_only():
    text = (PACKAGE / "app.py").read_text(encoding="utf-8")
    assert "mode=ro" in text and "uri=True" in text and "busy_timeout" in text


def test_the_templates_post_nothing_yet():
    for page in (PACKAGE / "templates").glob("*.html"):
        assert "hx-post" not in page.read_text(encoding="utf-8"), page.name
