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
    assert got == ("the narrator, neat close-trimmed dark brown moustache, "
                   "mid-grey herringbone tweed lounge suit")


def test_a_fragment_the_row_does_not_say_refuses_the_plan(tmp_path):
    with pytest.raises(ValueError, match="clipped sandy moustache"):
        tag(book(tmp_path), "narrator", "the narrator", ["clipped sandy moustache", "grey tweed"])


def test_matching_ignores_case_and_punctuation_but_not_words(tmp_path):
    b = book(tmp_path)
    assert tag(b, "narrator", "the narrator", ["Neat close-trimmed dark brown moustache"])
    with pytest.raises(ValueError):
        tag(b, "narrator", "the narrator", ["neat dark moustache"])
