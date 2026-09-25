"""Step 01 binds the chapter's cast from its analysis when no --cast is given.

ep12, 2026-09-24: the registry describes a cast_lister agent at 01_01; the step
instead refused and asked for --cast by hand, though the analysis already says
who is in each chapter (every character file's `journey` lists its chapters).
Groups (the gunners, the Martians) have no single face and are not bound.
"""
import json
from types import SimpleNamespace

from scripts.episode import step_01_bind as step


def book_with(tmp_path, rows):
    chars = tmp_path / "analysis" / "characters"
    chars.mkdir(parents=True)
    for r in rows:
        (chars / f"{r['id']}.json").write_text(json.dumps(r), encoding="utf-8")
    return tmp_path


def test_the_chapters_individuals_are_the_cast_protagonist_first(tmp_path):
    book = book_with(tmp_path, [
        {"id": "artilleryman", "role": "major", "appearances": 10, "journey": [{"chapter": 12}]},
        {"id": "gunners", "role": "group", "appearances": 1, "journey": [{"chapter": 12}]},
        {"id": "unnamed_first_person_narrator", "role": "protagonist", "appearances": 40,
         "journey": [{"chapter": 11}, {"chapter": 12}]},
        {"id": "narrators_wife", "role": "major", "appearances": 8, "journey": [{"chapter": 10}]},
    ])
    assert step.chapter_cast(book, 12) == ["unnamed_first_person_narrator", "artilleryman"]


def test_run_binds_the_derived_cast_when_none_is_given(tmp_path):
    book = book_with(tmp_path, [
        {"id": "unnamed_first_person_narrator", "role": "protagonist", "appearances": 40,
         "journey": [{"chapter": 12}]}])
    ran = []
    ctx = SimpleNamespace(book_dir=book, number=12, extra=[],
                          run_script=lambda script, *a, **kw: ran.append((script, a)))
    step.run(ctx)
    assert ran == [("scripts/refs/cast_rows.py", ("unnamed_first_person_narrator",))]
