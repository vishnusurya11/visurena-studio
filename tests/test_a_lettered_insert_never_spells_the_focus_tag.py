"""A panel that stages print says its focus tag in lower case (Jekyll ep06 shot 19, retro 2026-10-30).

The insert asks for a packet "lettered in black ink" -- staged print, so the lettering gate expects type
(`panel_content.lettering_expected`).  The only capitals in the panel were the plan's scaffold, "THE FOCUS OF
THE PICTURE IS", and the drawer wrote them on the envelope: the public master shows it for five seconds.  Trial
on the real shot (1x1, four seeds an arm, read by eye): the tag in capitals lettered 4 of 4 envelopes, in lower
case 0 of 4 -- the cover takes illegible handwriting instead.  A panel that stages no print keeps the tag."""
from types import SimpleNamespace

from scripts.episode import grids
from studio import storyboard_grid as sg

TAG = "THE FOCUS OF THE PICTURE IS"
INSERT = SimpleNamespace(
    index=19, size="insert", faces=[], extras=0,
    frame="Insert on a second sealed packet lying on the green leather, its cover lettered in black ink.",
    at_rest=f"{TAG} the sealed inner packet at the CENTRE, black ink lettering across its cover.")
CLOSE = SimpleNamespace(
    index=20, size="close", faces=["gabriel_john_utterson"], extras=0,
    frame="Close on the man staring at the packet in the candlelight.",
    at_rest=f"{TAG} the man's gaunt face at the CENTRE, his head half the frame's height.")


def test_a_lettered_insert_says_its_focus_in_lower_case():
    body = grids.body_of(INSERT)
    assert TAG not in body and TAG.lower() in body


def test_the_edge_words_keep_their_capitals():
    assert "at the CENTRE" in grids.body_of(INSERT)


def test_a_panel_without_print_keeps_the_tag():
    assert TAG in grids.body_of(CLOSE)


def test_the_grid_still_reads_the_lower_case_focus():
    assert sg.FOCUS.search(grids.body_of(INSERT)).group(1).startswith("the sealed inner packet")
