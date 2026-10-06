"""The twin reader's answer is parsed strictly or refused, never defaulted.

G-TWIN-PANEL: `parse_twins` raises `Unreadable` on a missing count, a count
that is not a number, or more distinct people than figures -- the same
raise-not-default rule `parse` learned when a malformed answer passed every
panel of ep07 as 'flat, 0 people, night'.  Canned strings only; no model runs.
"""
import json

import pytest

from studio import panel_content as pc

CLEAN = '{"figures": 2, "distinct": 1, "twins": ["woman in a grey shawl x2"]}'


def test_clean_json_is_read():
    t = pc.parse_twins(CLEAN)
    assert (t.figures, t.distinct, t.twins) == (2, 1, ["woman in a grey shawl x2"])


def test_the_workflows_array_wrapped_string_of_json_is_unwrapped():
    """`image_qwen3vl_caption` returns a JSON ARRAY whose one element is a
    STRING of JSON, the same wrapping `parse` already unwraps."""
    t = pc.parse_twins(json.dumps([CLEAN]))
    assert (t.figures, t.distinct) == (2, 1)


def test_prose_wrapped_json_is_read():
    t = pc.parse_twins('Sure! Here is the JSON you asked for: ' + CLEAN)
    assert (t.figures, t.distinct) == (2, 1)


def test_a_missing_distinct_is_refused():
    with pytest.raises(pc.Unreadable):
        pc.parse_twins('{"figures": 2, "twins": []}')


def test_figures_that_are_not_a_number_are_refused():
    with pytest.raises(pc.Unreadable):
        pc.parse_twins('{"figures": "two", "distinct": 1, "twins": []}')


def test_more_distinct_than_figures_is_refused():
    with pytest.raises(pc.Unreadable):
        pc.parse_twins('{"figures": 1, "distinct": 2, "twins": []}')


def test_twin_readable_mirrors_the_parser():
    assert pc.twin_readable(CLEAN)
    assert not pc.twin_readable('{"figures": 2, "twins": []}')
    assert not pc.twin_readable("no json at all")
