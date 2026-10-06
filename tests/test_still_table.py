"""The shared stillness substitution table (G-ROWTEXT / L2 cures): one ordered
regex table in studio/row_lint, applied to plan fields and to row texts alike,
so 'revolver held at her lap' can never ride a cast row into every take of an
episode.  Idempotent, $0, and measured by the lint's own STILL regex."""
from __future__ import annotations

from studio import episode_ref_official as ro
from studio import plan_cures as pc
from studio import row_lint


def test_held_at_becomes_resting_at():
    assert row_lint.cure_row_text("a revolver held at her lap") == "a revolver resting at her lap"


def test_holds_her_fire_becomes_her_guns_silent():
    out = row_lint.cure_row_text("she holds her fire")
    assert "guns silent" in out


def test_every_cured_output_is_clean_under_the_lints_own_still_regex():
    rows = ("a revolver held at her lap", "she holds her fire", "he holds the reins",
            "a scarf held in one hand", "she remains by the gate", "he stays close",
            "he waits by the door", "a coat held loosely")
    for row in rows:
        cured = row_lint.cure_row_text(row)
        assert not ro.STILL.search(cured), (row, cured)


def test_the_table_is_idempotent():
    for row in ("a revolver held at her lap", "she holds her fire", "he remains still"):
        once = row_lint.cure_row_text(row)
        assert row_lint.cure_row_text(once) == once, row


def test_a_pace_is_appended_to_a_row_gait():
    out = row_lint.cure_row_text("she walks with a straight back")
    assert any(p in out.lower() for p in ro.PACE)


def test_motionless_is_cured_only_in_the_at_rest_field():
    doc = {"shots": [{"index": 0, "frame": "A man motionless at the rail.",
                      "at_rest": "He sits motionless at the rail.", "motion": "", "end": ""}],
           "setups": {}}
    out = pc.stillness_words(doc)
    assert "motionless" not in out["shots"][0]["at_rest"]
    assert "at rest" in out["shots"][0]["at_rest"]
    assert "motionless" in out["shots"][0]["frame"]      # the frame's word is the llm cure's


def test_stillness_words_covers_setups_and_cuts():
    doc = {"shots": [{"index": 0, "frame": "", "at_rest": "", "motion": "", "end": "",
                      "cuts": [{"frame": "His hand held at the brim.", "motion": "", "at_rest": "", "end": ""}]}],
           "setups": {"bar": {"described": "A tray held in the crook of an arm.", "crowd": "", "geometry": ""}}}
    out = pc.stillness_words(doc)
    assert "held" not in out["shots"][0]["cuts"][0]["frame"]
    assert "held" not in out["setups"]["bar"]["described"]
    assert not ro.STILL.search(out["setups"]["bar"]["described"])
