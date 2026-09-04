"""Step 08 of the trailer stage: the deterministic cut.

The step has no gate of its own -- an exception here is a bug -- but it
is where step 07's verdicts land: a shot longer than a capped take allows,
or a shot of a dropped beat, is sourced from a neighbouring take exactly
as a missing file would be.  ffmpeg is never run here.
"""
from __future__ import annotations

import json

import pytest

from scripts.trailer import step_08_assemble as step
from studio import db
from studio.trailer_run import RunContext

HAVE = ["B00", "B01", "B02"]


def clips_doc(capped=None, dropped=()):
    clips = [{"beat_id": b, "capped": (capped or {}).get(b)} for b in HAVE]
    return {"clips": clips, "dropped": list(dropped)}


class TestResolveTake:
    def test_a_bound_take_serves_its_own_shots(self):
        resolve = step.resolver_for(clips_doc())
        assert resolve("B01", 4, 2.5, HAVE) == "B01"

    def test_a_capped_take_serves_only_shots_under_its_cap(self):
        resolve = step.resolver_for(clips_doc(capped={"B01": 0.6}))
        assert resolve("B01", 4, 0.5, HAVE) == "B01"
        assert resolve("B01", 4, 2.5, HAVE) == step.neighbouring_take("B99", 4, 2.5, HAVE)

    def test_a_dropped_beat_is_sourced_like_a_missing_file(self):
        resolve = step.resolver_for(clips_doc(dropped=["B07"]))
        assert resolve("B07", 2, 1.0, HAVE) == HAVE[2]

    def test_no_clips_document_resolves_as_before(self):
        assert step.resolver_for(None) is step.neighbouring_take


@pytest.fixture()
def ctx(tmp_path):
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    codex_id = db.insert_codex(conn, "Scarlet", codex_id="20260901000008")
    book = tmp_path / "20260901000008_scarlet"
    context = RunContext(conn, codex_id, book, logs_root=tmp_path / "logs")
    context.out_dir.mkdir(parents=True)
    (context.out_dir / "clips.json").write_text(json.dumps(clips_doc(capped={"B01": 0.6})),
                                                encoding="utf-8")
    context.open_step("08")
    return context


class TestRun:
    def test_builds_in_the_book_with_the_clip_verdicts(self, ctx, monkeypatch):
        seen = {}

        def build_at(book, trailer_id, resolve):
            seen.update(book=book, trailer_id=trailer_id, resolve=resolve)
            master = book / "trailer" / trailer_id / "TRAILER-scarlet.mp4"
            master.write_bytes(b"mp4")
            return master
        monkeypatch.setattr(step, "build_at", build_at)
        step.run(ctx.codex_id, ctx)
        assert seen["book"] == ctx.book_dir and seen["trailer_id"] == "main"
        assert seen["resolve"]("B01", 0, 2.5, HAVE) != "B01"
        assert step.master_of(ctx).name == "TRAILER-scarlet.mp4"

    def test_a_missing_master_is_a_bug_not_a_gate(self, ctx, monkeypatch):
        monkeypatch.setattr(step, "build_at", lambda book, trailer_id, resolve: book / "nowhere.mp4")
        with pytest.raises(RuntimeError, match="no master"):
            step.run(ctx.codex_id, ctx)
