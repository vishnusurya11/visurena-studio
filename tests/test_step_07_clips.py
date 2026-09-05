"""Step 07 of the trailer stage: one take per beat, identity-gated, IN ROUNDS.

A round renders every live beat's next take back to back with the video model
resident, unloads once, reads the whole round in one vision session, and gates
every take from it.  A take whose person does not read as its reference sheet
-- DISTINCT_AT or more traits apart -- climbs seed then a whole-take close-up
in the NEXT round; the terminal rung ships the BEST take capped at a short
shot.  A beat is dropped only when no take exists at all -- the budget gone
before its first render, or the render itself failing.
Renders and readings are faked; nothing here touches a GPU.
"""
from __future__ import annotations

import json

import pytest
from PIL import Image

from scripts.trailer import step_07_clips as step
from scripts.trailer.build_clips import FRAMING
from studio import comfy, db
from studio import describe
from studio.clip_cache import fingerprint, is_current, record, stored_fingerprint
from studio.describe import DISTINCT_AT, TIMEOUT, TraitCard
from studio.frames import HEAD_LEAK_SECONDS
from studio.learnings import Learning, load
from studio.run_budget import TRAILER_SHARES, Budget
from studio.trailer_run import RunContext

HOLMES = "sherlock_holmes"
SHEET = TraitCard(age="middle-aged", hair_colour="dark brown", hair_length="short",
                  facial_hair="clean-shaven", headgear="bowler", complexion="sallow", build="slight")
NEAR = SHEET.model_copy(update={"headgear": "none"})                       # 1 apart: bound
FAR = SHEET.model_copy(update={"hair_colour": "fair", "headgear": "none",
                               "facial_hair": "beard", "build": "stocky"})  # 4 apart: not him
MID = SHEET.model_copy(update={"hair_colour": "grey", "headgear": "none", "build": "heavy"})  # 3
NOTCHED = SHEET.model_copy(update={"age": "old", "hair_colour": "brown", "headgear": "none"})  # 2.0
TILTED = FAR.model_copy(update={"age": "old"})                            # 4.5 apart
BLIND = SHEET.model_copy(update={t: "unclear" for t in ("age", "hair_colour", "headgear", "build")})


def beat(beat_id, cast, loc):
    return {"beat_id": beat_id, "scene_number": 1, "arc": "quiet", "location_id": loc,
            "cast": cast, "image_prompt": "He crosses to the window.",
            "motion": "The camera pushes in slowly.", "line": None, "speaker": None}


def ref(ref_id, kind, rel_path):
    return {"ref_id": ref_id, "kind": kind, "entity_id": ref_id[4:], "name": ref_id[4:],
            "physical": "A tall thin man with a hawk nose.", "prompt": "", "rel_path": rel_path}


def one_beat_plan(count):
    """`count` beats, each with a character and exactly one shot: the shape
    step 06 now plans -- one take, one shot."""
    beats = [beat(f"B{n:02}", [HOLMES], "baker_street") for n in range(count)]
    return {"beats": beats,
            "shots": [{"beat_id": b["beat_id"], "index": n, "seconds": 2.0, "size": "medium"}
                      for n, b in enumerate(beats)]}


