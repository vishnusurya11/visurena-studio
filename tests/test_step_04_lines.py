"""Step 04 of the trailer stage: the slate is ranked by code, labelled once by
the model, ordered by code, and written as lines.json.

The one judged thing is Function.  A labelling that yields no hook is quoted
back and the next ten candidates are labelled; a second failure ships
`music_only` and writes why.  Nothing here touches the network: Wikiquote is
reached through the module's FETCH seam, which the tests point at an outage.
"""
from __future__ import annotations

import json
import re
from urllib.error import URLError

import pytest

from scripts.trailer import step_04_lines as step
from studio import db, llm
from studio.learnings import load
from studio.trailer_run import RunContext
from studio.trailer_stage_spec import LineSlate, SlateLine

HOLMES, WATSON, HOPE = "sherlock_holmes", "john_watson", "jefferson_hope"
AFGHAN = "You have been in Afghanistan, I perceive."
DEATH = "There is death in one and life in the other."
PERCEIVE = "I perceive nothing of what you perceive."
NO_DATA = "No data yet."
BLOOD = "There is a great deal of blood on my hands."
NAMES = "Jefferson Hope did this to us all."
FILLER = ["The lamp is lit and the fire is warm tonight.", "We walked to the station together.",
          "A cab is waiting at the corner for us.", "The papers are full of the case.",
          "I want to see the room again before dark.", "The rain has stopped at last."]


def dialogue(character, text):
    return {"kind": "dialogue", "character": character, "text": text, "emotion": "level"}


def screenplay():
    scenes = [
        {"number": 1, "elements": [dialogue(HOLMES, AFGHAN), dialogue(WATSON, PERCEIVE)]},
        {"number": 2, "elements": [dialogue(HOLMES, DEATH), dialogue(HOLMES, NO_DATA)]},
        {"number": 3, "elements": [dialogue(HOPE, BLOOD), dialogue(WATSON, NAMES)]},
        {"number": 4, "elements": [dialogue(WATSON, t) for t in FILLER]},
        {"number": 8, "elements": [dialogue(HOLMES, "The murderer is Jefferson Hope.")]}]
    return {"title": "A Study in Scarlet", "logline": "x", "scenes": scenes}


def story():
    return {"lead": WATSON, "figure": HOPE, "turn_scene": 3, "resolution_scenes": [8],
            "restricted_scenes": [8], "narrator": WATSON, "register": "detective",
            "thesis": None, "setting": "1881 London"}


def metre(*slot_seconds):
    beats = [round(i * 0.5, 2) for i in range(160)]
    start, slots = 10.0, []
    for s in slot_seconds:
        slots.append({"start": start, "end": start + s})
        start += s + 6.0
    return {"seed": 1, "rel_path": "music/seed_1.wav", "seconds": 80.0, "bpm": 120.0,
            "bar": 2.0, "beats": beats, "downbeats": beats[::4], "bars_in_mode": 0.9,
            "grid": "metre", "fitness": 0.8, "slots": slots}


def write(path, doc):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc), encoding="utf-8")


@pytest.fixture()
def ctx(tmp_path, monkeypatch):
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    codex_id = db.insert_codex(conn, "Scarlet", codex_id="20260901000001")
    book = tmp_path / "book"
    write(book / "screenplay/feature/screenplay.json", screenplay())
    write(book / "source/book.json", {"title": "A Study in Scarlet", "author": "Arthur Conan Doyle"})
    write(book / "source/chapters/ch_01.json", {"n": 1, "paragraphs": [
        {"n": 1, "text": "I had neither kith nor kin in England at that time."}]})
    write(book / "analysis/registry.json", {"characters": [
        {"id": HOLMES, "name": "Sherlock Holmes", "aliases": ["Holmes"], "role": "protagonist"},
        {"id": WATSON, "name": "John Watson", "aliases": ["Watson"], "role": "major"},
        {"id": HOPE, "name": "Jefferson Hope", "aliases": ["Hope"], "role": "major"}]})
    (book / "analysis/characters").mkdir()
    write(book / "trailer/main/story.json", story())
    write(book / "trailer/main/music/metre.json", metre(6, 6, 6, 6))

    def offline(params):
        raise URLError("no network in tests")
    monkeypatch.setattr(step, "FETCH", offline)
    context = RunContext(conn, codex_id, book, logs_root=tmp_path / "logs")
    context.open_step("04")
    return context


RULES = [("Afghanistan", "hook"), ("death in one", "threat"), ("perceive nothing", "stakes"),
         ("No data", "button"), ("blood on my hands", "threat"), ("Jefferson Hope", "stakes")]


class FakeLabeller:
    """Labels by keyword, reading the candidates back out of the prompt: the
    prompt's numbering is the contract the sheet's indexes refer to."""

    def __init__(self, rules=RULES, default="exposition"):
        self.rules, self.default, self.prompts = rules, default, []

    def __call__(self, tier, prompt, schema, **kw):
        self.prompts.append(prompt)
        labels = []
        for index, text in re.findall(r"^\[(\d+)\] .*?: (.*)$", prompt, re.M):
            function = next((f for key, f in self.rules if key in text), self.default)
            labels.append({"index": int(index), "function": function})
        return schema.model_validate({"labels": labels})


