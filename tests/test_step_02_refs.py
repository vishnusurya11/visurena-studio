"""Step 02 of the trailer stage: reference sheets a viewer can tell apart.

Every character sheet is rendered, READ BACK by a vision model into a trait
card, and judged twice: did the render OBEY its card on the traits the
channel can express (a clean-shaven sheet under a prompt that says walrus
moustache would condition every clip against its own words), and is it
fewer than DISTINCT_AT traits from anyone already bound (a collision).
Either failure climbs three `distinguish` rungs -- a collision rewrites
exactly the shared traits, a disobedient render is asked again as written on
a new seed; a character that still fails is UNBOUND -- in refs.json's
`unbound` list, absent from `refs`, so every setup needing it is excluded
downstream.  Renders are faked and read back as the card they were asked
for, unless a test queues a drift; nothing here touches a GPU or a model file.
"""
from __future__ import annotations

import json

import pytest
from PIL import Image

from scripts.trailer import step_02_refs as step
from studio import db
from studio import describe, portrait
from studio.describe import DISTINCT_AT
from studio.distinguish import expected
from studio.learnings import load
from studio.portrait import Portrait
from studio.trailer_run import RunContext

HOLMES, WATSON = "sherlock_holmes", "john_watson"
DISTINCT = {WATSON: "A stout man with a heavy walrus moustache, a brown bowler hat and fair hair.",
            HOLMES: "A tall thin man, clean-shaven, with black hair swept back and a top hat."}
"""Cards that read 3.5 apart when rendered faithfully."""
CLOSE = {WATSON: "A stout man with a heavy walrus moustache and fair hair.",
         HOLMES: "A thin man with a heavy walrus moustache and fair hair."}
"""Cards `cast_card` lets through (a felt hat and a straw boater are different
words) that the model reads as the same face: distance 0."""
BLIND = {t: "unclear" for t in ("age", "hair_colour", "hair_length", "headgear", "build")}
UNSHAVEN = {"facial_hair": "clean-shaven", "hair_colour": "grey"}
"""What run 6 read off Lestrade's rung-2 render; the card said walrus moustache."""


def character(char_id, name, physical):
    return {"id": char_id, "name": name, "aliases": [], "role": "protagonist",
            "profile": {"physical": physical}}


def scene(number, cast, loc="baker_street"):
    return {"number": number, "cast": cast, "speaking": cast[:1],
            "slug": {"location_id": loc, "location_name": loc.replace("_", " ").title()},
            "elements": [{"kind": "action", "text": "He crosses the room."}]}


def make_ctx(tmp_path, physicals):
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    codex_id = db.insert_codex(conn, "Scarlet", codex_id="20260901000002")
    book = tmp_path / "20260901000002_scarlet"
    (book / "analysis/characters").mkdir(parents=True)
    for char_id, name in ((HOLMES, "Sherlock Holmes"), (WATSON, "John Watson")):
        (book / "analysis/characters" / f"{char_id}.json").write_text(
            json.dumps(character(char_id, name, physicals[char_id])), encoding="utf-8")
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


@pytest.fixture()
def ctx(tmp_path):
    return make_ctx(tmp_path, DISTINCT)


@pytest.fixture()
def close_ctx(tmp_path):
    return make_ctx(tmp_path, CLOSE)


def fake_generate(prompt, prefix, seed, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (8, 8)).save(dest)
    return dest


@pytest.fixture()
def rendered(monkeypatch):
    """Faked renders, each read back as the card it was asked for.  `drifts`
    is consumed per describe call: the traits the reading departs from the
    card on, or None for a faithful read.  `prompts` records every render."""
    state = {"drifts": [], "prompts": [], "cards": []}
    real = step.render_sheet

    def generate(prompt, prefix, seed, dest):
        state["prompts"].append(prompt)
        return fake_generate(prompt, prefix, seed, dest)

    def render_sheet(book, char_id, card, palette, seed, fresh):
        state["cards"].append(card)
        return real(book, char_id, card, palette, seed, fresh)

    def read(path, seed):
        drift = state["drifts"].pop(0) if state["drifts"] else None
        return expected(state["cards"][-1]).model_copy(update=drift or {})
    monkeypatch.setattr(step, "generate", generate)
    monkeypatch.setattr(step, "render_sheet", render_sheet)
    monkeypatch.setattr(step, "describe", read)
    return state


def refs_doc(ctx):
    return json.loads((ctx.book_dir / "refs/refs.json").read_text(encoding="utf-8"))


def sheet_prompts(rendered):
    return [p for p in rendered["prompts"] if p.startswith("A man")]


