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
from pathlib import Path
from urllib.error import URLError

import pytest

from scripts.trailer import step_04_lines as step
from studio import db, llm
from studio.learnings import load
from studio.trailer_dialogue import speech_seconds, windows_of
from studio.trailer_run import RunContext
from studio.trailer_stage_spec import LineSlate, Metre, SlateLine, StorySpec
from tests.test_line_windows import plan_doc

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


def plan():
    """Step 03's cue plan over the 80 s fixture cue: two sustains, three
    troughs, two accents and three section starts (tests/test_line_windows)."""
    return plan_doc()


def write(path, doc):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc), encoding="utf-8")


def logged(ctx) -> list[str]:
    path = ctx.tracker.log_path
    if not path.exists():
        return []
    return [json.loads(l)["msg"] for l in path.read_text(encoding="utf-8").splitlines()]


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
        assert len(slate.spoken()) >= 3
        # This pool holds no question and no threat short enough to be the
        # button, so R8 is refused twice and the last rung drops it.
        assert len(fake.prompts) == 3
        assert isinstance(raw["pool"], list) and str(ctx.book_dir) not in json.dumps(raw)
        spare = [SlateLine.model_validate(p) for p in raw["pool"]]
        assert spare and all(l.text not in {x.text for x in slate.lines} for l in spare)

    def test_the_figure_and_the_resolution_stay_out(self, ctx, monkeypatch):
        monkeypatch.setattr(llm, "structured", FakeLabeller())
        step.run(ctx.codex_id, ctx)
        texts = [l["text"] for l in slate_of(ctx)["lines"]]
        assert NAMES not in texts and "The murderer is Jefferson Hope." not in texts

    def test_run_6_troughs_hold_a_hook_that_ducks_and_a_short_threat(self, ctx, monkeypatch):
        """Scarlet run 6: an onset grid with troughs of 2.6 and 2.0 s, the
        best hook 3.3 s -- music_only three runs in a row.  The hook overruns
        its trough by less than the ducker's release and is taken; the second
        slot holds the two-word threat inside it."""
        rubato = {**metre(2.6, 2.0), "grid": "onsets", "downbeats": [], "bars_in_mode": 0.43}
        write(ctx.book_dir / "trailer/main/music/metre.json", rubato)
        rules = RULES + [("Rache", "threat")]
        monkeypatch.setattr(llm, "structured", FakeLabeller(rules=rules))
        doc = screenplay()
        doc["scenes"][2]["elements"].append(dialogue(HOPE, "Rache, revenge."))
        write(ctx.book_dir / "screenplay/feature/screenplay.json", doc)
        step.run(ctx.codex_id, ctx)
        slate = LineSlate.model_validate(slate_of(ctx))
        assert not slate.music_only
        assert [l.text for l in slate.lines] == [AFGHAN, "Rache, revenge."]

    def test_no_hook_after_relabel_ships_music_only_and_learns(self, ctx, monkeypatch):
        fake = FakeLabeller(rules=[("death", "threat")])
        monkeypatch.setattr(llm, "structured", fake)
        step.run(ctx.codex_id, ctx)
        slate = LineSlate.model_validate(slate_of(ctx))
        assert slate.music_only and slate.lines == []
        assert len(fake.prompts) == 3
        assert "refused: no line is labelled hook" in fake.prompts[1]
        rows = load(ctx.learnings_path)
        assert rows[-1].terminal and rows[-1].action == "music_only"
        assert rows[0].action == "relabel_next_10" and rows[0].gate == "slate"
        assert rows[-2].action == "drop_story_rules"


class TestSheets:
    def test_every_label_sheet_is_kept_for_the_retrospect(self, ctx, monkeypatch):
        """Run 9 shipped music_only twice over and nothing on disk said what
        the labeller had labelled: work/labels-N.json is each sheet as
        applied, text and function, in the order they were asked for."""
        monkeypatch.setattr(llm, "structured", FakeLabeller(rules=[("death", "threat")]))
        step.run(ctx.codex_id, ctx)
        sheets = sorted((ctx.out_dir / "work").glob("labels-*.json"))
        assert [p.name for p in sheets] == ["labels-0.json", "labels-1.json", "labels-2.json"]
        first = json.loads(sheets[0].read_text(encoding="utf-8"))
        assert first and all(set(row) == {"text", "speaker", "function"} for row in first)
        assert "hook" not in {row["function"] for row in first}
        assert any(row["function"] == "threat" and "death" in row["text"].lower() for row in first)


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


