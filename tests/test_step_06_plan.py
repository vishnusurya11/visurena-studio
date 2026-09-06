"""Step 06 of the trailer stage: the cue's MEASURED spans are the shot list.

Step 03's music/plan.json decides where every cut falls; setups fill the
spans from the screenplay's own framings; a setup whose scene holds a face
with no sheet is refused and replaced, not rendered from imagination.  Lines,
where steps 04 and 05 have run, are given windows in the cue's own slots.
Without a cue plan the step refuses: nothing here invents a cut.
"""
from __future__ import annotations

import json

import pytest

from scripts.trailer import step_06_plan as step
from studio import db
from studio.learnings import load
from studio.trailer_run import RunContext
from studio.trailer_plan import arc_of
from studio.trailer_edit import quantise
from studio.trailer_spec import TrailerBeat
from studio.trailer_stage_spec import LineSlate, Metre, SlateLine, Slot, StorySpec, VoiceLine
from studio.trailer_story import (MOVEMENTS, authored_setups, identity_scenes, late_floor,
                                  movement_bounds, movement_of)

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
    (context.out_dir / "music/plan.json").write_text(cue_plan().model_dump_json(), encoding="utf-8")
    context.open_step("06")
    return context


@pytest.fixture()
def uncued(ctx):
    (ctx.out_dir / "music/plan.json").unlink()
    return ctx


def plan_of(ctx) -> dict:
    return json.loads((ctx.out_dir / "plan.json").read_text(encoding="utf-8"))


def ends_at(plan: dict) -> float:
    """Where the picture stops: the last shot's start plus its length."""
    last = plan["shots"][-1]
    return last["start"] + last["seconds"]


class TestPieces:
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
        assert plan["path"] == "spans" and "stretch" not in plan

    def test_every_shot_has_its_own_setup(self, ctx):
        """The owner's rule: a rendered take is never seen twice.  Run 10
        played 25 takes over 51 shots and 24% of the picture was a repeat."""
        step.run(ctx.codex_id, ctx)
        plan = plan_of(ctx)
        ids = [s["beat_id"] for s in plan["shots"]]
        assert len(set(ids)) == len(ids) == len(plan["beats"])
        assert ids == [b["beat_id"] for b in plan["beats"]]

    def test_lines_are_windowed_into_the_slots(self, ctx):
        """A window past the end of the picture is a line nobody hears: the
        picture stops where the cue's spans run out, so the windows are
        filtered to what the trailer actually reaches."""
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
        assert all(0.0 <= at < ends_at(plan) for at in starts)
        assert not any(s["line"] for s in plan["shots"])

    def test_a_scene_with_no_alternative_ships_a_plate_or_drops_it(self, ctx, monkeypatch):
        monkeypatch.setattr(step, "alternates", lambda *a, **k: [])
        step.run(ctx.codex_id, ctx)
        rows = load(ctx.learnings_path)
        assert [r.action for r in rows] == ["select_setups", "alternate_setup_same_beat"]
        assert all(s["char_refs"] or s["loc_ref"] for s in plan_of(ctx)["shots"])


class TestTheBedIsTheMeasuredCue:
    def test_the_bed_carries_the_cues_sections_and_cuts_on_its_span_starts(self):
        plan = cue_plan()
        bed = step.music_of(plan, plan.picture_spans())
        assert bed.rel_path == plan.rel_path and bed.seconds == plan.seconds
        assert bed.sections == plan.sections
        assert bed.cuts == [s.start for s in plan.picture_spans()]

    def test_a_folded_cue_cuts_only_on_the_spans_it_kept(self):
        plan = cue_plan()
        kept = plan.picture_spans()[:5]
        assert step.music_of(plan, kept).cuts == [s.start for s in kept]

    def test_a_picture_that_reaches_the_hit_takes_it(self):
        plan = cue_plan().model_copy(update={"title_hit": 32.0})
        bed = step.music_of(plan, plan.picture_spans())
        assert bed.title_impact == 32.0 and bed.title_stopdown == 27.5

    def test_a_picture_that_stops_short_has_no_title_moment(self):
        """A cut folded to end before the hit would hold a static title until
        the hit came; the card lands on the picture's own end."""
        plan = cue_plan().model_copy(update={"title_hit": 32.0})
        bed = step.music_of(plan, plan.picture_spans()[:5])
        assert bed.title_impact is None and bed.title_stopdown is None


