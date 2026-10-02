"""ep16 shot 19 (2026-10-02): a WIDE naming only Miss Elphinstone came back
with FOUR of her -- the exact four poses of her character sheet (front,
three-quarter, profile, back).  The grid prompt bound <image1> to her
wardrobe and never said the sheet is ONE person seen from several angles,
so on open ground the drawer placed every view.  Each binding line now
states it, positively (the negation lint reads 'no' as noise)."""
from __future__ import annotations

from studio.storyboard_grid import _binding


def test_a_binding_says_the_sheet_is_one_person_drawn_once():
    said = _binding({"ref": 1, "wear": "Wearing: Dark aubergine serge travelling costume."})
    assert "one person" in said and "exactly once" in said
    assert said.startswith("The person in <image1>")
