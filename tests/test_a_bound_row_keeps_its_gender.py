"""A cast row without a gender is refused at BIND, not after the plan.

Jekyll ep01 (2026-10-12): all eight rows were rebuilt bare -- no display, no
gender -- and the episode wrote a two-hour plan before takes_r2v refused the
first row at G-TAKELINT.  The row writer (`pack_refs.rows_for`) now keeps every
identity field a rebuild cannot know, and refuses a bound row with no gender,
every one at once, in the first minute."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from studio import pack_refs


def dossier(book: Path, who: str) -> None:
    folder = book / "analysis" / "characters"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{who}.json").write_text(
        json.dumps({"name": who.title(), "profile": {"physical": "A lean man of fifty."}}),
        encoding="utf-8")


def test_a_rebuild_keeps_every_identity_field_of_the_old_row(tmp_path):
    dossier(tmp_path, "jekyll")
    old = [{"entity_id": "jekyll", "kind": "character", "display": "Dr Jekyll", "gender": "male",
            "pronouns": "he/him", "aka": ["Harry"], "physical": "Old words."}]
    row = pack_refs.rows_for(tmp_path, 1, ["jekyll"], old)[0]
    assert (row["display"], row["gender"], row["pronouns"], row["aka"]) == \
        ("Dr Jekyll", "male", "he/him", ["Harry"])


def test_a_named_display_without_a_gender_never_drops_the_old_gender(tmp_path):
    dossier(tmp_path, "utterson")
    old = [{"entity_id": "utterson", "kind": "character", "display": "Utterson", "gender": "male"}]
    row = pack_refs.rows_for(tmp_path, 1, ["utterson"], old, {"utterson": ("Mr Utterson", "")})[0]
    assert row["display"] == "Mr Utterson" and row["gender"] == "male"


def test_bind_refuses_every_cast_row_with_no_gender_at_once(tmp_path):
    for who in ("jekyll", "utterson", "poole"):
        dossier(tmp_path, who)
    with pytest.raises(SystemExit) as refused:
        pack_refs.rows_for(tmp_path, 1, ["jekyll", "utterson", "poole"], [],
                           {"poole": ("Poole", "male")})
    said = str(refused.value)
    assert "G-ROWGENDER" in said and "jekyll" in said and "utterson" in said
    assert "poole" not in said


def test_a_bare_row_outside_the_cast_is_not_this_binds_fault(tmp_path):
    dossier(tmp_path, "jekyll")
    bare = {"entity_id": "hyde", "kind": "character", "physical": "A small man."}
    rows = pack_refs.rows_for(tmp_path, 1, ["jekyll"], [bare], {"jekyll": ("Jekyll", "male")})
    assert bare in rows
