"""A possessive in a row's NAME is not a name.

MEASURED on episode 13's plan (2026-09-17): the row named "a wife of Drebber's"
gave the token "drebber's" to the map, and that token was claimed by nobody
else -- so "Enoch Drebber's coarse florid face" named HER, and the marks gate
reported the wife wearing Brigham Young's sandy hair on a close of Drebber.
The possessive belongs to the same claim as the bare name, and "drebber" is
claimed by more than one row, so it identifies nobody.
"""
from studio.episode_spec import name_map


def rows(*names):
    return [{"kind": "character", "entity_id": eid, "name": name} for eid, name in names]


def test_a_possessive_token_is_the_bare_name():
    got = name_map(rows(("drebber_wife", "a wife of Drebber's"), ("enoch_j_drebber", "Enoch J. Drebber"),
                        ("enoch_drebber_young", "Enoch Drebber")))
    assert "drebber's" not in got
    assert "drebber" not in got


def test_a_name_without_a_possessive_is_unchanged():
    got = name_map(rows(("jefferson_hope", "Jefferson Hope"), ("cowper", "Cowper")))
    assert got.get("cowper") == "cowper" and got.get("jefferson") == "jefferson_hope"
