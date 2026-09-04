"""Step 02 of the trailer stage: reference sheets a viewer can tell apart.

Every character sheet is rendered, READ BACK by a vision model into a trait
card, and judged against the cast already bound: fewer than DISTINCT_AT
traits apart is a collision.  A collision climbs one reroll, then three
`distinguish` rungs that rewrite exactly the shared traits; a character that
still collides is UNBOUND -- in refs.json's `unbound` list, absent from
`refs`, so every setup needing it is excluded downstream.  Renders and
descriptions are faked; nothing here touches a GPU or a model file.
"""
from __future__ import annotations

import json

import pytest
from PIL import Image

from scripts.trailer import step_02_refs as step
from studio import db
from studio.describe import DISTINCT_AT, TraitCard
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
    """Faked renders and readings: `cards` is consumed per describe call;
    `prompts` records what each render was asked for."""
    state = {"cards": [], "prompts": []}

    def generate(prompt, prefix, seed, dest):
        state["prompts"].append(prompt)
        return fake_generate(prompt, prefix, seed, dest)
    monkeypatch.setattr(step, "generate", generate)
    monkeypatch.setattr(step, "describe", lambda path, seed: state["cards"].pop(0))
    return state


A = TraitCard(age="middle-aged", hair_colour="dark brown", hair_length="short",
              facial_hair="clean-shaven", headgear="bowler", complexion="sallow", build="slight")
B = A.model_copy(update={"hair_colour": "fair", "headgear": "none", "build": "stocky"})
BLIND = A.model_copy(update={t: "unclear" for t in ("age", "hair_colour", "headgear", "build")})


def refs_doc(ctx):
    return json.loads((ctx.book_dir / "refs/refs.json").read_text(encoding="utf-8"))


class TestRun:
    def test_binds_a_distinct_cast_and_renders_locations(self, ctx, rendered):
        rendered["cards"] = [A, B]
        step.run(ctx.codex_id, ctx)
        doc = refs_doc(ctx)
        assert {r["ref_id"] for r in doc["refs"]} == {
            f"char-{WATSON}", f"char-{HOLMES}", "loc-baker_street", "loc-brixton_road"}
        assert doc["unbound"] == [] and "1881 London" in doc["palette"]
        assert (ctx.book_dir / "refs/characters" / f"char-{HOLMES}.png").exists()

    def test_a_collision_rerolls_the_seed_then_binds(self, ctx, rendered):
        rendered["cards"] = [A, A, B]
        step.run(ctx.codex_id, ctx)
        doc = refs_doc(ctx)
        assert doc["unbound"] == []
        rows = load(ctx.learnings_path)
        assert [r.action for r in rows] == ["reroll_seed"]
        assert rows[0].threshold == DISTINCT_AT and WATSON in str(rows[0].measured)
        holmes = next(r for r in doc["refs"] if r["entity_id"] == HOLMES)
        assert holmes["identity"]["closest"] == WATSON
        assert set(holmes["identity"]["differs"]) == {"hair_colour", "headgear", "build"}
        assert holmes["identity"]["traits"]["hair_colour"] == "fair"

    def test_distinguish_rewrites_the_shared_traits_into_the_prompt(self, ctx, rendered):
        rendered["cards"] = [A, A, A, B]
        step.run(ctx.codex_id, ctx)
        assert refs_doc(ctx)["unbound"] == []
        assert [r.action for r in load(ctx.learnings_path)] == ["reroll_seed", "distinguish"]
        before, after = [p for p in rendered["prompts"] if p.startswith("A man")][-2:]
        assert before != after and "frame," in after  # build, shared, now said outright

    def test_a_persistent_collision_unbinds_the_character(self, ctx, rendered):
        rendered["cards"] = [A] * 5
        step.run(ctx.codex_id, ctx)
        doc = refs_doc(ctx)
        assert doc["unbound"] == [HOLMES]
        assert f"char-{HOLMES}" not in {r["ref_id"] for r in doc["refs"]}
        actions = [r.action for r in load(ctx.learnings_path)]
        assert actions == ["reroll_seed"] + ["distinguish"] * 3 + ["unbound"]

    def test_a_face_too_unclear_to_read_is_accepted_and_flagged(self, ctx, rendered):
        rendered["cards"] = [A, BLIND]
        step.run(ctx.codex_id, ctx)
        assert refs_doc(ctx)["unbound"] == []
        assert {r.action for r in load(ctx.learnings_path)} == {"accepted_unverifiable"}


class TestAttemptShape:
    def test_every_try_gets_a_seed_no_earlier_try_used(self):
        seeds = [step.seed_for(0, rung, i) for rung in step.LADDER.rungs for i in range(rung.tries)]
        assert len(set(seeds)) == len(seeds)
