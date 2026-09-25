"""The audio-first contract: lines name their shots, shots derive their seconds."""
import pytest
from pydantic import ValidationError

from studio import episode_timeline as tl
from studio.episode_spec import Episode, Line, Setup, Shot, SubShot

SETUPS = {"lab": Setup(described="a lab", cast=["a", "b"])}
NARR = ("Then we walked on together down the long corridor and neither of us spoke "
        "a word.")  # 17 words


def shot(i, section="friction", size="wide", faces=(), beat=0.0, coda=0.0):
    return Shot(index=i, section=section, setup="lab", size=size, faces=list(faces),
                frame="f", motion="m", beat_s=beat, coda_s=coda)


def episode(n_narration=24):
    """Hook dialogue, narration cutaways, a turn, a button with a beat before it, a coda."""
    shots = [shot(0, "hook", "medium_close", ["a"])]
    lines = [Line(index=0, kind="dialogue", speaker="a", shot=0,
                  text="You must not blame me if you do not get on with him at all.")]
    for k in range(n_narration):
        section = "turn" if k == int(n_narration * 0.62) else "friction"
        shots.append(shot(k + 1, section))
        lines.append(Line(index=k + 1, kind="narration", speaker="b", text=NARR, shot=k + 1))
    shots[-1] = shot(shots[-1].index, beat=1.5)
    shots.append(shot(len(shots), "button", "close", ["c"]))
    lines.append(Line(index=len(lines), kind="dialogue", speaker="c",
                      text="The question now is about blood.", shot=shots[-1].index))
    shots.append(shot(len(shots), "answer", coda=3.0))
    return Episode(number=1, title="t", protagonist="b", setups=SETUPS, shots=shots, lines=lines)


class TestTheShape:
    def test_a_sound_plan_validates_and_projects_inside_the_band(self):
        assert 120 <= episode().projected_seconds() <= 180

    def test_the_last_line_is_the_button_and_not_the_lead(self):
        ep = episode()
        last = ep.lines[-1]
        ep.lines[-1] = Line(index=last.index, kind="dialogue", speaker="b", text="What?", shot=last.shot)
        ep.shots[last.shot] = shot(last.shot, "button", "close", ["b"])
        with pytest.raises(ValidationError, match="is the protagonist's"):
            Episode(**ep.model_dump())

    def test_a_shot_with_no_line_and_no_beat_is_a_hole(self):
        ep = episode()
        data = ep.model_dump()
        data["shots"].insert(5, shot(99).model_dump())
        for k, s in enumerate(data["shots"]):
            s["index"] = k
        for l in data["lines"]:
            if l["shot"] >= 5:
                l["shot"] += 1
        with pytest.raises(ValidationError, match="a hole"):
            Episode(**data)

    def test_the_shot_before_the_button_names_a_beat(self):
        ep = episode()
        data = ep.model_dump()
        data["shots"][ep.lines[-1].shot - 1]["beat_s"] = 0.0
        with pytest.raises(ValidationError, match="beat of >= 1.0"):
            Episode(**data)


class TestDialogueOnCamera:
    def test_a_dialogue_line_needs_the_speakers_readable_face(self):
        data = episode().model_dump()
        data["shots"][0] = shot(0, "hook", "wide", []).model_dump()
        with pytest.raises(ValidationError, match="lips are driven"):
            Episode(**data)

    def test_the_dialogue_dial(self):
        with pytest.raises(ValidationError):
            episode(n_narration=2)


class TestTheTimeline:
    def test_shot_seconds_come_from_the_measured_lines(self):
        ep = episode()
        placed = tl.place(ep, {line.index: 3.0 for line in ep.lines})
        assert placed["shots"][0]["seconds"] == 0.25 + 3.0 + 0.25
        assert placed["lines"][0]["at"] == 0.25
        assert placed["shots"][-1]["seconds"] == 0.5 + 3.0
        assert placed["duration_s"] == round(sum(s["seconds"] for s in placed["shots"]), 3)

    def test_lanes_follow_the_line_kind(self):
        ep = episode()
        placed = tl.place(ep, {line.index: 2.0 for line in ep.lines})
        assert placed["shots"][0]["lane"] == "dialogue" and placed["shots"][1]["lane"] == "narration"

    def test_holes_are_found_between_placed_lines(self):
        placed = {"lines": [{"at": 0.0, "seconds": 2.0}, {"at": 5.0, "seconds": 1.0},
                            {"at": 6.5, "seconds": 1.0}]}
        assert tl.holes(placed) == [(2.0, 5.0)]


