"""Step 06 of the trailer stage: the plan is cut on the MEASURED metre.

The beat walk decides where the cuts fall; setups fill them from the
screenplay's own framings; a setup whose scene holds a face with no sheet is
refused and replaced, not rendered from imagination.  Lines, where step 04
and 05 have run, are given windows in the cue's measured slots.
"""
from __future__ import annotations

import json

import pytest

from scripts.trailer import step_06_plan as step
from studio import db
from studio.learnings import load
from studio.trailer_edit import LITERARY_STRETCH, plan_cuts
from studio.trailer_run import RunContext
from studio.trailer_stage_spec import LineSlate, Metre, SlateLine, Slot, StorySpec, VoiceLine
from studio.trailer_story import authored_setups

HOLMES, WATSON, HOPE, STRANGER = "holmes", "watson", "hope", "stangerson"
PROSE = ["A hand on the door, candle light on the wall.",
         "Blood on the floor by the window; a ring on the table.",
         "Boots on the wet street under a gas lamp, a cab waiting."]


def framed(cast, i):
    return " and ".join(dict.fromkeys(c.title() for c in (cast[0], cast[i % len(cast)])))


def scene(number, cast, location, term="locked-off", speaking=None):
    """Three authored shots: singles of the first-billed, and a two-shot with
    cast[i % len(cast)] where that is someone else."""
    elements = [{"kind": "action", "text": t} for t in PROSE]
    shots = [{"index": i, "setup": f"Locked-off on the {w}, {framed(cast, i)} in frame.",
              "term": term, "covers_start": i, "covers_end": i}
             for i, w in enumerate(("door", "floor", "street"))]
    return {"number": number, "cast": cast, "speaking": speaking or cast[:1],
            "slug": {"location_id": location, "location_name": location.title()},
            "duration_s": 90.0, "elements": elements, "shots": shots}


def screenplay():
    scenes = [scene(1, [WATSON, HOLMES], "room"), scene(2, [HOLMES, WATSON], "street"),
              scene(3, [HOPE], "plain"), scene(4, [STRANGER], "street", term="dolly in"),
              scene(5, [HOLMES, WATSON, HOPE], "room"), scene(6, [HOPE], "plain")]
    return {"title": "A Study in Scarlet", "logline": "A doctor meets a detective.",
            "spine": "Watson witnesses Holmes.", "scenes": scenes}


def refs():
    ids = [f"char-{c}" for c in (HOLMES, WATSON, HOPE)] + ["loc-room", "loc-street", "loc-plain"]
    kinds = {"char": "character", "loc": "location"}
    return {"refs": [{"ref_id": r, "kind": kinds[r.split("-")[0]], "name": r, "prompt": r,
                      "rel_path": f"refs/{r}.png"} for r in ids]}


def story():
    return {"lead": HOLMES, "figure": HOPE, "turn_scene": 3, "resolution_scenes": [6],
            "restricted_scenes": [6], "narrator": WATSON, "register": "detective",
            "thesis": None, "setting": "1881 London"}


def metre(seconds=100.0, bpm=120.0, title_hit=88.0) -> Metre:
    beat = 60.0 / bpm
    beats = [round(i * beat, 4) for i in range(int(seconds / beat))]
    return Metre(seed=7, rel_path="trailer/main/music/cue-7.wav", seconds=seconds, bpm=bpm,
                 bar=4 * beat, beats=beats, downbeats=beats[::4], bars_in_mode=0.97,
                 grid="metre", fitness=12.0, hits=[16.0, 40.0, 64.0, title_hit],
                 stopdowns=[title_hit - 2.5, title_hit - 2.0, title_hit - 1.5],
                 phrase_starts=beats[::16], title_hit=title_hit,
                 slots=[Slot(start=30.0, end=34.0), Slot(start=52.0, end=56.0)])


def slate():
    return LineSlate(iconicity="thin", lines=[
        SlateLine(text="You have been in Afghanistan, I perceive.", speaker=HOLMES,
                  function="hook", pool="dialogue", score=3.0),
        SlateLine(text="There has been bad work here.", speaker=WATSON,
                  function="threat", pool="dialogue", score=2.0)])