class TestRun:
    def test_binds_a_distinct_cast_and_renders_locations(self, ctx, rendered):
        step.run(ctx.codex_id, ctx)
        doc = refs_doc(ctx)
        assert {r["ref_id"] for r in doc["refs"]} == {
            f"char-{WATSON}", f"char-{HOLMES}", "loc-baker_street", "loc-brixton_road"}
        assert doc["unbound"] == [] and "1881 London" in doc["palette"]
        assert (ctx.book_dir / "refs/characters" / f"char-{HOLMES}.png").exists()
        assert load(ctx.learnings_path) == []

    def test_a_read_that_outlives_the_timeout_binds_the_sheet_unverified(self, ctx, rendered,
                                                                          monkeypatch):
        """Scarlet run 5: the VLM took 10:14 to read one sheet (16 GB re-streamed
        off the spinning disk) and the TimeoutError ended the run in step 02.
        Retry, then degrade and ship: interrupt the engine, bind the sheet
        flagged, go on."""
        stopped = []
        monkeypatch.setattr(describe.comfy, "interrupt", lambda: stopped.append(True))
        faithful = step.describe
        readings = iter([faithful, None])

        def read(path, seed):
            got = next(readings)
            if got is None:
                raise TimeoutError("job-9 still running after 600.0s")
            return got(path, seed)
        monkeypatch.setattr(step, "describe", read)
        step.run(ctx.codex_id, ctx)
        assert refs_doc(ctx)["unbound"] == [] and stopped == [True]
        assert [r.action for r in load(ctx.learnings_path)] == [
            "accepted_on_timeout", "accepted_unverifiable"]

    def test_a_render_that_reads_as_another_character_is_asked_again(self, ctx, rendered):
        """Holmes' first render comes back looking like Watson: it disobeyed
        its card, so the same card on another seed reads as written and binds."""
        rendered["drifts"] = [None, {"facial_hair": "moustache", "headgear": "bowler",
                                     "hair_colour": "fair"}]
        step.run(ctx.codex_id, ctx)
        doc = refs_doc(ctx)
        assert doc["unbound"] == []
        rows = load(ctx.learnings_path)
        assert [r.action for r in rows] == ["reroll_seed"]
        assert rows[0].threshold == "faithful" and "facial_hair" in str(rows[0].measured)
        holmes = next(r for r in doc["refs"] if r["entity_id"] == HOLMES)
        assert holmes["identity"]["closest"] == WATSON
        assert {"hair_colour", "headgear", "facial_hair"} <= set(holmes["identity"]["differs"])
        assert holmes["identity"]["traits"]["hair_colour"] == "dark brown"

    def test_a_faithful_collision_is_distinguished_in_the_prompt(self, close_ctx, rendered):
        """Two cards the words let through but the model reads as one face:
        a new seed cannot help, the distinguish rung moves the shared traits."""
        step.run(close_ctx.codex_id, close_ctx)
        assert refs_doc(close_ctx)["unbound"] == []
        rows = load(close_ctx.learnings_path)
        assert [r.action for r in rows] == ["reroll_seed"]  # the first render's rung
        assert rows[0].threshold == DISTINCT_AT and WATSON in str(rows[0].measured)
        before, after = sheet_prompts(rendered)[-2:]
        assert "walrus moustache" in before and "walrus moustache" not in after

    def test_a_disobedient_render_is_asked_again_as_written(self, ctx, rendered):
        """Scarlet run 6, Lestrade rung 2: the card said walrus moustache, the
        render was clean-shaven, and the ladder rewrote the card as if Hope
        had been matched.  A render that ignores its card is not a collision:
        the same card goes again on the next seed."""
        rendered["drifts"] = [None, UNSHAVEN, UNSHAVEN]
        step.run(ctx.codex_id, ctx)
        assert refs_doc(ctx)["unbound"] == []
        rows = load(ctx.learnings_path)
        assert [r.action for r in rows] == ["reroll_seed", "distinguish"]
        assert all(r.threshold == "faithful" for r in rows)
        first, second, third = sheet_prompts(rendered)[-3:]
        assert first == second == third

    def test_an_invented_slot_the_render_reinterprets_binds_and_the_card_follows(
            self, tmp_path, rendered):
        """Scarlet run 7: the book is silent on Holmes's hair, the rotation
        said 'receding sandy hair', the render put dark hair under his bowler
        four times, and the lead went UNBOUND over an invention.  A render
        owes the book; a slot the book left empty is the render's, and the
        card is rewritten to what was drawn so the take prompts agree with
        the sheet."""
        ctx = make_ctx(tmp_path, {WATSON: DISTINCT[WATSON], HOLMES: ""})
        holmes = step.cast_cards(ctx.book_dir, [WATSON, HOLMES])[HOLMES]
        assert holmes["asserted"] == [] and expected(holmes).hair_colour == "dark brown"
        rendered["drifts"] = [None, {"hair_colour": "fair", "hair_length": "short"}]
        step.run(ctx.codex_id, ctx)
        doc = refs_doc(ctx)
        assert doc["unbound"] == [] and load(ctx.learnings_path) == []
        record = next(r for r in doc["refs"] if r["entity_id"] == HOLMES)
        assert "receding sandy hair" in record["physical"]
        assert holmes["hair"] not in record["physical"]

    def test_a_persistent_collision_unbinds_the_character(self, close_ctx, rendered):
        watson = expected(step.cast_cards(close_ctx.book_dir, [WATSON])[WATSON])
        rendered["drifts"] = [None] + [dict(watson)] * 4
        step.run(close_ctx.codex_id, close_ctx)
        doc = refs_doc(close_ctx)
        assert doc["unbound"] == [HOLMES]
        assert f"char-{HOLMES}" not in {r["ref_id"] for r in doc["refs"]}
        actions = [r.action for r in load(close_ctx.learnings_path)]
        assert actions == ["reroll_seed"] + ["distinguish"] * 3 + ["unbound"]

    def test_a_face_too_unclear_to_read_is_accepted_and_flagged(self, ctx, rendered):
        rendered["drifts"] = [None, BLIND]
        step.run(ctx.codex_id, ctx)
        assert refs_doc(ctx)["unbound"] == []
        assert {r.action for r in load(ctx.learnings_path)} == {"accepted_unverifiable"}


