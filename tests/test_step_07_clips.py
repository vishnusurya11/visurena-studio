"""Step 07 of the trailer stage: one take per beat, identity-gated.

A take whose person does not read as its reference sheet -- DISTINCT_AT or
more traits apart, as a vision model reads the sampled frames -- climbs
seed x2 then a whole-take close-up; the terminal rung ships the BEST take
capped at a short shot.  A beat is dropped only when no take exists at all
-- the budget gone before its first render, or the render itself failing.
Renders and readings are faked; nothing here touches a GPU.
"""
from __future__ import annotations

import json

import pytest
from PIL import Image

from scripts.trailer import step_07_clips as step
from scripts.trailer.build_clips import FRAMING
from studio import db
from studio.describe import DISTINCT_AT, TraitCard
from studio.learnings import load
from studio.run_budget import TRAILER_SHARES, Budget
from studio.trailer_run import RunContext

HOLMES = "sherlock_holmes"
SHEET = TraitCard(age="middle-aged", hair_colour="dark brown", hair_length="short",
                  facial_hair="clean-shaven", headgear="bowler", complexion="sallow", build="slight")
NEAR = SHEET.model_copy(update={"headgear": "none"})                       # 1 apart: bound
FAR = SHEET.model_copy(update={"hair_colour": "fair", "headgear": "none",
                               "facial_hair": "beard", "build": "stocky"})  # 4 apart: not him
MID = SHEET.model_copy(update={"hair_colour": "grey", "headgear": "none", "build": "heavy"})  # 3
BLIND = SHEET.model_copy(update={t: "unclear" for t in ("age", "hair_colour", "headgear", "build")})


def beat(beat_id, cast, loc):
    return {"beat_id": beat_id, "scene_number": 1, "arc": "quiet", "location_id": loc,
            "cast": cast, "image_prompt": "He crosses to the window.",
            "motion": "The camera pushes in slowly.", "line": None, "speaker": None}


def ref(ref_id, kind, rel_path):
    return {"ref_id": ref_id, "kind": kind, "entity_id": ref_id[4:], "name": ref_id[4:],
            "physical": "A tall thin man with a hawk nose.", "prompt": "", "rel_path": rel_path}


def make_ctx(tmp_path, clock, ceiling=6 * 3600):
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
    plan = {"beats": [beat("B00", [HOLMES], "baker_street"), beat("B01", [], "brixton_road")],
            "shots": [{"beat_id": "B00", "index": 0, "seconds": 2.5, "size": "medium"},
                      {"beat_id": "B00", "index": 1, "seconds": 1.0, "size": "close"},
                      {"beat_id": "B01", "index": 2, "seconds": 1.5, "size": "wide"}]}
    (context.out_dir / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
    context.open_step("07")
    return context


@pytest.fixture()
def rendered(monkeypatch):
    """Faked renders and readings: `cards` is consumed per bound take."""
    calls = []

    def render_take(values, bound, refs, book, dest):
        calls.append({"seed": values["seed"], "prompt": values["prompt"], "dest": dest.name})
        state["clock"][0] += step.RENDER_SECONDS
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"mp4" + str(values["seed"]).encode())
        return dest
    state = {"calls": calls, "cards": [], "clock": [0.0]}
    monkeypatch.setattr(step, "render_take", render_take)
    monkeypatch.setattr(step, "is_complete", lambda p: p.exists())
    monkeypatch.setattr(step, "clip_seconds", lambda p: 7.0)
    monkeypatch.setattr(step, "describe", lambda path, seed: SHEET)
    monkeypatch.setattr(step, "frames_of", lambda video, seconds, work: [])
    monkeypatch.setattr(step, "describe_frames", lambda frames, seed: state["cards"].pop(0))
    return state


@pytest.fixture()
def ctx(tmp_path, rendered):
    return make_ctx(tmp_path, rendered["clock"])