@pytest.fixture()
def ctx(tmp_path):
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    codex_id = db.insert_codex(conn, "Scarlet", codex_id="20260901000006")
    book = tmp_path / "1_scarlet"
    (book / "screenplay/feature").mkdir(parents=True)
    (book / "screenplay/feature/screenplay.json").write_text(json.dumps(screenplay()), encoding="utf-8")
    (book / "refs").mkdir()
    (book / "refs/refs.json").write_text(json.dumps(refs()), encoding="utf-8")
    context = RunContext(conn, codex_id, book, logs_root=tmp_path / "logs")
    (context.out_dir / "music").mkdir(parents=True)
    (context.out_dir / "story.json").write_text(json.dumps(story()), encoding="utf-8")
    (context.out_dir / "music/metre.json").write_text(metre().model_dump_json(), encoding="utf-8")
    context.open_step("06")
    return context


def plan_of(ctx) -> dict:
    return json.loads((ctx.out_dir / "plan.json").read_text(encoding="utf-8"))


def ends_at(plan: dict) -> float:
    """Where the picture stops: the last shot's start plus its length."""
    last = plan["shots"][-1]
    return last["start"] + last["seconds"]


class TestPieces:
    def test_stopdown_starts_keep_one_event_per_trough(self):
        assert step.stopdown_starts([20.05, 20.55, 21.05, 49.0, 49.5, 60.0]) == [20.05, 49.0, 60.0]

    def test_events_are_hits_stopdown_starts_and_the_title(self):
        found = step.events_of(metre())
        assert 88.0 in found and 85.5 in found and 86.0 not in found and 16.0 in found

    def test_stretch_ladder_lengthens_shots_per_attempt(self):
        assert step.stretch_for(0) == LITERARY_STRETCH < step.stretch_for(1) < step.stretch_for(2)
        assert step.stretch_for(9) == step.stretch_for(2)

    def test_unbound_is_a_beat_whose_shot_names_an_unsheeted_face(self):
        sheets = {r["ref_id"] for r in refs()["refs"]}
        beats = step.setups_for(screenplay()["scenes"], sheets, 6, {}, HOLMES, HOPE)
        bad = step.unbound(beats, sheets)
        assert bad and all(b.scene_number == 4 for b in beats if b.beat_id in bad)

    def test_a_shot_binds_on_who_it_names_not_on_who_is_in_the_scene(self):
        """Run 9: every Utah shot was refused because the SCENE held a
        Mormon nobody had sheeted.  A close-up of Hope is a shot of Hope."""
        sheets = {r["ref_id"] for r in refs()["refs"]}
        setups = list(authored_setups([scene(7, [HOPE, STRANGER], "plain")]))
        beats = [step.beat_of(e, i, 0.5, sheets, HOLMES, HOPE) for i, e in enumerate(setups)]
        by_subject = {tuple(b.subjects): b for b in beats}
        assert set(by_subject) == {(HOPE,), (HOPE, STRANGER)}
        assert by_subject[(HOPE,)].cast == [HOPE]
        assert step.unbound(beats, sheets) == [by_subject[(HOPE, STRANGER)].beat_id]

    def test_rung_beats_substitutes_then_plates(self):
        sheets = {r["ref_id"] for r in refs()["refs"]}
        found = {"screenplay": screenplay(), "refs": sheets, "iconicity": {},
                 "story": StorySpec(**story())}
        beats = step.setups_for(screenplay()["scenes"], sheets, 6, {}, HOLMES, HOPE)
        state = {"beats": beats, "bad": step.unbound(beats, sheets)}
        swapped = step.rung_beats(step.LADDER.rungs[1], state, found)
        assert not step.unbound(swapped, sheets)
        plates = step.rung_beats(step.LADDER.rungs[2], state, found)
        assert all(b.image_prompt.startswith(step.PLATE) and not b.subjects
                   for b in plates if b.beat_id in state["bad"])
        assert step.rung_beats(step.LADDER.rungs[0], state, found) == beats

    def test_alternates_are_shots_of_sheeted_faces_from_any_scene(self):
        """A spare may come from a scene that holds a stranger, so long as
        the spare's own frame does not."""
        sheets = {r["ref_id"] for r in refs()["refs"]}
        scenes = [scene(7, [HOPE, STRANGER], "plain")]
        spare = step.alternates(scenes, sheets, set(), {}, 3)
        assert spare and all(c["subjects"] == [HOPE] for c in spare)

    def test_lead_share_counts_shots_not_beats(self):
        assert step.lead_share([[HOLMES], [HOPE], [], [HOLMES, WATSON]], HOLMES) == 0.5

    def test_windows_start_a_beat_into_each_line_window(self):
        placed = [l.model_copy(update={"window": w}) for l, w in
                  zip(slate().lines, (Slot(start=30.0, end=34.0), Slot(start=52.0, end=60.0, made=True)))]
        found = step.windows(placed, slate().lines, metre())
        assert found == [{"index": 0, "at": 30.5}, {"index": 1, "at": 52.5}]

    def test_a_line_without_a_window_is_not_laid(self):
        assert step.windows(slate().lines, slate().lines, metre()) == []

    def test_ordered_falls_back_to_slate_order(self):
        lines = slate().lines
        def refuse(*a, **k):
            raise ValueError("no hook fits the first slot")
        kept = step.ordered(slate(), metre(), HOPE, {}, order=refuse)
        assert kept == lines


