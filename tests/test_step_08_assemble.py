"""Step 08 of the trailer stage: the deterministic cut.

The step has no gate of its own -- an exception here is a bug -- but it is
where step 07's verdicts land.  A beat whose take never rendered, came back
capped shorter than its shot, or is a leftover from an earlier plan does not
get a stand-in: the plan is re-fitted around the takes that exist and the
trailer gets shorter.  Run 10 substituted instead, and 24% of the delivered
picture was a frame already seen.  ffmpeg is never run here.
"""
from __future__ import annotations

import json

import pytest

from scripts.trailer import step_08_assemble as step
from studio import db
from studio.clip_cache import fingerprint, record
from studio.trailer_run import RunContext

HAVE = ["B00", "B01", "B02"]
RECIPE = {"prompt": "a man in fog", "seed": 51000}


def clip(book, beat_id, capped=None, recipe=RECIPE):
    """A promoted clip and the record step 07 wrote beside it."""
    video = book / "trailer/main/clips" / f"{beat_id}.mp4"
    video.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(b"mp4")
    record(video, recipe)
    return {"beat_id": beat_id, "rel_path": video.relative_to(book).as_posix(),
            "capped": capped, "fingerprint": fingerprint(RECIPE)}


def clips_doc(book, beats=HAVE, capped=None, dropped=()):
    clips = [clip(book, b, (capped or {}).get(b)) for b in beats]
    return {"clips": clips, "dropped": list(dropped)}


def plan_doc(beats=HAVE):
    return {"shots": [{"beat_id": b, "index": i, "start": 2.0 * i, "seconds": 2.0}
                      for i, b in enumerate(beats)],
            "beats": [{"beat_id": b} for b in beats]}


@pytest.fixture()
def ctx(tmp_path):
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    codex_id = db.insert_codex(conn, "Scarlet", codex_id="20260901000008")
    book = tmp_path / "20260901000008_scarlet"
    context = RunContext(conn, codex_id, book, logs_root=tmp_path / "logs")
    context.out_dir.mkdir(parents=True)
    (context.out_dir / "plan.json").write_text(json.dumps(plan_doc()), encoding="utf-8")
    (context.out_dir / "clips.json").write_text(json.dumps(clips_doc(book)), encoding="utf-8")
    context.open_step("08")
    return context


def write(ctx, clips=None, plan=None):
    if clips is not None:
        (ctx.out_dir / "clips.json").write_text(json.dumps(clips), encoding="utf-8")
    if plan is not None:
        (ctx.out_dir / "plan.json").write_text(json.dumps(plan), encoding="utf-8")


class TestUsable:
    def test_a_fresh_take_of_this_plan_serves_its_shot(self, tmp_path):
        assert step.usable(clips_doc(tmp_path), plan_doc(), tmp_path) == HAVE

    def test_a_dropped_beat_is_not_usable(self, tmp_path):
        """No record, no file: the shot has nothing of its own to play."""
        assert step.usable(clips_doc(tmp_path, HAVE[:2], dropped=["B02"]),
                           plan_doc(), tmp_path) == HAVE[:2]

    def test_a_clip_from_an_earlier_plan_is_not_usable(self, tmp_path):
        doc = clips_doc(tmp_path)
        record(tmp_path / "trailer/main/clips/B01.mp4", {**RECIPE, "prompt": "an old shot"})
        assert step.usable(doc, plan_doc(), tmp_path) == ["B00", "B02"]

    def test_a_capped_take_serves_only_a_shot_under_its_cap(self, tmp_path):
        """Step 07 caps a take whose face never bound at SHORT_SHOT; a longer
        shot would hold a wrong face on screen long enough to read."""
        doc = clips_doc(tmp_path, capped={"B01": 0.6})
        assert step.usable(doc, plan_doc(), tmp_path) == ["B00", "B02"]
        short = plan_doc()
        short["shots"][1]["seconds"] = 0.5
        assert step.usable(doc, short, tmp_path) == HAVE


class TestRun:
    def test_a_complete_set_of_takes_is_cut_as_planned(self, ctx, monkeypatch):
        seen, refits = {}, []
        monkeypatch.setattr(step, "build_at", built(seen))
        monkeypatch.setattr(step, "refit", lambda c, attempt, rendered: refits.append(rendered))
        step.run(ctx.codex_id, ctx)
        assert seen["book"] == ctx.book_dir and seen["trailer_id"] == "main"
        assert refits == [] and step.master_of(ctx).name == "TRAILER-scarlet.mp4"

    def test_a_missing_take_shortens_the_cut_instead_of_borrowing_one(self, ctx, monkeypatch):
        write(ctx, clips=clips_doc(ctx.book_dir, HAVE[:2], dropped=["B02"]))
        seen, refits = {}, []
        monkeypatch.setattr(step, "build_at", built(seen))
        monkeypatch.setattr(step, "refit", lambda c, attempt, rendered: refits.append(rendered))
        step.run(ctx.codex_id, ctx)
        assert refits == [["B00", "B01"]] and seen["book"] == ctx.book_dir

    def test_a_capped_take_shortens_the_cut_too(self, ctx, monkeypatch):
        write(ctx, clips=clips_doc(ctx.book_dir, capped={"B01": 0.6}))
        seen, refits = {}, []
        monkeypatch.setattr(step, "build_at", built(seen))
        monkeypatch.setattr(step, "refit", lambda c, attempt, rendered: refits.append(rendered))
        step.run(ctx.codex_id, ctx)
        assert refits == [["B00", "B02"]]

    def test_without_step_07s_record_the_cut_is_refused(self, ctx, monkeypatch):
        (ctx.out_dir / "clips.json").unlink()
        monkeypatch.setattr(step, "build_at", built({}))
        with pytest.raises(SystemExit, match="no clips.json"):
            step.run(ctx.codex_id, ctx)

    def test_a_missing_master_is_a_bug_not_a_gate(self, ctx, monkeypatch):
        monkeypatch.setattr(step, "build_at", lambda book, trailer_id: book / "nowhere.mp4")
        with pytest.raises(RuntimeError, match="no master"):
            step.run(ctx.codex_id, ctx)


class TestRecut:
    def test_the_recut_refits_at_the_attempt_s_stretch_then_builds(self, ctx, monkeypatch):
        seen, refits = {}, []
        monkeypatch.setattr(step, "build_at", built(seen))
        monkeypatch.setattr(step, "refit",
                            lambda c, attempt, rendered: refits.append((attempt, rendered)))
        step.recut(ctx, 2)
        assert refits == [(2, HAVE)] and seen["trailer_id"] == "main"


def built(seen: dict):
    """A `build_at` that records its arguments and writes a master."""
    def build_at(book, trailer_id):
        seen.update(book=book, trailer_id=trailer_id)
        master = book / "trailer" / trailer_id / "TRAILER-scarlet.mp4"
        master.write_bytes(b"mp4")
        return master
    return build_at
