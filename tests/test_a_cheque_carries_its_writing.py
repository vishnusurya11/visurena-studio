"""A cheque is print by what it is (Jekyll ep01 v2 T10, 2026-10-15): the insert of
the little man's hand holding out "gold coins and a folded cheque" is the book's own
prop, signed with another man's name -- its writing is the point of the chapter.
The content gate called it "text or lettering in the picture" and the take shipped
flagged.  A wide still never excuses it."""
from __future__ import annotations

from studio import panel_content

T10 = ("Insert of the knuckly hand of the little man holding out gold coins and a "
       "folded cheque to the hand of Mr. Enfield before the door step")


def test_an_insert_on_a_cheque_expects_its_writing():
    assert panel_content.lettering_expected(T10, "insert")


def test_cheques_plural_too():
    assert panel_content.lettering_expected("Close on two signed cheques on the desk", "close")


def test_a_wide_with_a_cheque_in_it_still_refuses_lettering():
    assert not panel_content.lettering_expected("Wide of the bank hall, a clerk holding a cheque", "wide")


def test_a_checked_waistcoat_is_not_a_cheque():
    assert not panel_content.lettering_expected("Close on his checked waistcoat", "close")
