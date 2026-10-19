"""Step 06 lints a take prompt as the render will build it (Jekyll Kawajiri ep01, 2026-10-18).

Step 06 (`takes_r2v --prompts`) runs before step 08 draws a single panel, so every take was
built panel-less and judged on the references band (240-360 words a block): T05, T16, T24
and T26 refused at 227-234.  The plan's dry build (`dry_prompt`) and the render both build
with the storyboard panel staged, on the panel band (150-360).  In the prompt pass a take
whose panel the board will draw is built as the dry build is: panel staged, no picture count."""
from __future__ import annotations

from scripts.episode import takes_r2v as tr
from studio import refs_only


def test_the_prompt_pass_expects_the_boards_panel(tmp_path, monkeypatch):
    monkeypatch.setattr(tr, "PANEL_AHEAD", True)
    monkeypatch.setattr(refs_only, "read", lambda home: set())
    assert tr.panel_ahead(tmp_path, 1, 5, None) is True


def test_a_drawn_panel_is_not_ahead(tmp_path, monkeypatch):
    monkeypatch.setattr(tr, "PANEL_AHEAD", True)
    assert tr.panel_ahead(tmp_path, 1, 5, tmp_path / "shot_05.png") is False


def test_a_refs_only_shot_never_expects_a_panel(tmp_path, monkeypatch):
    monkeypatch.setattr(tr, "PANEL_AHEAD", True)
    monkeypatch.setattr(refs_only, "read", lambda home: {5})
    assert tr.panel_ahead(tmp_path, 1, 5, None) is False


def test_the_render_never_builds_ahead(tmp_path, monkeypatch):
    monkeypatch.setattr(tr, "PANEL_AHEAD", False)
    monkeypatch.setattr(refs_only, "read", lambda home: set())
    assert tr.panel_ahead(tmp_path, 1, 5, None) is False


def test_the_prompt_pass_turns_it_on(monkeypatch):
    seen = {}
    monkeypatch.setattr(tr, "PANEL_AHEAD", False)
    monkeypatch.setattr(tr, "opened", lambda b, n: (_ for _ in ()).throw(RuntimeError("stop")))
    try:
        tr.prompts("book", 1)
    except RuntimeError:
        seen["ahead"] = tr.PANEL_AHEAD
    assert seen["ahead"] is True


def test_every_clause_after_the_line_drops_as_he_speaks():
    """T22/T23: the second post-line clause rode the 'seconds ran out' join with its
    'as he speaks' (P8 line ended yet speaking)."""
    from studio import episode_ref_official as ro
    motion = ("The camera holds a locked-off frame across the whole shot; the lawyer turns his face toward "
              "the RIGHT edge; his brows draw down; his hand lifts to his coat front as he speaks.")
    said = " ".join(ro.beat_sentences(motion, 0, 5, line_end=4))
    assert "as he speaks" not in said and "his hand lifts to his coat front" in said


def test_a_childs_epithet_binds_its_bare_noun():
    """T07: the plan tagged 'the fallen girl (...)' once and said 'the girl' and 'the child'
    bare; the staged <Subject 2> was never cited (P4)."""
    from studio import cast_alias
    rows = {"child_of_hyde_incident": "Fair hair in two plaits, plain grey pinafore dress",
            "edward_hyde": "Coarse black hair, wideawake hat"}
    table = cast_alias.aliases(["the fallen girl (Fair hair in two plaits, plain grey pinafore dress) runs"], rows)
    assert {"the fallen girl", "the girl"} <= set(table["child_of_hyde_incident"])
    assert "the child" not in table["child_of_hyde_incident"]   # a mention of 'the child' elsewhere stages nobody (P13)


def test_a_mans_epithet_is_never_shortened():
    from studio import cast_alias
    rows = {"edward_hyde": "Coarse black hair, wideawake hat"}
    table = cast_alias.aliases(["the small man (Coarse black hair, wideawake hat) stumps"], rows)
    assert table["edward_hyde"] == ["the small man"]
