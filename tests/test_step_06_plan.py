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

HOLMES, WATSON, HOPE, STRANGER = "holmes", "watson", "hope", "stangerson"
PROSE = ["A hand on the door, candle light on the wall.",
         "Blood on the floor by the window; a ring on the table.",
         "Boots on the wet street under a gas lamp, a cab waiting."]


def scene(number, cast, location, term="locked-off", speaking=None):
    elements = [{"kind": "action", "text": t} for t in PROSE]
    shots = [{"index": i, "setup": f"Locked-off on the {w}.", "term": term,
              "covers_start": i, "covers_end": i} for i, w in enumerate(("door", "floor", "street"))]
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


class TestPieces:
    def test_stopdown_starts_keep_one_event_per_trough(self):
        assert step.stopdown_starts([20.05, 20.55, 21.05, 49.0, 49.5, 60.0]) == [20.05, 49.0, 60.0]

    def test_events_are_hits_stopdown_starts_and_the_title(self):
        found = step.events_of(metre())
        assert 88.0 in found and 85.5 in found and 86.0 not in found and 16.0 in found

    def test_stretch_ladder_lengthens_shots_per_attempt(self):
        assert step.stretch_for(0) == LITERARY_STRETCH < step.stretch_for(1) < step.stretch_for(2)
        assert step.stretch_for(9) == step.stretch_for(2)

    def test_unbound_is_a_beat_whose_scene_has_an_unsheeted_face(self):
        sheets = {r["ref_id"] for r in refs()["refs"]}
        beats = step.setups_for(screenplay()["scenes"], sheets, 6, {}, HOLMES, HOPE)
        bad = step.unbound(beats, screenplay()["scenes"], sheets)
        assert bad and all(b.scene_number == 4 for b in beats if b.beat_id in bad)

    def test_rung_beats_substitutes_then_plates(self):
        sheets = {r["ref_id"] for r in refs()["refs"]}
        found = {"screenplay": screenplay(), "refs": sheets, "iconicity": {},
                 "story": StorySpec(**story())}
        beats = step.setups_for(screenplay()["scenes"], sheets, 6, {}, HOLMES, HOPE)
        state = {"beats": beats, "bad": step.unbound(beats, screenplay()["scenes"], sheets)}
        swapped = step.rung_beats(step.LADDER.rungs[1], state, found)
        assert not step.unbound(swapped, screenplay()["scenes"], sheets)
        plates = step.rung_beats(step.LADDER.rungs[2], state, found)
        assert all(b.image_prompt.startswith(step.PLATE) for b in plates if b.beat_id in state["bad"])
        assert step.rung_beats(step.LADDER.rungs[0], state, found) == beats

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
        assert plan["music"]["title_impact"] == 88.0 and plan["stretch"] == LITERARY_STRETCH

    def test_shots_follow_the_beat_walk(self, ctx):
        step.run(ctx.codex_id, ctx)
        plan = plan_of(ctx)
        points = plan_cuts(metre(), step.events_of(metre()), 88.0, LITERARY_STRETCH)
        assert [s["start"] for s in plan["shots"]] == pytest.approx(points[:-1])
        assert sum(s["seconds"] for s in plan["shots"]) == pytest.approx(88.0, abs=0.05)

    def test_replan_lengthens_the_shots(self, ctx):
        step.replan(ctx, 0)
        first = len(plan_of(ctx)["shots"])
        step.replan(ctx, 2)
        assert len(plan_of(ctx)["shots"]) < first and plan_of(ctx)["stretch"] == step.stretch_for(2)

    def test_lines_are_windowed_into_the_slots(self, ctx):
        (ctx.out_dir / "lines.json").write_text(slate().model_dump_json(), encoding="utf-8")
        voice = [VoiceLine(index=i, text=l.text, speaker=l.speaker, rel_path=f"trailer/main/voice/{i}.wav",
                           seconds=1.4).model_dump() for i, l in enumerate(slate().lines)]
        (ctx.out_dir / "voice.json").write_text(json.dumps(voice), encoding="utf-8")
        step.run(ctx.codex_id, ctx)
        plan = plan_of(ctx)
        assert {w["index"] for w in plan["lines"]} == {0, 1}
        starts = [w["at"] for w in sorted(plan["lines"], key=lambda w: w["index"])]
        assert starts == sorted(starts) and all(20.0 <= at <= 88.0 for at in starts)
        assert not any(s["line"] for s in plan["shots"])

    def test_a_scene_with_no_alternative_ships_a_plate_or_drops_it(self, ctx, monkeypatch):
        monkeypatch.setattr(step, "alternates", lambda *a, **k: [])
        step.run(ctx.codex_id, ctx)
        rows = load(ctx.learnings_path)
        assert [r.action for r in rows] == ["select_setups", "alternate_setup_same_beat"]
        assert all(s["char_refs"] or s["loc_ref"] for s in plan_of(ctx)["shots"])


class TestBudgetSizesThePlan:
    """Step 07 renders ~11 min per setup; the plan must not ask for more takes
    than its share affords, or the budget rung drops the climax beats."""

    def test_setups_are_capped_by_what_step_07_can_afford(self, ctx):
        from scripts.trailer.step_07_clips import RENDER_SECONDS
        from studio.run_budget import TRAILER_SHARES, Budget
        ctx.budget = Budget(6 * 3600, TRAILER_SHARES, clock=lambda: 0.0)
        affordable = int(ctx.budget.remaining("07") // RENDER_SECONDS)
        assert step.setup_count(60, ctx) == affordable - step.RETRY_RESERVE
        assert step.setup_count(5, ctx) == 5
