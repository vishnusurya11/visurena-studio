"""Every beat as a shot H3 can render, bound to sheets that exist."""
from __future__ import annotations

import json

import pytest

from studio import trailer_shots as shots
from studio.trailer_script import ScriptBeat, TrailerScript

REFS = {"palette": "Muted soot-black and gaslight amber, 1881 London, fog and deep shadow",
        "refs": [
            {"ref_id": "char-sherlock_holmes", "kind": "character", "name": "Sherlock Holmes",
             "physical": "A lean man in his late twenties, over six feet, pale, hawk-nosed"},
            {"ref_id": "char-john_watson", "kind": "character", "name": "Dr. John Watson",
             "physical": "A man in his late twenties, sun-browned, dark hair swept back"},
            {"ref_id": "loc-221b_baker_street", "kind": "location", "name": "221B",
             "physical": "A cluttered first-floor sitting room, bow window, gaslight"}]}


def a_page() -> TrailerScript:
    beats = ([ScriptBeat(id=f"B{i:02d}", movement="M1", function="question", seconds=3.0,
                         see="blood on plaster", why="the crime") for i in range(5)]
             + [ScriptBeat(id=f"B{10 + i:02d}", movement="M2", function="escalation",
                           seconds=3.0, see="fog", why="the hunt") for i in range(9)]
             + [ScriptBeat(id=f"B{30 + i:02d}", movement="M3", function="escalation",
                           seconds=3.0, see="the arrest", why="the answer") for i in range(4)]
             + [ScriptBeat(id="B40", movement="M3", function="title", seconds=3.0,
                           card="A STUDY IN SCARLET", why="the logo"),
                ScriptBeat(id="B41", movement="M3", function="button", seconds=3.0,
                           card="EPISODE 1 OUT NOW", why="the next action")])
    return TrailerScript(title="A Study in Scarlet", runtime=60.0, beats=beats,
                         genre="detective mystery")


def a_shot(beat_id: str, **kw) -> shots.Shot:
    fields = {"place": "loc-221b_baker_street", "character": "char-sherlock_holmes",
              "action": "He crosses to the window and looks down into the street.",
              "open_framing": "A wide of the room, the window bright behind him.",
              "close_framing": "A tight profile, gaslight raking one cheek.",
              "camera": "A slow push in from the doorway to the window."}
    fields.update(kw)
    return shots.Shot(beat_id=beat_id, **fields)


def a_list(page: TrailerScript, **kw) -> shots.ShotList:
    return shots.ShotList(shots=[a_shot(b.id, **kw) for b in page.beats])


class TestTheBrief:
    def test_it_shows_the_page_and_only_the_sheets_that_exist(self):
        text = shots.brief(a_page(), REFS)
        assert "char-sherlock_holmes" in text and "loc-221b_baker_street" in text
        assert "B00" in text and "the crime" in text
        assert "char-irene_adler" not in text

    def test_it_asks_for_a_vertical_composition(self):
        """9:16 is the default frame, and the top and bottom of it are covered
        by platform interface -- so the subject has to sit in the centre band."""
        text = shots.brief(a_page(), REFS)
        assert "9:16" in text and "centre band" in text


class TestWhatComesBack:
    def test_a_shot_naming_a_sheet_the_book_lacks_is_refused(self):
        page = a_page()
        bad = a_list(page)
        bad.shots[2].character = "char-irene_adler"
        with pytest.raises(shots.NoSuchRef, match="irene_adler"):
            shots.check(bad, page, shots.sheets(REFS))

    def test_a_refused_shot_list_is_asked_again_with_the_refusal_quoted_back(self, tmp_path):
        """MEASURED on the first real run: the model set a shot in a constable's
        face -- char-john_rance -- who has an analysis card but no BOUND sheet,
        because step 02 binds only the cast the trailer needs.  The refusal
        names the missing sheet and the list is asked again."""
        page = a_page()
        asked = []

        def model(tier, prompt, schema, **kw):
            asked.append(prompt)
            if len(asked) == 1:
                bad = a_list(page)
                bad.shots[2].character = "char-john_rance"
                return bad
            return a_list(page)

        shots.write(tmp_path, page, REFS, model=model)
        assert len(asked) == 2
        assert "char-john_rance" in asked[1] and "refused" in asked[1].lower()

    def test_a_shot_list_that_skips_a_beat_is_refused(self):
        page = a_page()
        short = shots.ShotList(shots=[a_shot(b.id) for b in page.beats[:-1]])
        with pytest.raises(shots.NoSuchRef, match="every beat"):
            shots.check(short, page, shots.sheets(REFS))

    def test_each_prompt_is_the_six_section_ref2v_document(self, tmp_path):
        page = a_page()
        shots.write(tmp_path, page, REFS, model=lambda *a, **k: a_list(page))
        found = json.loads((tmp_path / "shot_prompts.json").read_text(encoding="utf-8"))
        assert len(found["shots"]) == len(page.beats) and found["aspect"] == "9:16"
        prompt = found["shots"][0]["prompt"]
        for section in ("subject_definitions", "summary", "retention_analysis",
                        "detailed_description", "overall_soundscape", "non_diegetic_music"):
            assert f"{section}:" in prompt
        assert "<Subject 1>" in prompt and "fully_preserved" in prompt
        assert "hawk-nosed" in prompt            # the sheet's own words reach the prompt
        assert "gaslight amber" in prompt        # and so does the book's palette

    def test_the_readable_file_names_who_is_in_each_shot(self, tmp_path):
        page = a_page()
        shots.write(tmp_path, page, REFS, model=lambda *a, **k: a_list(page))
        text = (tmp_path / "shot_prompts.txt").read_text(encoding="utf-8")
        assert "B00  3.0s  [char-sherlock_holmes @ loc-221b_baker_street]" in text
