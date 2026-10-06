"""The re-add killer: the writer re-added the ghost clause on every improve
round, so every draft any rung writes is scrubbed by the free mechanical cure
in Desk.write BEFORE episode_home.write_plan -- the battery never re-judges a
draft still carrying one.  A ctx without refs.json writes the draft verbatim
(every existing Desk test, and a refs-less book, are untouched)."""
from __future__ import annotations

import json
from types import SimpleNamespace

from studio import plan_ladder
from studio.episode_spec import Episode
from tests.test_episode_writer import canned_plan

GHOST_AT_REST = ("The cup stands on the table at the window's near edge, his hand beside it, "
                 "the morning light laid flat across the boards and the rim; "
                 "the ghost's shoulder rises at the lower LEFT.")


class GhostWriter:
    """A fake writer whose every draft re-adds the ghost clause."""

    def write(self, brief, refusals=None, previous=None, _agent=None, **kw):
        plan = canned_plan(3)
        plan["shots"][2]["at_rest"] = GHOST_AT_REST
        return Episode.model_validate(plan)


def desk_of(tmp_path, with_refs: bool):
    book = tmp_path / "book"
    (book / "refs").mkdir(parents=True)
    if with_refs:
        (book / "refs" / "refs.json").write_text(json.dumps({"refs": [
            {"entity_id": "lead", "display": "the Lead"},
            {"entity_id": "ghost_man", "display": "the Ghost Man"}]}), encoding="utf-8")
    desk = plan_ladder.Desk(SimpleNamespace(book_dir=book, number=3),
                            tmp_path / "plan.json", writer=GhostWriter())
    desk.brief = {}
    return desk


def test_a_re_added_ghost_clause_dies_before_the_battery(tmp_path):
    desk = desk_of(tmp_path, with_refs=True)
    desk.write(None)
    written = json.loads((tmp_path / "plan.json").read_text(encoding="utf-8"))
    at = written["shots"][2]["at_rest"]
    assert "ghost" not in at and at.startswith("The cup stands on the table")


def test_a_ctx_without_refs_writes_the_draft_verbatim(tmp_path):
    desk = desk_of(tmp_path, with_refs=False)
    desk.write(None)
    written = json.loads((tmp_path / "plan.json").read_text(encoding="utf-8"))
    assert written["shots"][2]["at_rest"] == GHOST_AT_REST


def test_the_names_table_is_read_once_and_cached(tmp_path):
    desk = desk_of(tmp_path, with_refs=True)
    first = desk._names()
    (desk.ctx.book_dir / "refs" / "refs.json").unlink()
    assert desk._names() is first and first.get("ghost") == "ghost_man"