class TestSpeaksEnough:
    """R1/R8.  `music_only` is a refusal to be quoted back, not an outcome:
    run 10 spoke one line in a hundred seconds and shipped."""

    def test_a_slate_that_speaks_too_little_is_refused_and_relabelled(self, ctx, monkeypatch):
        """One spoken line and two cards is what run 10 delivered."""
        fake = FakeLabeller(rules=[("Afghanistan", "hook"), ("death in one", "threat")])
        monkeypatch.setattr(llm, "structured", fake)
        step.run(ctx.codex_id, ctx)
        assert "needs" in fake.prompts[1] or "speaks" in fake.prompts[1]

    def test_the_prompt_names_how_many_lines_must_be_spoken(self, ctx, monkeypatch):
        fake = FakeLabeller()
        monkeypatch.setattr(llm, "structured", fake)
        step.run(ctx.codex_id, ctx)
        assert "must SPEAK at least" in fake.prompts[0]

    def test_a_question_button_satisfies_the_last_word_rule(self, ctx, monkeypatch):
        doc = screenplay()
        doc["scenes"][2]["elements"].append(dialogue(HOPE, "Now, who am I?"))
        write(ctx.book_dir / "screenplay/feature/screenplay.json", doc)
        fake = FakeLabeller(rules=RULES + [("who am I", "button")])
        monkeypatch.setattr(llm, "structured", fake)
        step.run(ctx.codex_id, ctx)
        slate = LineSlate.model_validate(slate_of(ctx))
        assert slate.lines[-1].text.rstrip().endswith("?")
        assert len(fake.prompts) == 1

    def test_the_last_rung_ships_lines_rather_than_silence(self, ctx, monkeypatch):
        """The story rules are dropped before the trailer goes silent."""
        monkeypatch.setattr(llm, "structured", FakeLabeller())
        step.run(ctx.codex_id, ctx)
        slate = LineSlate.model_validate(slate_of(ctx))
        assert not slate.music_only and slate.lines
        rows = load(ctx.learnings_path)
        assert [r.action for r in rows] == ["relabel_next_10", "relabel_next_10"]


class TestNarratorMaySpeak:
    def test_the_top_narration_lines_get_the_narrators_voice(self):
        rows = [{"text": "There is a scarlet thread of murder.", "speaker": None,
                 "pool": "narration", "scene": None},
                {"text": "The fog hangs over the river.", "speaker": None,
                 "pool": "narration", "scene": None},
                {"text": "A word was written on the wall.", "speaker": None,
                 "pool": "source", "scene": None}]
        found = step.voiced(rows, WATSON, cap=1)
        assert found[0]["speaker"] == WATSON
        assert found[1]["speaker"] is None and found[2]["speaker"] is None

    def test_an_omniscient_book_gets_no_voice_over(self):
        rows = [{"text": "x", "speaker": None, "pool": "narration", "scene": None}]
        assert step.voiced(rows, "omniscient") == rows


class TestThesisReachesTheScreen:
    def test_a_thesis_becomes_a_candidate(self):
        spec = StorySpec(**{**story(), "thesis": "nobody is who they say"})
        assert step.thesis_card(spec) == [{"text": "Nobody is who they say.", "speaker": None,
                                          "pool": "thesis", "scene": None}]

    def test_no_thesis_adds_nothing(self):
        assert step.thesis_card(StorySpec(**story())) == []

    def test_the_thesis_is_always_offered_to_the_labeller(self):
        ranked = step.rank(step.thesis_card(StorySpec(**{**story(), "thesis": "nobody is who they say"}))
                           + [{"text": t, "speaker": HOLMES, "pool": "screenplay", "scene": 1}
                              for t in FILLER], [], (HOLMES,), longest_slot=9.0)
        window = step.quota_fill(ranked, 2, HOPE, set())
        assert "Nobody is who they say." in [l["text"] for l in window]


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


