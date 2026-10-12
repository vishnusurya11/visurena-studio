"""A title's full stop does not end a sentence (Jekyll's Enfield, 2026-10-11).

Enfield's dossier: "The dossier provides no direct description of Mr. Enfield's
age, build, face, hair, clothing ...".  The sentence splitter cut after "Mr.",
so the negation stayed in the first half and the second half gave "hair,
clothing, or distinguishing physical features" to the hair layer: a head with
no colour that also blocked the bound row's "receding brown hair".
"""
from __future__ import annotations

from studio import head_author, look_table as lt

ENFIELD = ("The dossier provides no direct description of Mr. Enfield's age, build, face, hair, "
           "clothing, or distinguishing physical features. He walks with Utterson.")


def test_mr_dr_mrs_and_st_do_not_end_a_sentence():
    assert len(lt.parse("Mr. Hyde met Dr. Lanyon and Mrs. Poole in St. Giles. Then he left.")) == 2


def test_a_negated_list_after_a_title_names_no_hair():
    assert lt.layer_text(ENFIELD, "", "hair") == ""


def test_the_superseded_note_after_a_title_is_dropped():
    assert head_author.with_head(ENFIELD, "Brown hair; clean-shaven; a bowler hat.", old="") == \
        "He walks with Utterson. Brown hair; clean-shaven; a bowler hat."