def make_ctx(tmp_path, clock, ceiling=6 * 3600, beats=None):
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    codex_id = db.insert_codex(conn, "Scarlet", codex_id="20260901000007")
    book = tmp_path / "20260901000007_scarlet"
    for rel in ("refs/characters/char-sherlock_holmes.png", "refs/locations/loc-baker_street.png",
                "refs/locations/loc-brixton_road.png"):
        (book / rel).parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (8, 8)).save(book / rel)
    refs = [ref(f"char-{HOLMES}", "character", "refs/characters/char-sherlock_holmes.png"),
            ref("loc-baker_street", "location", "refs/locations/loc-baker_street.png"),
            ref("loc-brixton_road", "location", "refs/locations/loc-brixton_road.png")]
    (book / "refs/refs.json").write_text(json.dumps(
        {"book_id": book.name, "palette": "Noir.", "refs": refs, "unbound": []}), encoding="utf-8")
    context = RunContext(conn, codex_id, book, logs_root=tmp_path / "logs", ceiling=ceiling)
    # A fake clock the fake render advances, so time is spent without waiting.
    context.budget = Budget(ceiling, TRAILER_SHARES, clock=lambda: clock[0])
    context.out_dir.mkdir(parents=True)
    plan = one_beat_plan(beats) if beats else {
        "beats": [beat("B00", [HOLMES], "baker_street"), beat("B01", [], "brixton_road")],
        "shots": [{"beat_id": "B00", "index": 0, "seconds": 2.5, "size": "medium"},
                  {"beat_id": "B00", "index": 1, "seconds": 1.0, "size": "close"},
                  {"beat_id": "B01", "index": 2, "seconds": 1.5, "size": "wide"}]}
    (context.out_dir / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
    context.open_step("07")
    return context


@pytest.fixture()
def rendered(monkeypatch):
    """Faked renders and readings.  `cards` is consumed per bound take in
    ROUND order, and every read of a round is handed that round's one reader:
    the reader is what unloads the video model, so counting readers counts
    model swaps."""
    calls = []

    def render_take(values, bound, refs, book, dest):
        calls.append({"seed": values["seed"], "prompt": values["prompt"], "dest": dest.name,
                      "frames": values["frames"]})
        state["clock"][0] += step.RENDER_SECONDS
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"mp4" + str(values["seed"]).encode())
        # The real renderer records the recipe beside the take; the fake must
        # too, or every clip this run makes reads as stale to step 08.
        record(dest, {"prompt": values["prompt"], "seed": values["seed"]})
        return dest

    def reader(free=True):
        state["sessions"].append(free)
        return f"reader-{len(state['sessions'])}"

    def describe_frames(frames, seed, run=None):
        state["reads"].append(run)
        state["clock"][0] += step.SHEET_SECONDS if run in state["open"] else step.SESSION_SECONDS
        state["open"].add(run)
        return state["cards"].pop(0)

    state = {"calls": calls, "cards": [], "clock": [0.0], "sessions": [], "reads": [], "open": set()}
    monkeypatch.setattr(step, "render_take", render_take)
    monkeypatch.setattr(step, "reader", reader)
    monkeypatch.setattr(step, "is_complete", lambda p: p.exists())
    monkeypatch.setattr(step, "clip_seconds", lambda p: 4.85)
    monkeypatch.setattr(step, "describe", lambda path, seed: SHEET)
    monkeypatch.setattr(step, "frames_of", lambda video, seconds, work: [])
    monkeypatch.setattr(step, "describe_frames", describe_frames)
    return state


@pytest.fixture()
def ctx(tmp_path, rendered):
    return make_ctx(tmp_path, rendered["clock"])


def clips_doc(ctx):
    return json.loads((ctx.out_dir / "clips.json").read_text(encoding="utf-8"))


def rungs(ctx):
    """The learnings that are RUNGS.  A round also writes what it measured --
    the cycle and the reader session -- and those are data, not gates."""
    return [row for row in load(ctx.learnings_path) if row.gate not in step.MEASURED]


