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


def refitting(refits: list):
    """A `refit` that does what step 06's does to the plan: writes it around
    the takes it was given."""
    def refit(ctx, attempt, rendered):
        refits.append(rendered)
        write(ctx, plan=plan_doc(rendered))
    return refit


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
        monkeypatch.setattr(step, "refit", refitting(refits))
        step.run(ctx.codex_id, ctx)
        assert refits == [["B00", "B01"]] and seen["book"] == ctx.book_dir

    def test_a_capped_take_shortens_the_cut_too(self, ctx, monkeypatch):
        write(ctx, clips=clips_doc(ctx.book_dir, capped={"B01": 0.6}))
        seen, refits = {}, []
        monkeypatch.setattr(step, "build_at", built(seen))
        monkeypatch.setattr(step, "refit", refitting(refits))
        step.run(ctx.codex_id, ctx)
        assert refits == [["B00", "B02"]]

    def test_a_refit_that_lengthens_a_capped_shot_is_fitted_again(self, ctx, monkeypatch):
        """The walk re-fitted to fewer takes gives each a longer shot; a take
        capped at 2.5 s that held a 2.0 s shot may now hold a 3.0 s one and
        must leave the plan too.  Run 10's step 08 computed `usable` once."""
        write(ctx, clips=clips_doc(ctx.book_dir, HAVE[:2] + ["B02"], dropped=["B03"],
                                   capped={"B01": 2.5}))
        write(ctx, plan=plan_doc(HAVE + ["B03"]))
        seen, refits = {}, []

        def refit(c, attempt, rendered):
            refits.append(rendered)
            plan = plan_doc(rendered)
            for shot in plan["shots"]:
                shot["seconds"] = 8.0 / len(rendered)
            write(c, plan=plan)

        monkeypatch.setattr(step, "build_at", built(seen))
        monkeypatch.setattr(step, "refit", refit)
        step.run(ctx.codex_id, ctx)
        assert refits == [["B00", "B01", "B02"], ["B00", "B02"]]

    def test_a_walk_that_never_settles_is_refused(self, ctx, monkeypatch):
        write(ctx, clips=clips_doc(ctx.book_dir, capped={"B01": 1.0}))
        monkeypatch.setattr(step, "build_at", built({}))
        monkeypatch.setattr(step, "refit", lambda c, attempt, rendered: write(
            c, plan=plan_doc(["B00", "B01", "B02"])))
        with pytest.raises(SystemExit, match="settle"):
            step.run(ctx.codex_id, ctx)

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


class TestSettledSpans:
    """Row 53: with a cue plan on disk, step 08 settles like an editor -- the
    cue bends, the story does not -- and only then hands the survivors to
    step 06's spans path, which has nothing left to fold."""

    IDS = [f"B{i:02d}" for i in range(10)]
    CUE = "trailer/main/music/cue-1.flac"
    CUT_MAP = {"events": [{"t": 8.0, "rank": 3, "kind": "hit", "evidence": ["x"]},
                          {"t": 12.0, "rank": 2, "kind": "hit", "evidence": ["x"]}],
               "spans": [{"start": 16.0, "end": 20.0, "kind": "dropout"}],
               "hard_out": 24.0, "title_hit": 24.0, "seconds": 30.0}

    def stage(self, ctx, monkeypatch, lost: str):
        from tests.test_cue_edit import RATE, click
        from tests.test_cue_qc import build_plan
        music = ctx.out_dir / "music"
        music.mkdir()
        samples, metre = click(30.0)
        metre = metre.model_copy(update={"rel_path": self.CUE})
        (music / "plan.json").write_text(
            build_plan().model_copy(update={"rel_path": self.CUE}).model_dump_json(), encoding="utf-8")
        (music / "metre.json").write_text(metre.model_dump_json(), encoding="utf-8")
        (music / "cutmap-1.json").write_text(json.dumps(self.CUT_MAP), encoding="utf-8")
        have = [b for b in self.IDS if b != lost]
        write(ctx, clips=clips_doc(ctx.book_dir, have, dropped=[lost]), plan=plan_doc(self.IDS))
        seen, refits = {}, []
        monkeypatch.setattr(step, "read_cue", lambda path: (samples, RATE))
        monkeypatch.setattr(step, "write_cue",
                            lambda path, out, rate: seen.update(path=path, samples=len(out), rate=rate))
        monkeypatch.setattr(step, "refit", refitting(refits))
        return seen, refits, have

    def music(self, ctx, name):
        return json.loads((ctx.out_dir / "music" / name).read_text(encoding="utf-8"))

    def test_a_lost_sustain_cuts_the_cue_and_refits_to_the_survivors(self, ctx, monkeypatch):
        from tests.test_cue_edit import RATE
        seen, refits, have = self.stage(ctx, monkeypatch, lost="B05")
        assert step.settle(ctx) == have
        assert refits == [have] and seen["rate"] == RATE and seen["samples"] == 26 * RATE
        assert seen["path"] == ctx.book_dir / "trailer/main/music/cue-1-settled.flac"
        plan = self.music(ctx, "plan.json")
        assert plan["rel_path"] == "trailer/main/music/cue-1-settled.flac"
        assert plan["seconds"] == 26.0 and plan["hard_out"] == 20.0 and len(plan["spans"]) == 10
        metre = self.music(ctx, "metre.json")
        assert metre["rel_path"] == plan["rel_path"] and metre["seconds"] == 26.0
        cut_map = self.music(ctx, "cutmap-1-settled.json")
        assert cut_map["seconds"] == 26.0 and [e["t"] for e in cut_map["events"]] == [8.0]

    def test_a_lost_accent_touches_no_audio(self, ctx, monkeypatch):
        seen, refits, have = self.stage(ctx, monkeypatch, lost="B04")
        assert step.settle(ctx) == have
        assert seen == {} and refits == [have]
        plan = self.music(ctx, "plan.json")
        assert plan["rel_path"] == self.CUE and len(plan["spans"]) == 10
        door = plan["spans"][3]
        assert (door["start"], door["end"], door["kind"]) == (8.0, 10.5, "section")

    def test_a_join_the_cue_refuses_falls_back_to_the_fold(self, ctx, monkeypatch):
        """Two sides of a join too far apart in level: the music is left
        whole, the spans fold to the survivors, and the run learns why."""
        seen, refits, have = self.stage(ctx, monkeypatch, lost="B05")

        def refuse(*_):
            raise ValueError("levels differ by more than 6.0 dB at the join")

        monkeypatch.setattr(step, "cut_cue", refuse)
        assert step.settle(ctx) == have
        assert refits == [have] and self.music(ctx, "plan.json")["seconds"] == 30.0
        rows = [json.loads(l) for l in ctx.learnings_path.read_text(encoding="utf-8").splitlines()]
        assert [(r["step"], r["gate"], r["action"]) for r in rows] == [("08", "settle", "folded")]

    def test_the_cut_map_is_named_after_the_cue_it_measures(self):
        assert step.cut_map_name("trailer/main/music/cue-1003.flac") == "cutmap-1003.json"
        assert step.cut_map_name("trailer/main/music/cue-1003-settled.flac") == "cutmap-1003-settled.json"