class TestNoCuePlanNoPlan:
    def test_run_refuses_when_step_03_wrote_no_cue_plan(self, uncued):
        with pytest.raises(FileNotFoundError, match="music/plan.json"):
            step.run(uncued.codex_id, uncued)
        assert not (uncued.out_dir / "plan.json").exists()

    def test_refit_refuses_without_a_cue_plan_too(self, ctx):
        step.run(ctx.codex_id, ctx)
        (ctx.out_dir / "music/plan.json").unlink()
        with pytest.raises(FileNotFoundError, match="music/plan.json"):
            step.refit(ctx, rendered=[])


class TestTheSpine:
    """Change 1: order shots BY MOVEMENT.  `one_each` plays the beats in the
    order it is handed them, so the list order IS the trailer's order and a
    score ranking scattered on the beat grid is what run 10 shipped."""

    def test_the_beats_play_M1_then_M2_then_M3(self, ctx):
        step.run(ctx.codex_id, ctx)
        played = [b["movement"] for b in plan_of(ctx)["beats"]]
        assert played == sorted(played)
        assert played[0] == "M1"

    def test_the_arc_is_derived_from_the_movement_not_the_list_index(self, ctx):
        """Run 10 stamped `arc` from position in a score-sorted list, so
        B00-B05 were 'quiet' because they scored highest."""
        step.run(ctx.codex_id, ctx)
        beats = plan_of(ctx)["beats"]
        assert all(b["arc"] == arc_of(b["movement"]) for b in beats[:-1])
        assert beats[-1]["arc"] == "aftermath"

    def test_a_restricted_scene_is_never_photographed(self, ctx):
        """story.json lists scene 6 as the resolution; run 10 shipped two
        takes of its own restricted scene 21."""
        step.run(ctx.codex_id, ctx)
        assert all(b["scene_number"] not in story()["restricted_scenes"]
                   for b in plan_of(ctx)["beats"])

    def test_the_answer_is_never_shown_in_the_first_three_quarters(self, ctx):
        step.run(ctx.codex_id, ctx)
        beats = plan_of(ctx)["beats"]
        reveal = identity_scenes(screenplay()["scenes"], HOLMES, HOPE)
        early = beats[:late_floor(len(beats))]
        assert all(b["scene_number"] not in reveal for b in early)

    def test_setups_for_stamps_the_movement_the_scene_belongs_to(self):
        sheets = {r["ref_id"] for r in refs()["refs"]}
        beats = step.setups_for(screenplay()["scenes"], sheets, 6, {}, HOLMES, HOPE)
        bounds = movement_bounds(screenplay()["scenes"], HOLMES)
        assert all(b.movement == movement_of(b.scene_number, bounds) for b in beats)