class TestRun:
    def test_a_bound_take_ships_first_try_and_a_location_take_is_ungated(self, ctx, rendered):
        rendered["cards"] = [NEAR]
        step.run(ctx.codex_id, ctx)
        doc = clips_doc(ctx)
        by_id = {c["beat_id"]: c for c in doc["clips"]}
        assert set(by_id) == {"B00", "B01"} and doc["dropped"] == []
        assert by_id["B00"]["similarity"] == pytest.approx(6 / 7, abs=0.001)
        assert by_id["B00"]["differs"] == ["headgear"]
        assert by_id["B00"]["reference"] == f"char-{HOLMES}" and by_id["B00"]["capped"] is None
        assert by_id["B01"]["similarity"] is None and by_id["B01"]["reference"] is None
        assert by_id["B00"]["rel_path"] == "trailer/main/clips/B00.mp4"
        assert by_id["B00"]["fingerprint"] == stored_fingerprint(ctx.book_dir / by_id["B00"]["rel_path"])
        assert (ctx.book_dir / by_id["B00"]["rel_path"]).exists()
        assert len(rendered["calls"]) == 2 and rungs(ctx) == []
        assert rendered["sessions"] == [True] and rendered["reads"] == ["reader-1"]

    def test_a_weak_face_rerolls_the_seed_then_binds(self, ctx, rendered):
        rendered["cards"] = [FAR, NEAR]
        step.run(ctx.codex_id, ctx)
        clip = next(c for c in clips_doc(ctx)["clips"] if c["beat_id"] == "B00")
        assert clip["similarity"] == pytest.approx(6 / 7, abs=0.001) and clip["capped"] is None
        rows = rungs(ctx)
        assert [r.action for r in rows] == ["reroll_seed"]
        assert rows[0].measured == 4 and rows[0].threshold == DISTINCT_AT
        assert rendered["sessions"] == [True, True]  # a round each, one swap each
        seeds = [c["seed"] for c in rendered["calls"] if c["dest"].startswith("B00")]
        assert len(seeds) == 2 and len(set(seeds)) == 2

    def test_one_notch_drifts_on_ordered_traits_still_bind(self, ctx, rendered):
        """Scarlet run 4, B02: the sheet read old/white/bowler Holmes as
        middle-aged/grey/top hat -- three traits, two of them one notch."""
        rendered["cards"] = [NOTCHED]
        step.run(ctx.codex_id, ctx)
        clip = next(c for c in clips_doc(ctx)["clips"] if c["beat_id"] == "B00")
        assert clip["differs"] == ["age", "hair_colour", "headgear"] and clip["capped"] is None
        assert rungs(ctx) == []

    def test_the_learning_records_the_distance_not_the_count(self, ctx, rendered):
        rendered["cards"] = [TILTED, NEAR]
        step.run(ctx.codex_id, ctx)
        assert rungs(ctx)[0].measured == 4.5

    def test_a_gate_timeout_ships_the_take_unverified_instead_of_killing_the_run(
            self, ctx, rendered, monkeypatch):
        """Scarlet run 4: one VLM call took 10:23 and the TimeoutError ended the
        run with 19 beats unrendered.  The policy is retry, then degrade and
        ship: the engine is interrupted, the take ships flagged, the run goes on."""
        stopped = []
        monkeypatch.setattr(describe.comfy, "interrupt", lambda: stopped.append(True))

        def slow(frames, seed, run=None):
            raise TimeoutError("job-9 still running after 600.0s")
        monkeypatch.setattr(step, "describe_frames", slow)
        step.run(ctx.codex_id, ctx)
        clip = next(c for c in clips_doc(ctx)["clips"] if c["beat_id"] == "B00")
        assert clip["capped"] is None and stopped == [True]
        rows = rungs(ctx)
        assert rows[0].action == "accepted_on_timeout" and rows[0].threshold == f"{TIMEOUT}s"

    def test_a_face_that_never_binds_ships_its_best_take_short(self, ctx, rendered):
        """Scarlet run 6: B12 read 4.0 then 3.5 on two seeds -- a seed moves
        the reading half a trait -- and the third seed cost the cut three
        beats.  One reroll, then a framing the reader can see the face in."""
        rendered["cards"] = [FAR, MID, FAR]
        step.run(ctx.codex_id, ctx)
        doc = clips_doc(ctx)
        clip = next(c for c in doc["clips"] if c["beat_id"] == "B00")
        assert clip["capped"] == step.SHORT_SHOT and clip["similarity"] == pytest.approx(4 / 7, abs=0.001)
        assert doc["dropped"] == []
        actions = [r.action for r in rungs(ctx)]
        assert actions == ["reroll_seed", "alternate_setup", "short_shot"]
        holmes_calls = [c for c in rendered["calls"] if c["dest"].startswith("B00")]
        assert len(holmes_calls) == 2
        assert holmes_calls[-1]["prompt"].count(FRAMING["close"]) == 2
        assert (ctx.book_dir / clip["rel_path"]).read_bytes() == b"mp4" + str(clip["seed"]).encode()

    def test_a_person_too_unclear_to_read_is_accepted_and_flagged(self, ctx, rendered):
        rendered["cards"] = [BLIND]
        step.run(ctx.codex_id, ctx)
        clip = next(c for c in clips_doc(ctx)["clips"] if c["beat_id"] == "B00")
        assert clip["capped"] is None and clip["known"] == 3
        assert [r.action for r in rungs(ctx)] == ["accepted_unverifiable"]

    def test_a_take_lost_to_an_engine_restart_is_rendered_once_more(self, ctx, rendered,
                                                                    monkeypatch):
        """The engine came back without the job: it is back, so the take is
        submitted again -- once.  A second loss is the machine's answer."""
        real, tries = step.render_take, []

        def flaky(values, bound, refs, book, dest):
            tries.append(values["seed"])
            if len(tries) == 1:
                raise comfy.EngineLost("job-1 vanished: the engine restarted")
            return real(values, bound, refs, book, dest)
        monkeypatch.setattr(step, "render_take", flaky)
        rendered["cards"] = [NEAR]
        step.run(ctx.codex_id, ctx)
        assert clips_doc(ctx)["dropped"] == [] and tries[0] == tries[1]

    def test_a_take_lost_twice_fails_like_any_other(self, ctx, rendered, monkeypatch):
        def gone(values, bound, refs, book, dest):
            raise comfy.EngineLost("job-1 vanished: the engine restarted")
        monkeypatch.setattr(step, "render_take", gone)
        step.run(ctx.codex_id, ctx)
        assert clips_doc(ctx)["dropped"] == ["B00", "B01"]

    def test_a_take_that_fails_to_render_drops_the_beat(self, ctx, rendered, monkeypatch):
        def broken(values, bound, refs, book, dest):
            raise RuntimeError("no video")
        monkeypatch.setattr(step, "render_take", broken)
        step.run(ctx.codex_id, ctx)
        doc = clips_doc(ctx)
        assert doc["clips"] == [] and doc["dropped"] == ["B00", "B01"]
        rows = rungs(ctx)
        assert {r.gate for r in rows} == {"render"} and all(r.terminal for r in rows)
        assert rendered["sessions"] == []  # nothing rendered, so nothing to unload for


