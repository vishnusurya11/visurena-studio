"""The story layer's text rules, added after episode 10 (docs/analysis/ep10_dq_synthesis.md B).

Six narration lines in ep10 reported a present character's speech (0 in ep07/ep09); the
protagonist was not in his own turn shot; "Jefferson Hope" was heard for the first time
in the series with no role beside the name; and nothing said where the episode question
was answered.  Every rule here is pure text -- no disk, no model -- so the gate in
`studio.plan_gates` and the report in `story_layer.report` share one mechanism."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from studio import story_layer as sl
from studio.episode_spec import Episode, Line, Setup, Shot


def a_shot(index: int, faces: list[str], text: str = "") -> Shot:
    return Shot(index=index, section="setup", setup="room", size="medium", faces=faces,
                frame=text or "Medium of the room", motion=text or "The camera pushes in; a; b")


# ---- reported speech ------------------------------------------------------------

def test_a_comma_he_said_is_reported_speech():
    assert sl.reported_speech("She should have a month, he said, and at the end of it her answer.") == "he"


def test_a_named_speaker_reports_as_the_lowercased_name_token():
    assert sl.reported_speech("The true believers had fed him, and Young said so.") == "young"
    assert sl.reported_speech("Her father heard him gladly. Lucy said very little at all.") == "lucy"


def test_free_indirect_speech_reports_by_its_modal():
    assert sl.reported_speech("There was a party leaving in the morning. He would send Hope word.") == "he"
    assert sl.reported_speech("If he knew the young man, he would be back at a speed to whip the telegraph.") == "he"


def test_plain_narration_reports_nobody():
    assert sl.reported_speech("Ferrier had never married, and had never said why. He had his daughter.") == ""
    assert sl.reported_speech("The man would be desperate, and it was as well to be ready.") == ""


def test_pronouns_are_read_off_the_plans_own_single_face_shots():
    shots = [a_shot(0, ["lucy_ferrier"], "Close on Lucy, her hair back; she bows her head"),
             a_shot(1, ["john_ferrier"], "Close on Ferrier; he lifts his chin; his hand"),
             a_shot(2, ["john_ferrier", "lucy_ferrier"], "she and he")]
    assert sl.pronouns(shots) == {"lucy_ferrier": "she", "john_ferrier": "he"}


def test_a_bare_pronoun_resolves_to_every_face_of_that_gender_on_the_shot():
    who = {"brigham_young": "he", "john_ferrier": "he", "lucy_ferrier": "she"}
    names = {"young": "brigham_young", "ferrier": "john_ferrier", "lucy": "lucy_ferrier"}
    assert sl.speakers_on("he", ["brigham_young", "john_ferrier"], who, names) == ["brigham_young", "john_ferrier"]
    assert sl.speakers_on("he", ["lucy_ferrier"], who, names) == []
    assert sl.speakers_on("young", ["brigham_young", "john_ferrier"], who, names) == ["brigham_young"]
    assert sl.speakers_on("young", ["john_ferrier"], who, names) == []


# ---- names and their first hearing ------------------------------------------------

def test_names_are_capitalised_runs_that_do_not_open_a_sentence():
    text = "Three weeks after Jefferson Hope rode for Nevada, John Ferrier heard his own gate click."
    assert sl.names_in(text) == ["Jefferson Hope", "Nevada", "John Ferrier"]


def test_a_single_capitalised_word_after_an_article_is_a_title_not_a_name():
    assert sl.names_in("It was Brigham Young himself, and a visit from the Prophet boded no man any good.") == ["Brigham Young"]
    assert sl.names_in("I am a free-born American, and too old to knuckle under.") == []
    assert sl.names_in("It were better you lay skeletons than defy the Holy Four.") == ["Holy Four"]


def test_a_first_hearing_without_a_role_noun_is_naked():
    lines = ["There was a thing in Utah that year.", "Three weeks after Jefferson Hope rode, the gate clicked.",
             "He would send Hope word."]
    assert sl.naked_names(lines, earlier=["The valley of Utah lay below."]) == [(1, "Jefferson Hope")]


def test_a_role_noun_beside_the_name_dresses_it():
    lines = ["Jefferson Hope, the young man who rode for Nevada, was three weeks gone."]
    assert sl.naked_names(lines, earlier=[]) == []
    assert sl.naked_names(["It was Brigham Young himself, the Prophet."], earlier=[]) == []


def test_a_name_heard_in_an_earlier_episode_needs_no_role():
    assert sl.naked_names(["Three weeks after Jefferson Hope rode away."], earlier=["Jefferson Hope rode west."]) == []


# ---- caption-lines --------------------------------------------------------------

def test_content_words_drop_stopwords_and_stem():
    assert sl.content_words("Ferrier heard his heavy step going away down the shingle.") == {
        "ferrier", "heard", "heavy", "step", "going", "away", "shingle"}


def test_overlap_is_the_share_of_the_lines_content_words_in_the_shots_text():
    line = "Ferrier heard his heavy step going away down the shingle."
    shot = "His back going away down the shingly path; the shingle turns under his heavy boots."
    assert sl.overlap(line, shot) == pytest.approx(4 / 7)
    assert sl.overlap("", shot) == 0.0


# ---- the answer -----------------------------------------------------------------

SETUPS = {"lab": Setup(described="a lab", cast=["a", "b"])}
NARR = "Then we walked on together down the long corridor and neither of us spoke a word."


def episode(**over) -> Episode:
    def shot(i, section="friction", size="wide", faces=(), beat=0.0, coda=0.0):
        return Shot(index=i, section=section, setup="lab", size=size, faces=list(faces),
                    frame="f", motion="m", beat_s=beat, coda_s=coda)
    shots = [shot(0, "hook", "medium_close", ["a"])]
    lines = [Line(index=0, kind="dialogue", speaker="a", shot=0,
                  text="You must not blame me if you do not get on with him at all.")]
    for k in range(24):
        shots.append(shot(k + 1, "turn" if k == 14 else "friction"))
        lines.append(Line(index=k + 1, kind="narration", speaker="b", text=NARR, shot=k + 1))
    shots[-1] = shot(shots[-1].index, beat=1.5)
    shots.append(shot(len(shots), "button", "close", ["c"]))
    lines.append(Line(index=len(lines), kind="dialogue", speaker="c", text="The question now is about blood.",
                      shot=shots[-1].index))
    shots.append(shot(len(shots), "answer", coda=3.0))
    data = dict(number=1, title="t", protagonist="b", setups=SETUPS, shots=shots, lines=lines)
    data.update(over)
    return Episode(**data)


def test_the_answer_is_optional_and_names_a_shot_or_a_line():
    assert episode().answer == ""
    assert episode(answer="shot 26").answer == "shot 26"
    assert episode(answer="line 25").answer == "line 25"


def test_an_answer_that_names_nothing_in_the_plan_is_refused():
    with pytest.raises(ValidationError, match="answer"):
        episode(answer="shot 99")
    with pytest.raises(ValidationError, match="answer"):
        episode(answer="somewhere in the middle")


def test_the_report_says_where_the_question_is_answered():
    ep = episode(answer="shot 26")
    says = sl.report("Today, can b walk?", ep.shots, answer=ep.answer)["says"]
    assert "answered at: shot 26" in says


def test_the_report_says_nowhere_and_does_not_refuse():
    out = sl.report("Today, can b walk?", episode().shots)
    assert "answered: nowhere" in out["says"] and out["answer"] == ""
