"""Step 05 -- voice: every spoken line cloned, gated on similarity, cards for the rest.

The engine (`studio.voice`) is faked at its three seams -- design, clone,
similarity -- so the step's decisions are what is tested: which lines it
tries, how it climbs, what it writes.  Nothing renders.
"""
from __future__ import annotations

import json

import pytest

from scripts.trailer import step_05_voice as step
from studio import db, voice
from studio.learnings import load
from studio.trailer_run import RunContext
from studio.trailer_stage_spec import LineSlate, SlateLine, VoiceLine

CODEX = "20260901000005"
HOLMES = {"id": "sherlock_holmes", "name": "Sherlock Holmes", "aliases": ["Holmes"], "role": "protagonist",
          "profile": {"physical": "a young man", "voice": "Direct, confident, formal."},
          "quotes": [{"quote": "You have been in Afghanistan, I perceive."}]}
WATSON = {"id": "john_watson", "name": "John Watson", "aliases": ["Watson"], "role": "narrator",
          "profile": {"physical": "a man of middle age", "voice": "Warm and plain."}, "quotes": []}


def slate(*lines: SlateLine, music_only: bool = False, pool: list[SlateLine] = ()) -> dict:
    raw = LineSlate(lines=list(lines), iconicity="thin", music_only=music_only).model_dump()
    raw["pool"] = [p.model_dump() for p in pool]
    return raw


def spoken(text, speaker="sherlock_holmes", function="hook"):
    return SlateLine(text=text, speaker=speaker, function=function, pool="quotes", score=0.9)


def card(text, function="threat"):
    return SlateLine(text=text, speaker=None, function=function, pool="narration", score=0.5)


@pytest.fixture()
def ctx(tmp_path):
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    db.insert_codex(conn, "Book", codex_id=CODEX)
    book = tmp_path / "book"
    for who in (HOLMES, WATSON):
        path = book / "analysis" / "characters" / f"{who['id']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(who), encoding="utf-8")
    context = RunContext(conn, CODEX, book, logs_root=tmp_path / "logs")
    context.out_dir.mkdir(parents=True)
    return context


class FakeEngine:
    """Design writes a ref; clone returns a line whose similarity the test scripts."""

    def __init__(self, monkeypatch, score):
        self.score, self.designed, self.cloned = score, [], []
        monkeypatch.setattr(voice, "design_reference", self.design)
        monkeypatch.setattr(voice, "clone_line", self.clone)
        monkeypatch.setattr(voice, "similarity", self.similarity)

    def design(self, speaker, out_dir):
        self.designed.append(speaker["id"])
        out = out_dir / f"{speaker['id']}.wav"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"ref")
        return out

    def clone(self, reference, text, seed, out, index=0, speaker=None):
        self.cloned.append((text, seed, out.name))
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        return VoiceLine(index=index, text=text, speaker=speaker, seed=seed, seconds=1.5,
                         rel_path=voice.book_relative(out))

    def similarity(self, a, b):
        text = a.read_text(encoding="utf-8")
        return self.score(text) if callable(self.score) else self.score


def written(ctx) -> list[VoiceLine]:
    raw = json.loads((ctx.out_dir / "voice.json").read_text(encoding="utf-8"))
    return [VoiceLine.model_validate(v) for v in raw]


class TestHappyPath:
    def test_step_clones_every_spoken_line(self, ctx, monkeypatch):
        engine = FakeEngine(monkeypatch, 0.9)
        (ctx.out_dir / "lines.json").write_text(json.dumps(slate(
            spoken("Poison."), card("A study in scarlet."),
            spoken("Come along.", speaker="john_watson", function="button"))), encoding="utf-8")

        step.run(CODEX, ctx)

        lines = written(ctx)
        assert [l.index for l in lines] == [0, 1, 2]
        assert [l.card for l in lines] == [False, True, False]
        assert lines[0].rel_path == "trailer/main/voice/lines/00-0.wav"
        assert lines[0].seconds == 1.5 and lines[0].similarity == 0.9
        assert lines[1].rel_path is None and lines[1].text == "A study in scarlet."
        assert sorted(engine.designed) == ["john_watson", "sherlock_holmes"]
        assert (ctx.out_dir / "voice/refs/sherlock_holmes.wav").exists()
        assert len(engine.cloned) == 2

    def test_music_only_slate_writes_empty_voice(self, ctx, monkeypatch):
        engine = FakeEngine(monkeypatch, 0.9)
        (ctx.out_dir / "lines.json").write_text(json.dumps(slate(music_only=True)), encoding="utf-8")
        step.run(CODEX, ctx)
        assert written(ctx) == [] and engine.cloned == [] and engine.designed == []

    def test_an_all_card_slate_writes_empty_voice(self, ctx, monkeypatch):
        FakeEngine(monkeypatch, 0.9)
        (ctx.out_dir / "lines.json").write_text(json.dumps(slate(card("Who?", "hook"), card("Run."))),
                                                encoding="utf-8")
        step.run(CODEX, ctx)
        assert written(ctx) == []