class TestBudget:
    def test_no_time_for_a_retry_ships_the_first_take_short(self, tmp_path, rendered):
        ctx = make_ctx(tmp_path, rendered["clock"], ceiling=2200)  # 07's share: 1283 s
        rendered["cards"] = [FAR]
        step.run(ctx.codex_id, ctx)
        doc = clips_doc(ctx)
        assert doc["clips"][0]["capped"] == step.SHORT_SHOT and doc["dropped"] == ["B01"]
        rows = rungs(ctx)
        # Round order: B01 is refused its first render while the round is being
        # staged, B00 is gated when the round is read, and its reroll is refused
        # at the top of round two.
        assert [r.gate for r in rows] == ["budget", "identity", "budget"]
        assert [r.action for r in rows] == [step.DROPPED, "reroll_seed", "short_shot"]

    def test_a_retry_never_spends_a_later_beats_first_render(self, tmp_path, rendered):
        """Scarlet run 6: B12 rerolled twice (33 min) and B14-B21 were dropped
        with 391 s left.  Rounds make that structural -- every beat's first
        take is rendered in round one, so a reroll can only ever cost another
        reroll -- and a reroll is priced at what a reroll ROUND costs: one
        render and the reader session that has to follow it."""
        ctx = make_ctx(tmp_path, rendered["clock"], ceiling=3772)  # 07's share: 2200 s
        rendered["cards"] = [FAR]
        step.run(ctx.codex_id, ctx)
        doc = clips_doc(ctx)
        assert [c["beat_id"] for c in doc["clips"]] == ["B00", "B01"] and doc["dropped"] == []
        assert doc["clips"][0]["capped"] == step.SHORT_SHOT and doc["clips"][1]["capped"] is None
        assert len(rendered["calls"]) == 2
        rows = rungs(ctx)
        assert [r.gate for r in rows] == ["identity", "budget"]
        assert rows[1].threshold == step.RETRY_COST and rows[1].substep == "B00"

    def test_no_time_for_a_first_render_drops_the_remaining_beats(self, tmp_path, rendered):
        ctx = make_ctx(tmp_path, rendered["clock"], ceiling=100)
        step.run(ctx.codex_id, ctx)
        doc = clips_doc(ctx)
        assert doc["clips"] == [] and doc["dropped"] == ["B00", "B01"]
        assert rendered["calls"] == []
        assert {r.gate for r in rungs(ctx)} == {"budget"}