class TestStep:
    def test_plan_refuses_unbound_setup_then_substitutes(self, ctx):
        step.run(ctx.codex_id, ctx)
        plan = plan_of(ctx)
        rows = load(ctx.learnings_path)
        assert [r.action for r in rows] == ["select_setups"] and not rows[0].terminal
        assert rows[0].gate == "binding" and "unbound" in str(rows[0].measured)
        assert all(b["scene_number"] != 4 or not b["cast"] for b in plan["beats"])
        assert all(s["char_refs"] or s["loc_ref"] for s in plan["shots"])
        assert plan["stretch"] == LITERARY_STRETCH

    def test_shots_follow_the_beat_walk(self, ctx):
        """The walk is fitted to the takes, so the plan's own beat count is
        the count it was cut for -- and cutting it again reproduces it."""
        step.run(ctx.codex_id, ctx)
        plan = plan_of(ctx)
        points = step.fit_points(metre(), step.events_of(metre()),
                                 len(plan["beats"]), LITERARY_STRETCH)
        assert [s["start"] for s in plan["shots"]] == pytest.approx(points[:-1])
        assert sum(s["seconds"] for s in plan["shots"]) == pytest.approx(points[-1], abs=0.05)

    def test_every_shot_has_its_own_setup(self, ctx):
        """The owner's rule: a rendered take is never seen twice.  Run 10
        played 25 takes over 51 shots and 24% of the picture was a repeat."""
        step.run(ctx.codex_id, ctx)
        plan = plan_of(ctx)
        ids = [s["beat_id"] for s in plan["shots"]]
        assert len(set(ids)) == len(ids) == len(plan["beats"])
        assert ids == [b["beat_id"] for b in plan["beats"]]

    def test_replan_lengthens_the_shots(self, ctx):
        """A longer stretch buys a longer TRAILER, not more shots: the takes
        are fixed, so a stretched walk spends the same takes over more
        seconds."""
        step.replan(ctx, 0)
        first = plan_of(ctx)
        step.replan(ctx, 2)
        later = plan_of(ctx)
        assert ends_at(later) > ends_at(first)
        assert len(later["shots"]) == len(later["beats"]) <= step.affordable_takes(ctx)
        assert later["stretch"] == step.stretch_for(2)

    def test_lines_are_windowed_into_the_slots(self, ctx):
        """A window past the end of the picture is a line nobody hears: the
        walk stops where the takes run out, so the windows are filtered to
        what the trailer actually reaches."""
        early = metre().model_copy(update={
            "slots": [Slot(start=4.0, end=8.0), Slot(start=16.0, end=20.0)],
            "phrase_starts": [4.0, 16.0]})
        (ctx.out_dir / "music/metre.json").write_text(early.model_dump_json(), encoding="utf-8")
        (ctx.out_dir / "lines.json").write_text(slate().model_dump_json(), encoding="utf-8")
        voice = [VoiceLine(index=i, text=l.text, speaker=l.speaker, rel_path=f"trailer/main/voice/{i}.wav",
                           seconds=1.4).model_dump() for i, l in enumerate(slate().lines)]
        (ctx.out_dir / "voice.json").write_text(json.dumps(voice), encoding="utf-8")
        step.run(ctx.codex_id, ctx)
        plan = plan_of(ctx)
        starts = [w["at"] for w in sorted(plan["lines"], key=lambda w: w["index"])]
        assert starts and starts == sorted(starts)
        assert all(4.0 <= at < ends_at(plan) for at in starts)
        assert not any(s["line"] for s in plan["shots"])

    def test_a_scene_with_no_alternative_ships_a_plate_or_drops_it(self, ctx, monkeypatch):
        monkeypatch.setattr(step, "alternates", lambda *a, **k: [])
        step.run(ctx.codex_id, ctx)
        rows = load(ctx.learnings_path)
        assert [r.action for r in rows] == ["select_setups", "alternate_setup_same_beat"]
        assert all(s["char_refs"] or s["loc_ref"] for s in plan_of(ctx)["shots"])


