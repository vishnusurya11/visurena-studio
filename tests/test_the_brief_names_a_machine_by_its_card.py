"""ep17 (owner 2026-10-04: "dont say martian .. always define the characters in
detail .. we had character sheets before .. so use them").  The writer wrote
"a Martian wading" and put the creature row in `faces` on three sea shots; no
setup declared the fighting-machine, so its drawn sheet was never staged and
the drawer invented a humanoid.  The brief tells the writer: a drawn machine
or creature is named by its card's name and described, never by a bare word,
and the setup that shows it lists it in `props`.  $0: pure text."""
from __future__ import annotations

from studio import plan_brief


def test_the_brief_names_machines_by_their_card_and_declares_them():
    t = " ".join(plan_brief.PICTURE_RULES).lower()
    for must in ("never by a bare word", "card's name", "`props`"):
        assert must in t, must