class TestMeasure:
    def test_frames_of_samples_three_stills_outside_the_head_leak(self, tmp_path, monkeypatch):
        grabbed = []
        monkeypatch.setattr(step, "frame_at", lambda video, when, dest: grabbed.append(when) or dest)
        found = step.frames_of(tmp_path / "take.mp4", 4.85, tmp_path / "work")
        assert len(found) == 3 and (tmp_path / "work").is_dir()
        assert all(when > HEAD_LEAK_SECONDS for when in grabbed) and grabbed == sorted(grabbed)

    def test_the_stills_come_from_the_stretch_the_cut_uses(self, tmp_path, monkeypatch):
        """The leak is 2.6s, not the 1.0s `frame_times` defaults to.  A take is
        now barely longer than its shot, so sampling from 1.0s would read the
        reference sheet itself and the identity gate would pass on a picture
        of its own answer."""
        grabbed = []
        monkeypatch.setattr(step, "frame_at", lambda video, when, dest: grabbed.append(when) or dest)
        step.frames_of(tmp_path / "take.mp4", 4.85, tmp_path / "work")
        assert all(step.HEAD_TRIM < when < 4.85 for when in grabbed)

    def test_measure_scores_the_take_by_the_traits_it_shares(self, tmp_path, monkeypatch):
        monkeypatch.setattr(step, "clip_seconds", lambda p: 7.0)
        monkeypatch.setattr(step, "frames_of", lambda video, seconds, work: [])
        monkeypatch.setattr(step, "describe_frames", lambda frames, seed, run=None: MID)
        found = step.measure(tmp_path / "take.mp4", SHEET, tmp_path / "work", seed=1)
        assert found["differs"] == ["hair_colour", "headgear", "build"] and found["known"] == 7
        assert found["similarity"] == pytest.approx(4 / 7, abs=0.001)
        assert step.measure(tmp_path / "take.mp4", None, tmp_path / "work", seed=1)["similarity"] is None


class TestPromote:
    """A clip without its recipe cannot be told from last plan's render, and
    run 10 cut 24% of its picture from exactly that."""

    RECIPE = {"prompt": "a man in fog", "seed": 51000}

    def take(self, tmp_path, recipe=None):
        take = tmp_path / "takes" / "B00-51000.mp4"
        take.parent.mkdir(parents=True, exist_ok=True)
        take.write_bytes(b"mp4")
        if recipe is not None:
            record(take, recipe)
        return take

    def test_the_recipe_travels_with_the_take(self, tmp_path):
        dest = step.promote(self.take(tmp_path, self.RECIPE), tmp_path / "clips/B00.mp4")
        assert dest.read_bytes() == b"mp4" and is_current(dest, self.RECIPE)

    def test_a_take_with_no_recipe_still_promotes_its_video(self, tmp_path):
        dest = step.promote(self.take(tmp_path), tmp_path / "clips/B00.mp4")
        assert dest.exists() and stored_fingerprint(dest) is None