def clips_doc(ctx):
    return json.loads((ctx.out_dir / "clips.json").read_text(encoding="utf-8"))


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
        assert (ctx.book_dir / by_id["B00"]["rel_path"]).exists()
        assert len(rendered["calls"]) == 2 and load(ctx.learnings_path) == []

    def test_a_weak_face_rerolls_the_seed_then_binds(self, ctx, rendered):
        rendered["cards"] = [FAR, NEAR]
        step.run(ctx.codex_id, ctx)
        clip = next(c for c in clips_doc(ctx)["clips"] if c["beat_id"] == "B00")
        assert clip["similarity"] == pytest.approx(6 / 7, abs=0.001) and clip["capped"] is None
        rows = load(ctx.learnings_path)
        assert [r.action for r in rows] == ["reroll_seed"]
        assert rows[0].measured == 4 and rows[0].threshold == DISTINCT_AT
        seeds = [c["seed"] for c in rendered["calls"] if c["dest"].startswith("B00")]
        assert len(seeds) == 2 and len(set(seeds)) == 2

    def test_a_face_that_never_binds_ships_its_best_take_short(self, ctx, rendered):
        rendered["cards"] = [FAR, MID, FAR]
        step.run(ctx.codex_id, ctx)
        doc = clips_doc(ctx)
        clip = next(c for c in doc["clips"] if c["beat_id"] == "B00")
        assert clip["capped"] == step.SHORT_SHOT and clip["similarity"] == pytest.approx(4 / 7, abs=0.001)
        assert doc["dropped"] == []
        actions = [r.action for r in load(ctx.learnings_path)]
        assert actions == ["reroll_seed", "reroll_seed", "alternate_setup", "short_shot"]
        holmes_calls = [c for c in rendered["calls"] if c["dest"].startswith("B00")]
        assert len(holmes_calls) == 3
        assert holmes_calls[-1]["prompt"].count(FRAMING["close"]) == 2
        assert (ctx.book_dir / clip["rel_path"]).read_bytes() == b"mp4" + str(clip["seed"]).encode()

    def test_a_person_too_unclear_to_read_is_accepted_and_flagged(self, ctx, rendered):
        rendered["cards"] = [BLIND]
        step.run(ctx.codex_id, ctx)
        clip = next(c for c in clips_doc(ctx)["clips"] if c["beat_id"] == "B00")
        assert clip["capped"] is None and clip["known"] == 3
        assert [r.action for r in load(ctx.learnings_path)] == ["accepted_unverifiable"]

    def test_a_take_that_fails_to_render_drops_the_beat(self, ctx, rendered, monkeypatch):
        def broken(values, bound, refs, book, dest):
            raise RuntimeError("no video")
        monkeypatch.setattr(step, "render_take", broken)
        step.run(ctx.codex_id, ctx)
        doc = clips_doc(ctx)
        assert doc["clips"] == [] and doc["dropped"] == ["B00", "B01"]
        rows = load(ctx.learnings_path)
        assert {r.gate for r in rows} == {"render"} and all(r.terminal for r in rows)


class TestBudget:
    def test_no_time_for_a_retry_ships_the_first_take_short(self, tmp_path, rendered):
        ctx = make_ctx(tmp_path, rendered["clock"], ceiling=1500)
        rendered["cards"] = [FAR]
        step.run(ctx.codex_id, ctx)
        doc = clips_doc(ctx)
        assert doc["clips"][0]["capped"] == step.SHORT_SHOT and doc["dropped"] == ["B01"]
        rows = load(ctx.learnings_path)
        assert [r.gate for r in rows] == ["identity", "budget", "budget"]
        assert [r.action for r in rows[1:]] == ["short_shot", step.DROPPED]

    def test_no_time_for_a_first_render_drops_the_remaining_beats(self, tmp_path, rendered):
        ctx = make_ctx(tmp_path, rendered["clock"], ceiling=100)
        step.run(ctx.codex_id, ctx)
        doc = clips_doc(ctx)
        assert doc["clips"] == [] and doc["dropped"] == ["B00", "B01"]
        assert rendered["calls"] == []
        assert {r.gate for r in load(ctx.learnings_path)} == {"budget"}


class TestNeedSeconds:
    def test_the_longest_shot_of_the_beat_plus_the_head_leak(self):
        plan = {"shots": [{"beat_id": "B00", "seconds": 2.5}, {"beat_id": "B00", "seconds": 1.0},
                          {"beat_id": "B01", "seconds": 1.5}]}
        assert step.need_seconds("B00", plan) == pytest.approx(2.5 + step.HEAD_LEAK_SECONDS)
        assert step.need_seconds("B77", plan) == pytest.approx(step.HEAD_LEAK_SECONDS)


class TestMeasure:
    def test_frames_of_samples_three_stills_outside_the_head_leak(self, tmp_path, monkeypatch):
        grabbed = []
        monkeypatch.setattr(step, "frame_at", lambda video, when, dest: grabbed.append(when) or dest)
        found = step.frames_of(tmp_path / "take.mp4", 7.0, tmp_path / "work")
        assert len(found) == 3 and (tmp_path / "work").is_dir()
        assert all(when > step.HEAD_LEAK_SECONDS for when in grabbed) and grabbed == sorted(grabbed)

    def test_measure_scores_the_take_by_the_traits_it_shares(self, tmp_path, monkeypatch):
        monkeypatch.setattr(step, "clip_seconds", lambda p: 7.0)
        monkeypatch.setattr(step, "frames_of", lambda video, seconds, work: [])
        monkeypatch.setattr(step, "describe_frames", lambda frames, seed: MID)
        found = step.measure(tmp_path / "take.mp4", SHEET, tmp_path / "work", seed=1)
        assert found["differs"] == ["hair_colour", "headgear", "build"] and found["known"] == 7
        assert found["similarity"] == pytest.approx(4 / 7, abs=0.001)
        assert step.measure(tmp_path / "take.mp4", None, tmp_path / "work", seed=1)["similarity"] is None
