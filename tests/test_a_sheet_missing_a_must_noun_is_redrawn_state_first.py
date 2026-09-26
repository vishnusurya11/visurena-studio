"""A sheet whose look-back misses a MUST noun is a hard fault: the ladder redraws
it once on a bumped seed with the same words, then once with the sentence that
carries the missing noun moved to the front of the prompt (the defining state
first); the read that finds the noun signs the pack in the judge's name, and
every rung is a learning in refs/learnings.jsonl."""
from __future__ import annotations

from scripts.refs import step_04_verdict as step
from studio import learnings, refs_pack, sheet_ladder
from studio.judges import look
from tests import look_fixtures as lf


def test_a_missing_noun_climbs_seed_then_state_first_and_signs(tmp_path):
    book = lf.a_book(tmp_path)
    row = lf.character(book, "a", silhouette="A lantern-bearer in a grey coat.")
    drawn = []
    answers = {"a": [["a man in a grey coat"], ["a man in a grey coat"], list(lf.SEEN)]}
    ctx = lf.a_ctx(tmp_path, book, **lf.tools(reader=lf.reader_of(answers=answers)), draw=lf.drawer(drawn, book))
    step.run(ctx)
    assert [d["seed"] for d in drawn] == [row["seed"] + 1, row["seed"] + 2]
    assert drawn[0]["prompt"] == refs_pack.styled(lf.PROMPT)
    assert drawn[1]["prompt"].startswith(refs_pack.styled("Standing, holding a brass lantern."))
    signed = lf.verdict(book)
    assert signed["signed_by"] == "judge:look@1" and signed["faults"] == []
    assert step.done(ctx) is True
    tries = sorted(p.name for p in (book / "refs" / "characters" / "a" / "superseded").iterdir())
    assert tries == ["sheet_try1.png", "sheet_try2.png"]
    learned = learnings.load(book / "refs" / "learnings.jsonl")
    assert [(l.action, l.gate) for l in learned] == [("redraw_seed", "LOOK"), ("defining_state_first", "LOOK"),
                                                              ("pass", "LOOK")]
    assert "must_noun" in learned[0].note and "lantern" in lf.logged(tmp_path)


def test_a_place_drawn_from_the_plan_is_redrawn_from_its_own_row(tmp_path):
    """A per-episode place picture has no design behind it: the ladder rebuilds
    its job from the pack row -- its workflow, its words, the pack's sheet size."""
    book = lf.a_book(tmp_path)
    row = lf.add_row(book, "refs/locations/lane/dusk.png", "A lane at dusk, wearing a mist.", seed=40)
    drawn = []
    ladder = sheet_ladder.SheetLadder(book, run=lf.drawer(drawn, book))
    fault = look.Fault(kind="must_noun", where=row["path"], evidence={"missing": ["mist"]})
    ladder.take(sheet_ladder.LADDER.rungs[0], 0, look.Verdict(judge="look", version="1", passed=False,
                                                              faults=[fault], confidence=1.0, reads=1))
    assert drawn[0]["seed"] == 41 and drawn[0]["width"] == sheet_ladder.SHEET_SIZE[0]
    assert drawn[0]["prompt"] == refs_pack.styled(row["prompt"])
    assert sheet_ladder.pack_rows(book)[-1]["rung"] == "redraw_seed"
    assert (book / "refs/locations/lane/superseded/dusk_try1.png").exists()


def test_state_first_moves_the_sentences_that_carry_the_nouns():
    prompt = "Character reference sheet. A man wearing a grey coat. Standing, holding a brass lantern."
    assert sheet_ladder.state_first(prompt, ["lantern"]) == (
        "Standing, holding a brass lantern. Character reference sheet. A man wearing a grey coat.")


def test_state_first_prepends_the_silhouette_when_no_noun_names_a_sentence():
    prompt = "A man in a coat. Standing."
    assert sheet_ladder.state_first(prompt, [], "A tall man in a long coat.") == (
        "A tall man in a long coat. A man in a coat. Standing.")
    assert sheet_ladder.state_first(prompt, [], "") == prompt