class TestClipRecord:
    def test_the_record_carries_the_promoted_clip_s_fingerprint(self, tmp_path):
        book = tmp_path
        dest = book / "trailer/main/clips/B00.mp4"
        dest.parent.mkdir(parents=True)
        dest.write_bytes(b"mp4")
        record(dest, {"prompt": "p", "seed": 1})
        found = step.clip_record("B00", {"seconds": 7.0, "seed": 1, "similarity": None,
                                         "differs": [], "known": 0}, book, dest, None, None, [])
        assert found["fingerprint"] == fingerprint({"prompt": "p", "seed": 1})

    def test_a_clip_with_no_sidecar_records_no_fingerprint(self, tmp_path):
        dest = tmp_path / "trailer/main/clips/B00.mp4"
        dest.parent.mkdir(parents=True)
        dest.write_bytes(b"mp4")
        found = step.clip_record("B00", {"seconds": 7.0, "seed": 1, "similarity": None,
                                         "differs": [], "known": 0}, tmp_path, dest, None, None, [])
        assert found["fingerprint"] is None


class TestRounds:
    """THE ROUND IS THE UNIT.  Run 10 spent 8.3 of every 15.76 minutes on a
    model swap: `describe_frames` freed the engine before every take's read,
    which unloaded H3's DiT, text encoder and VAEs, and the next take
    re-streamed 16 GB off a spinning disk.  A round renders every live beat
    back to back with H3 resident, unloads ONCE, and reads the lot in one
    session."""

    def test_twelve_beats_that_bind_cost_one_unload_and_one_session(self, tmp_path, rendered):
        ctx = make_ctx(tmp_path, rendered["clock"], beats=12)
        rendered["cards"] = [NEAR] * 12
        step.run(ctx.codex_id, ctx)
        assert len(rendered["calls"]) == 12
        assert rendered["sessions"] == [True]
        assert rendered["reads"] == ["reader-1"] * 12
        assert len(clips_doc(ctx)["clips"]) == 12 and rungs(ctx) == []

    def test_the_takes_of_a_round_are_rendered_before_any_of_them_is_read(
            self, tmp_path, rendered, monkeypatch):
        ctx = make_ctx(tmp_path, rendered["clock"], beats=3)
        order = []
        rendered["cards"] = [NEAR] * 3
        made, read = step.render_take, step.describe_frames
        monkeypatch.setattr(step, "render_take",
                            lambda *a: order.append("render") or made(*a))
        monkeypatch.setattr(step, "describe_frames",
                            lambda frames, seed, run=None:
                            order.append("read") or read(frames, seed, run))
        step.run(ctx.codex_id, ctx)
        assert order == ["render"] * 3 + ["read"] * 3

    def test_two_beats_that_reroll_make_a_second_round_of_two_renders_and_one_session(
            self, tmp_path, rendered):
        ctx = make_ctx(tmp_path, rendered["clock"], beats=4)
        rendered["cards"] = [NEAR, FAR, FAR, NEAR, NEAR, NEAR]
        step.run(ctx.codex_id, ctx)
        assert [c["dest"][:3] for c in rendered["calls"]] == [
            "B00", "B01", "B02", "B03", "B01", "B02"]
        assert rendered["sessions"] == [True, True]
        assert rendered["reads"] == ["reader-1"] * 4 + ["reader-2"] * 2
        assert [c["capped"] for c in clips_doc(ctx)["clips"]] == [None] * 4
        assert [r.action for r in rungs(ctx)] == ["reroll_seed", "reroll_seed"]

    def test_a_round_keeps_back_the_time_its_reader_session_needs(self, tmp_path, rendered):
        """A take rendered with no time left to read it ships unread, which is
        a take nobody gated.  The round reserves the session before it stages
        the first render."""
        ctx = make_ctx(tmp_path, rendered["clock"], ceiling=1715, beats=2)  # 07's share: 1000 s
        assert step.RENDER_SECONDS < ctx.budget.remaining("07") < step.take_cost(0)
        step.run(ctx.codex_id, ctx)
        assert rendered["calls"] == [] and rendered["sessions"] == []
        assert clips_doc(ctx)["dropped"] == ["B00", "B01"]
        assert rungs(ctx)[0].threshold == step.take_cost(0)

    def test_a_beat_that_binds_stops_asking_for_takes(self, tmp_path, rendered):
        """The round shrinks to the beats still climbing; a bound beat is not
        re-rendered because its neighbour rerolled."""
        ctx = make_ctx(tmp_path, rendered["clock"], beats=3)
        rendered["cards"] = [NEAR, FAR, NEAR, NEAR]
        step.run(ctx.codex_id, ctx)
        assert [c["dest"][:3] for c in rendered["calls"]] == ["B00", "B01", "B02", "B01"]
        assert rendered["reads"] == ["reader-1"] * 3 + ["reader-2"]


