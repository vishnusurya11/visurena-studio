"""ep16 attempt 4 (2026-10-02): the grid prompt defined the brother as 'the
person in <image1>' AND its panel prose said 'the brother stands beside it' --
the drawer drew two brothers (shot 21), and each Elphinstone woman twice (22,
25).  The same double identity the take prompts lost on 2026-10-02 morning,
one module over.  A staged person's names in the panel prose become their
slot phrase; an unstaged person keeps their words."""
from __future__ import annotations

from studio.storyboard_grid import _unnamed


def test_staged_names_in_the_body_become_their_slot():
    cast = [{"name": "GEORGE", "display": "the brother", "ref": 1},
            {"name": "MISS ELPHINSTONE", "display": "Miss Elphinstone", "ref": 2},
            {"name": "MRS. ELPHINSTONE", "display": "Mrs. Elphinstone", "ref": None,
             "wear": "Wearing: White muslin dress."}]
    shots = [{"who": ["GEORGE", "MISS ELPHINSTONE"],
              "body": ("The brother stands beside the chaise; Miss Elphinstone sits inside it; "
                       "the brother's hand rests on the wheel; Mrs. Elphinstone sits beside her.")}]
    body = _unnamed(shots, cast)[0]["body"]
    assert "brother" not in body.lower() and "Miss Elphinstone" not in body
    assert body.count("the person in <image1>") == 2 and "the person in <image2>" in body
    assert "the person in <image1>'s hand" in body
    assert "Mrs. Elphinstone" in body                 # unstaged: keeps her words
