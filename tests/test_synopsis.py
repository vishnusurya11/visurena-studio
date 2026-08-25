"""Scene synopsis — 2-3 lines per scene, composed deterministically. No agent, no spend.

WHERE THIS BELONGS: analysis, not screenplay. Two reasons, and they are the stage
boundary itself. A synopsis ASSERTS what the book says; analysis asserts and screenplay
invents. And one analysis feeds many screenplay targets, so a summary computed in the
screenplay stage would be bought again for every target.
"""

from __future__ import annotations

from studio import synopsis

EVENTS = [
    {"type": "action", "summary": "Watson meets Stamford at the Criterion Bar."},
    {"type": "action", "summary": "Stamford mentions a man looking for a flatmate."},
    {"type": "action", "summary": "They drive to St Bartholomew's to find him."},
]
STATE = [{"character": "john_watson", "change": "learns of a possible lodging"}]


def test_synopsis_leads_with_the_scene_summary():
    text = synopsis.compose("Watson runs into an old dresser.", EVENTS, STATE)
    assert text.startswith("Watson runs into an old dresser.")


def test_synopsis_is_two_or_three_sentences():
    text = synopsis.compose("Watson runs into an old dresser.", EVENTS, STATE)
    assert 2 <= synopsis.sentence_count(text) <= 3


def test_synopsis_adds_events_the_summary_did_not_already_say():
    text = synopsis.compose("Watson runs into an old dresser.", EVENTS, [])
    assert "Criterion" in text or "flatmate" in text


def test_synopsis_does_not_repeat_the_summary_back():
    """The extraction summary and the first event often say the same thing."""
    events = [{"summary": "Watson runs into an old dresser."}, EVENTS[1]]
    text = synopsis.compose("Watson runs into an old dresser.", events, [])
    assert text.count("runs into an old dresser") == 1


def test_synopsis_survives_a_scene_with_no_events():
    text = synopsis.compose("The days passed without incident.", [], [])
    assert text == "The days passed without incident."


def test_synopsis_survives_a_scene_with_nothing_at_all():
    assert synopsis.compose("", [], []) == ""


def test_synopsis_closes_with_a_state_change_when_there_is_room():
    text = synopsis.compose("Watson is wounded at Maiwand.", [], STATE)
    assert "lodging" in text


def test_synopsis_prefers_events_over_state_changes_for_the_middle_line():
    text = synopsis.compose("Watson meets a friend.", EVENTS, STATE)
    assert synopsis.sentence_count(text) == 3 and "Criterion" in text


def test_every_sentence_ends_with_a_stop():
    text = synopsis.compose("Watson meets a friend", EVENTS, STATE)
    assert all(s.strip().endswith(".") for s in synopsis.sentences(text))


def test_synopsis_never_runs_away_on_a_scene_with_forty_events():
    events = [{"summary": f"Thing number {i} happens."} for i in range(40)]
    text = synopsis.compose("Much occurs.", events, [])
    assert synopsis.sentence_count(text) <= 3


def test_events_without_summaries_are_skipped_not_crashed_on():
    events = [{"type": "action"}, {"summary": None}, EVENTS[0]]
    assert "Criterion" in synopsis.compose("Watson arrives.", events, [])


def test_sentence_count_of_empty_text_is_zero():
    assert synopsis.sentence_count("") == 0


def test_a_multi_sentence_event_cannot_blow_the_cap():
    """Found on the real book: 4-sentence synopses. The loop counted ITEMS picked, but
    one event summary can itself be two sentences. The cap is on sentences."""
    events = [{"summary": "He crossed the room. He opened the case. He looked inside."}]
    text = synopsis.compose("Holmes arrives.", events, [])
    assert synopsis.sentence_count(text) <= 3


def test_a_long_event_is_trimmed_rather_than_dropped():
    events = [{"summary": "He crossed the room. He opened the case."}]
    text = synopsis.compose("Holmes arrives.", events, [])
    assert "crossed the room" in text


def test_every_real_scene_of_the_book_respects_the_cap():
    """The regression this came from, run against the artifact itself."""
    import json
    from pathlib import Path
    path = Path("library/20260822113400_a-study-in-scarlet/screenplay/dossier.json")
    if not path.exists():
        return
    scenes = json.loads(path.read_text(encoding="utf-8"))["scenes"]
    over = [s for s in scenes if synopsis.sentence_count(s["synopsis"]) > 3]
    assert not over, f"{len(over)} scene(s) over the cap, e.g. ch{over[0]['chapter']}"