class TestRoundCost:
    """What a round costs, so the budget can be asked before one starts."""

    def test_reading_nothing_costs_nothing(self):
        assert step.read_seconds(0) == 0.0

    def test_a_session_is_paid_once_and_then_a_sheet_at_a_time(self):
        assert step.read_seconds(1) == step.SESSION_SECONDS
        assert step.read_seconds(3) == step.SESSION_SECONDS + 2 * step.SHEET_SECONDS

    def test_the_first_take_of_a_round_carries_the_whole_session(self):
        assert step.take_cost(0) == step.RENDER_SECONDS + step.SESSION_SECONDS

    def test_every_further_take_of_a_round_carries_only_its_sheet(self):
        assert step.take_cost(3) == step.RENDER_SECONDS + step.SHEET_SECONDS


class TestMeasuredCycle:
    """The cycle stops being a constant a person typed.  Run 10 planned on 11
    min a take and rendered at 15.76, and the budget rung dropped the last six
    beats -- which are the climax."""

    def test_every_round_learns_what_a_take_cost_it(self, ctx, rendered):
        rendered["cards"] = [NEAR]
        step.run(ctx.codex_id, ctx)
        cycle = [r for r in load(ctx.learnings_path) if r.gate == "cycle"]
        assert len(cycle) == 1 and cycle[0].step == "07" and cycle[0].action == "round_1"
        assert cycle[0].measured == pytest.approx(
            (2 * step.RENDER_SECONDS + step.SESSION_SECONDS) / 2, abs=0.1)
        assert cycle[0].threshold == step.RENDER_SECONDS

    def test_the_reader_session_is_measured_on_its_own(self, ctx, rendered):
        rendered["cards"] = [NEAR]
        step.run(ctx.codex_id, ctx)
        read = [r for r in load(ctx.learnings_path) if r.gate == "read"]
        assert len(read) == 1 and read[0].action == "session"
        assert read[0].measured == pytest.approx(step.SESSION_SECONDS, abs=0.1)
        assert read[0].threshold == step.read_seconds(1)

    def test_a_round_that_rendered_nothing_measures_no_cycle(self, tmp_path, rendered):
        ctx = make_ctx(tmp_path, rendered["clock"], ceiling=100)
        step.run(ctx.codex_id, ctx)
        assert [r for r in load(ctx.learnings_path) if r.gate in step.MEASURED] == []

    def test_with_nothing_measured_the_cycle_is_the_constant(self):
        assert step.render_seconds([]) == step.RENDER_SECONDS

    def test_the_cycle_is_the_median_of_the_rounds_that_measured_one(self):
        rows = [Learning(step="07", gate="cycle", action="round_1", measured=500.0),
                Learning(step="07", gate="cycle", action="round_2", measured=400.0),
                Learning(step="07", gate="cycle", action="round_3", measured=900.0)]
        assert step.render_seconds(rows) == 500.0

    def test_only_step_07_cycle_rows_are_a_take_s_cycle(self):
        rows = [Learning(step="07", gate="read", action="session", measured=240.0),
                Learning(step="02", gate="cycle", action="round_1", measured=90.0),
                Learning(step="07", gate="identity", action="reroll_seed", measured=4.0)]
        assert step.render_seconds(rows) == step.RENDER_SECONDS

    def test_the_next_plan_reads_this_run_s_cycle_off_the_book(self, ctx, rendered):
        """What step 06 calls: the plan is sized by what the machine has
        actually done on this book, not by the constant."""
        rendered["cards"] = [NEAR]
        step.run(ctx.codex_id, ctx)
        assert step.render_seconds_for(ctx) == pytest.approx(
            (2 * step.RENDER_SECONDS + step.SESSION_SECONDS) / 2, abs=0.1)