class TestSpeakOnFace:
    """R3: the speaker must be in the shot the line starts on.  Zero
    exceptions -- swap the SHOT, never the line."""

    POINTS = [0.0, 10.0, 20.0, 30.0, 40.0, 50.0]

    def beat(self, index, scene, cast, movement):
        return TrailerBeat(beat_id=f"B{index:02d}", scene_number=scene, arc="build",
                           movement=movement, location_id="room", cast=cast,
                           subjects=cast, image_prompt="A hand on the door.",
                           motion="the camera is static")

    def run_10(self):
        """Holmes's line laid at 29.755 s over B23, a shot of John Ferrier."""
        return [self.beat(0, 1, [HOLMES], "M1"), self.beat(1, 2, [HOLMES], "M2"),
                self.beat(2, 3, [WATSON], "M2"), self.beat(3, 4, ["john_ferrier"], "M2"),
                self.beat(4, 5, [HOPE], "M3")]

    def test_the_shot_under_a_time_is_the_one_playing_then(self):
        assert step.under(self.POINTS, 29.755) == 2
        assert step.under(self.POINTS, 0.0) == 0
        assert step.under(self.POINTS, 99.0) is None

    def test_run_10s_line_over_ferrier_ends_on_holmes(self):
        beats = self.run_10()
        laid = [{"index": 0, "at": 29.755}]
        order, kept, refused = step.speak_on_face(beats, self.POINTS, laid, {0: HOLMES})
        assert kept == laid and refused == []
        assert HOLMES in order[step.under(self.POINTS, 29.755)].cast

    def test_the_swap_stays_inside_the_movement(self):
        beats = self.run_10()
        order, _, _ = step.speak_on_face(beats, self.POINTS, [{"index": 0, "at": 29.755}],
                                         {0: HOLMES})
        assert [b.movement for b in order] == sorted(b.movement for b in order)

    def test_the_line_is_never_moved_only_the_picture(self):
        beats = self.run_10()
        laid = [{"index": 0, "at": 29.755}]
        _, kept, _ = step.speak_on_face(beats, self.POINTS, laid, {0: HOLMES})
        assert kept[0]["at"] == 29.755

    def test_a_speaker_absent_from_the_movement_is_dropped_with_a_reason(self):
        beats = self.run_10()
        laid = [{"index": 0, "at": 5.0}]
        order, kept, refused = step.speak_on_face(beats, self.POINTS, laid, {0: HOPE})
        assert kept == [] and order == beats
        assert refused and HOPE in refused[0]["why"] and refused[0]["index"] == 0

    def test_narration_plays_over_any_picture(self):
        beats = self.run_10()
        _, kept, refused = step.speak_on_face(beats, self.POINTS, [{"index": 0, "at": 29.755}],
                                              {0: None})
        assert kept and not refused

    def test_two_lines_never_fight_over_the_same_swap(self):
        beats = self.run_10()
        laid = [{"index": 0, "at": 12.0}, {"index": 1, "at": 29.755}]
        order, kept, _ = step.speak_on_face(beats, self.POINTS, laid,
                                            {0: HOLMES, 1: WATSON})
        assert len(kept) == 2
        assert HOLMES in order[step.under(self.POINTS, 12.0)].cast
        assert WATSON in order[step.under(self.POINTS, 29.755)].cast

    def test_the_step_lays_every_line_on_its_speaker(self, ctx):
        early = metre().model_copy(update={
            "slots": [Slot(start=4.0, end=8.0), Slot(start=16.0, end=20.0)],
            "phrase_starts": [4.0, 16.0]})
        (ctx.out_dir / "music/metre.json").write_text(early.model_dump_json(), encoding="utf-8")
        (ctx.out_dir / "lines.json").write_text(slate().model_dump_json(), encoding="utf-8")
        voice = [VoiceLine(index=i, text=l.text, speaker=l.speaker,
                           rel_path=f"trailer/main/voice/{i}.wav", seconds=1.4).model_dump()
                 for i, l in enumerate(slate().lines)]
        (ctx.out_dir / "voice.json").write_text(json.dumps(voice), encoding="utf-8")
        step.run(ctx.codex_id, ctx)
        plan = plan_of(ctx)
        assert plan["lines"] or plan["lines_refused"]
        for window in plan["lines"]:
            speaker = slate().lines[window["index"]].speaker
            shot = next(s for s in plan["shots"]
                        if s["start"] <= window["at"] < s["start"] + s["seconds"])
            assert speaker in shot["cast"]


class TestTheAnswerIsNeverACloseUp:
    """R4's second half.  `choose_sizes` caps a reference-carrying shot at
    BOUND_FLOOR, so "medium" is the WIDEST a bound shot may be; the reveal
    takes exactly that and never the eyes."""

    def test_a_shot_of_the_answer_is_held_at_the_widest_bound_size(self, ctx):
        from studio.shot_grammar import BOUND_FLOOR, MIN_SECONDS
        step.run(ctx.codex_id, ctx)
        plan = plan_of(ctx)
        reveal = identity_scenes(screenplay()["scenes"], HOLMES, HOPE)
        by_id = {b["beat_id"]: b for b in plan["beats"]}
        answers = [s for s in plan["shots"]
                   if by_id[s["beat_id"]]["scene_number"] in reveal
                   and s["seconds"] >= MIN_SECONDS[BOUND_FLOOR]]
        assert answers and all(s["size"] == BOUND_FLOOR for s in answers)

    def test_a_cut_too_short_to_read_keeps_the_grammars_size(self):
        from studio.shot_grammar import BOUND_FLOOR
        from scripts.trailer.build_plan import hold_wide
        assert hold_wide(["close"], ["B00"], [0.8], {"B00"}) == ["close"]
        assert hold_wide(["close"], ["B00"], [3.0], {"B00"}) == [BOUND_FLOOR]
        assert hold_wide(["close"], ["B00"], [3.0], set()) == ["close"]


