"""The web process is a reader with one hand (decision 2026-09-25, the board;
C11 the actions): it never runs a step, spawns a subprocess or writes a file
under library/ itself.  Enforced by grep over the package: no `subprocess`, no
`run_script`, no SQL INSERT/UPDATE, and no import of a runner, a step script or
a stage module; the read connection is opened `mode=ro`.  The only writes are
the actions module's calls into studio/work_orders -- `hold`, `lift`, `order`
(and the pure `default_artefact`) -- and every hx-post goes to /act/."""
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


def test_the_actions_module_is_covered_by_the_grep():
    assert PACKAGE / "actions.py" in SOURCES


def test_the_only_write_path_is_work_orders_hold_lift_and_order():
    calls = set()
    for source in SOURCES:
        calls |= set(re.findall(r"\bwork_orders\.(\w+)\(", source.read_text(encoding="utf-8")))
    assert calls == {"hold", "lift", "order", "default_artefact"}
    for source in SOURCES:
        if source.name != "actions.py":
            assert "work_orders." not in source.read_text(encoding="utf-8"), source.name


def test_the_write_connection_is_a_separate_factory():
    text = (PACKAGE / "app.py").read_text(encoding="utf-8")
    assert "def writable_factory" in text and "def readonly_factory" in text
    assert "request.app.state.write_factory" in text and "Depends(_write_conn)" in text


def test_every_template_post_goes_to_an_action_route():
    posts = []
    for page in (PACKAGE / "templates").glob("*.html"):
        posts += re.findall(r'hx-post="([^"]*)"', page.read_text(encoding="utf-8"))
    assert posts and all(p.startswith("/act/") for p in posts), posts