class TestLadder:
    def test_low_similarity_climbs_to_card_and_learns(self, ctx, monkeypatch):
        engine = FakeEngine(monkeypatch, 0.5)
        (ctx.out_dir / "lines.json").write_text(json.dumps(slate(
            spoken("Poison."), card("Run.", "threat"),
            pool=[spoken("There has been murder done."), spoken("Come along.", function="button")])),
            encoding="utf-8")

        step.run(CODEX, ctx)

        lines = written(ctx)
        assert lines[0].card and lines[0].rel_path is None and lines[0].text == "Poison."
        # Three seeds on the line, then the next hook from the pool, then the card.
        assert [t for t, _, _ in engine.cloned] == ["Poison."] * 3 + ["There has been murder done."]
        assert len({s for _, s, _ in engine.cloned[:3]}) == 3
        learned = load(ctx.learnings_path)
        assert [l.action for l in learned] == ["reroll_seed"] * 3 + ["next_line_same_function", "card"]
        assert all(l.gate == "similarity" for l in learned)
        assert all(l.threshold == voice.SIMILARITY_FLOOR for l in learned[:-1])
        assert learned[0].measured == 0.5 and learned[-1].terminal

    def test_the_next_line_with_the_same_function_can_win(self, ctx, monkeypatch):
        engine = FakeEngine(monkeypatch, lambda text: 0.9 if "murder" in text else 0.5)
        (ctx.out_dir / "lines.json").write_text(json.dumps(slate(
            spoken("Poison."), card("Run."),
            pool=[spoken("Come along.", function="button"), spoken("There has been murder done.")])),
            encoding="utf-8")

        step.run(CODEX, ctx)

        lines = written(ctx)
        assert not lines[0].card and lines[0].text == "There has been murder done."
        assert lines[0].similarity == 0.9 and lines[0].index == 0
        assert len(engine.cloned) == 4

    def test_no_candidate_in_the_pool_goes_straight_to_card(self, ctx, monkeypatch):
        engine = FakeEngine(monkeypatch, 0.5)
        (ctx.out_dir / "lines.json").write_text(json.dumps(slate(spoken("Poison."), card("Run."))),
                                                encoding="utf-8")
        step.run(CODEX, ctx)
        assert written(ctx)[0].card and len(engine.cloned) == 3

    def test_an_unknown_speaker_is_a_card_without_trying(self, ctx, monkeypatch):
        engine = FakeEngine(monkeypatch, 0.9)
        (ctx.out_dir / "lines.json").write_text(json.dumps(slate(
            spoken("Who goes there?", speaker="ghost"), card("Run."))), encoding="utf-8")
        step.run(CODEX, ctx)
        lines = written(ctx)
        assert lines[0].card and lines[0].speaker == "ghost"
        assert engine.cloned == [] and engine.designed == []
        assert load(ctx.learnings_path)[0].gate == "speaker_card"

    def test_a_rung_costs_what_the_render_took(self, ctx, monkeypatch):
        """Rerolls are gated on MEASURED render time, not a guess."""
        FakeEngine(monkeypatch, 0.5)
        ladder = step.fresh_ladder()
        clock = iter([10.0, 22.5])
        monkeypatch.setattr(step.time, "monotonic", lambda: next(clock))
        refs = {"sherlock_holmes": ctx.out_dir / "voice/refs/sherlock_holmes.wav"}
        step.attempt_line(ladder.rungs[0], 0, spoken("Poison."), 0, refs, ctx.out_dir)
        assert ladder.rungs[0].cost_seconds == pytest.approx(12.5)


class TestPool:
    def test_next_candidate_keeps_the_function_and_skips_used_text(self):
        pool = [spoken("A", function="threat"), spoken("B"), spoken("C")]
        assert step.next_candidate(pool, "hook", {"B"}, {"sherlock_holmes"}).text == "C"
        assert step.next_candidate(pool, "stakes", set(), {"sherlock_holmes"}) is None

    def test_a_candidate_needs_a_designed_speaker(self):
        pool = [spoken("A", speaker="ghost"), card("B", "hook")]
        assert step.next_candidate(pool, "hook", set(), {"sherlock_holmes"}) is None

    def test_pool_is_optional_in_lines_json(self, tmp_path):
        assert step.load_pool({"lines": []}) == []
        assert step.load_pool({"pool": [spoken("A").model_dump()]})[0].text == "A"
