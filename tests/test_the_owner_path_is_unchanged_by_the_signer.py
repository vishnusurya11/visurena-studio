"""The signer keyword is additive.  A file the owner signs by hand is the file
it always was: the same keys, the same words; `current`, `passed` and `require`
key on the verdict word and the sha, never on who signed."""
from __future__ import annotations

import json

from studio import eye_verdict as ev, plan_verdict, refs_verdict


def test_an_owner_eye_verdict_has_the_keys_it_always_had(tmp_path):
    folder = tmp_path / "board"
    folder.mkdir()
    pic = folder / "shot_01.png"
    pic.write_bytes(b"\x03" * 8)
    doc = json.loads(ev.sign(folder, [pic], "pass", "fine").read_text(encoding="utf-8"))
    assert set(doc) == {"sha8", "verdict", "note", "files", "signed_at"}
    assert ev.passed(folder, [pic])


def test_an_owner_plan_verdict_has_its_four_fields(tmp_path):
    plan = tmp_path / "plan.json"
    plan.write_text('{"a": 1}', encoding="utf-8")
    doc = json.loads(plan_verdict.sign(plan, "read it").read_text(encoding="utf-8"))
    assert set(doc) == {"plan_sha8", "verdict", "note", "date"}
    assert plan_verdict.current(plan)


def test_an_owner_look_verdict_has_its_five_fields(tmp_path):
    book = tmp_path / "book"
    (book / "refs").mkdir(parents=True)
    doc = json.loads(refs_verdict.sign(book, "every face its own").read_text(encoding="utf-8"))
    assert set(doc) == {"pack_sha8", "verdict", "note", "date", "rows"}
    assert refs_verdict.current(book)