class TestModelFacingWording:
    def test_the_plate_and_the_reveal_framing_are_affirmative(self):
        """No negative language reaches an image model: a plate says what IS
        in the frame, and the reveal's framing is one of the shipped captions."""
        from studio.affirm import negations
        from studio.shot_grammar import BOUND_FLOOR, FRAMING
        assert negations(step.PLATE) == []
        assert negations(FRAMING[BOUND_FLOOR]) == []


class TestWindowsThePictureReaches:
    """Step 04 orders the slate against the CUE; step 06 cuts a picture as
    long as the takes the budget affords.  Four lines spread over an 88 s cue
    in front of a 23 s picture speaks once and falls silent."""

    def test_only_the_windows_before_the_end_are_offered(self):
        found = step.reachable(metre(), 23.0)
        assert found and all(w.start < 23.0 for w in found)

    def test_a_picture_that_reaches_no_window_keeps_them_all(self):
        """Better a line the ordering can refuse than no ordering at all."""
        assert step.reachable(metre(), 0.0) == step.reachable(metre(), 1e9)


class TestTheDeliveredOrder:
    """R7 measured on the PLAN, after the ladder and after `speak_on_face`
    have had their say -- run 10's own number was a scatter with no notion of
    before and after."""

    @staticmethod
    def tau(key: list) -> float:
        pairs = [(a, b) for a in range(len(key)) for b in range(a + 1, len(key))]
        live = [(a, b) for a, b in pairs if key[a] != key[b]]
        if not live:
            return 1.0
        return (2 * sum(1 for a, b in live if key[a] < key[b]) - len(live)) / len(live)

    def test_the_plan_still_follows_movement_then_scene(self, ctx):
        step.run(ctx.codex_id, ctx)
        beats = plan_of(ctx)["beats"]
        key = [(MOVEMENTS.index(b["movement"]), b["scene_number"]) for b in beats]
        assert self.tau(key) >= 0.4


# --- the cue's spans ARE the shot list ------------------------------------------
#
# BUILD rows 51 and 55.  Step 03's music/plan.json is the shot list: step 06
# fills its picture spans with story and invents no cut -- shot in/out are the
# span's own bounds, and each span kind is filled by its grammar
# (studio/shot_grammar.py).  There is no other path.

from studio import frame_budget
from studio.cue_plan import CuePlan, CueSpan
from studio.trailer_spec import CueSection

BAR = 2.0
CUE = [(0.0, 8.0, "sustain", 0, "M1"), (8.0, 12.0, "phrase", 0, "M1"),
       (12.0, 14.0, "section", 1, "M2"), (14.0, 16.0, "phrase", 1, "M2"),
       (16.0, 16.5, "accent", 1, "M2"), (16.5, 22.5, "sustain", 1, "M2"),
       (22.5, 24.0, "phrase", 1, "M2"),
       (24.0, 26.0, "section", 2, "M3"), (26.0, 27.0, "phrase", 2, "M3"),
       (27.0, 27.5, "accent", 2, "M3"), (27.5, 32.0, "trough", 2, "M3"),
       (32.0, 38.0, "tail", 2, "M3")]
"""Eleven picture spans and a tail: as many as the fixture screenplay has
sheeted setups, so the whole cue is filled and both accents survive."""


def cue_span(index, start, end, kind, section, movement) -> CueSpan:
    return CueSpan(index=index, start=start, end=end, kind=kind, section=section,
                   movement=movement, bars=(end - start) / BAR)


def cue_plan() -> CuePlan:
    sections = [CueSection(index=0, start=0.0, end=12.0, movement="M1", pulse=False, level_db=-30.0),
                CueSection(index=1, start=12.0, end=24.0, movement="M2", pulse=True, level_db=-20.0),
                CueSection(index=2, start=24.0, end=38.0, movement="M3", pulse=True, level_db=-12.0)]
    return CuePlan(rel_path="trailer/main/music/cue-7.wav", seed=7, seconds=38.0, bpm=120.0,
                   bar=BAR, sections=sections, hard_out=32.0, title_hit=None,
                   spans=[cue_span(i, *spec) for i, spec in enumerate(CUE)])