class TestPortraits:
    """Scarlet run 6: the dossier said Holmes had 'limited physical description'
    and the card invented white hair and a beard; chapter 2 says lean and
    hawk-nosed.  The book's own sentences are the card's authority, asked
    once per character and kept in refs/portraits.json."""
    LOOK = ("In height he was rather over six feet, and so excessively lean that he seemed "
            "to be considerably taller. His eyes were sharp and piercing.")

    def with_source(self, ctx):
        chapters = ctx.book_dir / "source/chapters"
        chapters.mkdir(parents=True)
        (chapters / "ch_01.json").write_text(json.dumps({"n": 1, "paragraphs": [
            {"n": 1, "text": "Sherlock Holmes rose, a tall man."}, {"n": 2, "text": self.LOOK}]}),
            encoding="utf-8")
        return ctx

    def test_the_book_sentences_reach_the_sheet_prompt_and_are_kept(self, ctx, rendered,
                                                                     monkeypatch):
        self.with_source(ctx)
        found = Portrait(sentences=[self.LOOK.split(". ")[0] + "."], build="lean")
        fake = FakeLLM(found)
        monkeypatch.setattr(portrait.llm, "structured", fake)
        step.run(ctx.codex_id, ctx)
        assert len(fake.prompts) == 1  # Holmes; no paragraph names Watson
        holmes = next(p for p in sheet_prompts(rendered) if "excessively lean" in p)
        assert "limited physical description" not in holmes
        kept = json.loads((ctx.book_dir / "refs/portraits.json").read_text(encoding="utf-8"))
        assert kept[HOLMES]["build"] == "lean" and kept[WATSON] == Portrait().model_dump()
        step.cast_cards(ctx.book_dir, [HOLMES, WATSON])
        assert len(fake.prompts) == 1  # cached: nothing asked again

    def test_a_book_without_source_chapters_asks_nothing(self, ctx, rendered, monkeypatch):
        fake = FakeLLM()
        monkeypatch.setattr(portrait.llm, "structured", fake)
        step.run(ctx.codex_id, ctx)
        assert fake.prompts == [] and not (ctx.book_dir / "refs/portraits.json").exists()


class FakeLLM:
    def __init__(self, *answers):
        self.answers, self.prompts = list(answers), []

    def __call__(self, tier, prompt, schema, **kw):
        self.prompts.append(prompt)
        return self.answers.pop(0)


class TestAttemptShape:
    def test_every_try_gets_a_seed_no_earlier_try_used(self):
        seeds = [step.seed_for(0, rung, i) for rung in step.LADDER.rungs for i in range(rung.tries)]
        assert len(set(seeds)) == len(seeds)


class TestFollowed:
    def test_the_text_follows_the_render_on_invented_slots_only(self):
        card = {"age": "about forty", "hair": "receding sandy hair", "facial_hair": "clean-shaven",
                "headgear": "a brown bowler hat", "garment": "a frock coat", "neckwear": "a cravat",
                "complexion": "a sallow complexion", "gender": "man", "asserted": ["facial_hair"]}
        drawn = expected(card).model_copy(update={"hair_colour": "dark brown", "hair_length": "medium",
                                                  "facial_hair": "beard"})
        result = step.followed({"card": drawn, "path": None}, card)
        assert "dark hair swept back" in result["physical"] and "clean-shaven" in result["physical"]
        assert result["card"] is drawn


class TestRungPrice:
    def test_a_rung_is_priced_at_what_a_sheet_measured(self):
        """Run 7 timed four sheet attempts at 286, 237, 212 and 371 s (691 with
        the model load); the rung was priced at 90.  A budget that believes
        90 lets the ladder start a climb it cannot finish."""
        for rung in step.LADDER.rungs:
            assert 250 <= rung.cost_seconds <= 400
