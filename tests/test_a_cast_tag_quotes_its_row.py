"""A plan names a person with a short tag quoted from their row, checked when
the plan is built.

Two faults, one cure (audit items 24 and 34, 2026-09-22):
- ep09's plan inlined each character's full 66-94 word description into the
  shot prose, while the take prompt already defines every staged person in
  full from the row -- seven take prompts ran past the lint's 360-word block;
- descriptions typed into plans have contradicted their rows three times
  (ep07's four characters, Snippy's moustache, the gloves). A tag made of
  verbatim fragments of the row cannot contradict it, and one that stops
  matching refuses the plan at build time instead of reaching a picture.
"""
import json

import pytest

from studio.cast_refs import tag


def book(tmp_path):
    (tmp_path / "refs").mkdir()
    (tmp_path / "refs" / "refs.json").write_text(json.dumps({"chapter": 9, "refs": [
        {"entity_id": "narrator", "kind": "character",
         "physical": "Man of 34. Neat close-trimmed dark brown moustache; shaven cheeks. "
                     "Wearing: Mid-grey herringbone tweed lounge suit."}]}))
    return tmp_path


def test_a_tag_is_the_name_and_the_rows_own_words(tmp_path):
    got = tag(book(tmp_path), "narrator", "the narrator",
              ["neat close-trimmed dark brown moustache", "mid-grey herringbone tweed lounge suit"])
    # closed in parentheses so the plan's next verb cannot run on (ep09 T01)
    assert got == ("the narrator (neat close-trimmed dark brown moustache, "
                   "mid-grey herringbone tweed lounge suit)")


def test_a_fragment_the_row_does_not_say_refuses_the_plan(tmp_path):
    with pytest.raises(ValueError, match="clipped sandy moustache"):
        tag(book(tmp_path), "narrator", "the narrator", ["clipped sandy moustache", "grey tweed"])


def test_matching_ignores_case_and_punctuation_but_not_words(tmp_path):
    b = book(tmp_path)
    assert tag(b, "narrator", "the narrator", ["Neat close-trimmed dark brown moustache"])
    with pytest.raises(ValueError):
        tag(b, "narrator", "the narrator", ["neat dark moustache"])


def test_a_plan_tags_against_its_own_chapter_whatever_is_bound():
    """refs.json holds ONE chapter. With chapter 10 bound, ep09's plan could no
    longer regenerate: its narrator wears the chapter-9 boater (2026-09-23)."""
    from studio import episode_home
    book = episode_home.book_dir("20260827135508_the-war-of-the-worlds")
    got = tag(book, "unnamed_first_person_narrator", "the narrator",
              ["Straw boater with a black band"], chapter=9)
    assert "straw boater" in got


def card_book(tmp_path, monkeypatch):
    """A book whose chapter row has lost the body's hair clause (the look
    restates the head, c300c4f) while the dossier card still says it."""
    from studio import pack_refs
    chars = tmp_path / "analysis" / "characters"
    chars.mkdir(parents=True)
    (chars / "gunner.json").write_text(json.dumps({"profile": {
        "physical": "Man of 31. Thick straight black hair falling forward over the brow.",
        "wardrobe": {"hatless": "Blue tunic blackened with soot."}}}))
    monkeypatch.setattr(pack_refs, "character_row", lambda book, who, chapter: {
        "physical": "Man of 31. Hair matted with ash.", "look": "hatless",
        "wardrobe": {"indoor": "Blue tunic blackened with soot."}})
    return tmp_path


def test_a_fragment_the_card_says_but_the_row_drops_is_quoted(tmp_path, monkeypatch):
    """C2_verdict #1: the ep11 regen. row_text drops the body's hair when the
    look restates a head layer; the card's own chapter words still say it."""
    got = tag(card_book(tmp_path, monkeypatch), "gunner", "the gunner",
              ["Thick straight black hair falling forward over the brow"], chapter=11)
    assert got == "the gunner (thick straight black hair falling forward over the brow)"


def test_a_fragment_neither_the_row_nor_the_card_says_still_refuses(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="the row does not say"):
        tag(card_book(tmp_path, monkeypatch), "gunner", "the gunner",
            ["clipped sandy moustache"], chapter=11)
