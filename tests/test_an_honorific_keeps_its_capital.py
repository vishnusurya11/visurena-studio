"""An honorific keeps its capital in the take prompt (Jekyll HEL ep01, 2026-10-14).

Shot 19's end "Mr. Enfield at the CENTRE, his open hand stretched toward the lawyer's
shoulder" lent the arrival its noun; `noun_phrase` lowered the first letter blind
("mr. Enfield"), the subject swap could no longer eat the title, and the block closed
"... continues through the last frame, with mr. <Subject 1> now in frame." -- the
sentence splitter cut after "mr." and L21 ARRIVAL refused the take: its last sentence
"<Subject 1> now in frame." names nothing that moves.
"""
from __future__ import annotations

import pytest

from studio import episode_ref_official as ro


@pytest.mark.parametrize("title", ["Mr.", "Mrs.", "Dr.", "Miss", "Sir", "Inspector", "Lady", "Lord"])
def test_an_honorific_lead_is_not_lowered(title):
    assert ro.noun_phrase(f"{title} Enfield at the CENTRE").startswith(title)


def test_a_common_lead_is_still_lowered():
    assert ro.noun_phrase("The lawyer at the CENTRE").startswith("the lawyer")


def test_a_sentence_does_not_end_on_a_title():
    body = "By 00:07 the action continues through the last frame, with Mr. Enfield now in frame."
    assert len(ro.sentences(body)) == 1
    assert len(ro.sentences("He walks. The door opens.")) == 2