def slate_of(ctx) -> dict:
    return json.loads((ctx.out_dir / "lines.json").read_text(encoding="utf-8"))


class TestRun:
    def test_step_writes_a_slate(self, ctx, monkeypatch):
        fake = FakeLabeller()
        monkeypatch.setattr(llm, "structured", fake)
        step.run(ctx.codex_id, ctx)
        raw = slate_of(ctx)
        slate = LineSlate.model_validate(raw)
        assert [l.function for l in slate.lines][:2] == ["hook", "stakes"]
        assert slate.lines[0].text == AFGHAN
        assert "threat" in {l.function for l in slate.lines}
        assert slate.iconicity == "none" and not slate.music_only
        assert len(fake.prompts) == 1
        assert isinstance(raw["pool"], list) and str(ctx.book_dir) not in json.dumps(raw)
        spare = [SlateLine.model_validate(p) for p in raw["pool"]]
        assert spare and all(l.text not in {x.text for x in slate.lines} for l in spare)

    def test_the_figure_and_the_resolution_stay_out(self, ctx, monkeypatch):
        monkeypatch.setattr(llm, "structured", FakeLabeller())
        step.run(ctx.codex_id, ctx)
        texts = [l["text"] for l in slate_of(ctx)["lines"]]
        assert NAMES not in texts and "The murderer is Jefferson Hope." not in texts

    def test_no_hook_after_relabel_ships_music_only_and_learns(self, ctx, monkeypatch):
        fake = FakeLabeller(rules=[("death", "threat")])
        monkeypatch.setattr(llm, "structured", fake)
        step.run(ctx.codex_id, ctx)
        slate = LineSlate.model_validate(slate_of(ctx))
        assert slate.music_only and slate.lines == []
        assert len(fake.prompts) == 2
        assert "relabel" in fake.prompts[1].lower() or fake.prompts[1] != fake.prompts[0]
        rows = load(ctx.learnings_path)
        assert rows[-1].terminal and rows[-1].action == "music_only"
        assert rows[0].action == "relabel_next_10" and rows[0].gate == "slate"


class TestIconicity:
    def test_cached_kept_lines_make_the_slate_full(self, ctx, monkeypatch):
        """Offline, the cache is the record: two kept lines in the pool -> full,
        and the slate carries kept/bold beside each line."""
        write(ctx.book_dir / "analysis/iconicity.json", {
            "source": "Sherlock Holmes", "where": "character", "revid": 1, "n": 2,
            "kept": [{"text": AFGHAN, "bold": AFGHAN.rstrip("."), "page": "Sherlock Holmes"},
                     {"text": DEATH, "bold": None, "page": "Sherlock Holmes"}]})
        monkeypatch.setattr(llm, "structured", FakeLabeller())
        step.run(ctx.codex_id, ctx)
        slate = LineSlate.model_validate(slate_of(ctx))
        assert slate.iconicity == "full"
        hook = slate.lines[0]
        assert hook.kept and hook.bold

    def test_one_kept_line_is_thin(self, ctx, monkeypatch):
        write(ctx.book_dir / "analysis/iconicity.json", {
            "source": "Sherlock Holmes", "where": "character", "revid": 1, "n": 1,
            "kept": [{"text": DEATH, "bold": None, "page": "Sherlock Holmes"}]})
        monkeypatch.setattr(llm, "structured", FakeLabeller())
        step.run(ctx.codex_id, ctx)
        assert slate_of(ctx)["iconicity"] == "thin"


class TestRanking:
    def test_kept_lines_rank_first(self):
        lines = [{"text": FILLER[0], "speaker": WATSON, "pool": "screenplay", "scene": 4},
                 {"text": AFGHAN, "speaker": HOLMES, "pool": "screenplay", "scene": 1}]
        kept = [{"text": AFGHAN, "bold": None, "page": "x"}]
        ranked = step.rank(lines, kept, (WATSON,), longest_slot=6.0)
        assert ranked[0]["text"] == AFGHAN and ranked[0]["kept"] and not ranked[0]["bold"]

    def test_a_line_twice_the_longest_slot_is_dropped(self):
        long = " ".join(["word"] * 40)
        lines = [{"text": long, "speaker": HOLMES, "pool": "source", "scene": None}]
        assert step.rank(lines, [], (), longest_slot=2.0) == []

    def test_labels_become_slate_lines(self):
        ranked = [{"text": AFGHAN, "speaker": HOLMES, "pool": "screenplay", "scene": 1,
                   "score": 3.0, "kept": False, "bold": False}]
        sheet = step.LabelSheet(labels=[{"index": 0, "function": "hook"}, {"index": 7, "function": "button"}])
        lines = step.labelled(ranked, sheet)
        assert len(lines) == 1 and lines[0].function == "hook" and lines[0].pool == "screenplay"