@pytest.fixture()
def cued(ctx):
    (ctx.out_dir / "music/plan.json").write_text(cue_plan().model_dump_json(), encoding="utf-8")
    return ctx


def voiced(ctx) -> None:
    (ctx.out_dir / "lines.json").write_text(slate().model_dump_json(), encoding="utf-8")
    voice = [VoiceLine(index=i, text=l.text, speaker=l.speaker,
                       rel_path=f"trailer/main/voice/{i}.wav", seconds=1.4).model_dump()
             for i, l in enumerate(slate().lines)]
    (ctx.out_dir / "voice.json").write_text(json.dumps(voice), encoding="utf-8")


class TestTheCueIsTheShotList:
    def test_every_shot_is_a_span_and_every_span_is_a_shot(self, cued):
        step.run(cued.codex_id, cued)
        plan = plan_of(cued)
        shots = [(s["start"], s["seconds"]) for s in plan["shots"]]
        spans = [(s["start"], round(s["end"] - s["start"], 3)) for s in plan["spans"]]
        assert shots == spans and plan["path"] == "spans"
        assert len({s["beat_id"] for s in plan["shots"]}) == len(spans) == len(plan["beats"])

    def test_no_cut_is_invented(self, cued):
        """Every shot opens and closes on a bound the cue measured."""
        step.run(cued.codex_id, cued)
        starts = {s.start for s in cue_plan().spans}
        ends = {s.end for s in cue_plan().spans}
        for shot in plan_of(cued)["shots"]:
            assert shot["start"] in starts
            assert round(shot["start"] + shot["seconds"], 3) in ends

    def test_a_sustain_shot_carries_one_move_and_three_actions(self, cued):
        step.run(cued.codex_id, cued)
        sustains = [s for s in plan_of(cued)["shots"] if s["span_kind"] == "sustain"]
        assert sustains
        for shot in sustains:
            assert shot["move"] and len(shot["actions"]) == 3
            assert [a["phase"] for a in shot["actions"]] == ["open", "middle", "final"]
            assert all(shot["start"] <= a["at"] < shot["start"] + shot["seconds"]
                       for a in shot["actions"])

    def test_an_accent_shot_carries_no_face(self, cued):
        """Step 07 binds from the BEAT, so the beat under an accent is an
        insert too: object alone, cast empty."""
        step.run(cued.codex_id, cued)
        plan = plan_of(cued)
        by_id = {b["beat_id"]: b for b in plan["beats"]}
        accents = [s for s in plan["shots"] if s["span_kind"] == "accent"]
        assert accents
        for shot in accents:
            assert shot["char_refs"] == {} and shot["cast"] == [] and not shot["binds_face"]
            assert shot["size"] == "insert" and by_id[shot["beat_id"]]["cast"] == []

    def test_a_section_shot_reveals_on_its_downbeat(self, cued):
        step.run(cued.codex_id, cued)
        sections = [s for s in plan_of(cued)["shots"] if s["span_kind"] == "section"]
        assert sections and all(s["reveal_at"] == s["start"] for s in sections)

    def test_a_trough_shot_holds_still(self, cued):
        step.run(cued.codex_id, cued)
        troughs = [s for s in plan_of(cued)["shots"] if s["span_kind"] == "trough"]
        assert troughs and all(s["move"] is None for s in troughs)

    def test_the_beats_take_the_cues_movements(self, cued):
        """The cue's sections are the movement doors: a beat plays in the
        movement of the span it fills."""
        step.run(cued.codex_id, cued)
        plan = plan_of(cued)
        by_id = {b["beat_id"]: b for b in plan["beats"]}
        assert all(by_id[s["beat_id"]]["movement"] == s["movement"] for s in plan["shots"])
        assert [b["movement"] for b in plan["beats"]] == sorted(b["movement"] for b in plan["beats"])

    def test_lines_sit_in_the_spans_windows_and_name_a_speaker_mode(self, cued):
        voiced(cued)
        step.run(cued.codex_id, cued)
        plan = plan_of(cued)
        assert plan["lines"]
        for window in plan["lines"]:
            shot = next(s for s in plan["shots"]
                        if s["start"] <= window["at"] < s["start"] + s["seconds"])
            assert shot["span_kind"] in ("sustain", "trough")
            assert shot["speaker_mode"] is not None
            speaker = slate().lines[window["index"]].speaker
            assert speaker in shot["cast"]

    def test_every_shot_names_the_kind_of_span_it_fills(self, cued):
        step.run(cued.codex_id, cued)
        plan = plan_of(cued)
        assert plan["spans"] and all(s["span_kind"] for s in plan["shots"])

    def test_the_spans_path_says_so(self, cued, capsys):
        step.run(cued.codex_id, cued)
        assert "spans are the shot list" in capsys.readouterr().out

    def test_refit_keeps_the_rendered_takes_on_the_spans_path(self, cued):
        step.run(cued.codex_id, cued)
        rendered = [b["beat_id"] for b in plan_of(cued)["beats"][:5]]
        step.refit(cued, rendered=rendered)
        plan = plan_of(cued)
        assert [b["beat_id"] for b in plan["beats"]] == rendered
        assert [s["beat_id"] for s in plan["shots"]] == rendered
        assert len(plan["spans"]) == 5