class TestBudgetSizesThePlan:
    """Step 07 renders ~16 min per take (run 10, measured).  The render is the
    only fixed thing: the takes are what the share affords, and the walk is
    shortened until its cut count fits them."""

    def test_the_takes_are_what_step_07_can_afford(self, ctx):
        from scripts.trailer.step_07_clips import RENDER_SECONDS
        from studio.run_budget import TRAILER_SHARES, Budget
        ctx.budget = Budget(6 * 3600, TRAILER_SHARES, clock=lambda: 0.0)
        affordable = int(ctx.budget.remaining("07") // RENDER_SECONDS)
        assert step.affordable_takes(ctx) == affordable - step.RETRY_RESERVE

    def test_the_plan_never_asks_for_more_takes_than_it_can_render(self, ctx):
        step.run(ctx.codex_id, ctx)
        plan = plan_of(ctx)
        assert len(plan["shots"]) == len(plan["beats"]) <= step.affordable_takes(ctx)


class TestFitTheWalkToTheTakes:
    """The render is the only fixed thing; the walk bends to it."""

    def test_the_walk_is_shortened_until_its_cuts_fit_the_takes(self):
        found = metre()
        points = step.fit_points(found, step.events_of(found), 12, LITERARY_STRETCH)
        assert len(points) - 1 <= 12 and points[-1] < 88.0

    def test_takes_enough_for_the_whole_cue_keep_the_whole_walk(self):
        found = metre()
        whole = plan_cuts(found, step.events_of(found), 88.0, LITERARY_STRETCH)
        assert step.fit_points(found, step.events_of(found), len(whole) - 1,
                               LITERARY_STRETCH) == whole

    def test_a_walk_that_fits_nothing_is_refused(self):
        found = metre()
        with pytest.raises(ValueError, match="no walk fits 0 takes"):
            step.fit_points(found, step.events_of(found), 0, LITERARY_STRETCH)

    def test_agree_trims_the_beats_to_the_cuts_it_fitted(self):
        found = metre()
        beats = step.setups_for(screenplay()["scenes"],
                                {r["ref_id"] for r in refs()["refs"]}, 12, {}, HOLMES, HOPE)
        kept, points = step.agree(found, step.events_of(found), beats, LITERARY_STRETCH)
        assert len(kept) == len(points) - 1 <= len(beats)
        assert [b.beat_id for b in kept] == [b.beat_id for b in beats[:len(kept)]]


class TestTheTitleLandsOnlyWhereThePictureReaches:
    def test_a_picture_that_reaches_the_hit_takes_it(self):
        bed = step.music_of(metre(), 88.0)
        assert bed.title_impact == 88.0 and bed.title_stopdown == 86.5

    def test_a_picture_that_stops_short_has_no_title_moment(self):
        """A 50 s cut with its card timed to a hit at 88 s would hold a static
        title for 38 seconds; the card lands on the picture's own end."""
        bed = step.music_of(metre(), 50.0)
        assert bed.title_impact is None and bed.title_stopdown is None


class TestRefit:
    def test_refit_keeps_only_the_takes_that_exist_in_plan_order(self, ctx):
        """Step 08's answer to a missing clip: a shorter trailer, never a
        neighbouring take played a second time."""
        step.run(ctx.codex_id, ctx)
        rendered = [b["beat_id"] for b in plan_of(ctx)["beats"][:5]]
        step.refit(ctx, 0, rendered=rendered)
        plan = plan_of(ctx)
        assert [b["beat_id"] for b in plan["beats"]] == rendered
        assert [s["beat_id"] for s in plan["shots"]] == rendered
        assert ends_at(plan) < 88.0