def test_every_shot_lands_on_a_whole_frame():
    ep = episode()
    placed = tl.place(ep, {line.index: 3.137 for line in ep.lines})
    for shot in placed["shots"]:
        assert abs(shot["seconds"] * 24 - round(shot["seconds"] * 24)) < 1e-3
        assert abs(shot["t_start"] * 24 - round(shot["t_start"] * 24)) < 1e-3


def test_the_sync_rule_holds_for_a_placed_timeline_and_catches_a_shifted_line():
    ep = episode()
    placed = tl.place(ep, {line.index: 2.0 for line in ep.lines})
    assert tl.misaligned(placed) == []
    placed["lines"][0]["at"] += 0.1
    assert any("does not start one handle" in f for f in tl.misaligned(placed))


def test_a_frame_that_puts_a_glove_on_anyone_is_refused():
    """Iteration 2 drew Watson's handshake in a tan leather glove because the
    frame text asked for one; the book gives him a bare sunburnt hand."""
    with pytest.raises(ValidationError, match="glove"):
        Shot(index=1, section="friction", setup="lab", size="insert", frame="two hands, one in a tan glove",
             motion="m")
    with pytest.raises(ValidationError, match="glove"):
        Shot(index=1, section="friction", setup="lab", size="insert", frame="f", motion="m",
             cuts=[SubShot(at_s=3.0, size="close", frame="a gloved hand", motion="m")])


class TestWhatTheStoryboardDraws:
    """The fields the sheet prompt is compiled from (owner, 2026-09-11).  Each one
    exists because the drawer got the previous form wrong, and each one says what
    IS: a negated noun is still that noun in the prompt."""

    def test_the_picture_fields_default_empty_so_a_plan_written_before_them_still_validates(self):
        shot = Shot(index=0, section="hook", setup="lab", size="wide", frame="f", motion="m")
        assert (shot.camera, shot.at_rest, shot.end, shot.changed, shot.crowd) == ("", "", "", "", "")
        cut = SubShot(at_s=3.0, size="close", frame="f", motion="m")
        assert (cut.camera, cut.at_rest, cut.end, cut.changed, cut.crowd) == ("", "", "", "", "")

    def test_a_setup_carries_its_geometry_its_crowd_its_sky_and_its_prop_plates(self):
        bare = Setup(described="a lab")
        assert (bare.geometry, bare.crowd, bare.outdoors, bare.props) == ("", "", False, [])
        street = Setup(described="a street", geometry="The wheel fills the LEFT third.",
                       crowd="four pedestrians under umbrellas", outdoors=True, props=["cab"])
        assert street.outdoors and street.props == ["cab"]

    def test_a_picture_field_that_asks_for_an_absence_is_refused(self):
        """"no gloves" in a character description reached six sheets and drew a
        glove; the drawer can only put nouns in places."""
        with pytest.raises(ValidationError, match="absence"):
            Shot(index=0, section="hook", setup="lab", size="wide", frame="f", motion="m",
                 at_rest="his hand is not yet on the glass")
        with pytest.raises(ValidationError, match="absence"):
            Setup(described="a lab with no windows")

    def test_a_named_change_without_the_end_picture_it_changes_into_is_refused(self):
        """"Changed since panel 1" is only checkable against a written end picture."""
        with pytest.raises(ValidationError, match="write the end picture"):
            Shot(index=0, section="hook", setup="lab", size="wide", frame="f", motion="m",
                 changed="the glass reaches his mouth")
        Shot(index=0, section="hook", setup="lab", size="wide", frame="f", motion="m",
             end="The glass rests at his lips.", changed="the glass reaches his mouth")