class TestSpanPieces:
    def test_counts_by_movement_reads_the_plan(self):
        assert step.counts_by_movement(cue_plan()) == {"M1": 2, "M2": 5, "M3": 4}

    def test_points_of_are_the_span_bounds(self):
        spans = cue_plan().picture_spans()
        assert step.points_of(spans) == [s.start for s in spans] + [32.0]

    def test_fit_to_frames_folds_the_plan_until_the_frames_afford_it(self):
        plan = cue_plan()
        whole = step.fit_to_frames(plan, 1e9, frame_budget.TYPED)
        assert whole is plan
        tight = step.fit_to_frames(plan, 4000.0, frame_budget.TYPED)
        assert len(tight.picture_spans()) < len(plan.picture_spans())
        assert frame_budget.fits(tight, 4000.0, frame_budget.TYPED)

    def test_agree_spans_folds_the_plan_to_the_beats_it_has(self):
        sheets = {r["ref_id"] for r in refs()["refs"]}
        beats = step.setups_for(screenplay()["scenes"], sheets, 9, {}, HOLMES, HOPE)[:9]
        kept, plan = step.agree_spans(cue_plan(), beats)
        assert len(kept) == len(plan.picture_spans()) == len(beats)
        assert all(s.kind != "accent" for s in plan.spans) or len(beats) >= 11

    def test_folded_to_ends_the_picture_early_when_the_fixed_spans_outnumber_the_takes(self, capsys):
        plan = cue_plan()
        five = step.folded_to(plan, 5)
        picture = five.picture_spans()
        assert len(picture) == 5 and [s.kind for s in picture] == [s.kind for s in plan.spans[:5]]
        assert five.hard_out == plan.spans[5].start == five.spans[-1].start
        assert five.spans[-1].kind == "tail" and five.spans[-1].end == plan.seconds
        assert all(c.start < five.hard_out for c in five.sections)
        assert "ends after 5 spans" in capsys.readouterr().out
        assert step.folded_to(plan, 10) is not plan and len(step.folded_to(plan, 10).picture_spans()) == 10

    def test_restamped_beats_take_their_spans_movement(self):
        sheets = {r["ref_id"] for r in refs()["refs"]}
        spans = cue_plan().picture_spans()
        beats = step.setups_for(screenplay()["scenes"], sheets, len(spans), {}, HOLMES, HOPE)
        beats, plan = step.agree_spans(cue_plan(), beats)
        spans = plan.picture_spans()
        stamped = step.restamped(beats, spans)
        assert [b.movement for b in stamped] == [s.movement for s in spans]
        assert stamped[-1].arc == "aftermath"
        assert all(b.arc == arc_of(b.movement) for b in stamped[:-1])

    def test_inserts_strip_the_face_from_the_beat_under_an_accent(self):
        sheets = {r["ref_id"] for r in refs()["refs"]}
        spans = cue_plan().picture_spans()
        beats = step.setups_for(screenplay()["scenes"], sheets, len(spans), {}, HOLMES, HOPE)
        beats, plan = step.agree_spans(cue_plan(), beats)
        spans = plan.picture_spans()
        made = step.inserts(beats, spans)
        for beat, span in zip(made, spans):
            if span.kind == "accent":
                assert beat.cast == [] and beat.subjects == []
                assert beat.image_prompt.startswith(step.INSERT)
        assert step.inserts(made, spans) == made

    def test_spoken_in_finds_the_line_that_opens_inside_the_span(self):
        span = cue_plan().spans[5]
        laid = [{"index": 0, "at": 17.0}, {"index": 1, "at": 29.5}]
        assert step.spoken_in(span, laid, {0: HOLMES, 1: WATSON}) == (True, HOLMES)
        assert step.spoken_in(cue_plan().spans[1], laid, {0: HOLMES}) == (False, None)

    def test_accent_slots_are_never_swapped_by_a_line(self):
        beats = [TrailerBeat(beat_id=f"B{i:02d}", scene_number=1, arc="build", movement="M2",
                             location_id="room", cast=cast, subjects=cast,
                             image_prompt="A hand on the door.", motion="the camera is static")
                 for i, cast in enumerate(([WATSON], [HOLMES], [WATSON]))]
        points = [0.0, 8.0, 8.5, 16.0]
        on_accent = [{"index": 0, "at": 8.2}]
        order, kept, refused = step.speak_on_face(beats, points, on_accent, {0: WATSON}, pinned={1})
        assert order == beats and not kept and "accent" in refused[0]["why"]
        wants_pinned_face = [{"index": 0, "at": 8.6}]
        order, kept, refused = step.speak_on_face(beats, points, wants_pinned_face, {0: HOLMES},
                                                  pinned={1})
        assert order == beats and not kept and refused

    def test_shots_land_on_whole_frames_so_the_picture_never_drifts_from_the_plan(self):
        """Run 11.4 died in step 08: the walk's plan drifted 0.130s from the
        delivered picture.  Span bounds are onset times, frames are the
        render's ruler, so each shot's in and out are the span's bounds
        quantised to frames and the picture's length is the last bound's
        quantised value, never a sum of roundings."""
        sheets = {r["ref_id"] for r in refs()["refs"]}
        cue = cue_plan()
        # every interior bound off the frame grid by a different fraction
        bounds = [s.start for s in cue.spans] + [cue.seconds]
        at = {b: b + (0.013 * i if 0 < i < len(bounds) - 1 else 0.0) for i, b in enumerate(bounds)}
        moved = [s.model_copy(update={"start": at[s.start], "end": at[s.end]}) for s in cue.spans]
        sections = [c.model_copy(update={"start": at[c.start], "end": at[c.end]}) for c in cue.sections]
        cue = cue.model_copy(update={"spans": moved, "sections": sections, "hard_out": at[cue.hard_out]})
        beats = step.setups_for(screenplay()["scenes"], sheets, len(cue.picture_spans()), {}, HOLMES, HOPE)
        beats, spans = step.filled(beats, cue)
        shots = step.shots_from_spans(beats, spans, refs()["refs"], [], {})
        for shot, span in zip(shots, spans):
            assert shot.start == quantise(span.start)
            assert shot.seconds == pytest.approx(quantise(span.end) - quantise(span.start), abs=1e-9)
            assert shot.seconds * 24 == pytest.approx(round(shot.seconds * 24), abs=1e-6)
        assert sum(s.seconds for s in shots) == pytest.approx(quantise(spans[-1].end), abs=1e-6)
        assert step.music_of(cue, spans).cuts == [quantise(s.start) for s in spans]

    def test_shots_from_spans_refuse_a_count_mismatch(self):
        spans = cue_plan().picture_spans()
        with pytest.raises(ValueError, match="span"):
            step.shots_from_spans([], spans, {}, [], {})

    def test_picture_seconds_left_is_step_07s_remaining_net_of_a_read(self, ctx):
        from scripts.trailer.step_07_clips import read_seconds
        plan = cue_plan()
        want = ctx.budget.remaining("07") - read_seconds(len(plan.picture_spans()))
        assert step.picture_seconds_left(ctx, plan) == pytest.approx(want, abs=1.0)

    def test_the_cue_plan_is_read_when_present_and_refused_when_not(self, ctx):
        assert step.cue_plan_of(ctx).seconds == 38.0
        (ctx.out_dir / "music/plan.json").unlink()
        with pytest.raises(FileNotFoundError, match="music/plan.json"):
            step.cue_plan_of(ctx)
