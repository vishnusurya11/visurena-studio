"""Writing the trailer's page from the book: inputs in, a script out.

No test calls a paid API -- the model is injected as a fake and what is tested
is the CONTRACT: what the drafter shows the model, what it refuses to accept
back, and that the page it writes is one the pipeline can build.
"""
from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from studio import trailer_draft as draft
from studio.trailer_script import ScriptBeat, TrailerScript

CAST = {"sherlock_holmes": "Sherlock Holmes", "john_watson": "John Watson",
        "jefferson_hope": "Jefferson Hope"}
LINES = [
    {"text": "You have been in Afghanistan, I perceive.", "speaker": "sherlock_holmes",
     "function": "hook", "kept": True, "scene": 2},
    {"text": "Rache, revenge.", "speaker": "sherlock_holmes", "function": "hook",
     "kept": False, "scene": 5},
    {"text": "Choose and eat.", "speaker": "jefferson_hope", "function": "threat",
     "kept": False, "scene": 11},
    {"text": "Police Inspector speaks here.", "speaker": "Police Inspector",
     "function": "stakes", "kept": False, "scene": 9},
]
SCENES = [{"number": 2, "summary": "Watson meets Holmes at Bart's"},
          {"number": 5, "summary": "The word RACHE on the wall"},
          {"number": 11, "summary": "Hope offers the pills"}]
STORY = {"lead": "sherlock_holmes", "figure": "jefferson_hope", "turn_scene": 11,
         "register": "detective", "setting": "1881 London", "narrator": "john_watson"}


def a_page() -> TrailerScript:
    beats = ([ScriptBeat(id=f"B{i:02d}", movement="M1", function="question", seconds=3.0,
                         see="a gloved hand in blood", why="the crime without the body")
              for i in range(5)]
             + [ScriptBeat(id=f"B{10 + i:02d}", movement="M2", function="escalation",
                           seconds=3.0, see="fog and wheels", why="the pursuit")
                for i in range(9)]
             + [ScriptBeat(id=f"B{30 + i:02d}", movement="M3", function="escalation",
                           seconds=3.0, see="the arrest", why="the answer") for i in range(4)]
             + [ScriptBeat(id="B40", movement="M3", function="title", seconds=3.0,
                           card="A STUDY IN SCARLET", why="the logo on the hit"),
                ScriptBeat(id="B41", movement="M3", function="button", seconds=3.0,
                           card="EPISODE 1 OUT NOW", why="the next action")])
    return TrailerScript(title="A Study in Scarlet", runtime=60.0, beats=beats,
                         genre="detective mystery", kind="series teaser")


def fake_model(pages: list, asked: list):
    """A caller that records the prompt and returns canned pages in order."""
    def structured(tier, prompt, schema, **kw):
        asked.append(prompt)
        return pages[min(len(asked) - 1, len(pages) - 1)]
    return structured


class TestWhatTheModelIsShown:
    def test_the_brief_carries_the_material_the_page_must_be_built_from(self):
        """A page may only ask for what the pipeline can render.  The whole
        counter-case against writing a trailer in advance is that it specifies
        shots nobody can deliver -- so the brief IS the inventory: the cast that
        has sheets, the scenes, and the lines that were actually found."""
        brief = draft.brief(STORY, SCENES, LINES, CAST, genre="detective mystery",
                            title="A Study in Scarlet")
        assert "sherlock_holmes" in brief and "Sherlock Holmes" in brief
        assert "You have been in Afghanistan, I perceive." in brief
        assert "The word RACHE on the wall" in brief
        assert "60" in brief and "9:16" in brief

    def test_the_brief_names_the_book_by_its_title_not_its_setting(self):
        """The first draft's title card read "1881 LONDON" because the brief
        passed story.setting as the book's name.  The title is what the card
        holds and what the viewer is being sold."""
        brief = draft.brief(STORY, SCENES, LINES, CAST, genre="detective mystery",
                            title="A Study in Scarlet")
        assert "A Study in Scarlet" in brief
        assert "'A STUDY IN SCARLET' on screen as a CARD" in brief   # the card holds the TITLE
        assert "1881 LONDON' on screen" not in brief                 # not the setting

    def test_the_brief_budgets_the_speech_and_the_runtime(self):
        """The first draft ran 72% of its length with someone speaking, against
        the ~41-45% real trailers measure, and came in at 52 s against a 60 s
        format.  Both were unstated, so both drifted."""
        brief = draft.brief(STORY, SCENES, LINES, CAST, genre="detective mystery",
                            title="A Study in Scarlet")
        assert "45%" in brief or "45 %" in brief
        assert "60" in brief and "seconds in total" in brief

    def test_the_brief_names_the_genre_and_the_move_that_genre_makes(self):
        """The genre decides the TYPE, and the type decides what the trailer
        withholds: mystery withholds the answer, horror the creature."""
        brief = draft.brief(STORY, SCENES, LINES, CAST, genre="detective mystery",
                            title="A Study in Scarlet")
        assert "withhold" in brief.lower()
        assert draft.genre_note("detective mystery") != draft.genre_note("gothic horror")

    def test_a_line_nobody_in_the_cast_can_speak_is_never_offered(self):
        """Run 19 slated a line spoken by "Police Inspector", who has no cast
        card, and the trailer spoke 4 of 5.  The page cannot choose it if the
        brief never shows it."""
        brief = draft.brief(STORY, SCENES, LINES, CAST, genre="detective mystery",
                            title="A Study in Scarlet")
        assert "Police Inspector" not in brief


