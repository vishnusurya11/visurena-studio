"""INT/EXT is half of every slugline, and it arrived in eight flavours.

Audit 2026-08-25, measured across A Study in Scarlet's 92 scenes:

    INT 49 · EXT 19 · UNKNOWN 16 · INT/EXT 3 · INT / EXT 2 ·
    EXT / UNKNOWN 1 · EXT/INT 1 · EXT / INT 1

The cause is one line of the scene_breakdown skill: `int_ext: INT / EXT / UNKNOWN`.
It uses " / " as a MENU SEPARATOR for a field whose legal values THEMSELVES contain a
slash — INT/EXT is a real screenplay term. The notation collided with the vocabulary,
so the agent read it as an invitation to combine, and produced combinations.

The field was also dropped entirely by step 03's remap, so nothing downstream could
even see the damage.
"""

from __future__ import annotations

import pytest

from scripts.analysis import step_03_standardize as s03
from studio import screenformat as sf


@pytest.mark.parametrize("raw, want", [
    ("INT", "INT"),
    ("EXT", "EXT"),
    ("int", "INT"),
    ("  ext  ", "EXT"),
    ("INT/EXT", "INT/EXT"),
    ("INT / EXT", "INT/EXT"),          # the spaced form the skill's notation invited
    ("EXT/INT", "INT/EXT"),            # order is not meaningful
    ("EXT / INT", "INT/EXT"),
    ("I/E", "INT/EXT"),                # the industry's own abbreviation
    ("INTERIOR", "INT"),
    ("EXTERIOR", "EXT"),
])
def test_the_eight_observed_forms_normalize(raw, want):
    assert sf.normalize_int_ext(raw) == want


@pytest.mark.parametrize("raw", ["UNKNOWN", "", None, "EXT / UNKNOWN", "nonsense"])
def test_an_unusable_value_becomes_unknown(raw):
    """A slugline cannot be written from these. Saying UNKNOWN keeps that visible
    rather than guessing INT and being wrong half the time."""
    assert sf.normalize_int_ext(raw) == "UNKNOWN"


def test_a_partial_pair_does_not_silently_become_a_pair():
    """'EXT / UNKNOWN' is one known half and one unknown half — not INT/EXT."""
    assert sf.normalize_int_ext("EXT / UNKNOWN") == "UNKNOWN"


# --- it has to survive the remap to be worth anything ------------------------------

def _extraction(int_ext):
    return [{"chapter": 1, "scenes": [{
        "n": 1, "type": "scene", "int_ext": int_ext, "location_text": "the room",
        "time_of_day": "DAY", "summary": "s", "characters": [], "time_evidence": [],
        "state_changes": [], "para_start": 1, "para_end": 2}]}]


REGISTRY = {"characters": [], "locations": [{"id": "room", "name": "the room",
                                             "aliases": []}]}


def test_remap_carries_int_ext_through_normalized():
    scenes = s03.remap_scenes(_extraction("INT / EXT"), REGISTRY)
    assert scenes[0]["int_ext"] == "INT/EXT"


def test_remap_defaults_a_missing_int_ext_to_unknown():
    ex = _extraction("INT")
    del ex[0]["scenes"][0]["int_ext"]
    assert s03.remap_scenes(ex, REGISTRY)[0]["int_ext"] == "UNKNOWN"
