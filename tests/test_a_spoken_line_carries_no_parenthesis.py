"""ep16 (2026-10-02): six narration lines read "the brother (grey eyes) ..."
and the narrator SAID "the brother Gray Eyes" -- QC heard the words it was
told to expect, because the fault was in the script itself.  Spoken text never
carries a parenthesis: the contract refuses it before anything is recorded."""
from __future__ import annotations

import pytest

from studio.episode_spec import Line


def line(text):
    return Line(index=0, kind="narration", speaker="narrator", text=text, shot=0)


def test_a_parenthesis_in_spoken_text_is_refused():
    with pytest.raises(ValueError, match="parenthes"):
        line("The brother (grey eyes) keeps watch.")


def test_plain_text_is_fine():
    assert line("The brother keeps watch.").text == "The brother keeps watch."