class TestWhatComesBack:
    def test_a_valid_page_is_written_to_both_files(self, tmp_path):
        asked = []
        out = draft.write(tmp_path, STORY, SCENES, LINES, CAST, genre="detective mystery",
                          model=fake_model([a_page()], asked))
        assert len(asked) == 1
        assert out.seconds == pytest.approx(60.0, abs=0.5)
        page = json.loads((tmp_path / "trailer_script.json").read_text(encoding="utf-8"))
        assert page["beats"][0]["id"] == "B00" and page["aspect"] == "9:16"
        assert "ACT I" in (tmp_path / "trailer_script.txt").read_text(encoding="utf-8")

    def test_a_refused_page_is_asked_again_with_the_refusal_quoted_back(self, tmp_path):
        """The contract refuses a page that talks too much or misses its act
        shares -- but the refusal happens inside the model's own parse, so the
        model never hears it.  Quote it back and ask again, the way every other
        ladder in this repo does.  MEASURED: two Scarlet drafts came back at
        72% and 68% speech, and asking nicely in the brief moved neither."""
        asked = []

        def model(tier, prompt, schema, **kw):
            asked.append(prompt)
            if len(asked) == 1:
                raise ValidationError.from_exception_data(
                    "TrailerScript",
                    [{"type": "value_error", "loc": (), "input": {},
                      "ctx": {"error": "the page speaks for 68% of its runtime"}}])
            return a_page()

        out = draft.write(tmp_path, STORY, SCENES, LINES, CAST, genre="detective mystery",
                          model=model, title="A Study in Scarlet")
        assert len(asked) == 2
        assert "68% of its runtime" in asked[1] and "refused" in asked[1].lower()
        assert out.seconds == pytest.approx(60.0, abs=0.5)

    def test_a_page_that_will_not_come_back_valid_raises(self, tmp_path):
        def always_bad(tier, prompt, schema, **kw):
            raise ValidationError.from_exception_data(
                "TrailerScript", [{"type": "value_error", "loc": (), "input": {},
                                   "ctx": {"error": "still too talky"}}])
        with pytest.raises(ValidationError):
            draft.write(tmp_path, STORY, SCENES, LINES, CAST, genre="detective mystery",
                        model=always_bad, title="A Study in Scarlet")

    def test_a_page_that_speaks_a_line_the_book_never_wrote_is_refused(self, tmp_path):
        """The model may choose lines; it may not invent them.  Every spoken
        line must be one the finder actually found in the text."""
        invented = a_page()
        beats = list(invented.beats)
        beats[1] = beats[1].model_copy(update={"line": "Elementary, my dear Watson.",
                                               "speaker": "sherlock_holmes"})
        with pytest.raises(draft.NotInTheBook, match="Elementary"):
            draft.write(tmp_path, STORY, SCENES, LINES, CAST, genre="detective mystery",
                        model=fake_model([invented.model_copy(update={"beats": beats})], []))

    def test_a_page_that_casts_a_speaker_with_no_sheet_is_refused(self, tmp_path):
        page = a_page()
        beats = list(page.beats)
        beats[1] = beats[1].model_copy(update={"line": "Choose and eat.",
                                               "speaker": "irene_adler"})
        with pytest.raises(draft.NotInTheBook, match="irene_adler"):
            draft.write(tmp_path, STORY, SCENES, LINES, CAST, genre="detective mystery",
                        model=fake_model([page.model_copy(update={"beats": beats})], []))
