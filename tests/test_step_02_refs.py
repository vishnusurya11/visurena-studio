"""Step 02 of the trailer stage: reference sheets that a recogniser can tell apart.

Every character sheet is rendered, embedded, and judged against the cast
already bound.  A collision climbs seed x3 then pose x2; a character that
still collides is UNBOUND -- written to refs.json's `unbound` list, absent
from `refs`, so every setup needing it is excluded downstream.  Renders and
embeddings are faked; nothing here touches a GPU or a model file.
"""
from __future__ import annotations

import json

import numpy as np
import pytest
from PIL import Image

from scripts.trailer import step_02_refs as step
from studio import db
from studio.learnings import load
from studio.trailer_run import RunContext

HOLMES, WATSON = "sherlock_holmes", "john_watson"


def character(char_id, name, physical="A tall thin man with a hawk nose."):
    return {"id": char_id, "name": name, "aliases": [], "role": "protagonist",
            "profile": {"physical": physical}}


def scene(number, cast, loc="baker_street"):
    return {"number": number, "cast": cast, "speaking": cast[:1],
            "slug": {"location_id": loc, "location_name": loc.replace("_", " ").title()},
            "elements": [{"kind": "action", "text": "He crosses the room."}]}


@pytest.fixture()
def ctx(tmp_path):
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    codex_id = db.insert_codex(conn, "Scarlet", codex_id="20260901000002")
    book = tmp_path / "20260901000002_scarlet"
    (book / "analysis/characters").mkdir(parents=True)
    for char_id, name in ((HOLMES, "Sherlock Holmes"), (WATSON, "John Watson")):
        (book / "analysis/characters" / f"{char_id}.json").write_text(
            json.dumps(character(char_id, name)), encoding="utf-8")
    (book / "screenplay/feature").mkdir(parents=True)
    scenes = [scene(1, [WATSON, HOLMES]), scene(2, [HOLMES], "brixton_road"), scene(3, [WATSON])]
    (book / "screenplay/feature/screenplay.json").write_text(
        json.dumps({"title": "A Study in Scarlet", "scenes": scenes}), encoding="utf-8")
    context = RunContext(conn, codex_id, book, logs_root=tmp_path / "logs")
    context.out_dir.mkdir(parents=True)
    (context.out_dir / "story.json").write_text(json.dumps(
        {"lead": WATSON, "figure": "jefferson_hope", "turn_scene": 2, "narrator": WATSON,
         "register": "detective", "thesis": None, "setting": "1881 London"}), encoding="utf-8")
    context.open_step("02")
    return context


def fake_generate(prompt, prefix, seed, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (8, 8)).save(dest)
    return dest


@pytest.fixture()
def rendered(monkeypatch):
    """Faked renders and embeddings: `vectors` is consumed per embed call."""
    monkeypatch.setattr(step, "generate", fake_generate)
    monkeypatch.setattr(step, "ensure_models", lambda: {})
    monkeypatch.setattr(step, "open_sessions", lambda models: None)
    state = {"vectors": [], "px": 90}
    monkeypatch.setattr(step, "embed_file", lambda s, p: (state["vectors"].pop(0), state["px"]))
    return state


A, B = np.array([1.0, 0.0]), np.array([0.0, 1.0])


def refs_doc(ctx):
    return json.loads((ctx.book_dir / "refs/refs.json").read_text(encoding="utf-8"))


class TestRun:
    def test_binds_a_distinct_cast_and_renders_locations(self, ctx, rendered):
        rendered["vectors"] = [A, B]
        step.run(ctx.codex_id, ctx)
        doc = refs_doc(ctx)
        assert {r["ref_id"] for r in doc["refs"]} == {
            f"char-{WATSON}", f"char-{HOLMES}", "loc-baker_street", "loc-brixton_road"}
        assert doc["unbound"] == [] and "1881 London" in doc["palette"]
        assert (ctx.book_dir / "refs/characters" / f"char-{HOLMES}.png").exists()

    def test_a_collision_rerolls_the_seed_then_binds(self, ctx, rendered):
        rendered["vectors"] = [A, A, B]
        step.run(ctx.codex_id, ctx)
        assert refs_doc(ctx)["unbound"] == []
        rows = load(ctx.learnings_path)
        assert [r.action for r in rows] == ["reroll_seed"]
        assert rows[0].measured == pytest.approx(1.0)

    def test_a_persistent_collision_unbinds_the_character(self, ctx, rendered):
        rendered["vectors"] = [A] * 7
        step.run(ctx.codex_id, ctx)
        doc = refs_doc(ctx)
        assert doc["unbound"] == [HOLMES]
        assert f"char-{HOLMES}" not in {r["ref_id"] for r in doc["refs"]}
        actions = [r.action for r in load(ctx.learnings_path)]
        assert actions == ["reroll_seed"] * 3 + ["alternate_pose"] * 2 + ["unbound"]

    def test_a_face_too_small_to_read_is_accepted_and_flagged(self, ctx, rendered):
        rendered["vectors"] = [A, A]
        rendered["px"] = 30
        step.run(ctx.codex_id, ctx)
        assert refs_doc(ctx)["unbound"] == []
        assert {r.action for r in load(ctx.learnings_path)} == {"accepted_unverifiable"}


class TestAttemptShape:
    def test_reroll_changes_the_seed_and_pose_changes_the_prompt(self):
        first = step.seed_for(0, step.LADDER.rungs[0], 0)
        assert step.seed_for(0, step.LADDER.rungs[0], 1) != first
        assert step.pose_for(step.LADDER.rungs[0], 2) == ""
        assert step.pose_for(step.LADDER.rungs[1], 0) != step.pose_for(step.LADDER.rungs[1], 1)
