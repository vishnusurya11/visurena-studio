"""The tiny-face rung (step 09_08, face-blur round 2; BENCH_R2 lead 5, arm A3c).

The face refine refuses a face it cannot paste cleanly; under about 40 px nothing else can give it
an eye.  The bench's 1024x1024 draw of ep01 T01 was the only arm that drew both refused faces
(Utterson 36 px, Enfield 30 px, seam 19.1) with clean ink lines.  So a take whose refine REFUSED
(seam or drift) a planned person's face of 20-40 px earns ONE re-render on the 1024 graph, judged by
every take gate; it is kept only when it passes them all, else the old take stays.  Replayed on the
bench's own ep01 refine rows (tests/fixtures/ep01_replay/tiny_face/refine.json, a copy of
bench/r2/room/refine.json), ep01's plan (P08/plan.json) and its cards (face_blur/cards.json).
Nothing renders here: the render, the checks and the judge are fakes."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.episode import face_refine as cli
from scripts.episode import tiny_face as tf
from studio import episode_home, step_attempts, step_caps, take_ladder
from studio.judges.verdict import Fault, Verdict
from studio.run_budget import EPISODE_SHARES, Budget

FIX = Path(__file__).resolve().parent / "fixtures" / "ep01_replay"
DOC = json.loads((FIX / "tiny_face" / "refine.json").read_text(encoding="utf-8"))
PLAN = json.loads((FIX / "P08" / "plan.json").read_text(encoding="utf-8"))
CARDS = json.loads((FIX / "face_blur" / "cards.json").read_text(encoding="utf-8"))


def row(who="mr_a", kept=False, why="seam 19.1 > 18.0", face_px=33.0, **more):
    return {"who": who, "kept": kept, "why": why, "face_px": face_px, **more}


# ---- the rule, replayed on ep01's bench rows -------------------------------------------------

def test_ep01_t01_earns_the_rung_for_both_refused_faces():
    assert tf.qualifying(DOC, CARDS, PLAN) == {1: ["gabriel_john_utterson", "richard_enfield"]}


def test_ep01_t07s_child_is_refused_but_its_insert_renders_on_wuli_not_the_1024_graph():
    child = next(p for p in DOC["T07"]["people"] if p["who"] == "child_of_hyde_incident")
    assert tf.refused_tiny(child) and "child_of_hyde_incident" in tf.planned(PLAN, [7])
    assert not tf.on_spark(CARDS[7]) and 7 not in tf.qualifying(DOC, CARDS, PLAN)


def test_ep01_t06s_far_hyde_was_kept_and_is_under_the_floor():
    hyde = next(p for p in DOC["T06"]["people"] if p["who"] == "edward_hyde")
    assert hyde["kept"] and not tf.refused_tiny(hyde)
    assert not tf.refused_tiny({**hyde, "kept": False, "why": "seam 19.0 > 18.0"})


def test_only_a_seam_or_drift_refusal_of_a_face_under_40_px_counts():
    assert tf.refused_tiny(row()) and tf.refused_tiny(row(why="drift 43.3 > 35.0"))
    assert not tf.refused_tiny(row(kept=True, why="kept"))
    assert not tf.refused_tiny(row(why="identity ccip 0.21 > 0.18"))
    assert not tf.refused_tiny(row(face_px=40.0)) and not tf.refused_tiny(row(face_px=19.9))


def test_the_smallest_tracked_face_rules_over_the_median():
    assert tf.refused_tiny(row(face_px=44.0, min_px=36.0))
    assert not tf.refused_tiny(row(face_px=36.0, min_px=12.0))


def test_a_planned_person_is_a_face_of_the_shot_or_a_speaker_in_it():
    assert tf.planned(PLAN, [6]) == {"richard_enfield", "edward_hyde"}
    plan = {"shots": [{"index": 3, "faces": []}], "lines": [{"shot": 3, "speaker": "mr_a", "kind": "dialogue"},
                                                             {"shot": 3, "speaker": "narrator", "kind": "narration"}]}
    assert tf.planned(plan, [3]) == {"mr_a"}


def test_an_unplanned_person_earns_nothing():
    doc = {"T01": {"people": [row(who="a_stranger")]}}
    assert tf.qualifying(doc, CARDS, PLAN) == {}


def test_only_a_square_episode_draws_at_1024():
    assert tf.square({"aspect": "1:1"}) and tf.square({}) and not tf.square({"aspect": "9:16"})


def test_the_price_is_a_cold_load_and_175_times_a_take_per_take_plus_the_refine_again():
    assert tf.price(1, 2) == pytest.approx(take_ladder.COLD_S + 1.75 * take_ladder.TAKE_S + tf.fr.price(2, tf.fr.REF_FRAMES))


# ---- what is owed, on disk ---------------------------------------------------------------------

def room_at(tmp_path, entry_people=None, aspect="1:1"):
    book = tmp_path / "book"
    home = episode_home.home(book, 1)
    room = home / "takes" / "r2v"
    (room / "attempts").mkdir(parents=True)
    (room / "T01.mp4").write_bytes(b"old take")
    (room / "T01.dq.json").write_text('{"old": "dq"}', encoding="utf-8")
    (room / "T01.content.json").write_text('{"old": "content"}', encoding="utf-8")
    (room / "T01.graph.json").write_text('{"old": "graph"}', encoding="utf-8")
    (room / "shots.json").write_text(json.dumps([{"index": 1, "seed": 5, "tries": 0}]), encoding="utf-8")
    (room / "prompts.json").write_text(json.dumps([CARDS[1]]), encoding="utf-8")
    (home / "plan.json").write_text(json.dumps({**PLAN, "aspect": aspect}), encoding="utf-8")
    people = entry_people if entry_people is not None else DOC["T01"]["people"]
    (room / "refine.json").write_text(json.dumps({"T01": {"status": "unrefined", "people": people,
                                                          "take_sha8": cli.sha8(room / "T01.mp4")}}), encoding="utf-8")
    return book, home, room


def test_a_refusal_on_the_current_bytes_is_owed(tmp_path):
    book, home, room = room_at(tmp_path)
    assert tf.owed(home) == {1: ["gabriel_john_utterson", "richard_enfield"]}


def test_a_refusal_of_other_bytes_is_not(tmp_path):
    book, home, room = room_at(tmp_path)
    (room / "T01.mp4").write_bytes(b"another take")
    assert tf.owed(home) == {}


def test_one_draw_per_take_per_episode(tmp_path):
    book, home, room = room_at(tmp_path)
    step_attempts.spend(home, tf.key(1))
    assert tf.owed(home) == {}


def test_a_portrait_episode_is_not_drawn_at_1024(tmp_path):
    book, home, room = room_at(tmp_path, aspect="9:16")
    assert tf.owed(home) == {}


def test_a_take_the_cut_shows_as_a_still_is_not_drawn(tmp_path):
    book, home, room = room_at(tmp_path)
    (room / "stills.json").write_text(json.dumps({"1": {"panel": "x.png", "seconds": 2.0}}), encoding="utf-8")
    assert tf.owed(home) == {}


def test_the_rungs_draw_buys_the_take_one_more_refine(tmp_path):
    book, home, room = room_at(tmp_path)
    cli.count_refine(home, 1)
    assert cli.refined_out(home, 1)
    step_attempts.spend(home, tf.key(1))
    assert not cli.refined_out(home, 1)
    cli.count_refine(home, 1)
    assert cli.refined_out(home, 1)


# ---- the walls --------------------------------------------------------------------------------

def ctx_at(home, spent=0.0, renders=None, fail_render=False):
    now = [0.0]
    budget = Budget(5 * 3600, EPISODE_SHARES, clock=lambda: now[0], limit=6 * 3600)
    budget.start("09")
    now[0] = spent
    ran, logged = [], []

    def run_script(script, *extra, **kw):
        ran.append((script, extra, kw))
        if script == tf.RENDER:
            if fail_render:
                raise SystemExit(f"REFUSED: {script} exit 1")
            for i in renders or []:
                take = home / "takes" / "r2v" / f"T{i:02d}.mp4"
                episode_home.displace(take, i)              # what takes_r2v.make_room does
                take.write_bytes(b"1024 draw")
        return 0
    return SimpleNamespace(home=home, book_dir=home.parents[1], number=1, budget=budget, ran=ran, logged=logged,
                           log=lambda msg, **k: logged.append(msg), run_script=run_script)


def test_a_full_retakes_wall_refuses_the_rung(tmp_path):
    book, home, room = room_at(tmp_path)
    step_attempts.add_seconds(home, take_ladder.RETAKES, step_caps.wall_s(take_ladder.RETAKES) - 60.0)
    assert "retakes wall" in tf.refused(ctx_at(home), 1, 2)


def test_a_short_clock_refuses_the_rung_before_any_check(tmp_path):
    book, home, room = room_at(tmp_path)
    assert "reserve" in tf.refused(ctx_at(home, spent=6 * 3600), 1, 2)
    assert tf.refused(ctx_at(home), 1, 2) == ""


# ---- the pass ---------------------------------------------------------------------------------

def verdict(passed: bool) -> Verdict:
    faults = [] if passed else [Fault(kind="warp", where="T01", severity="high", evidence={})]
    return Verdict(judge="take_eye", version="1", passed=passed, faults=faults, confidence=1.0, reads=1)


def test_a_draw_that_passes_every_gate_is_kept_and_named(tmp_path):
    book, home, room = room_at(tmp_path)
    ctx = ctx_at(home, renders=[1])
    assert tf.rung(ctx, "--approved=render", judge=lambda take: verdict(True)) == [1]
    assert (room / "T01.mp4").read_bytes() == b"1024 draw"
    render = ctx.ran[0]
    assert render[0] == tf.RENDER and "--tiny-face" in render[1] and "--retake=1" in render[1]
    assert "--last" in render[1] and render[2]["gpu"] is True
    assert [s for s, _, _ in ctx.ran[1:]] == [tf.DQ, tf.CONTENT]
    assert "--attempts" not in ctx.ran[1][1]


def test_a_draw_that_fails_a_gate_gives_the_old_take_back_with_its_verdicts(tmp_path):
    book, home, room = room_at(tmp_path)
    ctx = ctx_at(home, renders=[1])
    assert tf.rung(ctx, "--approved=render", judge=lambda take: verdict(False)) == []
    assert (room / "T01.mp4").read_bytes() == b"old take"
    assert json.loads((room / "T01.dq.json").read_text()) == {"old": "dq"}
    assert json.loads((room / "T01.graph.json").read_text()) == {"old": "graph"}
    assert (room / "T01.content.json").stat().st_mtime >= (room / "T01.mp4").stat().st_mtime
    assert json.loads((room / "shots.json").read_text()) == [{"index": 1, "seed": 5, "tries": 0}]
    assert [p.read_bytes() for p in (room / "attempts").glob("T01_fail*.mp4")] == [b"1024 draw"]
    assert any("old take stays" in m for m in ctx.logged)


def test_the_rung_spends_its_one_draw_and_books_its_seconds(tmp_path):
    book, home, room = room_at(tmp_path)
    ctx = ctx_at(home, renders=[1])
    tf.rung(ctx, "--approved=render", judge=lambda take: verdict(True))
    assert step_attempts.count(home, tf.key(1)) == 1
    assert step_attempts.count(home, take_ladder.RETAKES) == 0
    ran = len(ctx.ran)
    assert tf.rung(ctx, "--approved=render", judge=lambda take: verdict(True)) == [] and len(ctx.ran) == ran


def test_a_render_that_died_gives_back_every_take_it_left_missing(tmp_path):
    book, home, room = room_at(tmp_path)
    (room / "T01.mp4").rename(room / "attempts" / "T01_fail1.mp4")   # make_room ran, the draw never landed
    (room / "T01.mp4").write_bytes(b"old take")
    ctx = ctx_at(home, fail_render=True)

    def vanish(script, *extra, **kw):
        episode_home.displace(room / "T01.mp4", 1)
        raise SystemExit("REFUSED: takes_r2v exit 1")
    ctx.run_script = vanish
    with pytest.raises(SystemExit):
        tf.rung(ctx, "--approved=render", judge=lambda take: verdict(True))
    assert (room / "T01.mp4").read_bytes() == b"old take"


def test_nothing_owed_renders_nothing(tmp_path):
    book, home, room = room_at(tmp_path, entry_people=[row(kept=True, why="kept")])
    ctx = ctx_at(home)
    assert tf.rung(ctx, "--approved=render", judge=lambda take: verdict(True)) == [] and ctx.ran == []


def test_a_refused_rung_says_so_and_renders_nothing(tmp_path):
    book, home, room = room_at(tmp_path)
    ctx = ctx_at(home, spent=6 * 3600)
    assert tf.rung(ctx, "--approved=render", judge=lambda take: verdict(True)) == [] and ctx.ran == []
    assert any(m.startswith("TINY FACE CUT") for m in ctx.logged)