class TestRun10Regression:
    """R12, on run 10's own candidate pool (tests/fixtures/scarlet_line_pool.json,
    228 rows drawn from the four pools) and its own Wikiquote page.

    Offline in both directions: the pool is a file, the kept quotations are
    the recorded API response test_iconicity already ships.
    """

    POOL = Path(__file__).parent / "fixtures" / "scarlet_line_pool.json"
    PAGE = Path(__file__).parent / "fixtures" / "wikiquote_sherlock_holmes.json"
    CLIMAX = {11, 18, 19}
    LONGEST = 9.72

    def pool(self):
        return json.loads(self.POOL.read_text(encoding="utf-8"))

    def kept(self):
        from studio import iconicity
        doc = json.loads(self.PAGE.read_text(encoding="utf-8"))["response"]
        body = iconicity.section_for(doc["parse"]["wikitext"]["*"], "A Study in Scarlet")
        return [{**q, "page": "Sherlock Holmes"} for q in iconicity.quotes_in(body)]

    def window(self, where="character"):
        ranked = step.rank(self.pool(), self.kept(), (HOLMES,), self.LONGEST, where)
        return step.quota_fill(ranked, step.TOP_N, HOPE, self.CLIMAX)

    def test_the_books_own_threat_reaches_the_labeller(self):
        """Run 10 ranked these #663, #664 and #178 of 2336 and the labeller
        saw the top 24."""
        texts = [l["text"] for l in self.window()]
        assert "Now, Enoch Drebber, who am I?" in texts
        assert "Choose and eat." in texts
        assert "You dog!" in texts
        assert any("hunted you from Salt Lake City" in t for t in texts)

    def test_the_hook_is_still_the_first_line_of_the_book(self):
        assert any("Afghanistan" in l["text"] for l in self.window())

    def test_the_aphorisms_no_longer_own_the_window(self):
        """17 of run 10's 24 candidates came from outside the screenplay."""
        window = self.window()
        off_book = sum(l["pool"] not in ("screenplay", "thesis") for l in window)
        assert off_book / len(window) < 0.5

    def test_a_character_page_ranks_below_the_book(self):
        """The same quotation, weighted for whose page it came from."""
        rows = [{"text": "You have been in Afghanistan, I perceive.", "speaker": HOLMES,
                 "pool": "screenplay", "scene": 1}]
        as_book = step.rank(rows, self.kept(), (HOLMES,), self.LONGEST, "book")
        as_character = step.rank(rows, self.kept(), (HOLMES,), self.LONGEST, "character")
        assert as_book[0]["kept"] and as_character[0]["score"] < as_book[0]["score"]

    def test_the_confrontation_arrives_in_the_order_it_is_spoken(self):
        ranked = step.rank(self.pool(), self.kept(), (HOLMES,), self.LONGEST, "character")
        spoken = step.confrontation(ranked, HOPE, self.CLIMAX)
        assert [l["order"] for l in spoken] == sorted(l["order"] for l in spoken)
        assert len(spoken) <= step.CONFRONTATION

    def test_every_role_has_something_to_label(self):
        ranked = step.rank(self.pool(), self.kept(), (HOLMES,), self.LONGEST, "character")
        window = step.quota_fill(ranked, step.TOP_N, HOPE, self.CLIMAX)
        for role, mark in step.ROLE_MARKS.items():
            assert any(mark(l["text"]) for l in window), role


class TestPlanWindows:
    """BUILD 50: with a cue plan, a line sits in a trough or a sustain and
    ends at least a beat before the span does, so the cut lands on music
    and never on a word.  The metre's slots (10-16, 22-28, ...) sit on
    phrases of this plan and must not be used."""

    def spans_by_window(self, ctx, slate):
        spans = plan()["spans"]
        found = []
        for line in slate.lines:
            span = next(s for s in spans if s["start"] <= line.window.start < s["end"])
            found.append((line, span))
        return found

    def test_a_line_window_is_a_trough_or_a_sustain(self, ctx, monkeypatch):
        write(ctx.book_dir / "trailer/main/music/plan.json", plan())
        monkeypatch.setattr(llm, "structured", FakeLabeller())
        step.run(ctx.codex_id, ctx)
        slate = LineSlate.model_validate(slate_of(ctx))
        assert not slate.music_only and len(slate.lines) >= 3
        for line, span in self.spans_by_window(ctx, slate):
            assert span["kind"] in ("trough", "sustain"), (line.text, span)
            assert line.window.start == span["start"]
            assert line.window.made == (span["kind"] == "sustain")
        assert any("plan.json" in msg for msg in logged(ctx))

    def test_a_line_ends_a_beat_before_the_span(self, ctx, monkeypatch):
        write(ctx.book_dir / "trailer/main/music/plan.json", plan())
        monkeypatch.setattr(llm, "structured", FakeLabeller())
        step.run(ctx.codex_id, ctx)
        slate = LineSlate.model_validate(slate_of(ctx))
        beat = plan()["bar"] / 4.0
        for line, span in self.spans_by_window(ctx, slate):
            assert line.window.end <= span["end"] - beat + 1e-6
            spoken_end = line.window.start + beat + speech_seconds(line.text)
            assert spoken_end <= span["end"] - beat + 1e-6, (line.text, span)

    def test_without_a_plan_the_metre_windows_are_the_fallback(self, ctx, monkeypatch):
        monkeypatch.setattr(llm, "structured", FakeLabeller())
        step.run(ctx.codex_id, ctx)
        slate = LineSlate.model_validate(slate_of(ctx))
        starts = {l.window.start for l in slate.lines}
        assert starts <= {s.start for s in windows_of(Metre.model_validate(metre(6, 6, 6, 6)))}
        assert any("metre.json" in msg for msg in logged(ctx))
