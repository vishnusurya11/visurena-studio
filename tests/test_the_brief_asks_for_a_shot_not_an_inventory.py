"""ep16 (2026-10-03): the brief told the writer "each shot's `frame` names its
edges", the writer obeyed, and every ep14-16 frame became an inventory --
'Left edge holds ...; centre holds ...' -- with no subject, no action, no
lens and no light; 0/26 frames opened with a size against 23/23 in the
hand-authored era.  The brief now asks for the good-era shot: size first, one
subject and its action, a lens and the light's side, ONE named focus, one
move with an amount, at most two faces, crowds only on wides."""
from __future__ import annotations

from studio import plan_brief


def text():
    return " ".join(plan_brief.PICTURE_RULES)


def test_the_brief_never_asks_frame_for_its_edges():
    assert "names its edges" not in text()


def test_the_brief_asks_for_the_good_era_shot():
    t = text().lower()
    for must in ("size first", "lens", "focus", "at most two faces", "only on wide"):
        assert must in t, must
