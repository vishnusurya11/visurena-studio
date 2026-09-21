"""A staged storyboard panel IS the room, so the plate stops being needed.

MEASURED 2026-09-21 on ep06 T17 and T21, which failed both the pinned and the
unpinned render with a hard cut at frame 8 of 132. The frames say what
happened: the take opens on the LOCATION PLATE -- the road with the burning
beeches and the lit cottage -- holds it for a third of a second, and hard-cuts
into its own shot.

The repo already knows this fault. `test_refs_only_drops_the_plate_on_a_tight_take`
records ep14's T21 opening on the room and hard-cutting into the shot at frame
14, and ep02's 13-of-14 foreign frames being the take's own plate. The reason
the plate was staged anyway was that a take with only a FACE invented a room:
"a room that opens at the wrong size is a fixable framing fault; a room that is
the wrong room is a continuity break."

That reason is spent. A references-only take now stages a storyboard panel:
the same location, at the same hour, in the same style, framed for this shot.
It cannot invent the wrong room because the right room is staged. Keeping the
plate beside it stages the room TWICE and gives the model a second whole
picture to open on -- which is the fault, exactly.

So: panel staged -> no plate. No panel -> ep14's rule stands untouched.
"""
from __future__ import annotations

import sys

sys.path.insert(0, "scripts/episode")

import takes_r2v as tr


def test_a_refs_only_take_with_a_panel_drops_the_plate():
    assert tr.staged_facts(["wide"], from_refs=True, panel=True)["has_plate"] is False


def test_a_refs_only_take_without_a_panel_keeps_it():
    """ep14's rule, untouched: with no panel the plate is the only room."""
    assert tr.staged_facts(["insert"], from_refs=True, panel=False)["has_plate"] is True


def test_a_panel_take_still_stages_no_cells():
    assert tr.staged_facts(["wide"], from_refs=True, panel=True)["cells_staged"] is False


def test_the_normal_path_is_unchanged_by_the_panel():
    """Episodes already built must be told exactly what they were told before."""
    for panel in (True, False):
        said = tr.staged_facts(["wide", "insert"], from_refs=False, panel=panel)
        assert said == {"has_plate": True}
        assert tr.staged_facts(["insert"], from_refs=False, panel=panel) == {"has_plate": False}


def test_the_default_keeps_the_old_answer():
    """Called the way every existing caller calls it, nothing moves."""
    assert tr.staged_facts(["wide"], from_refs=True)["has_plate"] is True
